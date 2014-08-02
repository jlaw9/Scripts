#! /usr/bin/env python

import sys
import json
import os
import fnmatch
import re
from datetime import datetime as dt

project_dir = sys.argv[1]

if __name__ == "__main__":
	json_files = []
	# first, find all of the sample's json files
	for root, dirnames, filenames in os.walk(project_dir):
		for filename in fnmatch.filter(filenames, "*_QC.json*"):
			json_files.append(os.path.join(root, filename))

	# loop through the files, and fix the different metrics
	for json_file in json_files:

		# load the json_data
		json_data = json.load(open(json_file))
#		# for each run's json
#		json_data['project'] = 'Einstein'
#
#		if 'sample_folder' in json_data:
#			sample_path = json_data['sample_folder'].split("/")
#			if sample_path[4] != json_data['sample']:
#				print "ERROR: %s sample_path: %s does not match sample: %s"%(json_file, sample_path[4], json_data['sample'])
#				sys.exit(1)
#			if len(sample_path) > 5:
#				json_data['sample_folder'] = "/".join(sample_path[:5])
#
#		if 'torrent_suite_link' in json_data:
#			if 'proton' not in json_data:
#				if re.search("192.168.200.42", json_data['torrent_suite_link']):
#					json_data['proton'] = "PLU"
#				else:
#					if 'run_date' in json_data:
#						run_date = dt.strptime(json_data['run_date'], "%m/%d/%y")
#						mercury_date = dt(2014, 5, 20) # The day mercury began
#						if run_date < mercury_date:
#							json_data['proton'] = "NEP"
#						else:
#							json_data['proton'] = "MER"
#					else:
#						print "%s cannot choose proton yet"%json_file
#			if not re.search("192.168.200.42", json_data['torrent_suite_link']) and not re.search("192.168.200.41", json_data['torrent_suite_link']):
#				run_id = json_data['torrent_suite_link'].split('/')[-1]
#				if 'proton' in json_data:
#					if json_data['proton'] == "PLU":
#						json_data['torrent_suite_link'] = "http://192.168.200.42/report/" + run_id
#					else:
#						json_data['torrent_suite_link'] = "http://192.168.200.41/report/" + run_id
#				else:
#					print "%s cannot fix ts_link"%json_file
		
		# The _QC.json fix
		json_data['analysis']['settings']['beg_bed'] = "/rawdata/support_files/BED/startLoci_Ampliseq.bed"
		json_data['analysis']['settings']['end_bed'] = "/rawdata/support_files/BED/endLoci_Ampliseq.bed"
		
		# dump the json file
		with open(json_file, 'w') as newJSONFile:
			json.dump(json_data, newJSONFile, sort_keys=True, indent=4)
		print json_file + " fixed!"
