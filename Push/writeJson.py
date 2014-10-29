#! /usr/bin/env python

import sys
import os
import re
import json
from optparse import OptionParser

# Set up the parser
parser = OptionParser()

parser.add_option('-b', '--barcode', dest='barcode', help="The Run's barode. Only used for barcoded runs.")
parser.add_option('-B', '--bam', dest='bam', help="The name of the bam file")
parser.add_option('-r', '--run_name', dest='runName', help="The Run's name")
parser.add_option('-s', '--sample', dest='sample', help="The sample's name")
parser.add_option('-p', '--proj_path', dest='projectPath', help="The Project path the files were pushed to on the server")
parser.add_option('-o', '--orig_path', dest='origPath', help="The original path the bam and other files were pushed from on the server")
parser.add_option('-P', '--proton', dest='proton', help="The proton used to sequence the data")
parser.add_option('-i', '--ip_address', dest='ip', help="The proton's server's ip address")
parser.add_option('-v', '--ts_version', dest='tsVersion', help="The TS version used to generate the BAM file")
parser.add_option('-j', '--json', dest='json', help="The name of the .json file to be written")
parser.add_option('-e', '--extra_json', dest='extraJson', help="Another json file holding more information")

(options, args) = parser.parse_args()

reportNum = options.origPath.split('_')[-1]
ip = options.ip
# If the ip passed in is ionadmin@ip, then just get the ip
if re.search("@", ip):
	ip = ip.split("@")[-1]

jsonData = {
	"analysis": { 
		"files": [
			options.bam
			], 
		"settings": {
			"queue":"all.q", # default queue is all.q, but it can be overriden here
			"priority":"0", # Qsub priority
			"mark_dups":"false", # Default is to remove the duplicates. set this to true to mark the duplicates. 
			"capture_type":"AmpliSeq", # for targetseq, use TargetSeq or Target_Seq
			"qc_merged_bed": "/rawdata/support_files/BED/AmpliSeq-Exome_merged.bed", # used for cov analysis
			"qc_unmerged_bed": "/rawdata/support_files/BED/AmpliSeq-Exome_unmerged.bed", # used for cov analysis
			"tvc_bed": "/rawdata/support_files/BED/AmpliSeq-Exome.bed", # this option is for ampliseq only. leave this off for targetseq.
			"tvc_parameter_json": "/rawdata/support_files/parameter_sets/ampliseqexome_germline_highstringency_p1_4.0_20130920_Updated_parameters.json"
			}, 
		"type": "qc_tvc"
	}, 
	"name": options.runName, 
	"orig_path": options.origPath,
	"project": "Einstein", 
	"proton": options.proton,
	"sample": options.sample, 
	"sample_folder": "%s/%s"%(options.projectPath, options.sample),
	"status": "pending", 
	"torrent_suite_link": "http://%s/report/%s"%(ip, reportNum),
	"ts_version": options.tsVersion
}

# default bam file name
if not options.bam:
	jsonData['analysis']['files'] = [ "rawlib.bam" ]

if options.barcode:
	jsonData['barcode'] == options.barcode

if options.extraJson:
	# If the json file is found, use it as the dictionary
	if os.path.isfile(options.extraJson):
		print "Adding " + option.extraJson + " to the json data."
		extraJson = json.load(open(option.extraJson))
		# Union the two dictionaries together. If a field is found in both dictionaries, then whatever's in extraJson will overwrite what is in jsonData.
		# Example: dict1 = { "a":1, "b": 2}		dict2 = { "b":3, "c": 4}  dict(dict1.items() + dict2.items()) 	{'a': 1, 'c': 4, 'b': 3}
		jsonData = dict(jsonData.items() + extraJson.items())
	else:
		print option.extraJson + " file was not found. Skipping this option."


# dump the json file
with open(options.json, 'w') as out:
	json.dump(jsonData, out, sort_keys=True, indent = 2)
