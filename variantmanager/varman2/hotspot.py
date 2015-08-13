#! /usr/bin/env python2.7
__author__ = 'durrantmm'

import os
import sys
import vcf
from varman2.mongotools import config_mongo, hotspot_mongo, sampleinfo_mongo, \
    variants_mongo, mongo, hotspothist_mongo
from varman2 import Logger
from bashcommands import bash, hotspot_bash
from glob import glob
import genotypetools
from annotate import Annotate


class Hotspot:
    def __init__(self):
        self.project_config = config_mongo.get_project_config()
        self.logger = Logger.get_logger()

    def run(self, number=0):
        if number == 0:
            number = hotspothist_mongo.get_next_number()
        else:
            if not hotspothist_mongo.is_hotspot_hist(number):
                self.__log_not_hotspot_number()
                sys.exit(1)
        hotspothist_mongo.add_new_hist(number)
        hotspot_dir = self.__ensure_directory(number)

        if not hotspothist_mongo.has_loaded_hotspots(number):

            if not self.__has_complete_hotspot_vcfs(hotspot_dir):
                # CREATING HOTSPOT FILE
                self.create_hotspot_file(hotspot_dir)

                print "Perform hotspotting"
                print "Load hotspot"

            # ANNOTATING
            annotate = Annotate()
            annovar_input = self.create_annovar_input(hotspot_dir)
            annovar_output = annotate.annotate_hotspot(annovar_input)
            annotate.save_annotations(annovar_output)

    def __ensure_directory(self, number=0):
        hotspot_dir = "%s/hotspots" % self.project_config['output_dir']
        bash.make_dir(hotspot_dir)
        config_mongo.change_config_field('hotspot_dir', hotspot_dir)

        directory = '%s/%s' % (hotspot_dir, number)
        bash.make_dir(directory)

        return directory

    def __has_complete_hotspot_vcfs(self, hotspot_dir):
        pass

    def create_annovar_input(self, hotspot_dir):

        annovar_input = "%s/annov_in.vcf" % hotspot_dir
        final_annovar_input = annovar_input.split(".vcf")[0]+'_prepped.vcf'

        if os.path.isfile(final_annovar_input):
            self.__log_hotspot_already_exists()
        else:

            with open(annovar_input, "w") as out_file:
                vcf_header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample\n"
                out_file.write(vcf_header)

                hotspots = hotspot_mongo.get_valid_hotspot_vars()
                self.__get_unannotated_hotspots(hotspots, out_file)

                ref_fasta = self.project_config['ref_fasta']
                final_annovar_input = annovar_input.split(".vcf")[0]+'_prepped.vcf'

                self.__log_preparing_hotpot()
                hotspot_bash.prep_hotspot(annovar_input, final_annovar_input, ref_fasta)

        return final_annovar_input

    def create_hotspot_file(self, hotspot_dir):

        hotspot_input = "%s/hotspot_orig.vcf" % hotspot_dir
        final_hotspot = hotspot_input.split(".vcf")[0]+'_prepped.vcf'

        if os.path.isfile(final_hotspot):
            self.__log_hotspot_already_exists()
        else:

            with open(hotspot_input, "w") as out_file:
                vcf_header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample\n"
                out_file.write(vcf_header)

                hotspots = hotspot_mongo.get_valid_hotspot_vars()
                self.__process_hotspot_vars(hotspots, out_file)

            ref_fasta = self.project_config['ref_fasta']
            final_hotspot = hotspot_input.split(".vcf")[0]+'_prepped.vcf'

            self.__log_preparing_hotpot()
            hotspot_bash.prep_hotspot(hotspot_input, final_hotspot, ref_fasta)

        self.reconcile_hotspot_and_database(final_hotspot)

    def reconcile_hotspot_and_database(self, hotspot_file):
        self.project_config = config_mongo.get_project_config()

        client, db = mongo.get_connection()
        vcf_reader = vcf.Reader(open(hotspot_file, 'r'))
        for rec in vcf_reader:
            chrom, pos, ref, alt = int(rec.CHROM.strip("chr")), int(rec.POS), rec.REF, [str(alt) for alt in rec.ALT]

            if not hotspot_mongo.is_hotspot(chrom, pos, ref, alt, db):
                self.__reconcile(chrom, pos, ref, alt, db)
        client.close()

    def __reconcile(self, chrom, pos, ref, alt, db):
        query = {'CHROM': chrom, 'POS': pos, 'REF': ref, 'ALT': {'$all': alt}}

        hotspot_coll = hotspot_mongo.get_collection(db)
        variants_coll = variants_mongo.get_collection(db)

        matched_documents = [doc for doc in hotspot_coll.find(query)]

        if len(matched_documents) == 1:
            self.__log_reconciling_variant(chrom, pos, ref, alt)
            # UPDATING THE ALTERNATE ALLELE FOR THE HOTSPOT VARIANT
            modified_count = hotspot_coll.update_one(query, {'$set': {'ALT': alt}}).modified_count
            if modified_count != 1:
                self.__log_serious_hotspot_discrepancy('THERE WAS A PROBLEM MODIFYING THE OLD HOTSPOT DOCUMENT')

            # UPDATING ALL THE PREVIOUSLY LOADED VARIANTS FOR THE HOTSPOT VARIANT
            variant_query = {'TYPE': 'orig', 'CHROM': chrom, 'POS': pos, 'REF': ref, 'ALT': {'$all': alt}}

            loaded_variants = [doc for doc in variants_coll.find(variant_query)]
            for var in loaded_variants:
                var_ref, var_alt, var_gt, var_gt_orig = var['REF'], var['ALT'], var['GT_calc'], var['GT_orig']
                var_fao, var_af = var['FAO'], var['AF_calc']

                new_alleles = [ref] + alt
                if var_gt != './.':
                    al1, al2 = genotypetools.get_genotype_alleles(var_ref, var_alt, var_gt)
                    al_num1 = new_alleles.index(al1)
                    al_num2 = new_alleles.index(al2)
                    corrected_gt_calc = "/".join([str(val) for val in sorted([al_num1, al_num2])])

                else:
                    corrected_gt_calc = './.'

                if var_gt_orig != './.':
                    al1, al2 = genotypetools.get_genotype_alleles(var_ref, var_alt, var_gt_orig)
                    al_num1 = new_alleles.index(al1)
                    al_num2 = new_alleles.index(al2)
                    corrected_gt_orig = "/".join([str(val) for val in sorted([al_num1, al_num2])])
                else:
                    corrected_gt_orig = './.'

                if len(var_fao) == 2:
                    var_fao = list(reversed(var_fao))
                    var_af = list(reversed(var_af))

                    ########################################################################################
                    # I'm going to put off correcting the AF_calc and FAO when number of alternate alleles is > 2
                    # for now, because it just is not needed for downstream analysis
                    # DO THIS LATER
                    ########################################################################################

                query = {'TYPE': 'orig', 'SAMPLE': var['SAMPLE'],'CHROM': chrom, 'POS': pos, 'REF': ref,
                         'ALT': {'$all': alt}}
                update = {'$set': {'ALT': alt, 'GT_calc': corrected_gt_calc, 'FAO': var_fao, 'AF_calc': var_af,
                                   'GT_orig': corrected_gt_orig}}

                modified_count = variants_coll.update_one(query, update).modified_count
                if modified_count != 1:
                    self.__log_serious_hotspot_discrepancy('THERE WAS A PROBLEM MODIFYING THE ORIGINAL VARIANTS '
                                                           'DOCUMENT')

        else:
            self.__log_serious_hotspot_discrepancy('THE NUMBER OF DOCUMENTS WITH MATCHING THE '
                                                   'ALLELE GROUP IS NOT 1')

    def perform_hotspot(self):
        self.project_config = config_mongo.get_project_config()
        hotspot_file = self.project_config['hotspot_file']
        hotspot_dir = self.project_config['hotspot_dir']

        output_dir = hotspot_dir + "/hotspot_output"

        if os.path.isdir(output_dir):
            self.__log_hotspot_files_already_exist()
        else:
            bash.make_dir(output_dir)

            ref_fasta = self.project_config['ref_fasta']
            bed_file = self.project_config['project_bed']
            tvc_params = self.project_config['tvc_params']

            bam_files = sampleinfo_mongo.get_bam_files()

            # HOTSPOT ALL OF THE BAM FILES
            self.__hotspot_bam_files(bam_files, hotspot_file, output_dir, ref_fasta, bed_file, tvc_params)

        # Delete the filter files
        all_files = glob(output_dir+"/*")
        for vcf in all_files:
            if "filtered.vcf" in vcf:
                bash.remove_file(vcf)

    def __hotspot_bam_files(self, bam_file_chunk, tvc_hotspot, output_dir, ref_fasta, bed_file, tvc_params):

        for bam_file in bam_file_chunk:
            sample = bam_file[0]
            bam_file = bam_file[1]
            output_vcf = sample + ".vcf"
            hotspot_bash.tvc_hotspot(tvc_hotspot, output_dir, output_vcf,
                                     ref_fasta, bam_file, bed_file, tvc_params)

    def __process_hotspot_vars(self, hotspots, out_file):

        dup_dict = {}
        for hotspot in hotspots:

            chrom, pos, ref, alt = str(hotspot['CHROM']), str(hotspot['POS']), hotspot['REF'], ",".join(hotspot['ALT'])
            dict_key = "|".join([chrom, pos])

            if len(dup_dict) == 0:
                dup_dict.update({dict_key: [hotspot]})
            elif dict_key in dup_dict:
                dup_dict[dict_key].append(hotspot)
            else:
                chrom, pos, ref, alt = self.__return_best_hotspot(dup_dict)
                list_entry = [chrom, pos, '.', str(ref), str(alt)]
                variant = list_entry + ['.', '.', '.', '.', '.']
                out_file.write("\t".join([str(val) for val in variant]) + "\n")

                dup_dict.clear()
                dup_dict.update({dict_key: [hotspot]})

    def __get_unannotated_hotspots(self, hotspots, out_file):
        dup_dict = {}
        for hotspot in hotspots:
            if "ANNOTATION" not in hotspot.keys():

                chrom, pos, ref, alt = str(hotspot['CHROM']), str(hotspot['POS']), hotspot['REF'], ",".join(hotspot['ALT'])
                dict_key = "|".join([chrom, pos])

                if len(dup_dict) == 0:
                    dup_dict.update({dict_key: [hotspot]})
                elif dict_key in dup_dict:
                    dup_dict[dict_key].append(hotspot)
                else:
                    chrom, pos, ref, alt = self.__return_best_hotspot(dup_dict)
                    list_entry = [chrom, pos, '.', str(ref), str(alt)]
                    variant = list_entry + ['.', '.', '.', '.', '.']
                    out_file.write("\t".join([str(val) for val in variant]) + "\n")

                    dup_dict.clear()
                    dup_dict.update({dict_key: [hotspot]})

    def __return_best_hotspot(self, dup_dict):
        """
        Enforces the current parameters for the "best hotspot" when there are multiple variants at a given position.
        It chooses the variant that:
            1) Has the fewest alternate alleles,
            and then if there are still duplicates,
            2) Choose the variant with the highest number of occurences in the project that pass the qc parameters

        :param dup_dict:
        :return:
        """
        hotspots = dup_dict[dup_dict.keys()[0]]
        fewest_alt_alleles = 10

        hotspot_with_fewest_alleles = []
        for hotspot in hotspots:
            if len(hotspot['ALT']) < fewest_alt_alleles:
                fewest_alt_alleles = len(hotspot['ALT'])

                del hotspot_with_fewest_alleles[:]
                hotspot_with_fewest_alleles = []
                hotspot_with_fewest_alleles.append(hotspot)
            elif len(hotspot['ALT']) == fewest_alt_alleles:
                hotspot_with_fewest_alleles.append(hotspot)

        if len(hotspot_with_fewest_alleles) == 1:
            best_hotspot = hotspot_with_fewest_alleles[0]
            return best_hotspot['CHROM'], best_hotspot['POS'], best_hotspot['REF'], ",".join(best_hotspot['ALT'])

        # Now checking for the highest number of variants that pass the qc parameters.
        highest_hotspot_count = 0
        most_frequent_hotspot = []
        for hotspot in hotspots:
            if hotspot['orig_stats']['qc']['final_qc_count'] > highest_hotspot_count:
                highest_hotspot_count = len(hotspot['ALT'])

                del most_frequent_hotspot[:]
                most_frequent_hotspot = []
                most_frequent_hotspot.append(hotspot)
            elif hotspot['orig_stats']['qc']['final_qc_count'] == highest_hotspot_count:
                most_frequent_hotspot.append(hotspot)

        best_hotspot = most_frequent_hotspot[0]
        return best_hotspot['CHROM'], best_hotspot['POS'], best_hotspot['REF'], ",".join(best_hotspot['ALT'])

    def __log_hotspot_already_exists(self):
        self.logger.info('Hotspot file already exists.')

    def __log_preparing_hotpot(self):
        self.logger.info('Preparing hotspot vcf for hotspotting.')

    def __log_hotspotting_bam_files(self):
        self.logger.info("Hotspotting all the BAM files")

    def __log_hotspot_files_already_exist(self):
        self.logger.info("Hotspot files already exist, not performing hotspot analysis on bam files")

    def __log_serious_hotspot_discrepancy(self, type):
        self.logger.error("There was a serious hotspot discrepancy: %s" % type)

    def __log_reconciling_variant(self, chrom, pos, ref, alt):
        self.logger.info("RECONCILING A DISCREPENCY BETWEEN HOTSPOT AND DATABASE: %s, %s, %s, %s" %
                         (chrom, pos, ref, alt))

    def __log_not_hotspot_number(self):
        self.logger.info("The hotspot number you specified does not exist in the hotspot, enter \"new\" to create a "
                         "new hotspot")



