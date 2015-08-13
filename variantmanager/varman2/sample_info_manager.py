# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------

import sys
from varman2.mongotools import config_mongo, sampleinfo_mongo
from varman2 import Logger

class SampleInputManager:

    def __init__(self):
        self.project_config = config_mongo.get_project_config()
        self.logger = Logger.get_logger()

    def load_sample_info_from_file(self):

        if not sampleinfo_mongo.has_sample_info():
            final_dict = {}
            final_dict.update({'project_name': self.project_config['project_name']})
            final_dict.update({'info': {}})

            with open(self.project_config['sample_info'], "r") as input:
                header = input.readline().strip().split()

                input_dict = final_dict['info']
                line_count = 0
                for line in input:
                    line_count += 1

                    line = line.strip().split()
                    line_dict = {header[i]: line[i] for i in range(len(line))}
                    input_dict.update({ line_dict['ID']: {} })

                    for key in line_dict:
                        if key != 'ID':
                            input_dict[line_dict['ID']].update({key: line_dict[key]})

            sampleinfo_mongo.add_sample_info_doc(final_dict)
            return sampleinfo_mongo.get_sample_info()

        else:
            print 'ERROR: A sample info file has already been loaded into the database. If you would like to set up' \
                  'a project from the beginning, see the wiki'
            sys.exit()


