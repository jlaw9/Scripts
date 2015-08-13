#! /usr/bin/env python2.7

# Goal: Now that all of the variants from all files that successsfully ran annovar.


from varman2.mongotools import config_mongo, variants_mongo, sampleinfo_mongo
from varman2 import Logger
from add import Add
from delete import Delete
from load_variants import LoadVariants
from hotspot import Hotspot
from output import Output
from vtools import VTools
from annotate import Annotate
from output import Output
import vcftools
import os, sys
from bashcommands import bash, output_bash



# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------

class ArgExecutor:

    def __init__(self, args):
        self.project_config = config_mongo.get_project_config()
        self.logger = Logger.get_logger()
        self.args = args

    def add(self):
        adder = Add()

        if self.args['one_sample'] is not None:
            new_sample = [tuple(entry.strip('}').strip('{').strip(',').split(':')) for entry in self.args['one_sample']]
            new_sample = dict(new_sample)

            adder.add_one_sample(new_sample)
            if len(self.args['email']) > 0:

                if not sampleinfo_mongo.is_fully_annotated(new_sample['SAMPLE']):
                    annotate = Annotate()
                    annotate.annotate_sample(new_sample['SAMPLE'], 'orig')

                output_files = Output()
                final_file = output_files.sample_variants_csv(new_sample['SAMPLE'], 'orig')

                message = "Here are all the variants for the sample %s with their QC status." % new_sample['SAMPLE']
                for address in self.args['email']:
                    self.__log_sending_email(address)
                    output_bash.email_file(message, final_file, address)

        elif self.args['sample_info'] is not None:

            print self.args['sample_info']
            adder.add_sample_info(self.args['sample_info'])

    def delete(self):
        delete = Delete()

        if self.args['sample'] is not None:
            delete.delete_sample(self.args['sample'])

        elif self.args['collection'] is not None:
            delete.delete_collection(self.args['collection'])

        else:
            print "See please --help to specify something to delete."

    def load_variants(self):
        self.logger.info("Loading the variants into the database and performing filtering to generate hotspot list.")
        load_vars = LoadVariants('orig')
        load_vars.load_all()

    def hotspot(self):
        hotspot = Hotspot()

        if "new" == self.args['number']:
            hotspot.run()
        else:
            try:
                number = int(self.args['number'])
                hotspot.run(number)

            except ValueError:
                self.logger.error("The number you specified is not a proper integer number")
                sys.exit()

    def stats(self):
        varstats = Output()
        varstats.hotspot_stats()

        vtools = VTools()
        vtools.create_vcf_files()

    def output(self):
        if self.args['type'] == 'sample':
            if not sampleinfo_mongo.is_fully_annotated(self.args['name']):
                annotate = Annotate()
                annotate.annotate_sample(self.args['name'], 'orig')

            output_files = Output()
            output_files.sample_variants_csv(self.args['name'], 'orig')

    def nothing(self):
        with open("/home/ionadmin/durrant/variantmanager/success.txt", "w") as output:
            output.write("SUCCESS!!!!!!! WE HAVE LIFT OFF!!!!!!!!")
            print "SUCCESS!!!!!!! WE HAVE LIFT OFF!!!!!!!!"

    def __log_sending_email(self, address):
        self.logger.info("Emailing the file to %s" % address)

