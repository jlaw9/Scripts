#! /usr/bin/env python

import sys
import json
import os

if len(sys.argv) < 2:
	print "USAGE: %s <sample_dir> <json_example>"
	sys.exit(8)

sample_dir = sys.argv[1]
json_example = sys.argv[2]

if __name__ == "__main__":
	print 'writing a json for ' + sample_dir
	jsonQC = json.load(open(json_example))
	jsonQC['sample'] = sample_dir.split('/')[-1]
	jsonQC['sample_folder'] = sample_dir

	jsonQCFile = "%s/%s.json"%(jsonQC['output_folder'], jsonQC['sample'])

	# dump the json file
	with open(jsonQCFile, 'w') as newJSONFile:
		json.dump(jsonQC, newJSONFile, sort_keys=True, indent=4)
	print "%s was written"%jsonQCFile

