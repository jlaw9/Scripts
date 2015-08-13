#!/usr/bin/env python2.7
# this script is responsible for managing / driving the execution of jobs for Atlas

import os
import sys
import argparse

from varman_logger import Logger
from variant_stats import VariantStats
from annotate_tools import AnnotateTools
from bash_commands import BashCommands
from load_variants import LoadVariants
from mongo_tools import MongoTools
from plink_tools import Plink
from hotspot import Hotspot

__author__ = 'mdurrant'


class VariantManager:

    def __init__(self):
        self.mongodb = MongoTools()
        self.args = None
        self.project_config = None

    def main(self, args):
        """
        This is the main function that runs Variant manager according to the arguments that were passed in by
         the user.
        :param args: These are the args as parsed by the parser at the bottom of this script.
        :return: None
        """

        self.args = args

        # Checks the arguments given to make sure that they can be processed correctly.
        self.__argcheck(args)

        # Setting up the project config file
        self.project_config = self.__setup_project_analysis(self.args)
        self.mongodb = MongoTools(self.project_config)
        self.mongodb.open_connection()

        ## SETTING UP LOGGING
        log = Logger(self.project_config['log_file'], 'a')
        logger = log.getLogger()

        # Loading the input file if specified
        if self.args['which'] == 'input':
            if logger: logger.info("Creating new input file in database...")
            input_man = SampleInputManager(self.project_config, self.mongodb, logger)
            input_man.load_sample_info_from_file(self.args['input_file_path'])

        # LOAD THE VARIANTS INTO THE DATABASE
        if self.args['which'] == 'all' or self.args['which'] == 'load':
            self.__load_variants(logger)

        # ANNOTATE THE VARIANTS IF NOT ALREADY COMPLETED
        if self.args['which'] == 'all' or self.args['which'] == 'anno':
            self.__annotate_variants(logger)

        # ANNOTATE THE VARIANTS IF NOT ALREADY COMPLETED
        if self.args['which'] == 'hotspot':
            self.__hotspot_variants(logger)

        # PERFORM VARIANT STATISTICAL ANALYSIS
        if self.args['which'] == 'all' or self.args['which'] == 'stats':
            varstats = VariantStats(self.project_config, self.mongodb, logger)
            varstats.generateStats(self.args['cpu_number'])

        # BEGINNING PLINK STATISTICAL ANALYSIS
        if self.args['which'] == 'plink':
            plink = Plink(self.project_config, self.mongodb, logger)
            plink.run()

    def __argcheck(self, args):
        self.mongodb.open_connection()

        if not self.mongodb.has_config(args['project_name']) and args['config_file'] is None:
            print "ERROR: The project does not exist in the the database, you must create a config file and input file" \
                  " for this project to begin managing it."
            sys.exit()

        self.mongodb.close_connection()

    def __parse_config(self, config_file):
        out_dict = {}

        with open(config_file,'r') as input:
            for line in input:
                line = line.strip().replace(' ', '')
                line = line.split(":")
                out_dict.update({line[0]: line[1]})

        return out_dict

    def __setup_project_analysis(self, args):
        self.mongodb.open_connection()

        if not self.mongodb.has_config(args['project_name']):

            config_file = self.__parse_config(args['config_file'])
            try:
                output_dir = "%s/%s_VarMan" % (config_file['output_dir'], args['project_name'])
                ref_fasta = config_file['ref_fasta']
                tvc_params = config_file['tvc_params']
                project_bed = config_file['project_bed']
                BashCommands.make_dir(output_dir)

            except KeyError:
                print "ERROR: some parameters in the config file were not specified correctly, see readme"
                sys.exit()

            log_file = output_dir + "/project.log"
            BashCommands.make_file(log_file)

            jsonData = {'log_file': log_file, 'output_dir': output_dir, 'project_name': args['project_name'],
                        'ref_fasta': ref_fasta, 'tvc_params': tvc_params, 'project_bed': project_bed}
            project_config = self.mongodb.create_project_config(jsonData)
            self.mongodb.close_connection()
            return project_config

        else:
            project_config = self.mongodb.get_project_config(args['project_name'])
            self.mongodb.close_connection()
            return project_config

    def __load_variants(self, logger):

        logger.info("Loading all project variants...")
        load_variants = LoadVariants(self.project_config, self.mongodb, logger)
        load_variants.load(self.args['cpu_number'])

        self.mongodb.open_connection()
        self.project_config = self.mongodb.get_project_config(self.args['project_name'])
        self.mongodb.close_connection()
        logger.info("All variants successfully loaded.")

    def __annotate_variants(self, logger):

        if 'annotation_path' not in self.project_config or not os.path.isdir(self.project_config['annotation_path']):

            logger.info("Beginning variant annotation...")

            annotools = AnnotateTools(self.project_config, self.mongodb, logger)
            annotools.annotate_variants(self.args['cpu_number'])

            self.mongodb.open_connection()
            self.project_config = self.mongodb.get_project_config(self.args['project_name'])
            self.mongodb.close_connection()

            logger.info("Variant annotation successfully completed")

        else:
            if logger: logger.info("Project variants already annotated: " + self.project_config["annotation_path"])

    def __hotspot_variants(self, logger):

        logger.info("Beginning variant hotspotting...")

        hotspotter = Hotspot(self.project_config, self.mongodb, logger)
        hotspotter.hotspot_variants(self.args['cpu_number'])

        self.mongodb.open_connection()
        self.project_config = self.mongodb.get_project_config(self.args['project_name'])
        self.mongodb.close_connection()

        logger.info("Variant hotspotting successfully completed")



