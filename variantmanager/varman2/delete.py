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

class Delete:

    def __init__(self):
        self.project_config = config_mongo.get_project_config()
        self.logger = Logger.get_logger()

    def delete_collection(self, collection):

        mongo.delete_collection(collection)

    def delete_sample(self, sample):

        self.__delete_from_sampleinfo(sample)
        self.__delete_sample_from_hotspot(sample)
        self.__delete_sample_from_variants(sample)

    def __delete_from_sampleinfo(self, sample):
        modified_count = sampleinfo_mongo.delete_sample(sample)
        self.__log_sampleinfo_deletion_status(modified_count)

    def __delete_sample_from_hotspot(self, sample):
        pass

    def __delete_sample_from_variants(self, sample):
        pass

    def __log_sampleinfo_deletion_status(self, modified_count):
        if modified_count == 1:
            self.logger.info("Successfully deleted the sample from the sample_info collection.")
        elif modified_count == 0:
            self.logger.warning("The sample you specified does not exist in the database.")
        else:
            self.logger.error("More than one sample was deleted. This was definitely an error of some kind")
