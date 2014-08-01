#! /usr/bin/env python

# GOAL: Take the information about each sample and generate the statistics for the QC metrics spreadsheet.
# Writes the output as key:value so the QC_generateSheet.py will be able to use them.
import sys
import re
import subprocess
import math
import os
import fnmatch
import glob
import json
import argparse

# -----------------------------------------------------------------------------------------
# ------------------------------ FUNCTIONS DEFINED HERE -----------------------------------
# -----------------------------------------------------------------------------------------
# Function to get error Rate stats for each run.
def calcStats(errRate, total_bases, meanErrorRate, standardDeviation):
	percAvailable = float(total_bases) / total_possible_bases
	zscore = (errRate - meanErrorRate) / float(standardDeviation)
	return zscore, percAvailable 

# @params takes a list of error Rates and finds the standardDeviation of the error rates.
# @return returns the meanErrorRate and the standardDeviation
def getStandardDeviation(errorRates):
	# Calculate the mean Error rate and the standard Deviation in order to calculate the zscore statistic for each error rate.
	total_errorRates = 0
	for rate in errorRates:
		total_errorRates += rate
	meanErrorRate = float(total_errorRates) / len(errorRates)
	#print meanErrorRate
	total_deviation = 0
	for rate in errorRates:
		total_deviation += (rate - meanErrorRate) ** 2
	#print 'total_deviation:',total_deviation, 'total_rates:', len(errorRates)
	standardDeviation = math.sqrt(float(total_deviation) / float(len(errorRates)))
	return meanErrorRate, standardDeviation

# Finds the best run out of all of the samle's runs
# @params takes a dictionary of the runs
# @return the name of the best run.
def findBestRun(runs):
	# first, filter the available runs by mean (or median) read length, and by % available read length
	read_length_filter = 95
	perc_avail_bases_filter = .6
	median_coverage_overall_filter = 100
	avail_runs = []
	while len(avail_runs) == 0:
		for run in runs:
			if 'median_read_length' in run['run_data']:
				read_length = run['run_data']['median_read_length']
			else:
				read_length = run['run_data']['mean_read_length']

			# If this run passes the filters, then it is a candidate for the ref run
			if read_length > read_length_filter and run['perc_avail_bases'] > perc_avail_bases_filter and run['median_coverage_overall'] > median_coverage_overall_filter:
				avail_runs.append(run)
		read_length_filter -= 5
		perc_avail_bases_filter -= .05
		median_coverage_overall_filter -= 10

	# Now find the lowest error rate of the available run combos
	bestRun = ""
	bestErrorRate = 1.0
	for run in avail_runs:
		for run_comp, error_metrics in runs['QC_comparisons'].iteritems():
			if re.search(run['name'], run_comp):
				if error_metrics['error_rate'] < bestErrorRate:
					bestRuns = run_comp
					bestErrorRate = error_metrics['error_rate']

	return findBestRun(runs['QC_comparisons'][bestRuns])


				
# @params takes a dictionary of runs (after findBestRunCombos has been run)
# @return returnj the better of the two runs
def findBestRun(QC_comp):
	run1_name = QC
	run1Errs = int(info[1]['HET_WT']) + int(info[1]['HOM_WT']) + int(info[1]['HOM_HET'])
	run2Errs = int(info[1]['WT_HET']) + int(info[1]['WT_HOM']) + int(info[1]['HET_HOM'])
	if run1Errs < run2Errs:
		return run1_name
	else:
		return run2_name

			
# @param a list of json files
# @return a dictionary containing the combined runs files
def getAllRunInfo(run_files):
	# the master dictionary containing each sample's runs and each run's info
	all_run_data = {}

	for jsonFile in run_files:
		# load the json file's data
		jsonData = json.load(open(jsonFile))
		# load this runs data into the master dictionary.
		# The dictionary is organized by sample, then by name, then by run data
		if jsonData['sample'] not in all_run_data:
			all_run_data[jsonData['sample']] = {}
		# the dictionary inside of run_data should hold all of this runs QC metrics such as % polyclonality and such
		all_run_data[jsonData['sample']][jsonData['name']] = jsonData['run_data']
	
	return all_run_data



# Function to write the info for each N-N, T-T and N-T pair.
#@param
#@return
def writePair(sample, run1, run2, errorInfo, SD, pair):
	key = "%s:%svs%s"%(sample, run1, run2)
	# info is a tuple containing 1. the total number of bases evaluated for the 3x3 table, 2. the error count, 3. the error rate, and 4, the status
	info = errorInfo[key]
	# calcStats will return the 1. percAvaliableBases, 2. the zscore
	zscore, percAvailableBases = calcStats(float(info[2]), info[0], SD[0], SD[1])
	#percAvailableBases = str(float(runStats[1]))
	error_rate_perc = str(float(info[2]))
	#zscore = str(runStats[0])
	statsOut.write('\t'.join(['%s_pair:%s vs %s'%(pair, run1, run2), '%s_total_evaluated:%s'%(pair, info[0]), \
			'%s_error_count:%s'%(pair, info[1]), '%s_error_rate:%s'%(pair, error_rate_perc), \
			'%s_perc_available_bases:%s'%(pair, percAvailableBases), '%s_zscore:%s'%(pair, zscore), '']))


