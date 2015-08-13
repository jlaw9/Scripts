#! /usr/bin/env python2.7
__author__ = 'durrantmm'

from pymongo import MongoClient

client = MongoClient()
db = client['varman']

variants = db['Wales']
hotspots = db['Wales_hotspot']

var_count = 0
diff_count = 0
for var in variants.find():
    var_count += 1
    sample, chrom, pos, ref, alt, gt  = var['SAMPLE'], var['CHROM'], var['POS'], var['REF'], var['ALT'], var['GT_calc']
    variant = [sample, chrom, pos, ref, alt, gt, var['CALL']['RO'], var['CALL']['AO'], var['AF_calc']]

    search = {'SAMPLE': sample, "CHROM": chrom, "POS": pos, "REF": ref, "ALT": alt}

    match = hotspots.find_one(search)

    try:

        hotspot = [match['SAMPLE'], match['CHROM'], match['POS'], match['REF'], match['ALT'], match['GT_calc'],
                   match['CALL']['RO'], match['CALL']['AO'], match['AF_calc']]

        if variant[-2] != hotspot[-2] or variant[-3] != hotspot[-3]:
            diff_count += 1
            print "--------------"
            print "\t".join(["SAMPLE", "CHROM", "POS", "REF", "ALT", "GT_Calc", "RO", "AO"])
            print "\t".join([str(elem) for elem in variant]) + "\tORIGINAL"
            print "\t".join([str(elem) for elem in hotspot]) + "\tHOTSPOT"

    except TypeError:
        continue

print diff_count, var_count
