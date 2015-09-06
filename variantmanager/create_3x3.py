__author__ = 'matt'
import argparse



if __name__ == '__main__':

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
