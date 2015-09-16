__author__ = 'matt'

import os
import sys
import json
from glob import glob

matches = []
for root, dirnames, filenames in os.walk(sys.argv[1]):
    matches += glob(root+"/results_QC.json")

for match in matches:
    if "QC/results" in match:
        results_file = json.load(open(match,'r'))

        three_by_three = results_file['QC_comparisons']['all']
        print match, esults_file['QC_comparisons']['all'].keys()
        continue
        print match.split("/")[-2]
        print "error rate: %s" % three_by_three['error_rate']
        print "% available bases: %s" % three_by_three['perc_avail_bases']
        print "# of GTs reassigned: %s" % three_by_three['reassigned_GTs']
        print "\tWT\tHET\tHOM\tSum:"
        print "WT\t%d\t%d\t%d\t%d" % (three_by_three['WT_WT'], three_by_three['WT_HET'], three_by_three['WT_HOM'],
                                     sum([three_by_three['WT_WT'], three_by_three['WT_HET'], three_by_three['WT_HOM']]))
        print "HET\t%d\t%d\t%d\t%d" % (three_by_three['HET_WT'], three_by_three['HET_HET'], three_by_three['HET_HOM'],
                                     sum([three_by_three['HET_WT'], three_by_three['HET_HET'], three_by_three['HET_HOM']]))
        print "HOM\t%d\t%d\t%d\t%d" % (three_by_three['HOM_WT'], three_by_three['HOM_HET'], three_by_three['HOM_HOM'],
                                     sum([three_by_three['HOM_WT'], three_by_three['HOM_HET'], three_by_three['HOM_HOM']]))
        print "Sum:\t%d\t%d\t%d\t%d" % (sum([three_by_three['WT_WT'], three_by_three['HET_WT'], three_by_three['HOM_WT']]),
                                        sum([three_by_three['WT_HET'], three_by_three['HET_HET'], three_by_three['HOM_HET']]),
                                        sum([three_by_three['WT_HOM'], three_by_three['HET_HOM'], three_by_three['HOM_HOM']]),
                                        three_by_three['total_eligible_bases'])