#! /usr/bin/env python

from optparse import OptionParser
import sys
import json
import os
import fnmatch
import re
from datetime import datetime as dt
import glob
import shutil

class Get_Merged_Data:
	def __init__(self, options):
		self.options = options
		#sample = options.sample
		samples = [options.sample]
		# if the project was specified, find all of the samples in the project, and loop through the samples
		if self.options.project:
			samples = self.find_samples(options.project)
		for sample in samples:
			if options.copy_merged_csv:
				self.copy_merged_csv(os.path.abspath(sample))

	# copy the merged csv of this sample to the specified directoy.
	def copy_merged_csv(self, sample_path):
		sample_name = sample_path.split('/')[-1]
		sample_json = "%s/%s.json"%(sample_path, sample_name)
		try:
			json_data = json.load(open(sample_json))
		except ValueError:
			#print traceback.format_exc().strip()
			print "ERROR: %s Unable to load the json file %s. Skipping this sample"%(sample_name, sample_json)
		if 'final_normal_json' in json_data and 'final_tumor_json' in json_data:
			# we can copy the matched variants csv
			try:
				normal_json = json.load(open(json_data['final_normal_json']))
				tumor_json = json.load(open(json_data['final_tumor_json']))
			except ValueError:
				#print traceback.format_exc().strip()
				print "ERROR: %s Unable to load the json file %s or %s. Skipping this sample"%(sample_name, json_data['final_normal_json'], json_data['final_tumor_json'])
			qc_comparison = "all%svs%s"%(normal_json['run_name'], tumor_json['run_name'])
			if os.path.isdir("%s/%s"%(json_data['qc_folder'], qc_comparison)):
				command = "cp %s/%s/matched_variants.csv %s/%s_final_matched_variants.csv"%(json_data['qc_folder'], qc_comparison, self.options.copy_merged_csv, json_data['sample_name'])
				if os.system(command) == 0:
					print "%s_final_matched_variants.csv copied successfully"%json_data['sample_name']
				else:
					print "ERROR: %s_final_matched_variants.csv Failed to copy..."%json_data['sample_name']
		else:
			print '%s is not ready to copy the final file'%json_data['sample_name']


	# find the samples in the project
	def find_samples(self, project):
		samples = glob.glob(project+"/A_*")
		samples += glob.glob(project+"/B_*")
		return samples

	# @param path the path of the json file
	# @json_data the json dictionary to be written
	def write_json(self, path, json_data):
		with open(path, 'w') as newJobFile:
			json.dump(json_data, newJobFile, sort_keys=True, indent=4)


	# find all of the json files in this sample
	def find_jsons(self, sample_path, json_filter=''):
		json_files = []
		# first, find all of the sample's json files
		for root, dirnames, filenames in os.walk(sample_path):
			for filename in fnmatch.filter(filenames, "*.json"):
				json_file = os.path.join(root, filename)
				json.load(open(json_file))
				if json_filter == '' or json_filter in json_file:
					json_files.append(json_file)
		return json_files


if __name__ == "__main__":
	# set up the option parser
	parser = OptionParser()
	
	# add the options to parse
	parser.add_option('-s', '--sample', dest='sample', help='move the specified sample')
	parser.add_option('-p', '--project', dest='project', help='find all of the samples in a specified directory, then either move them (-n), or make json files (-j)')
	parser.add_option('-c', '--copy_merged_csv', dest='copy_merged_csv', help='Location to copy the merged_csv files to')

	(options, args) = parser.parse_args()

	if not options.copy_merged_csv or (not options.sample and not options.project):
		print "USAGE_ERROR: -c and (-s or -p) are required"
		parser.print_help()
		sys.exit(1)

	if not os.path.isdir(options.copy_merged_csv):
		os.mkdir(options.copy_merged_csv)

	if options.project and not os.path.isdir(options.project):
		print "USAGE_ERROR: --project %s is not found!"%options.project
		parser.print_help()
		sys.exit(1)

	if options.sample and not os.path.isdir(options.sample):
		print "USAGE_ERROR: --sample %s is not found!"%options.sample
		parser.print_help()
		sys.exit(1)

	Get_Merged_Data(options)

