#! /usr/bin/env python2.7

# Goal: Now that all of the variants from all files that successsfully ran annovar.

import sys
from varman2.mongotools import config_mongo, sampleinfo_mongo, variants_mongo, hotspot_mongo, mongo
from varman2 import Logger
from varman2.load_variants import LoadVariants
from bashcommands import bash, hotspot_bash
from multiprocessing import Process

# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------

class Add:

    def __init__(self):
        self.project_config = config_mongo.get_project_config()
        self.logger = Logger.get_logger()

    def add(self, new_sample_dict):
        if 'SAMPLE' not in new_sample_dict:
            self.logger.info("The new sample entry does not contain a SAMPLE key.")
            sys.exit()
        else:
            new_sample_dict.update({"PROJECT": self.project_config['project_name']})
            sampleinfo_mongo.add_new_sample(new_sample_dict)

            sample = new_sample_dict["SAMPLE"]
            if not variants_mongo.is_sample_loaded(sample, "orig"):
                self.__load_variants(sample)

    def __load_variants(self, sample):
        self.logger.info("Loading the variants from the new sample.")
        load_vars = LoadVariants('orig')
        load_vars.load_single(sample)