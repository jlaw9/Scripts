#! /usr/bin/env python2.7

# Goal: Now that all of the variants from all files that successsfully ran annovar.

import os
from pymongo import MongoClient, ASCENDING
import glob
import vcf
from models import VariantCall
from multiprocessing import Process
from misc_tools import MiscTools

# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------

class LoadVariants:

    def __init__(self, project_config, mongodb, logger):
        self.project_config = project_config
        self.logger = logger
        self.mongodb = mongodb
        self.cpu_number = 1

    def load(self, cpu_number):
        self.cpu_number = cpu_number

        self.__load()

    def __load(self):

        ## CHECK TO SEE IF COLLECTION ALREADY HAS DOCUMENTS IN IT
        client = MongoClient()
        db = client['varman']
        proj_collection = db[self.project_config['project_name']]

        if proj_collection.count() > 0:
            self.logger.info("VCF collection already exists with project name, skipping variant loading")
            client.close()

        ## BEGIN LOADING THE VARIANTS

        else:

            vcf_files = self.mongodb.get_vcf_files(self.project_config['project_name'])

            vcf_file_chunks = MiscTools.split_list_to_chunks(vcf_files, self.cpu_number)

            jobs = []
            for i in range(self.cpu_number):
                p = Process(target=self.load_vcf_files, args=([vcf_file_chunks[i]]))
                jobs.append(p)
                p.start()

            for j in jobs:
                j.join()

            self.mongodb.open_connection()
            self.logger.info("Total Variants Loaded to database: " +
                             str(self.mongodb.count_project_vars(self.project_config['project_name'])))

            self.logger.info("Sorting and Indexing the new variant collection.")
            index = [("CHROM", ASCENDING), ("POS", ASCENDING)]
            self.mongodb.create_index(index, self.project_config['project_name'])

            self.mongodb.close_connection()

    def load_vcf_files(self, vcf_files):
        client = MongoClient()
        db = client['varman']
        proj_collection = db[self.project_config['project_name']]

        count = 0
        ENTRY_BATCH = []
        for vcf_file in vcf_files:
            vcf_reader = vcf.Reader(open(vcf_file[1], 'r'))
            self.logger.info("LOADING VARIANTS FROM VCF: " + vcf_file[1])
            for rec in vcf_reader:

                var_call = VariantCall(rec)
                sample_name = vcf_file[0]
                new_entries = var_call.get_new_variant_calls(sample_name)

                for entry in new_entries:
                    ENTRY_BATCH.append(entry)
                    count += 1

                    if count % 50000 == 0:

                        proj_collection.insert_many(ENTRY_BATCH)
                        del ENTRY_BATCH[:]
                        ENTRY_BATCH = []

        proj_collection.insert_many(ENTRY_BATCH)

        client.close()