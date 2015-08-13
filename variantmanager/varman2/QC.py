#! /usr/bin/env python2.7
__author__ = 'durrantmm'

import stats
import genotypetools

"""
QC methods to use for filtering variants.
"""

class QC:

    def __init__(self):
        self.read_depth_cutoff = 30
        self.equiv_margin = 0.15

    def variant_QC(self, new_variant_entry):

        read_depth = new_variant_entry['READ_DEPTH']
        fro = new_variant_entry['FRO']
        fao = new_variant_entry['FAO']
        gt = new_variant_entry['GT_calc']

        coverage_check = self.coverage_check(read_depth)
        if isinstance(fao, list):
            # IN CASE THERE ARE MULTIPLE ALTERNATE ALLELES
            alleles = [fro] + fao

            multi_allele_check = self.multi_allele_check(alleles)

            if multi_allele_check == 'FAIL':
                af_check = 'FAIL'
            else:
                fao, read_depth = genotypetools.get_two_alleles(alleles)
                af_check = self.af_check(gt, fao, read_depth)

        else:
            # SINGLE ALTERNATE ALLELE VARIANTS
            multi_allele_check = "PASS"
            af_check = self.af_check(gt, fao, read_depth)

        if [coverage_check, af_check, multi_allele_check] == ['PASS','PASS','PASS']:
            final_qc_status = 'PASS'
        else:
            final_qc_status = 'FAIL'

        return coverage_check, af_check, multi_allele_check, final_qc_status

    def coverage_check(self, read_depth):

        if read_depth >= self.read_depth_cutoff:
            return 'PASS'
        else:
            return 'FAIL'

    def multi_allele_check(self, alleles):

        if len(alleles) > 2:
            multi_allele_count = 0

            for al in alleles:
                if al > 0:
                    multi_allele_count += 1

            if multi_allele_count > 2:
                return "FAIL"
            else:
                return "PASS"

        else:
            return "PASS"

    def af_check(self, gt, fao, read_depth):
        zygos = genotypetools.get_zygosity(gt)

        ttest_result = stats.performTTest(fao, read_depth, zygos)
        tost_result = stats.performTOST(fao, read_depth, self.equiv_margin, zygos)

        pass_fail = stats.pass_fail_stats(ttest_result, tost_result)

        if pass_fail[-1] == 'PASS':

            return 'PASS'
        else:

            return 'FAIL'


