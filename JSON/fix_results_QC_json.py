#! /usr/bin/env python

import json
import os
import sys

results_QC = json.load(open(sys.argv[1]))

normal_normal = {}
tumor_normal = {}
tumor_tumor = {}
chr1normal_normal = {}
chr1tumor_normal = {}
chr1tumor_tumor = {}
for QC_comp in results_QC['QC_comparisons']:
	if 'chr' in results_QC['QC_comparisons'][QC_comp] and results_QC['QC_comparisons'][QC_comp]['chr'] == True:
		if results_QC['QC_comparisons'][QC_comp]['run1_type'] == "normal" and  results_QC['QC_comparisons'][QC_comp]['run2_type'] == "normal":
			chr1normal_normal[QC_comp[5:]] = results_QC['QC_comparisons'][QC_comp]
		if results_QC['QC_comparisons'][QC_comp]['run1_type'] == "normal" and  results_QC['QC_comparisons'][QC_comp]['run2_type'] == "tumor":
			chr1tumor_normal[QC_comp[5:]] = results_QC['QC_comparisons'][QC_comp]
		if results_QC['QC_comparisons'][QC_comp]['run1_type'] == "tumor" and  results_QC['QC_comparisons'][QC_comp]['run2_type'] == "tumor":
			chr1tumor_tumor[QC_comp[5:]] = results_QC['QC_comparisons'][QC_comp]
	else:
		if results_QC['QC_comparisons'][QC_comp]['run1_type'] == "normal" and  results_QC['QC_comparisons'][QC_comp]['run2_type'] == "normal":
			normal_normal[QC_comp] = results_QC['QC_comparisons'][QC_comp]
		if results_QC['QC_comparisons'][QC_comp]['run1_type'] == "normal" and  results_QC['QC_comparisons'][QC_comp]['run2_type'] == "tumor":
			tumor_normal[QC_comp] = results_QC['QC_comparisons'][QC_comp]
		if results_QC['QC_comparisons'][QC_comp]['run1_type'] == "tumor" and  results_QC['QC_comparisons'][QC_comp]['run2_type'] == "tumor":
			tumor_tumor[QC_comp] = results_QC['QC_comparisons'][QC_comp]

new_results = {}
new_results['QC_comparisons'] = {}
new_results['QC_comparisons']['chr1'] = {}
new_results['QC_comparisons']['chr1']['normal_normal'] = chr1normal_normal
new_results['QC_comparisons']['chr1']['tumor_normal'] = chr1tumor_normal
new_results['QC_comparisons']['chr1']['tumor_tumor'] = chr1tumor_tumor
new_results['QC_comparisons']['all'] = {}
new_results['QC_comparisons']['all']['normal_normal'] = normal_normal
new_results['QC_comparisons']['all']['tumor_normal'] = tumor_normal
new_results['QC_comparisons']['all']['tumor_tumor'] = tumor_tumor
new_results['sample_name'] = results_QC['sample']
new_results['sample'] = results_QC['sample']
new_results['json_type'] = 'QC_comparisons'

with open(sys.argv[1], 'w') as out_json:
	json.dump(new_results, out_json, sort_keys=True, indent=4)
