from varman2.mongotools import config_mongo, hotspot_mongo, sampleinfo_mongo, mongo
from varman2.bashcommands import bash
from varman2 import Logger
from varman2 import vcftools
import os
from multiprocessing import Process

class VTools:
    def __init__(self):
        self.project_config = config_mongo.get_project_config()
        self.logger = Logger.get_logger()

        self.vtools_dir = '%s/vtools' % self.project_config['output_dir']
        if 'vtools_dir' not in self.project_config or not os.path.isdir(self.project_config['vtools_dir']):
            bash.make_dir(self.vtools_dir)
            config_mongo.change_config_field('vtools_dir', self.vtools_dir)
        else:
            self.vtools_dir = self.project_config['vtools_dir']

    def create_vcf_files(self):
        num_processors = 10

        samples = sampleinfo_mongo.get_samples()

        client, db = mongo.get_connection()

        jobs = set()
        while len(samples) > 0:
            sample = samples.pop(0)

            p = Process(target=vcftools.create_vcf_gt_orig_no_qc, args=(sample, self.vtools_dir, db))
            jobs.add(p)
            p.start()

            if len(jobs) == num_processors:
                for j in jobs:
                    j.join()
                jobs.clear()

        client.close()