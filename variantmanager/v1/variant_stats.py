#! /usr/bin/env python2.7
__author__ = 'durrantmm'

import glob
import csv
import sys

from bash_commands import BashCommands
from mongo_tools import MongoTools
from multiprocessing import Process
from misc_tools import MiscTools
from pymongo import MongoClient

class VariantStats:
    def __init__(self, project_config, mongodb, logger):
        self.project_config = project_config
        self.mongodb = mongodb
        self.logger = logger

    def generateStats(self, num_processors):

        self.logger.info("Beginning statistical analysis of variants...")
        if not ('var_stats_dir' in self.project_config and not (len(glob.glob(self.project_config['var_stats_dir'] +
                                                                                "/var_stats*")) != 1)):
            self.__single_var_stats(num_processors)
            self.project_config = self.mongodb.get_project_config(self.project_config['project_name'])

        if len(glob.glob(self.project_config['var_stats_dir']+"/*")) == 1:
            self.logger.info("Generating summary statistics...")
            self.summary_stats()

        self.logger.info("Finished statistical analysis...")

    def summary_stats(self):
        var_stats_file = open(self.project_config['var_stats_dir']+"/var_stats.csv", 'r')
        csvreader = csv.reader(var_stats_file, delimiter=',', quotechar='"')

        var_stats_header = csvreader.next()

        unique_sumstats = self.__UniqueSumStats(var_stats_header, self.project_config, self.mongodb)
        gene_sumstats = self.__GeneSumStats(var_stats_header, self.project_config, self.mongodb)
        sample_sumstats = self.__SampleSumStats(var_stats_header, self.project_config, self.mongodb)
        project_sumstats = self.__ProjectSumStats(var_stats_header, self.project_config, self.mongodb)

        for var in csvreader:
            unique_sumstats.process_var(var)
            gene_sumstats.process_var(var)
            sample_sumstats.process_var(var)
            project_sumstats.process_var(var)

        unique_sumstats.write_csv()
        gene_sumstats.write_csv()
        sample_sumstats.write_csv()
        project_sumstats.write_csv()

        self.logger.info("Analyzing hotspotting files")
        unique_sumstats_file = unique_sumstats.getFile()
        hotspot_varstats = self.__HotspotSumStats(self.project_config, self.mongodb)
        hotspot_varstats.analyze(unique_sumstats_file)

    def __single_var_stats(self, num_processors):
        self.logger.info("Analyzing each variant call individually...")
        self.mongodb.open_connection()

        variant_stats_dir = self.project_config['output_dir'] + "/variant_stats"
        BashCommands.make_dir(variant_stats_dir)

        project_name = self.project_config['project_name']
        self.mongodb.change_info_field(project_name, 'var_stats_dir', variant_stats_dir)

        # SPLITTING THE VARIANTS INTO THE NUMBER OF PROCESSORS TO USE
        var_count = self.mongodb.count_project_vars(project_name)
        var_chunk_size = var_count / num_processors
        jobs = []
        skip_count = 0

        for var_chunk_num in range(num_processors):

            # INITIATE THE DATABASE CONNECTION TO HANDLE THE PROCESS
            tmp_mongo = MongoTools(self.project_config)

            # BEGIN THE PROCESS
            if (var_chunk_num + 1) == num_processors:
                var_chunk_size = var_count - skip_count

            p = Process(target=tmp_mongo.variant_stats_chunk, args=(variant_stats_dir, project_name,
                                                                    skip_count, var_chunk_size, var_chunk_num + 1))
            jobs.append(p)
            p.start()

            skip_count += var_chunk_size

        for j in jobs:
            j.join()

        var_stats_files = glob.glob(variant_stats_dir+"/*")

        header = ["SAMPLE", "AFFECTED", "CHROM", "POS", "REF", "ALT", "GT", "ALLELE", "RSID", "Gene.refGene",
                  "Func.refGene", "ExonicFunc.refGene", "AAChange", "ALLELE_FREQ", "ALLELE_READS", "TOTAL_READS",
                  "TTEST", "TOST", "SIG_DIFF", "SIG_EQUIV", "PASS/FAIL"]

        BashCommands.cat_csv_with_header(header, var_stats_files, variant_stats_dir+"/var_stats.csv")

        for f in var_stats_files:
            BashCommands.remove_file(f)

        self.logger.info("Finished analyzing each variant.")

        self.mongodb.close_connection()

    class __UniqueSumStats:

        def __init__(self, var_stats_header, project_config, mongodb):
            self.project_config = project_config
            self.mongodb = mongodb

            self.dict_header = ["Total_Vars", "Total_Het_Vars", "Total_Hom_Vars", "Total_Vars>30x", "Average_Allele_Freq", "Average_Read_Depth", "Sig_Diff_Perc",
                       "Sig_Equiv_Perc", "Pass_Perc", "Fail_Perc", "Unknown_Perc"]

            self.final_header = ['CHROM', 'AFFECTED', 'POS', 'REF',	'ALT', 'ALLELE', 'RSID', 'Gene.refGene',
                                 'Func.refGene', 'ExonicFunc.refGene', 'AAChange'] + self.dict_header
            self.variant_dict = {}
            self.variant_dict = {}
            self.var_stats_header = var_stats_header

            variant_stats_dir = self.project_config['var_stats_dir']
            self.csv_file = variant_stats_dir + "/uniquevars_sumstats.csv"

        def process_var(self, var):
            var = {self.var_stats_header[i]: var[i] for i in range(len(var))}

            gt_class = MiscTools.get_gtclass(var['GT'])
            allele_frq = float(var['ALLELE_FREQ'])
            read_depth = int(var['TOTAL_READS'])
            sig_diff = var['SIG_DIFF']
            sig_equiv = var['SIG_EQUIV']
            pass_fail = var['PASS/FAIL']
            sig_diff_count, sig_equiv_count, pass_count, fail_count, unknown_count \
                = VariantStats.get_sig_counts(sig_diff, sig_equiv, pass_fail)

            dict_key = "|".join([var['CHROM'], var['AFFECTED'], var['POS'], var['REF'], var['ALT'], var['ALLELE'],
                                 var['RSID'], var['Gene.refGene'], var['Func.refGene'], var['ExonicFunc.refGene'],
                                 var['AAChange']])

            mydict = self.variant_dict

            if dict_key not in mydict:
                if gt_class == 'het':
                    mydict.update({dict_key: [1, 1, 0, 0, allele_frq, read_depth, sig_diff_count, sig_equiv_count,
                                                pass_count, fail_count, unknown_count]})
                elif gt_class == 'hom':
                    mydict.update({dict_key: [1, 0, 1, 0, allele_frq, read_depth, sig_diff_count, sig_equiv_count,
                                                pass_count, fail_count, unknown_count]})

                if read_depth >= 30:
                    mydict[dict_key][3] += 1

            else:
                mydict[dict_key][0] += 1
                if gt_class == 'het':
                    mydict[dict_key][1] += 1
                if gt_class == 'hom':
                    mydict[dict_key][2] += 1
                if read_depth >= 30:
                    mydict[dict_key][3] += 1
                mydict[dict_key][4] += allele_frq
                mydict[dict_key][5] += read_depth
                mydict[dict_key][6] += sig_diff_count
                mydict[dict_key][7] += sig_equiv_count
                mydict[dict_key][8] += pass_count
                mydict[dict_key][9] += fail_count
                mydict[dict_key][10] += unknown_count

        def write_csv(self):
            for key in self.variant_dict:
                self.variant_dict[key] = [self.variant_dict[key][item] / float(self.variant_dict[key][0])
                                          if item not in [0, 1, 2, 3] else self.variant_dict[key][item]
                                          for item in range(len(self.variant_dict[key]))]

            csv_file = self.csv_file

            csv_out_writer = csv.writer(open(csv_file, "w"), delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            csv_out_writer.writerow(self.final_header)
            for key in self.variant_dict:
                entry = [str(item) for item in self.variant_dict[key]]
                new_row = key.split("|") + entry
                csv_out_writer.writerow(new_row)

        def getFile(self):
            return self.csv_file

    class __HotspotSumStats:

        def __init__(self, project_config, mongodb):
            self.project_config = project_config
            self.mongodb = mongodb
            self.final_header = ['CHROM', 'AFFECTED', 'POS', 'REF',	'ALT', 'ALLELE', 'RSID', 'Gene.refGene',
                                 'Func.refGene', 'ExonicFunc.refGene', 'AAChange', 'Total_Vars', 'Total_Het_Vars',
                                 'Total_Hom_Vars', 'Total_Vars>30x', 'Sig_Diff_Perc', 'Sig_Equiv_Perc', 'Pass_Perc',
                                 'Fail_Perc', 'Unknown_Perc', 'HS_Total', 'HS_Total_Vars', 'HS_Total_Wt',
                                 'HS_Total_Het', 'HS_Total_Hom', 'HS_Total_NoCalls', 'HS_Total<30x']

        def analyze(self, unique_varstats_file):
            client = MongoClient()
            db = client['varman']

            hotspots = db[self.project_config['project_name']+"_hotspot"]

            input = open(unique_varstats_file, "r")
            output = open(self.project_config['var_stats_dir']+"/hotspot_sumstats.csv", 'w')

            csv_in = csv.DictReader(input, delimiter=',', quotechar='"')
            csv_out = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

            csv_out.writerow(self.final_header)

            for line in csv_in:
                chrom, affected, pos, ref, alt, allele = int(line['CHROM']), line['AFFECTED'], int(line['POS']), \
                                                         line['REF'], line['ALT'].split(','), line['ALLELE']
                search = {'CHROM': chrom, 'POS': pos, 'REF': ref, 'ALT': alt}

                matches = hotspots.find(search)

                hs_total = 0
                hs_total_vars = 0
                hs_total_wt = 0
                hs_total_hets = 0
                hs_total_homs = 0
                hs_total_nocalls = 0
                hs_total_30x = 0
                for match in matches:
                    gt = match['GT_calc']
                    a1 = gt.split('/')[0]
                    a2 = gt.split('/')[1]

                    if gt == '0/0':
                        hs_total += 1
                        hs_total_wt += 1
                        if self.get_total_reads(match) <= 30:
                            hs_total_30x += 1

                    elif gt == './.':
                        hs_total += 1
                        hs_total_nocalls += 1
                        if self.get_total_reads(match) <= 30:
                            hs_total_30x += 1

                    elif a1 != a2:

                        if match['ALT'][int(a2)-1] == allele:
                            hs_total += 1
                            hs_total_vars += 1
                            hs_total_hets += 1
                            if self.get_total_reads(match) <= 30:
                                hs_total_30x += 1

                    elif a1 == a2:
                        if match['ALT'][int(a2)-1] == allele:
                            hs_total += 1
                            hs_total_vars += 1
                            hs_total_homs += 1
                            if self.get_total_reads(match) <= 30:
                                hs_total_30x += 1

                out_row = [chrom, affected, pos, ref, ",".join(alt), allele, line['RSID'], line['Gene.refGene'],
                           line['Func.refGene'], line['ExonicFunc.refGene'], line['AAChange'], line['Total_Vars'],
                           line['Total_Het_Vars'], line['Total_Hom_Vars'], line['Total_Vars>30x'], line['Sig_Diff_Perc'],
                           line['Sig_Equiv_Perc'], line['Pass_Perc'], line['Fail_Perc'], line['Unknown_Perc'],
                           hs_total, hs_total_vars, hs_total_wt, hs_total_hets, hs_total_homs, hs_total_nocalls,
                           hs_total_30x]

                if hs_total > 0:
                    csv_out.writerow(out_row)

            input.close()
            output.close()

        def get_total_reads(self, variant):
            if isinstance(variant['CALL']['FAO'], list):
                total_reads = sum(variant['CALL']['FAO']) + variant['CALL']['FRO']
            else:
                total_reads = variant['CALL']['FAO'] + variant['CALL']['FRO']

            return total_reads

    class __GeneSumStats:

        def __init__(self, var_stats_header, project_config, mongodb):
            self.project_config = project_config
            self.mongodb = mongodb

            self.dict_header = ["Total_Count", "Unique_Variants", "Average_Allele_Freq", "Average_Read_Depth",
                       "Sig_Diff_Perc", "Sig_Equiv_Perc", "Pass_Perc", "Fail_Perc", "Unknown_Perc"]
            self.het_variant_dict = {}
            self.hom_variant_dict = {}
            self.var_stats_header = var_stats_header

        def process_var(self, var):
            var = {self.var_stats_header[i]: var[i] for i in range(len(var))}

            allele_frq = float(var['ALLELE_FREQ'])
            read_depth = int(var['TOTAL_READS'])
            sig_diff = var['SIG_DIFF']
            sig_equiv = var['SIG_EQUIV']
            pass_fail = var['PASS/FAIL']
            sig_diff_count, sig_equiv_count, pass_count, fail_count, unknown_count \
                = VariantStats.get_sig_counts(sig_diff, sig_equiv, pass_fail)

            dict_key = var['Gene.refGene']

            unique_var_id = ",".join([var['CHROM'], var['POS'], var['REF'], var['ALT'], var['GT'], var['ALLELE']])

            gt_class = MiscTools.get_gtclass(var['GT'])
            if gt_class == 'het':
                mydict = self.het_variant_dict
            elif gt_class == 'hom' or gt_class == 'wt':
                mydict = self.hom_variant_dict

            if dict_key not in mydict:
                unique_vars = set()
                unique_vars.add(unique_var_id)

                mydict.update({dict_key: [1, unique_vars, allele_frq, read_depth, sig_diff_count, sig_equiv_count,
                                                pass_count, fail_count, unknown_count]})
            else:
                mydict[dict_key][0] += 1
                mydict[dict_key][1].add_one_sample(unique_var_id)
                mydict[dict_key][2] += allele_frq
                mydict[dict_key][3] += read_depth
                mydict[dict_key][4] += sig_diff_count
                mydict[dict_key][5] += sig_equiv_count
                mydict[dict_key][6] += pass_count
                mydict[dict_key][7] += fail_count
                mydict[dict_key][8] += unknown_count

        def write_csv(self):
            out_dictionaries = [self.het_variant_dict, self.hom_variant_dict]
            for mydict in out_dictionaries:
                for key in mydict:
                    mydict[key] = [mydict[key][item] / float(mydict[key][0])
                                              if item != 0 and item != 1 else mydict[key][item]
                                              for item in range(len(mydict[key]))]
                    mydict[key][1] = len(mydict[key][1])

            variant_stats_dir = self.project_config['var_stats_dir']
            het_csv_file = variant_stats_dir + "/gene_sumstats_het.csv"
            hom_csv_file = variant_stats_dir + "/gene_sumstats_hom.csv"

            csv_files = [het_csv_file, hom_csv_file]
            for i in range(len(csv_files)):
                csv_out_writer = csv.writer(open(csv_files[i], "w"), delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                csv_out_writer.writerow(["GENE"] + self.dict_header)
                for key in out_dictionaries[i]:
                    entry = [str(item) for item in out_dictionaries[i][key]]
                    new_row = [key] + entry
                    csv_out_writer.writerow(new_row)

    class __SampleSumStats:

        def __init__(self, var_stats_header, project_config, mongodb):
            self.project_config = project_config
            self.mongodb = mongodb

            self.dict_header = ["Total_Count", "Average_Allele_Freq", "Average_Read_Depth", "Sig_Diff_Perc",
                       "Sig_Equiv_Perc", "Pass_Perc", "Fail_Perc", "Unknown_Perc"]
            self.het_variant_dict = {}
            self.hom_variant_dict = {}
            self.var_stats_header = var_stats_header

        def process_var(self, var):
            var = {self.var_stats_header[i]: var[i] for i in range(len(var))}

            allele_frq = float(var['ALLELE_FREQ'])
            read_depth = int(var['TOTAL_READS'])
            sig_diff = var['SIG_DIFF']
            sig_equiv = var['SIG_EQUIV']
            pass_fail = var['PASS/FAIL']
            sig_diff_count, sig_equiv_count, pass_count, fail_count, unknown_count \
                = VariantStats.get_sig_counts(sig_diff, sig_equiv, pass_fail)

            dict_key = var['SAMPLE']

            gt_class = MiscTools.get_gtclass(var['GT'])
            if gt_class == 'het':
                mydict = self.het_variant_dict
            elif gt_class == 'hom' or gt_class == 'wt':
                mydict = self.hom_variant_dict

            if dict_key not in mydict:
                mydict.update({dict_key: [1, allele_frq, read_depth, sig_diff_count, sig_equiv_count,
                                                pass_count, fail_count, unknown_count]})
            else:
                mydict[dict_key][0] += 1
                mydict[dict_key][1] += allele_frq
                mydict[dict_key][2] += read_depth
                mydict[dict_key][3] += sig_diff_count
                mydict[dict_key][4] += sig_equiv_count
                mydict[dict_key][5] += pass_count
                mydict[dict_key][6] += fail_count
                mydict[dict_key][7] += unknown_count

        def write_csv(self):
            out_dictionaries = [self.het_variant_dict, self.hom_variant_dict]
            for mydict in out_dictionaries:

                for key in mydict:
                    mydict[key] = [mydict[key][item] / float(mydict[key][0])
                                              if item != 0 else mydict[key][0]
                                              for item in range(len(mydict[key]))]

            variant_stats_dir = self.project_config['var_stats_dir']
            het_csv_file = variant_stats_dir + "/sample_sumstats_het.csv"
            hom_csv_file = variant_stats_dir + "/sample_sumstats_hom.csv"

            csv_files = [het_csv_file, hom_csv_file]
            for i in range(len(csv_files)):
                csv_out_writer = csv.writer(open(csv_files[i], "w"), delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                csv_out_writer.writerow(["SAMPLE"] + self.dict_header)
                for key in out_dictionaries[i]:
                    entry = [str(item) for item in out_dictionaries[i][key]]
                    new_row = [key] + entry
                    csv_out_writer.writerow(new_row)

    class __ProjectSumStats:

        def __init__(self, var_stats_header, project_config, mongodb):
            self.project_config = project_config
            self.mongodb = mongodb

            self.dict_header = ["Total_Het","Total_Hom", "Total_Count", "Unique_Variants", "Average_Allele_Freq", "Average_Read_Depth",
                       "Sig_Diff_Perc", "Sig_Equiv_Perc", "Pass_Perc", "Fail_Perc", "Unknown_Perc"]
            self.het_variant_dict = {}
            self.hom_variant_dict = {}
            self.var_stats_header = var_stats_header

        def process_var(self, var):
            var = {self.var_stats_header[i]: var[i] for i in range(len(var))}

            allele_frq = float(var['ALLELE_FREQ'])
            read_depth = int(var['TOTAL_READS'])
            sig_diff = var['SIG_DIFF']
            sig_equiv = var['SIG_EQUIV']
            pass_fail = var['PASS/FAIL']
            sig_diff_count, sig_equiv_count, pass_count, fail_count, unknown_count \
                = VariantStats.get_sig_counts(sig_diff, sig_equiv, pass_fail)

            project_name = self.project_config['project_name']
            dict_key = project_name

            unique_var_id = ",".join([var['CHROM'], var['POS'], var['REF'], var['ALT'], var['GT'], var['ALLELE']])

            gt_class = MiscTools.get_gtclass(var['GT'])
            if gt_class == 'het':
                mydict = self.het_variant_dict
            elif gt_class == 'hom' or gt_class == 'wt':
                mydict = self.hom_variant_dict

            if dict_key not in mydict:
                unique_vars = set()
                unique_vars.add(unique_var_id)

                mydict.update({dict_key: [1, unique_vars, allele_frq, read_depth, sig_diff_count, sig_equiv_count,
                                                pass_count, fail_count, unknown_count]})
            else:
                mydict[dict_key][0] += 1
                mydict[dict_key][1].add_one_sample(unique_var_id)
                mydict[dict_key][2] += allele_frq
                mydict[dict_key][3] += read_depth
                mydict[dict_key][4] += sig_diff_count
                mydict[dict_key][5] += sig_equiv_count
                mydict[dict_key][6] += pass_count
                mydict[dict_key][7] += fail_count
                mydict[dict_key][8] += unknown_count

        def write_csv(self):
            out_dictionaries = [self.het_variant_dict, self.hom_variant_dict]
            for mydict in out_dictionaries:
                for key in mydict:
                    mydict[key] = [mydict[key][item] / float(mydict[key][0])
                                              if item != 0 and item != 1 else mydict[key][item]
                                              for item in range(len(mydict[key]))]
                    mydict[key][1] = len(mydict[key][1])

            variant_stats_dir = self.project_config['var_stats_dir']
            het_csv_file = variant_stats_dir + "/project_sumstats_het.csv"
            hom_csv_file = variant_stats_dir + "/project_sumstats_hom.csv"

            csv_files = [het_csv_file, hom_csv_file]
            for i in range(len(csv_files)):
                csv_out_writer = csv.writer(open(csv_files[i], "w"), delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                csv_out_writer.writerow(["PROJECT"] + self.dict_header)
                for key in out_dictionaries[i]:
                    entry = [str(item) for item in out_dictionaries[i][key]]
                    new_row = [key] + entry
                    csv_out_writer.writerow(new_row)

    @staticmethod
    def pass_fail_stats(ttest_result, tost_result):
        sig_diff = False
        sig_equiv = False
        pass_fail = "PASS"

        if ttest_result < 0.05:
            sig_diff = True
        if tost_result < 0.05:
            sig_equiv = True
        if sig_diff is True and sig_equiv is False:
            pass_fail = "FAIL"
        elif sig_diff is True and sig_equiv is True:
            pass_fail = "UNKNOWN"
        elif sig_diff is False and sig_equiv is False:
            pass_fail = "UNKNOWN"

        return sig_diff, sig_equiv, pass_fail

    @staticmethod
    def get_sig_counts(sig_diff, sig_equiv, pass_fail):
        sig_diff_count = 0
        sig_equiv_count = 0
        pass_count = 0
        fail_count = 0
        unknown_count = 0

        if sig_diff == 'True':
            sig_diff_count = 1
        if sig_equiv == 'True':
            sig_equiv_count = 1

        if pass_fail == 'PASS':
            pass_count = 1
        elif pass_fail == 'FAIL':
            fail_count = 1
        elif pass_fail == 'UNKNOWN':
            unknown_count = 1

        return sig_diff_count, sig_equiv_count, pass_count, fail_count, unknown_count