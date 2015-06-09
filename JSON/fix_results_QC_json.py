#! /usr/bin/env python

import json
import os
import sys
import shutil

results_QC = json.load(open(sys.argv[1]))

#normal_normal = {}
#tumor_normal = {}
#tumor_tumor = {}
#chr1normal_normal = {}
#chr1tumor_normal = {}
#chr1tumor_tumor = {}
germline_germline = {}
for QC_comp in results_QC['QC_comparisons']:
	germline_germline[QC_comp] = results_QC['QC_comparisons'][QC_comp]

new_results = {'QC_comparisons': {'chr1': {'germline_germline': germline_germline}}}
new_results['sample_name'] = results_QC['sample']
new_results['sample'] = results_QC['sample']
new_results['json_type'] = 'QC_comparisons'

with open(sys.argv[1], 'w') as out_json:
	json.dump(new_results, out_json, sort_keys=True, indent=4)

shutil.move(sys.argv[1], sys.argv[2])
