#! /usr/bin/env python2.7
__author__ = 'durrantmm'

from varman2.mongotools import variants_mongo, hotspot_mongo, mongo, sampleinfo_mongo
"""
varman2.vcftools

This module contains a few useful tools for understanding genotypes.
"""

def create_vcf_gt_orig_no_qc(sample, out_dir, db):
    sample_vars = variants_mongo.get_sample_vars(sample, 'hotspot', db)

    out_vcf = '%s/%s.vcf' % (out_dir, sample)
    with open(out_vcf, "w") as out_file:
        vcf_header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t%s\n" % sample
        out_file.write(vcf_header)

        for var in sample_vars:

            chrom, pos, ref, alt = str(var['CHROM']), str(var['POS']), var['REF'], ",".join(var['ALT'])

            gt = var['GT_orig']
            if gt is None:
                gt = './.'

            list_entry = [chrom, pos, '.', str(ref), str(alt)]
            variant = list_entry + ['.', '.', 'DP=%s' % var['READ_DEPTH'], 'GT', gt]
            out_file.write("\t".join([str(val) for val in variant]) + "\n")

def create_vcf_for_annotation(sample, type, out_dir):
    sample_vars = variants_mongo.get_sample_vars(sample, type)

    out_vcf = '%s/%s.vcf' % (out_dir, sample)
    with open(out_vcf, "w") as out_file:
        vcf_header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t%s\n" % sample
        out_file.write(vcf_header)

        client, db = mongo.get_connection()
        for var in sample_vars:
            chrom, pos, ref, alt = var['CHROM'], var['POS'], var['REF'], var['ALT']

            if not hotspot_mongo.has_annotation(chrom, pos, ref, alt, db):
                chrom, pos, ref, alt = str(chrom), str(pos), ref, ",".join(alt)
                gt = var['GT_orig']
                if gt is None:
                    gt = './.'

                list_entry = [chrom, pos, '.', str(ref), str(alt)]
                variant = list_entry + ['.', '.', 'DP=%s' % var['READ_DEPTH'], 'GT', gt]
                out_file.write("\t".join([str(val) for val in variant]) + "\n")
        client.close()
    return out_vcf

def create_vcf_for_annotation_all_samples(out_dir):

    out_vcf = '%s/%s.vcf' % (out_dir, 'all_samples')
    vcf_header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tALL\n"

    hotspot_vars = hotspot_mongo.get_hotspot_vars()
    print hotspot_vars.count()
    with open(out_vcf, "a") as out_file:
        out_file.write(vcf_header)
        client, db = mongo.get_connection()
        for var in hotspot_vars:
            chrom, pos, ref, alt = var['CHROM'], var['POS'], var['REF'], var['ALT']

            if not hotspot_mongo.has_annotation(chrom, pos, ref, alt, db):
                chrom, pos, ref, alt = str(chrom), str(pos), ref, ",".join(alt)
                gt = './.'
                if gt is None:
                    gt = './.'

                list_entry = [chrom, pos, '.', str(ref), str(alt)]
                variant = list_entry + ['.', '.', '.', 'GT', gt]
                out_file.write("\t".join([str(val) for val in variant]) + "\n")
        client.close()

    return out_vcf