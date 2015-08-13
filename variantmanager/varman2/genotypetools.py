#! /usr/bin/env python2.7
__author__ = 'durrantmm'

import copy

"""
mongoDAOs.mongotools.variants_mongo

This module contains a few useful tools for understanding genotypes.
"""

def calculate_gt(record, call):
        keys = record.FORMAT.split(":")
        call_data = {key: call[key] for key in keys}
        try:
            fao, fro = call_data['FAO'], call_data['FRO']

        except KeyError:
            fao, fro = call_data['AO'], call_data['RO']

        if isinstance(fao, list):
            read_depth = fro + sum(fao)
            gt_calc, freq_dict = __calculate_gt_from_list(fao, fro)
            af = [freq_dict[af] for af in sorted(freq_dict.keys())]

        else:
            read_depth = fro + fao
            gt_calc, af = __calculate_gt_single(fao, fro)

        return fao, fro, af, gt_calc, read_depth

def __calculate_gt_single(FAO, FRO):
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

def __calculate_gt_from_list(FAO, FRO):

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

def get_zygosity(gt):

        if gt == './.':
            return 'nocall'
        elif gt.split("/")[0] != gt.split("/")[1]:
            if '0' in gt.split('/'):
                return 'het'
            else:
                return 'het_alt'
        elif gt.split('/')[0] == '0' and gt.split('/')[0] == '0':
            return 'wt'
        elif gt.split('/')[0] == gt.split('/')[1]:
            return 'hom'

def get_two_alleles(multi_alleles):
    if multi_alleles == [0]*len(multi_alleles):
        return 0, 0

    two_alleles = []

    while len(multi_alleles) > 0:
        al = multi_alleles.pop(0)
        if al > 0:
            two_alleles.append(al)

    if len(two_alleles) == 1:
        fao = two_alleles[0]
        total_depth = fao
    else:
        fao = two_alleles[1]
        total_depth = sum(two_alleles)

    return fao, total_depth

def get_genotype_alleles(ref, alt, gt):
    alleles = [ref] + alt
    all_num1 = int(gt.split("/")[0])
    all_num2 = int(gt.split("/")[1])

    return alleles[all_num1], alleles[all_num2]