# Function to write the run combo specified by the third parameter "tnBestRuns
# @param sample: current sample, currentRun: current Run, tnRuns: dictionary containing the best or worst run (depending on what is passed in) for the current sample. 
# @param Type is either a B or a W to write the best or worst combinations.
def writeTNRunCombo(sample, currentRun, tnRuns, tnErrorInfo, nnErrorInfo, tnSD, nnSD, Type):
	try:
		bestNormalRun = tnRuns[sample][sample].split('vs')[0]
		bestTumorRun = tnRuns[sample][sample].split('vs')[1]
	
		# if the current currentRun is normal, match it with the ref Tumor Run
		# currentRun will be a N-1 or T-1 so we can use this tactic.
		if re.search("N-", currentRun):
			# If this is the reference normal Run, write -
			if currentRun == bestNormalRun:
				statsOut.write('\t'.join(['same%s_pair:REF'%Type, 'same%s_total_evaluated:REF'%Type, 'same%s_error_count:REF'%Type, \
						'same%s_error_rate:REF'%Type, 'same%s_status:REF'%Type, 'same%s_perc_available_bases:REF'%Type, \
						'same%s_zscore:REF'%Type, '']))
				statsOut.write('\t'.join(['tn%s_pair:-'%Type, 'tn%s_total_evaluated:-'%Type, 'tn%s_error_count:-'%Type, \
						'tn%s_error_rate:-'%Type, 'tn%s_status:-'%Type, 'tn%s_perc_available_bases:-'%Type, \
						'tn%s_zscore:-'%Type, '']))
			else:
				# First write the N-N pair
				currentNum = int(currentRun.split('-')[-1])
				bestNum = int(bestNormalRun.split('-')[-1])
				# Make sure the N-1 is compared with N-2 not N-2 with N-1.
				if currentNum < bestNum:	
					writePair(sample, currentRun, bestNormalRun, nnErrorInfo, nnSD, 'same%s'%Type)
				else:
					writePair(sample, bestNormalRun, currentRun, nnErrorInfo, nnSD, 'same%s'%Type)
				# Now write the N-T pair
				writePair(sample, currentRun, bestTumorRun, tnErrorInfo, tnSD, 'tn%s'%Type)
		
		elif re.search("T-", currentRun):
			# First write the N-N or T-T pair
			# If this is the reference normal Run, write -
			if currentRun == bestTumorRun:
				statsOut.write('\t'.join(['same%s_pair:REF'%Type, 'same%s_total_evaluated:REF'%Type, 'same%s_error_count:REF'%Type, \
						'same%s_error_rate:REF'%Type, 'same%s_status:REF'%Type, 'same%s_perc_available_bases:REF'%Type, \
						'same%s_zscore:REF'%Type, '']))
				writePair(sample, bestNormalRun, currentRun, tnErrorInfo, tnSD, 'tn%s'%Type)
			else:
				# First write the T-T pair
				currentNum = int(currentRun.split('-')[-1])
				bestTumorNum = int(bestTumorRun.split('-')[-1])
				if currentNum < bestTumorNum: 
					writePair(sample, currentRun, bestTumorRun, ttErrorInfo, ttSD, 'same%s'%Type)
				else:
					writePair(sample, bestTumorRun, currentRun, ttErrorInfo, ttSD, 'same%s'%Type)
				# Now write the N-T pair
				writePair(sample, bestNormalRun, currentRun, tnErrorInfo, tnSD, 'tn%s'%Type)

# if this sample only has tumor runs, then write their combination.
#			elif sample in ttBestRuns:
	except KeyError as e:
	#	print e.errno, e.strerror
		print e, "has a key error"
#			print 'error'
#			raise
	except TypeError as e:
		raise
#			sys.exit()
#			pass
#			print sample, "got a type error"



# -----------------------------------------------------------------------
# ---------------------- PROGRAM STARTS HERE ----------------------------
# -----------------------------------------------------------------------

# If I put everything in functions, then QC_generateSheets.py can just run the functions in this script to get the dicitonary rather than writing it back out to a .json file

