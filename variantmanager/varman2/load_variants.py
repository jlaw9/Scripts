#! /usr/bin/env python2.7

# Goal: Now that all of the variants from all files that successsfully ran annovar.

import sys
import os
import vcf
from varman2.mongotools import config_mongo, sampleinfo_mongo, variants_mongo, hotspot_mongo, mongo
from varman2 import Logger
from QC import QC
import genotypetools
from glob import glob

from bashcommands import bash, hotspot_bash
from multiprocessing import Process

# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------

class LoadVariants:

    def __init__(self, var_type):
        self.project_config = config_mongo.get_project_config()
        self.logger = Logger.get_logger()
        self.variant_type = var_type
        self.affected_dict = sampleinfo_mongo.get_affected_dict()

    def load_all(self):

        if self.variant_type == 'orig':
            client, db = mongo.get_connection()

            vcf_files = sampleinfo_mongo.get_vcf_files()

            # CHECK IF THE VCFS ARE ALL VALID BEFORE STARTING
            for sample in vcf_files:
                vcf_file = vcf_files[sample]
                if not os.path.isfile(vcf_file):
                    self.__log_invalid_vcf_file(vcf_file)
                    sys.exit(1)


            pending_vcf_files = []
            for sample in vcf_files:

                vcf_file = vcf_files[sample]

                is_loaded = variants_mongo.is_sample_loaded(sample, self.variant_type, db)
                if is_loaded:
                    self.__log_sample_already_loaded(sample)
                    continue
                else:
                    self.__log_adding_sample_to_queue(sample, vcf_file)
                    pending_vcf_files.append((sample, vcf_file))

            client.close()

        elif self.variant_type == 'hotspot':
            pending_vcf_files = self.__get_unsaved_hotspot_vcf_files()

        num_processors = 10
        self.__parallel_process_vcf_files(pending_vcf_files, num_processors)

        self.__log_successfully_loaded()

    def load_single(self, sample):

        variants_mongo.index_variants()
        vcf_files = sampleinfo_mongo.get_vcf_files()

        vcf_file = vcf_files[sample]
        self.__load_sample_variants(sample, vcf_file)

        self.__log_single_successfully_loaded(sample)

    def __parallel_process_vcf_files(self, vcf_files, num_processors):

        client, db = mongo.get_connection()
        variants_mongo.drop_variants_index(db)
        hotspot_mongo.index_hotspot(db)

        jobs = set()
        while len(vcf_files) > 0:
            args = vcf_files.pop(0)
            sample = args[0]
            vcf_file = args[1]

            p = Process(target=self.__load_sample_variants, args=(sample, vcf_file))
            jobs.add(p)
            p.start()

            if len(jobs) == num_processors:
                for j in jobs:
                    j.join()
                jobs.clear()

        variants_mongo.index_variants(db)
        client.close()

    def __get_unsaved_hotspot_vcf_files(self):
        hotspot_dir = self.project_config['hotspot_dir']

        output_dir = hotspot_dir + "/hotspot_output"

        vcf_files = glob(output_dir+"/*.vcf")

        final_vcf_files = []

        client, db = mongo.get_connection()
        for vcf_file in vcf_files:
            sample = os.path.basename(vcf_file).split(".")[0]

            if sampleinfo_mongo.is_sample(sample, db) and not \
                    variants_mongo.is_sample_loaded(sample, self.variant_type, db):
                self.__log_adding_hotspot_sample_to_queue(sample, vcf_file)
                final_vcf_files.append((sample, vcf_file))
            else:
                self.__log_hotspot_sample_already_loaded(sample)

        client.close()

        return final_vcf_files

    def __load_sample_variants(self, sample, vcf_file):
        self.__log_loading_new_sample(sample, vcf_file)

        vcf_reader = vcf.Reader(open(vcf_file, 'r'))

        client, db = mongo.get_connection()
        for record in vcf_reader:
            variant_doc = self.get_variant_doc(record, sample, vcf_file)

            variants_mongo.add_variant(variant_doc, db)

            if self.variant_type == 'orig':
                hotspot_mongo.add_variant(variant_doc, db)
            elif self.variant_type == 'hotspot':
                hotspot_mongo.add_hotspot_variant(variant_doc, db)

        client.close()

    def get_variant_doc(self, record, sample, vcf_file):

        if len(record.samples) > 1:
            self.__log_multisample_vcf(sample, vcf_file)
        else:
            call = record.samples[0]

            new_var_entry = {}
            new_var_entry.update({"SAMPLE": sample})
            try:
                new_var_entry.update({"AFFECTED": int(self.affected_dict[sample])})
            except TypeError:
                new_var_entry.update({"AFFECTED": self.affected_dict[sample]})
            new_var_entry.update({"CHROM": record.CHROM})

            # GET THE CHROMOSOME NUMBER
            if "X" in new_var_entry['CHROM']:
                new_var_entry['CHROM'] = 23
            elif "Y" in new_var_entry['CHROM']:
                new_var_entry['CHROM'] = 24
            else:
                new_var_entry['CHROM'] = int(new_var_entry['CHROM'].strip("chr"))

            # GET POSITION, ID, REFERENCE ALLELE, and ALTERNATE ALLELE
            new_var_entry.update({"POS": record.POS})
            new_var_entry.update({"ID": record.ID})
            new_var_entry.update({"REF": record.REF})
            new_var_entry.update({"ALT": [str(alt) for alt in record.ALT]})
            new_var_entry.update({"FILTER": record.FILTER})
            new_var_entry.update({'GT_orig': record.samples[0]['GT']})

            # Calculate the alternate read frequency from fao and fro
            fao, fro, af, gt, read_depth = genotypetools.calculate_gt(record, call)
            new_var_entry.update({"FAO": fao, "FRO": fro, "AF_calc": af, "GT_calc": gt, "READ_DEPTH": read_depth})

            # Perform Quality Control Calculations
            quality_checker = QC()
            coverage_check, af_check, multi_allele_check, final_qc = quality_checker.variant_QC(new_var_entry)
            new_var_entry.update({'COV_QC': coverage_check, 'AF_QC': af_check,
                                  'MULTI_ALLELE_QC': multi_allele_check, 'FINAL_QC': final_qc})

            # Set the type of variant uploaded
            new_var_entry.update({'TYPE': self.variant_type})

        return new_var_entry

    def __log_sample_already_loaded(self, sample):
        self.logger.debug('Variants have already been loaded from sample %s' % (sample))

    def __log_adding_sample_to_queue(self, sample, vcf_file):
        self.logger.info('Found unloaded sample %s in file %s. Adding to queue.' % (sample, vcf_file))

    def __log_loading_new_sample(self, sample, vcf_file):
        self.logger.info('Loading variants of sample %s from file %s' % (sample, vcf_file))

    def __log_multisample_vcf(self, sample, vcf_file):
        self.logger.info('The vcf for sample %s at the location %s was found to have more than one sample.'
                         'Please correct this vcf file.' % (sample, vcf_file))
        sys.exit()

    def __log_successfully_loaded(self):
        self.logger.info('All variants were successfully loaded from the specified vcf files')

    def __log_single_successfully_loaded(self, sample):
        self.logger.info('Variants successfully loaded for %s.' % sample)

    def __log_hotspot_sample_already_loaded(self, sample):
        self.logger.debug('Hotspot variants have already been loaded from sample %s' % sample)

    def __log_adding_hotspot_sample_to_queue(self, sample, vcf_file):
        self.logger.info('Found unloaded hotspot sample %s in file %s. Adding to queue.' % (sample, vcf_file))

    def __log_invalid_vcf_file(self, vcf_file):
        self.logger.info('A vcf file that was submitted is not valid: %s' % vcf_file)



