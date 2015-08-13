#! /usr/bin/env python2.7
__author__ = 'durrantmm'

import os
import glob
from bash_commands import BashCommands
from misc_tools import MiscTools
from multiprocessing import Process
from models import *
from pymongo import MongoClient, ASCENDING
import vcf
import sys

class Hotspot:
    def __init__(self, project_config, mongodb, logger):
        self.project_config = project_config
        self.mongodb = mongodb
        self.logger = logger
        self.cpu_number = None

    def hotspot_variants(self, cpu_number):
        self.cpu_number = cpu_number

        hotspot_dir, hotspot_file = self.__make_hotspot_file()
        out_dir = self.__perform_hotspot(hotspot_dir, hotspot_file)
        self.__load_hotspot_variants(out_dir)

    def __make_hotspot_file(self):
        self.mongodb.open_connection()
        self.logger.info("Making Hotspot file")

        hotspot_dir = self.project_config['output_dir'] + "/hotspot"
        BashCommands.make_dir(hotspot_dir)

        hotspot_input = hotspot_dir + "/hotspot.vcf"
        final_hotspot = hotspot_input.split(".vcf")[0]+'_prepped.vcf'

        if os.path.isfile(final_hotspot):
            self.logger.info('A hotspot already file already exists, using that.')
            return hotspot_dir, hotspot_input
        else:
            self.logger.info("Writing unique variants to tvc hotspot input vcf")

            with open(hotspot_input, "w") as out_file:
                vcf_header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample\n"
                out_file.write(vcf_header)

                annotations = self.mongodb.get_var_annotations()

                for annot in annotations:

                    chrom, pos, id, ref, alt = annot['CHROM'], annot['POS'], annot['ANNOVAR']['snp137NonFlagged'], \
                                               annot['REF'], annot['ALT']

                    list_entry = [str(chrom), str(pos), str(id), str(ref), str(alt)]

                    variant = list_entry + ['.', '.', '.', '.', '.']
                    out_file.write("\t".join([str(val) for val in variant]) + "\n")

            ref_fasta = self.project_config['ref_fasta']
            final_hotspot = hotspot_input.split(".vcf")[0]+'_prepped.vcf'

            self.logger.info('Preparing hotspot vcf for hotspotting.')
            BashCommands.prep_hotspot(hotspot_input, final_hotspot, ref_fasta)
            BashCommands.remove_file(hotspot_input)
            return hotspot_dir, final_hotspot

    def __perform_hotspot(self, hotspot_dir, hotspot_file):

        self.logger.info("Hotspotting all the BAM files")

        out_path = hotspot_dir + "/output"
        if os.path.isdir(out_path):
            self.logger.info("Hotspot files already exist, not performing hotspot analysis on bam files")
            return out_path

        else:
            BashCommands.make_dir(out_path)

            ref_fasta = self.project_config['ref_fasta']
            bed_file = self.project_config['project_bed']
            tvc_params = self.project_config['tvc_params']

            self.mongodb.change_info_field(self.project_config['project_name'], 'hotspot_dir', out_path, self.logger)

            bam_files = self.mongodb.get_bam_files(self.project_config['project_name'])

            # HOTSPOT ALL OF THE BAM FILES
            self.hotspot_bam_files(bam_files, hotspot_file, out_path, ref_fasta, bed_file, tvc_params)

            return out_path

    def hotspot_bam_files(self, bam_file_chunk, tvc_hotspot, output_dir, ref_fasta, bed_file, tvc_params):

        for bam_file in bam_file_chunk:
            output_vcf = bam_file[0] + ".vcf"
            BashCommands.tvc_hotspot(tvc_hotspot, output_dir, output_vcf,
                                     ref_fasta, bam_file[1], bed_file, tvc_params)

    def __load_hotspot_variants(self, variant_dir):
        if self.mongodb.has_hotspot_variants(self.project_config['project_name']):
            self.logger.info("The project has already loaded hotspot variants into the database. Skipping hotspot "
                             "variant loading")

        else:
            # Delete all the unwanted filtered.vcf files
            all_files = glob.glob(variant_dir+"/*")
            for vcf in all_files:
                if "filtered.vcf" in vcf:
                    BashCommands.remove_file(vcf)

            hotspot_vcfs = glob.glob(variant_dir+"/*.vcf")
            hotspot_collection_name = self.project_config['project_name'] + "_hotspot"

            vcf_file_chunks = MiscTools.split_list_to_chunks(hotspot_vcfs, self.cpu_number)

            jobs = []
            for i in range(self.cpu_number):
                p = Process(target=self.__load_hotspot_vcf_files, args=([vcf_file_chunks[i], hotspot_collection_name]))
                jobs.append(p)
                p.start()

            for j in jobs:
                j.join()

            self.mongodb.open_connection()
            self.logger.info("Total Variants Loaded to database: " +
                             str(self.mongodb.count_project_vars(hotspot_collection_name)))

            self.logger.info("Sorting and Indexing the new hotspot variant collection.")
            index = [("CHROM", ASCENDING), ("POS", ASCENDING)]
            self.mongodb.create_index(index, hotspot_collection_name)

            self.mongodb.close_connection()

    def __load_hotspot_vcf_files(self, vcf_files, collection_name):
        client = MongoClient()
        db = client['varman']
        proj_collection = db[collection_name]

        count = 0
        ENTRY_BATCH = []
        for vcf_file in vcf_files:

            vcf_reader = vcf.Reader(open(vcf_file, 'r'))
            self.logger.info("LOADING HOTSPOT VARIANTS FROM VCF: " + vcf_file)
            for rec in vcf_reader:

                var_call = VariantCall(rec)
                sample_name = os.path.basename(vcf_file).split(".")[0]
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
