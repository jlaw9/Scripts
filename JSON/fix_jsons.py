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

class Fix_Jsons:
	def __init__(self, options):
		self.options = options
		#sample = options.sample
		samples = [options.sample]
		if self.options.project:
			samples = self.find_samples(options.project)
		for sample in samples:
			if options.copy_merged_csv:
				self.copy_merged_csv(os.path.abspath(sample))
			else:
				self.fix_jsons(os.path.abspath(sample))

	def copy_merged_csv(self, sample_path):
		sample_name = sample_path.split('/')[-1]
		print sample_name
		sample_json = "%s/%s.json"%(sample_path, sample_name)
		json_data = json.load(open(sample_json))
		if 'final_normal_json' in json_data and 'final_tumor_json' in json_data:
			# we can copy the matched variants csv
			normal_json = json.load(open(json_data['final_normal_json']))
			tumor_json = json.load(open(json_data['final_tumor_json']))
			qc_comparison = "all%svs%s"%(normal_json['run_name'], tumor_json['run_name'])
			if os.path.isdir("%s/%s"%(json_data['qc_folder'], qc_comparison)):
				command = "cp %s/%s/matched_variants.csv %s/%s_final_matched_variants.csv"%(json_data['qc_folder'], qc_comparison, self.options.copy_merged_csv, json_data['sample_name'])
				if os.system(command) == 0:
					print "copied the %s_final_matched_variants.csv successfully"%json_data['sample_name']
				else:
					print "Failed to copy the %s_final_matched_variants.csv..."%json_data['sample_name']
		else:
			print '%s is not ready to copy the final file'%json_data['sample_name']


	def fix_jsons(self, sample_path):
		orig_path = sample_path
		print "fixing the json files for sample:",sample_path
		new_sample_path = sample_path
		# set the new path of the sample and fix the paths of the sample and run jsons (if they're there)
		if self.options.new_path:
			self.options.new_path = os.path.abspath(self.options.new_path)
			# fix the PNET samples
			sample_name = sample_path.split('/')[-1]
			sample_json = "%s/%s.json"%(sample_path, sample_name)
			self.ffpe = True
			try:
				if int(sample_name) > 99:
					print "Fresh sample"
					shutil.move("%s/%s.json"%(sample_path, sample_name), "%s/A_%s.json"%(sample_path, sample_name))
					sample_name = "A_%s"%sample_name
					sample_path = "%s/%s"%('/'.join(sample_path.split('/')[:-1]), sample_name)
					shutil.move(orig_path, sample_path)
					new_sample_json = "%s/A_%s.json"%(sample_path, sample_name)
					self.ffpe = False
				else:
					print "FFPE sample"
					shutil.move("%s/%s.json"%(sample_path, sample_name), "%s/B_0%s.json"%(sample_path, sample_name))
					sample_name = "B_0%s"%sample_name
					sample_path = "%s/%s"%('/'.join(sample_path.split('/')[:-1]), sample_name)
					shutil.move(orig_path, sample_path)
					new_sample_json = "%s/B_0%s.json"%(sample_path, sample_name)
					self.ffpe = True 
				sample_json = new_sample_json
			except ValueError:
				pass
			new_sample_path = "%s/%s"%(self.options.new_path, sample_path.split('/')[-1])	
			if os.path.isfile(sample_json):
				print "Fixing paths for %s"%(new_sample_path)
				self.fix_paths(orig_path, new_sample_path, sample_name, [sample_json])
			# move the sample to the specified new path
			if self.options.move:
				shutil.move(sample_path, new_sample_path)
				
		# if the user specified, fix the create the sample and run json files
		if self.options.ex_json:
			self.fix_sample_json(self.options.ex_json, new_sample_path)

		# if the user 
		if self.options.fix_qc:
			self.fix_results_QC_json(new_sample_path)

		if self.options.merged:
			self.combine_runs_merged(os.path.abspath(new_sample_path), os.path.abspath(options.merged))


	def fix_sample_json(self, ex_json, sample_path):
			sample_name = sample_path.split('/')[-1]
			self.ex_json = json.load(open(ex_json))
			# edit the sample's json file with this sample's info. The other metrics in the sample JSON file should already be set. 
			self.ex_json["json_file"] = "%s/%s.json"%(sample_path, sample_name) 
			self.ex_json["results_qc_json"] = "%s/QC/results_QC.json"%sample_path 
			self.ex_json["qc_folder"] = "%s/QC"%sample_path 
			self.ex_json["output_folder"] = sample_path 
			runs = self.find_runs(sample_path)
			new_runs = []
			for run in runs:
				# fix the run_jsons
				new_runs.append(self.fix_run_json(sample_path, sample_name, run))
			self.ex_json["runs"] = new_runs
			self.ex_json["sample_name"] = sample_name
			self.ex_json["sample_folder"] = sample_path
			self.ex_json["sample_status"] = 'pushed'
			self.ex_json["status"] = 'pending'
			self.write_json(self.ex_json['json_file'], self.ex_json)

	
	def find_runs(self, sample_path):
		runs = []
		# find the runs
		if self.ex_json['sample_type'] == 'tumor_normal':
			#runs += self.find_jsons(sample_path, 'name')
			run_paths = ["%s/Normal/N-[0-9]/*.json"%sample_path, "%s/Normal/N-[0-9]/*.json_read"%sample_path, "%s/Tumor/T-[0-9]/*.json"%sample_path, "%s/Tumor/T-[0-9]/*.json_read"%sample_path]
			for run_path in run_paths:
				runs += glob.glob(run_path)
		else:
			runs = glob.glob("%s/Run[0-9]/*.json"%sample_path)
		print "found runs:",runs
		return runs


	def fix_run_json(self, sample_path, sample_name, run):
		run_json = json.load(open(run))
		# if this run is already good to go, then skip it.
		if 'json_type' in run_json:
			return run
		else:
			run_path = '/'.join(run.split('/')[:-1])
			# fix the vcf file
			if os.path.isfile("%s/tvc4.2_out/TSVC_variants.vcf"%run_path):
				shutil.move("%s/tvc4.2_out/TSVC_variants.vcf"%run_path, "%s/4.2_TSVC_variants.vcf"%run_path)
			bam_name = glob.glob("%s/*.bam"%run_path)[0].split('/')[-1]
			run_name = run.split('/')[-2]
			run_num = run_path[-1]
			json_name = "%s_%s.json"%(sample_name,run_name)
			if self.ex_json['sample_type'] == 'tumor_normal':
				run_type = run_path.split('/')[-2].lower()
			else:
				run_type = 'germline'
			# Write the run's json file which will be used mainly to hold metrics.
			jsonData = {
				"analysis": {
					"files": [bam_name]
				},
				"run_data": run_json['run_data'],
				"json_file": "%s/%s"%(run_path,json_name), 
				"json_type": "run",
				"run_folder": run_path, 
				"run_name": run_name, 
				"run_num": run_num, 
				"run_type": run_type, 
				"pass_fail_status": "pending", 
				"project": self.ex_json['project'], 
				"sample": sample_name, 
				"sample_folder": sample_path,
				"sample_json": "%s/%s.json"%(sample_path, sample_name)
			}

			# If this is a barcoded run, save the barcode
			if re.search("Ion", bam_name):
				jsonData['barcode'] = '_'.join(bam_name.split('_')[:-1])

			if "report_name" in run_json:
				jsonData['orig_path'] = run_json['report_name']

			# dump the json file
			self.write_json(run, jsonData)
			# move the json file
			new_run_path = "%s/%s"%(run_path, json_name)
			shutil.move(run, new_run_path)
			return new_run_path

	# fix the paths in the json files
	def fix_paths(self, orig_path, sample_path, sample_name, json_files):
		for json_file in json_files:
			if os.path.isfile(json_file):
				json_data = json.load(open(json_file))
				# the values we'll have to change are all at the lowest level.
				for key in json_data:
					if key == "runs":
						new_runs = []
						# fix the run paths
						self.fix_paths(orig_path, sample_path, sample_name, json_data['runs'])
						for run in json_data['runs']:
							if self.ffpe:
								if re.search("B_0", run.split('/')[-1]):
									new_runs.append(run)
								else:
									new_run = "%s/B_0%s"%('/'.join(run.replace(orig_path, sample_path).split('/')[:-1]), run.split("/")[-1])
									new_runs.append(new_run)
									if os.path.isfile(run):
										shutil.move(run, new_run)
							else:
								if re.search("A_", run.split('/')[-1]):
									new_runs.append(run)
								else:
									new_run = "%s/A_%s"%('/'.join(run.replace(orig_path, sample_path).split('/')[:-1]), run.split("/")[-1])
									new_runs.append(new_run)
									if os.path.isfile(run):
										shutil.move(run, new_run)
						json_data['runs'] =  new_runs
					elif isinstance(json_data[key], str):
						json_data[key] = json_data[key].replace(orig_path, sample_path)
				if 'sample' in json_data:
					json_data['sample'] = sample_name
				elif 'sample_name' in json_data:
					json_data['sample_name'] = sample_name
				if 'results_qc_json' in json_data or 'results_QC_json' in json_data:
					if os.path.isfile("%s/QC/QC/results_QC.json"%sample_path):
						# fix the QC dir
						if 'results_QC_json' in json_data:
							del json_data['results_QC_json']
						json_data['results_qc_json'] = "%s/QC/results_QC.json"%sample_path
						json_data['qc_folder'] = "%s/QC"%sample_path
						json_data['output_dir'] = sample_path
						# fix the qc_dirs
						for qc_comp in glob.glob("%s/QC/QC/*vs*"%sample_path):
							qc_comp = qc_comp.split('/')
							if os.path.isdir("%s/%s"%("/".join(qc_comp[:-2]), qc_comp[-1])):
								shutil.rmtree("%s/%s"%("/".join(qc_comp[:-2]), qc_comp[-1]))
							shutil.move("/".join(qc_comp), "%s/%s"%("/".join(qc_comp[:-2]), qc_comp[-1]))
						# fix the qc_dirs
						for qc_comp in glob.glob("%s/QC/*vs*"%sample_path):
							qc_comp = qc_comp.split('/')
							if re.search('chr1', qc_comp[-1]) or re.search('all', qc_comp[-1]):
								pass
							elif os.path.isdir("%s/chr1%s"%("/".join(qc_comp[:-1]), qc_comp[-1])):
								shutil.rmtree("/".join(qc_comp))
							else:
								# TODO fix the double QC/QC
								#if qc_comp[-1] == qc_comp[-2]:
								shutil.move("/".join(qc_comp), "%s/chr1%s"%("/".join(qc_comp[:-1]), qc_comp[-1]))
				self.write_json(json_file, json_data)


	# find the samples in the project
	def find_samples(self, project):
		samples = glob.glob(project+"/*")
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

	def move(self):
		pass

	def fix_results_QC_json(self, sample_path):
		# fix the results_QC.json path
		if os.path.isfile("%s/QC/results_QC.json_read"%sample_path):
			shutil.move("%s/QC/results_QC.json_read"%sample_path, "%s/QC/results_QC.json"%sample_path)
		if os.path.isfile("%s/QC/results_QC.json"%sample_path):
			# fix the qc_dirs
			for qc_comp in glob.glob("%s/QC/*vs*"%sample_path):
				if re.search('chr1', qc_comp) or re.search('all', qc_comp):
					pass
				else:
					qc_comp = qc_comp.split('/')
					# TODO fix the double QC/QC
					#if qc_comp[-1] == qc_comp[-2]:
					shutil.move("/".join(qc_comp), "%s/chr1%s"%("/".join(qc_comp[:-1]), qc_comp[-1]))
			results_QC = json.load(open("%s/QC/results_QC.json"%sample_path))
			new_results = {'QC_comparisons':{'chr1': {'normal_normal': {}, 'normal_tumor': {}, 'tumor_tumor': {}}}}
			#new_results = {'QC_comparisons':{'all': {'normal_normal': {}, 'normal_tumor': {}, 'tumor_tumor': {}}}}
			if 'all' in results_QC['QC_comparisons'] or 'chr1' in results_QC['QC_comparisons']:
				pass
			else:
				for QC_comp in results_QC['QC_comparisons']:
					#if ('chr' in results_QC['QC_comparisons'][QC_comp] and results_QC['QC_comparisons'][QC_comp]['chr'] == True) or self.options.chr1:
					# just add to the chr1 for now.
					new_results['QC_comparisons']['chr1']['%s_%s'%(results_QC['QC_comparisons'][QC_comp]['run1_type'], results_QC['QC_comparisons'][QC_comp]['run2_type'])][QC_comp] = results_QC['QC_comparisons'][QC_comp]
					#else:
					#	new_results['QC_comparisons']['all']['%s_%s'%(results_QC['QC_comparisons'][QC_comp]['run1_type'], results_QC['QC_comparisons'][QC_comp]['run2_type'])][QC_comp] = results_QC['QC_comparisons'][QC_comp]
				new_results['sample_name'] = results_QC['sample']
				new_results['sample'] = results_QC['sample']
				new_results['json_type'] = 'QC_comparisons'
				self.write_json("%s/QC/results_QC.json"%sample_path, new_results)
				

	# combine the merged and runs of a sample
	def combine_runs_merged(self, sample_path, merged_path):
		if os.path.isfile("%s/QC/results_QC.json"%sample_path) and os.path.isfile("%s/QC/results_QC.json_read"%merged_path) and os.path.isdir("%s/QC/N-1vsT-1"%merged_path):
			# consolidate the two results_QC.json files and move the QC comparisons here
			print "consolidating the two results_QC.json files and moving the QC comparisons"
			results_QC = json.load(open("%s/QC/results_QC.json"%sample_path))
			merged_results_QC = json.load(open("%s/QC/results_QC.json_read"%merged_path))
			results_QC['QC_comparisons']['all'] = {'normal_normal': {}, 'normal_tumor': {}, 'tumor_tumor': {}}
			for QC_comp in merged_results_QC['QC_comparisons']:
				results_QC['QC_comparisons']['all']['%s_%s'%(merged_results_QC['QC_comparisons'][QC_comp]['run1_type'], merged_results_QC['QC_comparisons'][QC_comp]['run2_type'])][QC_comp] = merged_results_QC['QC_comparisons'][QC_comp]
			self.write_json("%s/QC/results_QC.json"%sample_path, results_QC)
			# move the comparison files:
			shutil.move("%s/QC/N-1vsT-1"%merged_path, "%s/QC/allN-1vsT-1"%sample_path)
		print "moving the Merged files in path %s to be with the runs in %s"%(merged_path, sample_path)
		# move the merged files to the sample
		if os.path.isdir("%s/Normal/N-1"%merged_path):
			shutil.move("%s/Normal/N-1"%merged_path, "%s/Normal/Merged"%sample_path)
			print "moved the Normal merged dir in %s/Normal/N-1 to be with the runs in %s"%(sample_path, merged_path)
			if os.path.isfile("%s/Normal/Merged/cov_full/merged.amplicon.cov.xls"%sample_path):
				shutil.move("%s/Normal/Merged/cov_full/merged.amplicon.cov.xls"%sample_path, "%s/Normal/Merged/merged.amplicon.cov.xls"%sample_path)
				shutil.rmtree("%s/Normal/Merged/cov_full"%sample_path)
			if os.path.isfile("%s/Normal/Merged/TSVC_variants.vcf"%sample_path):
				shutil.move("%s/Normal/Merged/TSVC_variants.vcf"%sample_path, "%s/Normal/Merged/4.2_TSVC_variants.vcf"%sample_path)
				shutil.rmtree("%s/Normal/Merged/tvc_out"%sample_path)
			if os.path.isfile("%s/Normal/Merged/tvc4.2_out/TSVC_variants.vcf"%sample_path):
				shutil.move("%s/Normal/Merged/tvc4.2_out/TSVC_variants.vcf"%sample_path, "%s/Normal/Merged/4.2_TSVC_variants.vcf"%sample_path)
				shutil.rmtree("%s/Normal/Merged/tvc4.2_out"%sample_path)
			# move the log file if there is one
			for log_file in glob.glob("%s/Normal/*.*"%merged_path):
				shutil.move(log_file, "%s/Normal/Merged"%sample_path)
		if os.path.isdir("%s/Tumor/T-1"%merged_path):
			shutil.move("%s/Tumor/T-1"%merged_path, "%s/Tumor/Merged"%sample_path)
			print "moved the Tumor merged dir in %s/Tumor/T-1 to be with the runs in %s"%(sample_path, merged_path)
			if os.path.isfile("%s/Tumor/Merged/cov_full/merged.amplicon.cov.xls"%sample_path):
				shutil.move("%s/Tumor/Merged/cov_full/merged.amplicon.cov.xls"%sample_path, "%s/Tumor/Merged/merged.amplicon.cov.xls"%sample_path)
				shutil.rmtree("%s/Tumor/Merged/cov_full"%sample_path)
			if os.path.isfile("%s/Tumor/Merged/TSVC_variants.vcf"%sample_path):
				shutil.move("%s/Tumor/Merged/TSVC_variants.vcf"%sample_path, "%s/Tumor/Merged/4.2_TSVC_variants.vcf"%sample_path)
				shutil.rmtree("%s/Tumor/Merged/tvc_out"%sample_path)
			if os.path.isfile("%s/Tumor/Merged/tvc4.2_out/TSVC_variants.vcf"%sample_path):
				shutil.move("%s/Tumor/Merged/tvc4.2_out/TSVC_variants.vcf"%sample_path, "%s/Tumor/Merged/4.2_TSVC_variants.vcf"%sample_path)
				shutil.rmtree("%s/Tumor/Merged/tvc4.2_out"%sample_path)
			# move the log file if there is one
			for log_file in glob.glob("%s/Tumor/*.*"%merged_path):
				shutil.move(log_file, "%s/Tumor/Merged"%sample_path)
		# TODO now add the merged files to the sample json
		# actually, shouldn't need to do that because QC_sample.py checks to see if hte merged.bam file already eixsts before creating it.
		# remove these files so they aredn't read.
		for json_file in glob.glob("%s/Normal/Merged/*.json_read"%sample_path):
			os.remove(json_file)
		for json_file in glob.glob("%s/Tumor/Merged/*.json_read"%sample_path):
			os.remove(json_file)

	def make_json(self):
		pass


