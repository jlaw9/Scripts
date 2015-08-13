#! /usr/bin/env python2.7
__author__ = 'durrantmm'

from pymongo import MongoClient, ASCENDING
import copy
from misc_tools import MiscTools
from misc_stats import MiscStats

import csv

class MongoTools:

    def __init__(self, project_config=None):
        self.client = None
        self.db = None

        self.annotation_find_cursor = None
        self.annotation_batch = None

        self.project_config = project_config

    def open_connection(self):
        self.client = MongoClient()
        self.db = self.client['varman']

    def close_connection(self):
        self.client.close()

    def initialize_annotation_cursor(self):
        project_name = self.project_config['project_name']
        query = {'PROJECT': project_name}
        sort_by = [('CHROM', ASCENDING), ('POS', ASCENDING)]

        self.annotation_find_cursor = self.db['annovar'].find(query, no_cursor_timeout=True).sort(sort_by)

    def write_unique_vars_vcf(self, vcf_path, collection_name, skip_num=None, read_num=None,
                              process_num=None, logger=None):

        self.open_connection()
        vcf_path = vcf_path + "/uniquevars" + str(process_num) + ".vcf"

        with open(vcf_path, "w") as out_file:

            vcf_header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample\n"

            out_file.write(vcf_header)

            last_chrom = 0
            last_pos = 0
            allele_set = set()
            var_count = 0

            results = self.get_all_variants(collection_name, skip_num, read_num, no_cursor_timeout=True)

            for result in results:

                chrom, pos, id, ref, alt = result['CHROM'], result['POS'], result['ID'], result['REF'], \
                                           ",".join([alt for alt in result['ALT']])

                if chrom != last_chrom or pos != last_pos:

                    for allele_key in allele_set:
                        last_id, last_ref, last_alt = allele_key.split("|")

                        out_snp = [last_chrom, last_pos, last_id, last_ref, last_alt]
                        out_snp = out_snp + [".", ".", "."]
                        out_snp = ["." if val is None else str(val) for val in out_snp]
                        out_file.write("\t".join(out_snp) + "\n")

                    last_chrom = chrom
                    last_pos = pos
                    allele_set.clear()

                    allele_key = "|".join([".", ref, alt])
                    allele_set.add(allele_key)

                allele_key = "|".join([".", ref, alt])
                allele_set.add(allele_key)

                var_count += 1

            else:
                # GET ANY REMAINING VARIANTS THAT HAVE NOT BEEN WRITTEN
                for allele_key in allele_set:
                    last_id, last_ref, last_alt = allele_key.split("|")

                    out_snp = [last_chrom, last_pos, last_id, last_ref, last_alt]
                    out_snp = out_snp + [".", ".", "."]
                    out_snp = ["." if val is None else str(val) for val in out_snp]
                    out_file.write("\t".join(out_snp) + "\n")

        self.close_connection()

    def load_annovar_vcf_to_db(self, annovar_path, project_name=None, logger=None):

        proj_collection = self.db['annovar']
        index = [("CHROM", ASCENDING), ("POS", ASCENDING)]
        proj_collection.create_index(index)

        with open(annovar_path, "r") as annov_in:
            header = annov_in.readline().strip().strip("#").split("\t")

            for line in annov_in:
                line = line.strip().split("\t")
                line = {header[n]: line[n] for n in range(len(line))}
                info = line['INFO']
                info = info.split("ALLELE_END")
                info = [MiscTools.remove_empty_elements(value.split(";")) for value in info]
                info = MiscTools.remove_empty_elements(info)
                info = [dict([(info[i][j].split("=")[0].replace('.', '_'), info[i][j].split("=")[1]) for j in range(len(info[i])) if
                              "=" in info[i][j]])
                        for i in range(len(info))]
                info = [dict([(key, set(info[i][key].split("\\x3b")).pop()) for key in info[i]]) for i in range(len(info))]

                for i in range(len(info)):
                    entry = {'PROJECT': project_name, 'CHROM': int(line['CHROM'].strip("chr")), 'POS': int(line['POS']), 'REF': line['REF'],
                             'ALT': line['ALT'].split(",")[i], 'ANNOVAR': info[i]}
                    proj_collection.replace_one(entry, entry, upsert=True)

        return proj_collection.find()

    def get_all_variants(self, collection_name, skip_num=None, read_num=None, no_cursor_timeout=False, collection=None):
        if not collection:
            collection = self.db[collection_name]

        sortby = [('CHROM', ASCENDING), ('POS', ASCENDING)]
        if read_num is None and skip_num is None:
            result = collection.find(no_cursor_timeout=no_cursor_timeout).sort(sortby)
        else:
            result = collection.find(no_cursor_timeout=no_cursor_timeout).sort(sortby).\
                skip(skip_num).limit(read_num)

        return result

    def get_sample_names(self, collection_name):

        collection = self.db[collection_name]

        return collection.distinct('SAMPLE')

    def get_var_annotations(self):
        project_name = self.project_config['project_name']
        query = {'PROJECT': project_name}
        sort_by = [('CHROM', ASCENDING), ('POS', ASCENDING)]
        annot_cursor = self.db['annovar'].find(query, no_cursor_timeout=True).sort(sort_by)
        return annot_cursor

    def create_index(self, index, collection_name, logger=None):
        proj_collection = self.db[collection_name]
        result = proj_collection.create_index(index)

        return result

    def count_project_vars(self, collection_name, logger=None):
        proj_collection = self.db[collection_name]

        count = proj_collection.find().count()

        return count

    def change_info_field(self, project_name, field, value, logger=None):

        proj_collection = self.db['configs']

        proj_collection.update_one({'project_name': project_name}, {'$set': {field: value}})

    def load_next_annotation_batch(self, batch_size, logger=None):

        new_annotation_batch = {}

        doc_count = 0
        current_pos = 0

        for annot in self.annotation_find_cursor:

            prev_pos = current_pos
            current_pos = annot['POS']

            annot_key = "|".join([str(val) for val in [annot['CHROM'], annot['POS'], annot['REF'], annot['ALT']]])

            new_annotation_batch.update({annot_key: annot})
            doc_count += 1

            if doc_count >= batch_size and current_pos != prev_pos:
                break

        self.annotation_batch = new_annotation_batch

    def load_sample_variants(self, collection, sample, logger=None):

        collection = self.db[collection]

        sortby = [('CHROM', ASCENDING), ('POS', ASCENDING)]
        result = collection.find({'SAMPLE': sample}).sort(sortby)

        new_samplevar_batch = {}

        for var in result:

            var_key = "|".join([str(var['CHROM']), str(var['POS'])])

            try:
                FRO = var['CALL']['FRO']
                FAO = var['CALL']['FAO']
            except KeyError:
                FRO = var['CALL']['RO']
                FAO = var['CALL']['AO']

            if isinstance(FAO, list):
                total_reads = FRO+sum(FAO)
            else:
                total_reads = FRO+FAO

            try:
                pass_fail = var['PASS/FAIL']
            except KeyError:
                pass_fail = 'FAIL'

            new_samplevar_batch.update({
                var_key: {
                    'GT': var['GT_calc'], 'PASS/FAIL': pass_fail, 'REF': var['REF'], 'ALT': var['ALT'],
                    'TOTAL_READS': total_reads
                }})

        sample_var_batch = new_samplevar_batch
        return sample_var_batch

    def variant_stats_chunk(self, variant_stats_dir, project_name, skip_count, var_chunk_size, var_chunk_num):
        self.open_connection()
        self.initialize_annotation_cursor()

        csv_file = open(variant_stats_dir + ("/var_stats%d.csv" % var_chunk_num), 'w')
        varwriter = csv.writer(csv_file, delimiter=',')

        proj_collection = self.db[project_name]
        variants = self.get_all_variants(project_name, skip_count, var_chunk_size, no_cursor_timeout=True,
                                         collection=proj_collection)

        # LOAD THE INITIAL 0-50000 VARIANT ANNOTATIONS
        self.load_next_annotation_batch(50000)

        for var in variants:
            alleles = self.get_annotated_variant(var, var_chunk_num)
            if alleles is None: continue

            for allele in alleles:

                call = allele['CALL']
                annot = allele['annotation']
                annovar = allele['annotation']['ANNOVAR']

                # BEGIN EXTRACTING NEEDED DATA FROM VARIANT DICTIONARY
                sample, chrom, pos, ref = allele['SAMPLE'], allele['CHROM'], allele['POS'], allele['REF']
                affected = self.get_affected(self.project_config['project_name'], sample)
                alt = ','.join(var['ALT'])
                gt = var['GT_calc']
                allele_base = annot['ALT']

                rsid = annovar['snp137NonFlagged']
                gene, func, exonic_func = annovar['Gene_refGene'], annovar['Func_refGene'], annovar[
                    'ExonicFunc_refGene']

                aa_change = annovar['AAChange_refGene']
                if 'p.' in aa_change:
                    aa_change = aa_change.split('p.')[1].split(",")[0]

                try:
                    all_frq, alt_reads, ref_reads = allele['AF_calc'], call['FAO'], call['FRO']
                except KeyError:
                    all_frq, alt_reads, ref_reads = allele['AF_calc'], call['AO'], call['RO']

                if isinstance(all_frq, list):
                    tot_reads = sum(alt_reads) + ref_reads
                    all_frq, alt_reads = all_frq[allele['allele_num']], alt_reads[allele['allele_num'] - 1]
                else:
                    tot_reads = alt_reads + ref_reads

                if gt.split("/")[0] != gt.split("/")[1]:
                    ttest_result = MiscStats.performTTest(alt_reads, tot_reads, 'het')
                    tost_result = MiscStats.performTTost(alt_reads, tot_reads, 0.15, 'het')

                elif gt.split("/")[0] == "0" and gt.split("/")[1] == "0":
                    ttest_result = MiscStats.performTTest(alt_reads, tot_reads, 'wt')
                    tost_result = MiscStats.performTTost(alt_reads, tot_reads, 0.15, 'wt')

                elif gt.split("/")[0] == gt.split("/")[1]:
                    ttest_result = MiscStats.performTTest(alt_reads, tot_reads, 'hom')
                    tost_result = MiscStats.performTTost(alt_reads, tot_reads, 0.15, 'hom')

                sig_diff, sig_equiv, pass_fail = MiscStats.pass_fail_stats(ttest_result, tost_result)

                var_data = [sample, affected, chrom, pos, ref, alt, gt, allele_base, rsid, gene, func, exonic_func, aa_change,
                            all_frq, alt_reads, tot_reads, ttest_result, tost_result, sig_diff, sig_equiv, pass_fail]

                var_data = [str(data) for data in var_data]

                # ADDING THE TOST AND TTEST RESULTS TO THE VARIANT IN THE DATABASE
                if 'TOST' not in var.keys() and 'TTEST' not in var.keys():
                    proj_collection.find_one_and_update(
                        {'_id': var['_id']},
                        {'$addToSet': {'TOST': tost_result, 'TTEST': ttest_result}, '$set':{'PASS/FAIL': pass_fail}}
                    )
                if var['GT_calc'] != '0/0':
                    varwriter.writerow(var_data)

        csv_file.close()
        self.close_connection()

    def get_annotated_variant(self, variant, proc_num, logger=None):

        results = []
        all_prev = -1
        if variant['GT_calc'] != "./.":
            for allele_num in variant['GT_calc'].split('/'):

                allele_num = int(allele_num)
                if (allele_num != 0 and allele_num != all_prev) or variant['GT_calc'] == '0/0':
                    alt_base = variant['ALT'][allele_num - 1]

                    annot_key = "|".join([str(val) for val in
                                          [variant['CHROM'], variant['POS'], variant['REF'], alt_base]])
                    try:
                        annotation = self.annotation_batch[annot_key]
                    except KeyError:
                        while annot_key not in self.annotation_batch.keys():
                            print "Process number %s Could not find %s. Loading more annotations." % (proc_num, annot_key)
                            self.load_next_annotation_batch(50000)
                        print "Process number %s finally found the key %s." % (proc_num, annot_key)
                        annotation = self.annotation_batch[annot_key]

                    output_variant = copy.deepcopy(variant)  # Make a copy of the variant to add annotation to.

                    output_variant.update({"annotation": annotation})
                    output_variant.update({"allele_num": allele_num})
                    results.append(output_variant)

                    all_prev = allele_num

                    # Break the loop so that the homozygous wildtype is only annotated once
                    if variant['GT_calc'] == '0/0':
                        break

            return results
        else:
            return None

    # ALL OF PLINK MONGO METHODs
    def add_plink_doc(self, entry, project):
        entry.update({'PROJECT': project})

        proj_collection = self.db['plink']
        proj_collection.replace_one(entry, entry, upsert=True)

    def get_plink_variants(self, project):
        sortby = [('CHROM', ASCENDING), ('POS', ASCENDING)]

        proj_collection = self.db['plink']
        results = proj_collection.find({"PROJECT":project, "TYPE": "MAP"}).sort(sortby)

        return results

    def drop_variant_index(self, collection):
        proj_collection = self.db[collection]

        proj_collection.drop_indexes()

    def create_plink_index(self):
        proj_collection = self.db['plink']
        index = [("CHROM", ASCENDING), ("POS", ASCENDING), ("PROJECT", ASCENDING), ("TYPE", ASCENDING)]
        proj_collection.create_index(index)

    ## ALL OF THE INPUT FILE MONGO METHODS
    def has_hotspot_variants(self, project):
        proj_collection = self.db[project+'_hotspot']
        input = proj_collection.find_one()

        if input is not None:
            return True
        else:
            return False

