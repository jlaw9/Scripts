#! /usr/bin/env python2.7
__author__ = 'durrantmm'

import copy

class VariantCall:
    def __init__(self, record):
        self.record = record

    def get_new_variant_calls(self, sample_name = None):

        calls = []
        for call in self.record.samples:
            new_var_entry = {}
            if sample_name is None:
                new_var_entry.update({"SAMPLE": call.sample})
            else:
                new_var_entry.update({"SAMPLE": sample_name})
            new_var_entry.update({"CHROM": self.record.CHROM})

            if "X" in new_var_entry['CHROM']:
                new_var_entry['CHROM'] = 23
            elif "Y" in new_var_entry['CHROM']:
                new_var_entry['CHROM'] = 24
            else:
                new_var_entry['CHROM'] = int(new_var_entry['CHROM'].strip("chr"))

            new_var_entry.update({"POS": self.record.POS})
            new_var_entry.update({"ID": self.record.ID})
            new_var_entry.update({"REF": self.record.REF})
            new_var_entry.update({"ALT": [str(alt) for alt in self.record.ALT]})

            keys = self.record.FORMAT.split(":")
            call_data = {key: call[key] for key in keys}
            try:
                FAO, FRO = call_data['FAO'], call_data['FRO']

            except KeyError:
                FAO, FRO = call_data['AO'], call_data['RO']

            if isinstance(FAO, list):
                gt_calc, freq_dict = self.calculate_gt_from_list(FAO, FRO)
                new_var_entry.update({"AF_calc": [freq_dict[af] for af in sorted(freq_dict.keys())]})
            else:
                gt_calc, af = self.calculate_gt(FAO, FRO)
                new_var_entry.update({"AF_calc": af})

            new_var_entry.update({"GT_calc": gt_calc})

            new_var_entry.update({"CALL": call_data})

            calls.append(new_var_entry)

        return calls

    @staticmethod
    def calculate_gt(FAO, FRO):
        allele_num = 1
        if float(FAO+FRO) == 0.0:
            return './.', 0.0
        else:
            af = float(FAO) / float(FAO + FRO)

            if af < 0.2:
                gt = '0/0'
            elif 0.2 <= af <= 0.8:
                gt = '0/%d' % allele_num
            elif af > 0.8:
                gt = '%d/%d' % (allele_num, allele_num)

            return gt, af

    @staticmethod
    def calculate_gt_from_list(FAO, FRO):
        freq_dict = {i + 1: 0.0 for i in range(len(FAO))}
        if float(sum(FAO)+FRO) == 0.0:
            return './.', {0: 0.0}
        else:
            freq_dict.update({0: float(FRO) / float(sum(FAO) + FRO)})

            for i in range(len(FAO)):
                allele_num = i + 1
                all_freq = float(FAO[i]) / float(sum(FAO) + FRO)

                freq_dict.update({allele_num: all_freq})

            out_freq_dict = copy.deepcopy(freq_dict)
            max_allele = (max(freq_dict, key=freq_dict.get), freq_dict[max(freq_dict, key=freq_dict.get)])
            freq_dict.pop(max_allele[0])
            second_max_allele = (max(freq_dict, key=freq_dict.get), freq_dict[max(freq_dict, key=freq_dict.get)])

            if max_allele[1] > 0.8:
                gt = '%d/%d' % (max_allele[0], max_allele[0])
            elif max_allele[1] <= 0.8 and second_max_allele[1] >= 0.2:
                gt_list = sorted([max_allele[0], second_max_allele[0]])
                gt = '%d/%d' % (gt_list[0], gt_list[1])
            else:
                gt = './.'

            return gt, out_freq_dict