if __name__ == "__main__":
	# set up the option parser
	parser = OptionParser()
	
	# add the options to parse
	parser.add_option('-n', '--new_path', dest='new_path', help='The new path of the sample. set the new path of the sample and fix the paths of the sample and run jsons (if theyre there)')
	parser.add_option('-m', '--move', dest='move', action="store_true", help='actually move the sample to this new path')
	parser.add_option('-s', '--sample', dest='sample', help='move the specified sample')
	parser.add_option('-p', '--project', dest='project', help='find all of the samples in a specified directory, then either move them (-n), or make json files (-j)')
	parser.add_option('-j', '--ex_json', dest='ex_json', help='the example sample json file used to get all of the settings and such. Will correct the sample and run jsons')
	parser.add_option('-M', '--merged', dest='merged', help='the path to the merged directory to combine with the sample')
	parser.add_option('-q', '--fix_qc', dest='fix_qc', help='Fix the results_QC.json file and directories.')
	parser.add_option('-C', '--chr1', dest='chr1', action="store_true", help='the QC results are chr1')
	parser.add_option('-c', '--copy_merged_csv', dest='copy_merged_csv', help='copy the merged files to a specified location')
	#parser.add_option('-c', '--cleanup', dest='cleanup', help='option to cleanup the temporary files used in merging and such.')

	(options, args) = parser.parse_args()

	if (not options.new_path and not options.ex_json) and (not options.sample and not options.project):
		print "USAGE_ERROR: -n or-j are required and -s or -p are required."
		parser.print_help()
		sys.exit(1)

	if options.sample and not os.path.isdir(options.sample):
		print "USAGE_ERROR: --sample %s is not found!"%options.sample
		parser.print_help()
		sys.exit(1)

	Fix_Jsons(options)

