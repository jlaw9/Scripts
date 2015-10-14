from varman2.mongotools import config_mongo, hotspot_mongo, variants_mongo, sampleinfo_mongo, mongo
from varman2.bashcommands import bash
from varman2 import Logger
import os, csv
import genotypetools
import sys

class Output:
    def __init__(self):
        self.project_config = config_mongo.get_project_config()
        self.logger = Logger.get_logger()

        self.output_files_dir = '%s/output_files' % self.project_config['output_dir']
        if 'output_files_dir' not in self.project_config or not os.path.isdir(self.project_config['output_files_dir']):
            bash.make_dir(self.output_files_dir)
            config_mongo.change_config_field('output_files_dir', self.output_files_dir)
        else:
            self.output_files_dir = self.project_config['output_files_dir']

    def hotspot_stats(self):
        outfile = open(self.output_files_dir+"/hotspot_stats.csv", 'w')

        header = ['CHROM', 'POS', 'REF', 'ALT', 'RSID', 'cosmic68', 'Gene',
                  'ExonicFunc', 'AAChange', 'Orig_Total', 'Orig_QC_Pass', 'Hotspot_Total', 'Hotspot_QC_Pass',
                  'Assumed_Orig_WT', 'Hotspot_WT', 'Orig_Het', 'Hotspot_Het', 'Orig_Hom',
                  'Hotspot_Hom', 'Orig_Het_Alt', 'Hotspot_Het_Alt', 'Hotspot_NoCalls']
        outfile.write("\t".join(header)+"\n")

        for var in hotspot_mongo.get_final_hotspot_vars():
            new_variant = {}
            new_variant.update({'CHROM': var['CHROM'], 'POS': var['POS'], 'REF': var['REF'],
                                'ALT': ",".join(var['ALT'])})
            annot = var['ANNOTATION'][0]

            new_variant.update({'RSID': annot['snp137NonFlagged'], 'cosmic68': annot['cosmic68'],
                                'Gene': annot['Gene_refGene'], 'ExonicFunc': annot['ExonicFunc_refGene'],
                                'AAChange': annot['AAChange_refGene']})
            if 'p.' in new_variant['AAChange']:
                    new_variant['AAChange'] = new_variant['AAChange'].split('p.')[1].split(",")[0]

            orig = var['orig_stats']
            hotspot = var['hotspot_stats']
            total_samples = hotspot['qc']['total_count']
            new_variant.update({'Orig_Total': orig['qc']['total_count'],
                                'Orig_QC_Pass': orig['qc']['final_qc_count'],
                                'Hotspot_Total': hotspot['qc']['total_count'],
                                'Hotspot_QC_Pass': hotspot['qc']['final_qc_count'],
                                'Assumed_Orig_WT': total_samples - sum([orig['zygosity']['het_count'],
                                                                        orig['zygosity']['het_alt_count'],
                                                                        orig['zygosity']['hom_count'],
                                                                        orig['zygosity']['nocall_count']]),
                                'Hotspot_WT': hotspot['zygosity']['wt_count'],
                                'Hotspot_NoCalls': hotspot['zygosity']['nocall_count'],
                                'Orig_Het': orig['zygosity']['het_count'],
                                'Hotspot_Het': hotspot['zygosity']['het_count'],
                                'Orig_Het_Alt': orig['zygosity']['het_alt_count'],
                                'Hotspot_Het_Alt': hotspot['zygosity']['het_alt_count'],
                                'Orig_Hom': orig['zygosity']['hom_count'],
                                'Hotspot_Hom': hotspot['zygosity']['hom_count'],
                                })

            out_row = [str(new_variant[field]) for field in header]
            outfile.write("\t".join(out_row)+"\n")

    def sample_variants_csv(self, sample, type):
        if not sampleinfo_mongo.is_sample(sample) or not variants_mongo.is_sample_loaded(sample, type):
            self.__log_sample_doesnt_exist()
            return

        out_path = "%s/%s.csv" % ( self.output_files_dir, sample)
        print out_path
        csv_writer = csv.writer(open(out_path, "w"), delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

        header = ['CHROM', 'POS', 'REF', 'ALT', 'GT', 'RSID', 'Gene',
                  'ExonicFunc', 'AAChange', 'FREQ', 'QC_Final', 'QC_Cov', 'QC_AF', 'In_Hotspot']
        csv_writer.writerow(header)

        client, db = mongo.get_connection()
        total_loaded_samples = variants_mongo.count_samples()

        for var in variants_mongo.get_sample_vars(sample, type, db):
            new_variant = {}
            chrom, pos, ref, alt = var['CHROM'], var['POS'], var['REF'], var['ALT']
            al1, al2 = genotypetools.get_genotype_alleles(ref, alt, var['GT_calc'])
            new_variant.update({'CHROM': chrom, 'POS': pos, 'REF': ref, 'ALT': ",".join(alt),
                                'GT': "/".join([al1, al2])})

            hotspot = hotspot_mongo.get_variant(chrom, pos, ref, alt, db)

            annot = hotspot['ANNOTATION'][0]

            new_variant.update({'RSID': annot['snp137NonFlagged'],
                                'Gene': annot['Gene_refGene'], 'ExonicFunc': annot['ExonicFunc_refGene'],
                                'AAChange': annot['AAChange_refGene']})
            if 'p.' in new_variant['AAChange']:
                    new_variant['AAChange'] = new_variant['AAChange'].split('p.')[1].split(",")[0]

            zygosity = hotspot['orig_stats']['zygosity']
            freq = sum([zygosity['het_count'], zygosity['het_alt_count'], zygosity['hom_count']]) / float(total_loaded_samples)
            final_qc, qc_cov, qc_af = var['FINAL_QC'], var['COV_QC'], var['AF_QC']

            if hotspot['orig_stats']['qc']['final_qc_count'] > 0:
                in_hotspot = "TRUE"
            else:
                in_hotspot = "FALSE"

            new_variant.update({"FREQ": freq, "QC_Final": final_qc, "QC_Cov": qc_cov, "QC_AF": qc_af,
                                "In_Hotspot": in_hotspot})

            out_row = [str(new_variant[field]) for field in header]
            csv_writer.writerow(out_row)
            #print "\t".join(out_row)

        return out_path

    def output_all_variants(self):

        out_path = "%s/%s.csv" % ( self.output_files_dir, "all_variants")

        csv_writer = csv.writer(open(out_path, "w"), delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

        header = ['CHROM', 'POS', 'REF', 'ALT', 'GT', 'RSID', 'Gene',
                      'ExonicFunc', 'AAChange', 'FREQ', 'QC_Final', 'QC_Cov', 'QC_AF', 'In_Hotspot']
        csv_writer.writerow(header)

        for sample in sampleinfo_mongo.get_samples():

            client, db = mongo.get_connection()
            total_loaded_samples = variants_mongo.count_samples()

            for var in variants_mongo.get_sample_vars(sample, 'orig', db):
                new_variant = {}
                chrom, pos, ref, alt = var['CHROM'], var['POS'], var['REF'], var['ALT']
                al1, al2 = genotypetools.get_genotype_alleles(ref, alt, var['GT_calc'])
                new_variant.update({'CHROM': chrom, 'POS': pos, 'REF': ref, 'ALT': ",".join(alt),
                                    'GT': "/".join([al1, al2])})

                hotspot = hotspot_mongo.get_variant(chrom, pos, ref, alt, db)

                annot = hotspot['ANNOTATION'][0]

                new_variant.update({'RSID': annot['snp137NonFlagged'],
                                    'Gene': annot['Gene_refGene'], 'ExonicFunc': annot['ExonicFunc_refGene'],
                                    'AAChange': annot['AAChange_refGene']})
                if 'p.' in new_variant['AAChange']:
                        new_variant['AAChange'] = new_variant['AAChange'].split('p.')[1].split(",")[0]

                zygosity = hotspot['orig_stats']['zygosity']
                freq = sum([zygosity['het_count'], zygosity['het_alt_count'], zygosity['hom_count']]) / float(total_loaded_samples)
                final_qc, qc_cov, qc_af = var['FINAL_QC'], var['COV_QC'], var['AF_QC']

                if hotspot['orig_stats']['qc']['final_qc_count'] > 0:
                    in_hotspot = "TRUE"
                else:
                    in_hotspot = "FALSE"

                new_variant.update({"FREQ": freq, "QC_Final": final_qc, "QC_Cov": qc_cov, "QC_AF": qc_af,
                                    "In_Hotspot": in_hotspot})

                out_row = [str(new_variant[field]) for field in header]
                csv_writer.writerow(out_row)
                #print "\t".join(out_row)

        return out_path

    def __log_performing_annotation(self):
        self.logger.info('Performing annotation of hotspot file using annovar.')

    def __log_already_annotated(self):
        self.logger.info('There is already an annotation file in the hotspot folder. Please delete it to reannotate.')

    def __log_saving_annotations(self):
        self.logger.info('Saving the annotations to the database')

    def __log_sample_doesnt_exist(self):
        self.logger.error('The sample you specified does not exist in the database.')