# start here when the script is launched
if (__name__ == "__main__"):
    """
    This runs the commandline parsing for VariantManager. There are a variety of options to choose from. VariantManager
    is intended to be used in conjunction with a database, keeping track of projects in a continuous way by saving the
    state of projects between uses. This will allow the several stages of analysis to be done a piece at a time, which
    is necessary considering how long some of the analyses can take to perform. It is designed to handle many millions
    of variants between hundreds or even thousands of samples.
    """

    # setup the option parser
    parser = argparse.ArgumentParser(description='VariantManager is a software suite that provides '
                                                 'several variant managing services.')

    # add universal arguments, arguments to be specified regardless of the type of arguments that follow.
    parser.add_argument('-p', '--project_name', required=True,
                        help='The name of the project being used.')

    # The output direc
    parser.add_argument('-c', '--config_file', metavar='config_file', required=False,
                        help='This is the path to the config file used to run this specific project, which is only '
                             'necesssary if a config file has not been specified previously')
    parser.add_argument('-cpu', '--cpu_number', metavar='cpu_number', required=False,
                        help='The number of processes to run the executions on.', default=10)

    # add the subparsers for various arguments
    subparsers = parser.add_subparsers(help="The argument specifying the type of analysis to perform." +
                                       " example: ./variant_manager.py all")

    # Create the Different Subparsers
    parser_all = subparsers.add_parser('all', help='perform all analyses sequentially')
    parser_input = subparsers.add_parser('input', help='load the variants in the specified project directory ')
    parser_load = subparsers.add_parser('load', help='load the variants in the specified project directory ')
    parser_anno = subparsers.add_parser('anno', help='annotate the variants in the specified project')
    parser_stats = subparsers.add_parser('stats', help='Perform a statistical analysis of the data')
    parser_plink = subparsers.add_parser('plink', help='Run PLINK statistical genetics analyses')
    parser_hotspot = subparsers.add_parser('hotspot', help='Perform a hotspot analysis using TVC')


    # Specify the options for the parser_all
    parser_all.set_defaults(which="all")


    # Specifying options for the input file
    parser_input.add_argument('input_file_path',
                            help='The path to the input file in the specified format. (See readme for format details)')
    parser_input.set_defaults(which="input")


    # Specify the options for the parser_load
    parser_load.add_argument('-vcf','--vcf_path', required=True,
                            help='REQUIRED either a path to a directory containing multiple vcfs, or a vcf itself.')
    parser_load.set_defaults(which="load")

    # Specify the options for the parser_anno
    parser_anno.set_defaults(which="anno")

    # Specify the options for the parser_anno
    parser_hotspot.set_defaults(which="hotspot")

    # Specify the options for the parser_stats
    parser_stats.set_defaults(which="stats")

    # Specify the options for the parser_plink
    parser_plink.set_defaults(which="plink")



    args = parser.parse_args()
    args = vars(args)

    # create the job manager
    varman = VariantManager()

    varman.main(args)