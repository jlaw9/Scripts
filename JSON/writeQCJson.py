#! /usr/bin/env python

import sys
import json
import os

sample_dir = sys.argv[1]

if __name__ == "__main__":
	print 'writing a json for ' + sample_dir
	jsonQC = json.load(open("E0002_QC.json"))
	jsonQC['sample'] = sample_dir.split('/')[-1]
	jsonQC['sample_folder'] = sample_dir
	jsonQC['output_folder'] = sample_dir + "/QC"

	jsonQCFile = "%s/%s_QC.json"%(jsonQC['output_folder'], jsonQC['sample'])

	# dump the json file
	with open(jsonQCFile, 'w') as newJSONFile:
		json.dump(jsonQC, newJSONFile, sort_keys=True, indent=4)
	print "%s was written"%jsonQCFile

