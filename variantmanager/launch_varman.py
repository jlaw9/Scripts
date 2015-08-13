#!/usr/bin/env python2.7
# this script is responsible for managing / driving the execution of jobs for Atlas
__author__ = 'mdurrant'

import sys
import os
import argparse

import varman2
from varman2 import Logger
from varman2.bashcommands import bash
from varman2.mongotools import config_mongo
from varman2.argexecutor import ArgExecutor


class VariantManager:
    def __init__(self):
        self.args = None
        self.project_config = None
        self.logger = None

    def main(self, args):
        """
        This is the main function that runs Variant manager according to the arguments that were passed in by
         the user.
        :param args: These are the args as parsed by the parser at the bottom of this script.
        :return: None
        """

        self.args = args
        varman2.set_project_name(args['project_name'])

        # Checks the arguments given to make sure that they can be processed correctly.
        self.__argcheck(args)

        # Setting up the project config file
        self.__setup_project_analysis(self.args)
        self.project_config = config_mongo.get_project_config()

        # SETTING UP LOGGING
        Logger.create_logger(self.project_config['log_file'], 'a')
        self.logger = Logger.get_logger()

        argexecute = ArgExecutor(self.args)
        if self.args['which'] == 'add':
            argexecute.add()

        elif self.args['which'] == 'delete':
            argexecute.delete()

        elif self.args['which'] == 'load':
            argexecute.load_variants()

        elif self.args['which'] == 'hotspot':
            argexecute.hotspot()

        elif self.args['which'] == 'stats':
            argexecute.stats()

        elif self.args['which'] == 'output':
            argexecute.output()

        elif self.args['which'] == 'nothing':
            argexecute.nothing()

    @staticmethod
    def __argcheck(args):
        # Checking the prerequisites for the config file
        if not config_mongo.has_config() and args['config'] is None:
            print("ERROR: The project does not exist in the the database, you must use the setup option and input "
                  "a config file for this project to begin managing it.")
            sys.exit()

        print args
        sys.exit()
        if args['add'] is not None:
            print "You chose to add"
            sys.exit()

    def __parse_config(self, config_file):
        out_dict = {}

        with open(config_file, 'r') as input_file:
            for line in input_file:
                line = line.strip().replace(' ', '')
                line = line.strip().split(":")
                out_dict.update({line[0]: line[1]})

        return out_dict

    def __setup_project_analysis(self, args):

        if not config_mongo.has_config():

            config_file = self.__parse_config(args['config'])
            try:
                output_dir = "%s/%s_VarMan" % (config_file['output_dir'], args['project_name'])
                ref_fasta = config_file['ref_fasta']
                tvc_params = config_file['tvc_params']
                project_bed = config_file['project_bed']
                bash.make_dir(output_dir)

            except KeyError:
                print "ERROR: some parameters in the config file were not specified correctly, see readme"
                sys.exit()

            log_file = output_dir + "/project.log"
            bash.make_file(log_file)

            config_data = {'log_file': log_file, 'output_dir': output_dir, 'project_name': args['project_name'],
                           'ref_fasta': ref_fasta, 'tvc_params': tvc_params, 'project_bed': project_bed
                            }
            config_mongo.create_project_config(config_data)

# start here when the script is launched
if __name__ == "__main__":
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
    parser.add_argument('project_name', help='The name of the project being used.')
    parser.add_argument('-cpu', '--cpu_number', metavar='cpu_number', required=False,
                        help='The number of processes to run the executions on.', default=10)

    # add the subparsers for various arguments
    subparsers = parser.add_subparsers(help="The argument specifying the type of analysis to perform." +
                                            " example: ./variant_manager.py all")

    # Create the Different Subparsers
    parser_setup = subparsers.add_parser('setup', help='Setup the project with a config file.')
    parser_add = subparsers.add_parser('add', help='add a new sample to the database')
    parser_delete = subparsers.add_parser('delete', help="Delete information from the database")
    parser_load = subparsers.add_parser('load', help='Load variants from vcf files into database and generate hotspot'
                                                     'list')
    parser_stats = subparsers.add_parser('stats', help='Perform a statistical analysis of the data')
    parser_hotspot = subparsers.add_parser('hotspot', help='Perform a hotspot analysis using TVC')
    parser_output = subparsers.add_parser('output', help='Output information of interest')
    parser_nothing = subparsers.add_parser('nothing')


    # Specifying options for the parser_setup
    parser_setup.set_defaults(which="setup")
    parser_setup.add_argument('-c', '--config', help='The path to the configuration file to be used by the project, '
                                                     'see readme for more information.', required=True)
    # Specify the options for the parser_add
    parser_add.set_defaults(which="add")
    parser_add.add_argument('-1','--one_sample', help='Multiple key:value arguments with new sample information to be added'
                                               'it must be formatted in a specific way, key1:value1 key2:value2 '
                                               'follow this format exactly, no quotes for strings are necessary.',
                            action='store', nargs='*')
    parser_add.add_argument('-f', '--sample_info', help='A file specifying sample info informatin to add to the sample info.',
                            action='store', nargs='*')
    parser_add.add_argument('-e', '--email', help='Emails to send the resulting csv to.',
                            action='store', nargs='*')

    # Specify the options for the parser_delete
    parser_delete.set_defaults(which="delete")
    parser_delete.add_argument('-s', '--sample', help='enter the name of the sample to be deleted.')
    parser_delete.add_argument('-col', '--collection', help='Deletes a collection by the given name from the mongodb')

    # Specifying options for the parser_load
    parser_load.set_defaults(which="load")

    # Specify the options for the parser_hotspot
    parser_hotspot.set_defaults(which="hotspot")
    parser_hotspot.add_argument('number', help='The hotspot to run, analyzing a specific number.')

    # Specify the options for the parser_stats
    parser_stats.set_defaults(which="stats")

    # Specify the options for the parser_output
    parser_output.set_defaults(which="output")
    parser_output.add_argument('type', choices=['sample'], help='The type of information you want to output')
    parser_output.add_argument('name', help='The name of the sample whose variants you want to output')

    parser_nothing.set_defaults(which="nothing")

    args = parser.parse_args()
    args = vars(args)

    # create the job manager
    varman = VariantManager()

    varman.main(args)
