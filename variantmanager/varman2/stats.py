#! /usr/bin/env python2.7
__author__ = 'durrantmm'

import statsmodels.stats.weightstats as smws
from scipy import stats


def performTTest(alt_reads, tot_reads, zygos):
    if zygos == 'nocall' or tot_reads < 2:
        return 1.0

    sample_reads = ([1.0] * alt_reads) + ([0.0] * (tot_reads - alt_reads))

    if zygos == 'het' or zygos == 'het_alt':
        expected = 0.5
    if zygos == 'hom':
        expected = 1.0
    if zygos == 'wt':
        expected = 0.0

    test_result = stats.ttest_1samp(sample_reads, expected)
    return test_result[1]

def performTOST(alt_reads, tot_reads, delta, zygos):
    if zygos == 'nocall' or tot_reads < 2:
        return 0.0

    sample_reads = ([1.0] * alt_reads) + ([0.0] * (tot_reads-alt_reads))

    if zygos == 'het' or zygos == 'het_alt':
        expected = 0.5
    if zygos == 'hom':
        expected = 1.0
    if zygos == 'wt':
        expected = 0.0

    samp1 = smws.DescrStatsW(sample_reads)
    tost_result = samp1.ttost_mean(expected - delta, expected + delta)

    return tost_result[0]

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