# If this script is called from the command line, parse the arguments, and output the .json file
if (__name__ == "__main__"):
	# parse the arguments
	if len(sys.argv) < 2:
		print "USAGE: use -h for help"
		sys.exit(8)
	
	# All of the arguments are specified here.
	parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, \
			description='GOAL: Find each runs json, and each samples QC json file to generate the statistics for the QC metrics spreadsheet.')
	parser.add_argument('-p', '--project_path', help='/path/to/the/project_dir')
	parser.add_argument('-o', '--out', type=argparse.FileType('w'), default='Files/qc_stats.json', help='Specify the path/to/.json file that QC_generateSheets.py will use\n(default: %(default)s)')
	parser.add_argument('-b', '--bases', nargs=3, help="Specify 1: the total_expected_bases, 2: the total_targeted_bases, 3: the total_possible_bases")
	
	# Gets all of the command line arguments specified and puts them into the dictionary args
	args = vars(parser.parse_args())
	
	# Place the arguemts into variables
	projectPath = args['project_path'] 
	statsOut = args['out']
	if args['bases'] != None:
		try:
			total_expected_bases = int(args['bases'][0])
			total_targeted_bases = int(args['bases'][1])
			total_possible_bases = int(args['bases'][2])
		except ValueError:
			print "ERROR: --bases option must have 3 integers. Given: total_expected_bases: %s, total_targeted_bases: %s, total_possible_bases: %s"%(args['bases'][0],args['bases'][1],args['bases'][2])
			sys.exit(8)
		print "Given -b (--bases) values: total_expected_bases: %s, total_targeted_bases: %s, total_possible_bases: %s"%(args['bases'][0],args['bases'][1],args['bases'][2])
	# Wales bases:
	#total_expected_bases = 83046
	#total_targeted_bases = 84447
	#total_possible_bases = 124490
	
	#main(project_path, t


	# get both lists containing the json files.
	run_files, QC_files = findRunsJsons(projectPath)

# Find and load info all of the run's json files
# @param the path to the project to look for the json files in
# @param the json file pattern used to find the .json files (i.e. *.json* or *_QC.json*)
# @return returns a dictionary containing each runs metrics
def findRunsJsons(projectPath):
	QC_files = []
	run_files = []
	# recurse through the projectDir and find the json files
	for root, dirnames, filenames in os.walk(projectDir):
		for filename in fnmatch.filter(filenames, "*.json*"):
			# append all of the QC sample run comparison json files to this list
			if re.search("_QC.json", filename):
				QC_files.append(os.path.join(root, filename))
			else:
				run_files.append(os.path.join(root, filename))
	
	all_samples_run_info = getAllRunInfo(run_files)
	all_samples_QC_info = {}

	# For each sample, find the best ref run.  
	# A ref run must have > 95 mean read length, a high median read count, and above 50% available bases. 
	# Then choose the ref  based on best error rate
	for jsonFile in QC_files:
		# load the QC json file's data
		jsonData = json.load(open(jsonFile))
		# load this samples QC data into the master dictionary.
		# the dictionary inside of run_data should hold all of this runs QC metrics such as % polyclonality and such
		all_samples_run_info[jsonData['sample']]['QC_comparisons'] = jsonData['QC_comparisons']
	

	tumor = normal = False
	# now get the REF runs.
	for sample, runs in all_samples_run_info.iteritems():
		# check to see if we're dealing with tumor normal or not in this sample
		tumor_dates = []
		normal_dates = []
		for run in runs:
			if run['run_type'] == "tumor":
				tumor_dates.append(run['run_date'])
			elif run['run_type'] != "tumor":
				normal_dates.append(run['run_date'])
		if len(tumor_dates) > 0 and len(normal_dates) > 0:
			tumor = normal = True
			# this is a tumor normal sample. Check to see if we have same day pairs
			for run in runs:
				# find the same day pairs, and add those to be written
		
			# Now find the best same day pair, and use those tumor and normal runs as the REF runs
			# if there arent any same day pairs, then find the best pairs and display those.

		else:
			normal = True
			# this is a germline or only tumor sample. We will treat them the same.
			ref_run = findBestRun(runs)


	if tumor and normal:
		tt_error_rates = []
		nn_error_rates = []
		tn_error_rates = []
		for sample in all_samples_run_info:
			if all_samples_run_info[sample]['QC_comparison']['error_rate']
			error_rates.append(all_samples_run_info[sample]['QC_comparison']['error_rate'])
		# Calculate the Z-score 
		zscore = calcZScore(QC_comparisons)

	else:
		error_rates = []
		for sample in all_samples_run_info:
			error_rates.append(all_samples_run_info[sample]['QC_comparison']['error_rate'])
		# Calculate the Z-score 
		zscore = calcZScore(QC_comparisons)

# find the z-score statistic 
def calcZScore(all_samples_run_info):

	for sample in all_samples_run_info:




# Write the master output .json file, or better, return the .json file

print 'Finished generating QC stats'
runInfoFile.close()
statsOut.close()

