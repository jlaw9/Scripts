#! /usr/bin/env python2.7

# Goal: Now that all of the variants from all files that successsfully ran annovar.

import sys
from varman2.mongotools import config_mongo, sampleinfo_mongo, variants_mongo, mongo
from varman2 import Logger
from varman2.load_variants import LoadVariants
import os

# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------

class Add:

    def __init__(self):
        self.project_config = config_mongo.get_project_config()
        self.logger = Logger.get_logger()

    def add_one_sample(self, new_sample_dict):
        """
        This a function for adding one sample, it is a handler that will access the sampleinfo_mongo class
        to actually make changes to the mongo database.

        :param new_sample_dict: a dictionary that was created from the command line options provided by the user
        :type new_sample_dict: dict
        :return:
        """

        # Check to make sure that the new sample was specified correctly.
        if 'SAMPLE' not in new_sample_dict:
            self.logger.info("The new sample entry does not contain a SAMPLE key.")
            sys.exit()
        else:
            # Specifiy the project the sample belongs to.
            new_sample_dict.update({"PROJECT": self.project_config['project_name']})

            # Actually add the new sample
            sampleinfo_mongo.add_new_sample(new_sample_dict)

            sample = new_sample_dict["SAMPLE"]
            # THIS IS WHERE THE SAMPLE IS THEN LOADED INTO THE DATABASE IF IT ISN'T ALREADY THERE
            # THIS COULD VERY EASILY BE MADE OPTIONAL, AND THEN THE SAMPLES COULD BE LOADED WITH
            # varman <project> load
            if not variants_mongo.is_sample_loaded(sample, "orig"):
                self.__load_variants(sample)

    def add_sample_info(self, sample_info_file):
        """
        Adds the sample info to the sample info collection.

        :param sample_info_file: this is the path to the specified sample info file.
        :type sample_info_file: str
        :return:
        """

        if not os.path.isfile(sample_info_file):
            # The path provided is not a real file, log an error.
            self.__log_invalid_file(sample_info_file)
            sys.exit(1)

        else:
            # Creates a mongo connection, parses the sample info file and actually adds everything
            # into the sample info collection
            client, db = mongo.get_connection()

            with open(sample_info_file, 'r') as infile:
                header = infile.readline().strip().split()

                for line in infile:
                    new_sample = {header[i]: line.strip().split()[i] for i in range(len(line.strip().split()))}
                    new_sample.update({"PROJECT": self.project_config['project_name']})
                    sampleinfo_mongo.add_new_sample(new_sample, db)

            client.close()

    def __load_variants(self, sample):
        """
        This loads the sample vcfs individually into the database, it does this because the load_variants method
        in the argexecutor.py module loads them in parallel, which wouldn't work in the case of loading a single
        sample.
        :param sample: the name of a sample to be loaded.
        :return:
        """
        self.logger.info("Loading the variants from the new sample.")
        load_vars = LoadVariants('orig')
        load_vars.load_single(sample)

    def __log_invalid_file(self, file_path):
        self.logger.error("The file path you provided is invalid: %s" % file_path)