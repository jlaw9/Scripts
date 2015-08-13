#! /usr/bin/env python2.7
__author__ = 'durrantmm'

import os
import glob
from multiprocessing import Process
from bash_commands import BashCommands
from mongo_tools import MongoTools


class AnnotateTools:
    def __init__(self, project_config, mongodb, logger):
        self.project_config = project_config
        self.mongodb = mongodb
        self.logger = logger

    def annotate_variants(self, num_processors):
        self.mongodb.open_connection()

        other_files_dir = self.project_config['output_dir'] + "/other_files"

        if not os.path.isdir(other_files_dir): BashCommands.make_dir(other_files_dir)
        self.logger.info("Writing unique variants to annovar input vcf")

        project_name = self.project_config['project_name']

        # PROCESS THE FILE IN CHUNKS, USING MULTIPLE PROCESSORS
        self.process_in_chunks(project_name, num_processors, other_files_dir)

        new_vcf_files = glob.glob(other_files_dir + "/*.vcf")
        out_path = other_files_dir + "/annovar"
        BashCommands.remove_dir(out_path)
        BashCommands.make_dir(out_path)

        self.logger.info("Annotating all the vcf files")
        jobs = []
        for vcf_file in new_vcf_files:
            annot_basename = os.path.basename(vcf_file)
            out_file = out_path + "/" + annot_basename
            p = Process(target=BashCommands.annotate_annovar, args=(vcf_file, out_file))
            jobs.append(p)
            p.start()

        for j in jobs:
            j.join()

        annotation_files = glob.glob(out_path + "/*multianno.vcf")

        self.mongodb.change_info_field(self.project_config['project_name'], 'annotation_path', out_path, self.logger)

        for annot_file in annotation_files:
            self.mongodb.load_annovar_vcf_to_db(annot_file, self.project_config['project_name'])

        self.mongodb.close_connection()

        return annotation_files

    def process_in_chunks(self, project_name, num_processors, other_files_dir):

        var_count = self.mongodb.count_project_vars(project_name)

        # SPLITTING THE VARIANTS INTO THE NUMBER OF PROCESSORS TO USE
        var_chunk_size = var_count / num_processors
        jobs = []
        skip_count = 0

        for var_chunk_num in range(num_processors):

            # INITIATE THE DATABASE CONNECTION TO HANDLE THE PROCESS
            tmp_mongo = MongoTools(self.project_config)

            # BEGIN THE PROCESS
            if (var_chunk_num + 1) == num_processors:
                var_chunk_size = var_count - skip_count

            self.logger.debug("PROCESS NUM: %s, SKIP COUNT: %s, VAR_CHUNK_SIZE: %s" %
                              (var_chunk_num + 1, skip_count, var_chunk_size))

            p = Process(target=tmp_mongo.write_unique_vars_vcf, args=(other_files_dir, project_name,
                                                                  skip_count, var_chunk_size, var_chunk_num + 1))
            jobs.append(p)
            p.start()

            skip_count += var_chunk_size

        self.logger.debug("Waiting for processes to complete")
        for j in jobs:
            j.join()