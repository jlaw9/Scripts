from glob import glob
from varman2.mongotools import config_mongo, annotate_mongo, mongo, sampleinfo_mongo
from bashcommands import annovar_bash, bash
from varman2 import Logger
import os
from varman2 import misctools, vcftools

class Annotate:
    def __init__(self):
        """
        This init method is different in that it will create the annotation_dir config parameter if it doesn't
        already exist. This is not necessarily the most elegant way to do this, but it works.
        :return:
        """
        self.project_config = config_mongo.get_project_config()
        self.logger = Logger.get_logger()

        # Creates the annotation_dir if needed and loads it into the config file
        self.annotations_dir = '%s/annotations' % self.project_config['output_dir']
        if 'annotation_dir' not in self.project_config or not\
                os.path.isdir(self.project_config['annotation_dir']):
            bash.make_dir(self.annotations_dir)
            config_mongo.change_config_field('annotation_dir', self.annotations_dir)
        else:
            self.annotations_dir = self.project_config['annotation_dir']

    def annotate_hotspot(self, annov_in):
        self.__log_performing_annotation()

        annovar_output = glob('%s/*multianno.vcf' % os.path.dirname(annov_in))
        if len(annovar_output) > 0:
            self.__log_already_annotated()
        else:
            annovar_bash.annotate_annovar(annov_in, annov_in)
            annovar_output = glob('%s/*multianno.vcf' % os.path.dirname(annov_in))[0]

        return annovar_output

    def annotate_sample(self, sample, type):
        """
        This will annotate a sample and load it into the database.

        :param sample: This is the name of the snmple to be annotated.
        :type sample: str
        :param type: This is the type of the sample to be annotated, either hotspot or orig.
        :type type: str
        :return:
        """

        # This creates a vcf for annotation based on the sample and returns the vcf path.
        vcf_path = vcftools.create_vcf_for_annotation(sample, type, self.annotations_dir)

        self.__log_performing_sample_annotation()

        # annotates the file, saves the annotations to the mongodb, and changes status of the sample in the
        # sample info collection to "FULLY ANNOTATED"
        annovar_output = annovar_bash.annotate_annovar(vcf_path, vcf_path)
        self.save_annotations(annovar_output)
        sampleinfo_mongo.change_sample_field(sample, "FULLY_ANNOTATED", True)

    def save_annotations(self, annovar_vcf):
        """
        This will save the annotations of a sample in the database.
        :param annovar_vcf:
        :return:
        """
        self.__log_saving_annotations()

        self.project_config = config_mongo.get_project_config()

        client, db = mongo.get_connection()

        with open(annovar_vcf, "r") as annov_in:
            line = annov_in.readline()
            if not line.startswith("#CHROM"):

                while line.startswith('##'):  # this reads through the junk lines
                    line = annov_in.readline()
                header = line.strip().strip("#").split("\t")

                for line in annov_in:

                    chrom, pos, ref, alt, annotations = self.__process_annovar_line(line, header)
                    annotate_mongo.save_annotation(chrom, pos, ref, alt, annotations, db)

        client.close()

    def __process_annovar_line(self, line, header):
        """
        This is what processes a vcf line to extract the information of interest.

        :param line: This is the line to process.
        :param header: This is the vcf header to use to query fields.
        :return:
        """
        line = line.strip().split("\t")
        line = {header[n]: line[n] for n in range(len(line))}

        info = line['INFO']
        info = info.split("ALLELE_END")
        info = [misctools.remove_empty_elements(value.split(";")) for value in info]
        info = misctools.remove_empty_elements(info)
        annotations = [dict([(info[i][j].split("=")[0].replace('.', '_'), info[i][j].split("=")[1]) for j in range(len(info[i])) if
                      "=" in info[i][j]]) for i in range(len(info))]

        for i in range(len(annotations)):
            annotations[i] = {key: annotations[i][key] for key in annotations[i]
                                  if key not in ['OID', 'OPOS', 'OREF', 'OALT', 'OMAPALT']}

        annotations = [dict([(key, set(annotations[i][key].split("\\x3b")).pop()) for key in annotations[i]])
                       for i in range(len(annotations))]

        chrom, pos, ref, alt = int(line['CHROM'].strip("chr")), int(line['POS']), line['REF'], line['ALT'].split(",")

        return chrom, pos, ref, alt, annotations

    def __log_performing_annotation(self):
        self.logger.info('Performing annotation of hotspot file using annovar.')

    def __log_performing_sample_annotation(self):
        self.logger.info('Annotating the sample file for output')

    def __log_already_annotated(self):
        self.logger.info('There is already an annotation file in the hotspot folder. Please delete it to reannotate.')

    def __log_saving_annotations(self):
        self.logger.info('Saving the annotations to the database')



