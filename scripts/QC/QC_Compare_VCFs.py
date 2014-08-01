#! /usr/bin/env python

#script to QC the VCF files of two different runs before merging them.

#  Goal: Run QC on all of the BAM files that have multiple runs (after filtering and matching with the hotspot file).
#  Because the two different runs are of the same genes of the same person, the VCF files are supposed to be the same.
#  Match the variant entries among the two different vcf files of the two runs. Report the corresponding freq and depths
#  Report any variant not matched in both files.

import sys
import os.path
import re
import json
from optparse import OptionParser

# ------------------------------------------
# ------------- FUNCTIONS ------------------
# ------------------------------------------

# (if flow-space values are present FAO/FRO values will be reported, if not then will use AO/RO values instead)
# based on FAO/FRO (or AO/RO) determine the total depth and allele frequency
# assign GT to each normal variant based on the determined thresholds: 
# anything < 0.2 will be WT, anything >= 0.8 and anything in between will be HOM
#@param Takes as input the line from a vcf file and the WT and HOM allele frequency cutoffs. (Could be different for Tumor / Normal pairs)
#@return Returns a tuple with 1. the GT, 2. alternate allele frequency, 3. the alt depth, and 4. the ref depth
def getGTInfo(line, WT_cutoff, HOM_cutoff):
	line = line.split("\t")
	alternates = line[4].split(",")
	GT = '.'
	alt_freq = '.'
	alt_depth = '.'
	ref_depth = '.'
	total_depth = 0
	# there should NOT be any multi-allelic calls in the input tumor/vcf files at this stage since these are filtered out upstream.
	# This "if" statement either could be removed, or replaced with an "if/else" to report any unexpected multi-allelic calls seen
	if len(alternates) != 1:
		GT = "ERROR: ", line[0], line[1], "has an alternate allele"
	else:
		info = dict(zip(line[8].split(":"), line[9].split(":"))) #Creates a dictionary with the description as the key, and the actual value as the value.
		try:
			if 'FAO' in info and info['FAO'] != '.': # Ozlem said that the frequency depth score is better than the regular depth score, so use that if we can.
				alt_depth = info['FAO']
				ref_depth = info['FRO']
			elif 'AO' in info:
				alt_depth = info['AO']
				ref_depth = info['RO']
			elif 'AD' in info: # For older vcf files (3.2), the format is different.
				alt_depth = info['AD'].split(',')[1]
				ref_depth = info['AD'].split(',')[0]
			total_depth = int(alt_depth) + int(ref_depth)
			if total_depth != 0:
				alt_freq = float(alt_depth) / float(total_depth)
				if alt_freq < WT_cutoff:
					GT = 'WT'
				elif alt_freq >= HOM_cutoff:
					GT = 'HOM'
				else:
					GT = 'HET'
		except KeyError, ValueError:
			print "Leaving GT as . for this variant:", line
			pass
	return GT, str(alt_freq)[0:5], alt_depth, ref_depth # returns the GT, and first three decimal points of the alt frequencies, and the alt and ref depth.

# @param line is the line of the current variant that is found in one vcf file but not the other. 
# File_num is the number of the vcf file line is from.
# @return returns the line after whichever variant was mismatched.
def skipVar(line, file_num):
	line1arr = line2arr = line.split('\t')
	if file_num == 1:
		GT1Info = getGTInfo(line, WT1_Cutoff, HOM1_Cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth
		outCSV.write('\t'.join([line1arr[0], line1arr[1], line1arr[3], line1arr[4], GT1Info[0], GT1Info[1], GT1Info[2], GT1Info[3], '.', '.', '.', '.']) + '\n')
		# I'm not sure if Bonnie wants variants only found in one vcf file to be counted as a WT change.
#		change_counts[GT1Info[0] + '_WT'] += 1
		# read another line in vcf1 to get vcf1 and 2 back in sync.		
		line1 = vcf1.readline().strip()
		return line1
	else:
		# Skip over this variant in vcf2.
		GT2Info = getGTInfo(line, WT2_Cutoff, HOM2_Cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth
		outCSV.write('\t'.join([line2arr[0], line2arr[1], line2arr[3], line2arr[4], '.', '.', '.', '.', GT2Info[0], GT2Info[1], GT2Info[2], GT2Info[3]]) + '\n')
		# I'm not sure if Bonnie wants variants only found in one vcf file to be counted as a WT change.
#		change_counts['WT_' + GT2Info[0]] += 1
		# read another line from vcf2 to get vcf1 and 2 back in sync.		
		line2 = vcf2.readline().strip()
		return line2

# Match the rest of the variants in the file. The rest should be like chrX, Y, chrM or other stuff
def matchTheRest(line1, line2):
	vcf1_leftovers = {}
	while line1 != '':
		vcf1_leftovers["_".join(line1.split('\t')[0:3])] = line1
		line1 = vcf1.readline().strip()
	vcf2_leftovers = {}
	while line2 != '':
		vcf2_leftovers["_".join(line2.split('\t')[0:3])] = line2
		line2 = vcf2.readline().strip()

	for chr_pos in vcf1_leftovers:
		line1arr = vcf1_leftovers[chr_pos].split('\t')
		GT1Info = getGTInfo(vcf1_leftovers[chr_pos], WT1_Cutoff, HOM1_Cutoff)
		if chr_pos in vcf2_leftovers:
			line2arr = vcf2_leftovers[chr_pos].split('\t')
			# this variant is found in both.
			GT2Info = getGTInfo(vcf2_leftovers[chr_pos], WT2_Cutoff, HOM2_Cutoff)
			outCSV.write('\t'.join([line1arr[0], line1arr[1], line1arr[3], line1arr[4], GT1Info[0], GT1Info[1], GT1Info[2], GT1Info[3], GT2Info[0], GT2Info[1], GT2Info[2], GT2Info[3]]) + '\n')
			GT1_GT2 = GT1Info[0] + "_" +  GT2Info[0]
			if GT1_GT2 in change_counts: # unknown (i.e ._.) will be skipped.
				change_counts[GT1_GT2] += 1
			# remove this variant from vcf2.
			vcf2_leftovers.pop(chr_pos, None)
		else:
			outCSV.write('\t'.join([line1arr[0], line1arr[1], line1arr[3], line1arr[4], GT1Info[0], GT1Info[1], GT1Info[2], GT1Info[3], '.', '.', '.', '.']) + '\n')

	for chr_pos in vcf2_leftovers:
		line2arr = vcf2_leftovers[chr_pos].split('\t')
		GT2Info = getGTInfo(vcf2_leftovers[chr_pos], WT2_Cutoff, HOM2_Cutoff)
		outCSV.write('\t'.join([line2arr[0], line2arr[1], line2arr[3], line2arr[4], '.', '.', '.', '.', GT2Info[0], GT2Info[1], GT2Info[2], GT2Info[3]]) + '\n')
	
# If the json file exists, get the dictionary from it. If not, then make it
def getJsonData(jsonFile):
	if not os.path.isfile(jsonFile):
		# If the json file doesn't exist for some reason, then add these simple metrics to it
		json_path = os.path.abspath(jsonFile)
		# Correct for tumor / normal projcets
		if json_path.split("/")[-3] == "Normal" or json_path.split("/")[-3] == "Tumor":
			sample = json_path.split("/")[-4]
		else:
			sample = json_path.split("/")[-3]
		run_name = json_path.split("/")[-2]
		jsonData = {'sample': sample, 'name': run_name}
		#dump the json file
		with open(jsonFile, 'w') as newJSONFile:
			json.dump(jsonData, newJSONFile, sort_keys=True, indent=2)
	else:
		# load each run's json data.
		jsonData = json.load(open(jsonFile))
	return jsonData

# get the run_type from each run's json file.
def getRunType(jsonData, WT_Cutoff):
	runType = ""
	if 'run_type' in jsonData:
		runType = jsonData['run_type']
	else:
		# Temporary fix because run_type is not yet implemented
		if re.search("N-", jsonData['name']):
			runType = 'normal'
		elif re.search("T-", jsonData['name']):
			runType = 'tumor'
		elif WT_Cutoff > .1:
			runType = 'normal'
		else:
			runType = "tumor"
	return runType


# ----------------------------------------------------
# ------------- PROGRAM STARTS HERE ------------------
# ----------------------------------------------------

# set up the option parser
parser = OptionParser()

# add the options to parse
parser.add_option('-v', '--vcfs', dest='vcfs', nargs=2, help='The two VCF files generated from the two runs combined Hotspot file')
parser.add_option('-j', '--jsons', dest='jsons', nargs=2, help='The json files in each VCFs sample dir. These the sample and run info')
parser.add_option('-g', '--gt_cutoffs', dest='gt_cutoffs', nargs=4, type="float", help='WT1_Cutoff, HOM1_Cutoff, WT2_Cutoff, HOM2_Cutoff. Variant filtering should already have been done before this step.')
parser.add_option('-b', '--total_bases', dest='total_eligible_bases', type="int", help='The VCF files generated from the two runs combined Hotspot file')
parser.add_option('-o', '--out_csv', dest='outCSV', help='Output csv file to summarize the matched variants')
parser.add_option('-t', '--json_out', dest='json_out',  help='This json file will hold the QC error metrics for this comparison. QC_generateSheets.py will use this json file to generate the master spreadsheet')
parser.add_option('-c', '--cds', dest='cds', action="store_true", help='Optional. Add a CDS feild to the json out file. This option should be used if the --run_gatk_twice option is specified in QC_2Runs.sh.')

(options, args) = parser.parse_args()

#check to make sure either ID or name was provided
if(not options.vcfs or not options.jsons or not options.gt_cutoffs or not options.total_eligible_bases or not options.outCSV or not options.json_out):
	print "USAGE ERROR: --vcfs, --jsons, --gt_cutoffs, --total_bases, --out_csv, and --json_out are all required. Only --cds is optional."
	print options.vcfs, options.jsons, options.gt_cutoffs, options.total_eligible_bases, options.outCSV, options.json_out
	print "Args given: %s"%args
	print "use -h for help"
	sys.exit(8)

vcf1 = open(options.vcfs[0], 'r')
vcf2 = open(options.vcfs[1], 'r')
WT1_Cutoff = options.gt_cutoffs[0]
HOM1_Cutoff = options.gt_cutoffs[1]
WT2_Cutoff = options.gt_cutoffs[2]
HOM2_Cutoff = options.gt_cutoffs[3]
total_eligible_bases = options.total_eligible_bases
outCSV = open(options.outCSV, 'w')


# add the header lines to the csv file
outCSV.write("chr\tpos\tRef\tAlt\tRun1 GT\tRun1 AF\tRun1 Alternate Depth\tRun1 Ref Depth\t " + \
		"Run2 GT\tRun2 AF\tRun2 Alternate Depth\tRun2 Ref Depth\n")
# a dictionary to keep track of the allele types of the two different files compared..
change_counts = {'WT_WT':0, 'WT_HET':0, "WT_HOM":0,'HET_WT':0, 'HET_HET':0, "HET_HOM":0, \
		'HOM_WT':0, 'HOM_HET':0, "HOM_HOM":0,} 

line1 = vcf1.readline().strip()
line2 = vcf2.readline().strip()
# Because the two vcf files were created from the same HotSpot file, they should have the same chromosome positions listed in the same order.
# Therefore, I am reading the two vcf files line by line at the same time.
while line1 != '' and line1[0] == '#':
	line1 = vcf1.readline().strip()
	line2 = vcf2.readline().strip()
while line1 != '' or line2 != '':
	line1arr = line1.split('\t')
	line2arr = line2.split('\t')
	# If I make it a while loop rather than an if statement, this will handle if there are more than one mismatches. If the error rate is really high, the vcf files given were probably not from the same hotspot file.
	# Rather than load the variants into memory, handle mismatches this way.
	while line1arr[0:2] != line2arr[0:2]:
		# A variant must have been filtered from one of the VCF files. We should just skip over it in the other one.
		#print 'line1:', line1arr[0:2], '\t', 'line2:',line2arr[0:2]
		if line2 == '':
			line1 = skipVar(line1, 1)
			line1arr = line1.split('\t')
		elif line1 == '':
			line2 = skipVar(line2, 2)
			line2arr = line2.split('\t')
		else:
			try:
				var1Chr = int(line1arr[0][3:])
				var2Chr = int(line2arr[0][3:])
				var1Pos = int(line1arr[1])
				var2Pos = int(line2arr[1])
				# Check first to see if the chromosomes match. IF they don't, then whichever file has an extra variant should write that var.
				if var1Chr != var2Chr:
					if var1Chr < var2Chr:
						line1 = skipVar(line1, 1)
						line1arr = line1.split('\t')
					else:
						line2 = skipVar(line2, 2)
						line2arr = line2.split('\t')
				# Check the positions if they are on the same chromosome..
				elif var1Pos < var2Pos:
					line1 = skipVar(line1, 1)
					line1arr = line1.split('\t')			
				else:
					line2 = skipVar(line2, 2)
					line2arr = line2.split('\t')
			# There could be a case where the x chromosome or the y chromosome has the extra variant. I'll have to figure that out later.
			except ValueError:
				matchTheRest(line1, line2)
				break

	# If the chr and positions match, then we're good to go.
	if line1 != '' and line2 != '': # If the while loop hit the end of the file, then don't do anything here.
		GT1Info = getGTInfo(line1, WT1_Cutoff, HOM1_Cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth
		GT2Info = getGTInfo(line2, WT2_Cutoff, HOM2_Cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth 
		# Write the chr, pos, ref Allele, alt Allele, vcf1 info, vcf2 info.
		outCSV.write('\t'.join([line1arr[0], line1arr[1], line1arr[3], line1arr[4], GT1Info[0], GT1Info[1], GT1Info[2], GT1Info[3], GT2Info[0], GT2Info[1], GT2Info[2], GT2Info[3]]) + '\n')
		GT1_GT2 = GT1Info[0] + "_" +  GT2Info[0]
		if GT1_GT2 in change_counts: # unknown (i.e ._.) will be skipped.
			change_counts[GT1_GT2] += 1
		line1 = vcf1.readline().strip()
		line2 = vcf2.readline().strip()
	
# get the sample and run info from each run's json files.
json1 = getJsonData(options.jsons[0])
json2 = getJsonData(options.jsons[1])

# Now that we have all of GT info for each variant listed in both VCFs, get the error metrics, and write the json output.
total_vars = 0
# get the WT_WT bases
for key in change_counts:
	if key != 'WT_WT':
		total_vars += int(change_counts[key])
change_counts['WT_WT'] = total_eligible_bases - total_vars

change_counts['run1_type'] = getRunType(json1, WT1_Cutoff)
change_counts['run2_type'] = getRunType(json2, WT2_Cutoff)

# Get the error_counts
if change_counts['run1_type'] == "normal" and change_counts['run2_type'] == 'tumor':
	# If you are comparing Tumor Normal pairs, the error count should only include the Normal side
	error_count =  int(change_counts['HET_WT'])  +  int(change_counts['HOM_WT']) + int(change_counts['HOM_HET'])
else:
	# If you are comparing Germline Germline  or Tumor Tumor, the error count should be everything off diagonal
	error_count =  int(change_counts['WT_HET']) + int(change_counts['WT_HOM']) + int(change_counts['HET_HOM']) + int(change_counts['HET_WT']) +  int(change_counts['HOM_WT']) + int(change_counts['HOM_HET'])

# Calc the error_rate
error_rate = (float(error_count) / float(total_eligible_bases))
change_counts['error_count'] = error_count
change_counts['error_rate'] = error_rate
change_counts['total_eligible_bases'] = total_eligible_bases


if not os.path.isfile(options.json_out):
	# If the QC json file doesn't exist yet, then make it.
	json_out = {'sample': json1['sample']}
else:
	# add this comparisons QC metrics to the sample's QC json file.
	json_out = json.load(open(options.json_out))

# If no QC_comparisons have been added yet, then start the list
if 'QC_comparisons' not in json_out:
	json_out['QC_comparisons'] = {} # a dictionary containing each QC_comparison

# if this is a cds specific comparison, append that to the key
if options.cds:
	change_counts['CDS'] = True
	# the key will be CDS:Run1vsRun2, and the value will be a dictionary containing the error metrics for these two run's comparisons
	json_out['QC_comparisons']['CDS:' + json1['name'] + 'vs' + json2['name']] = change_counts
else:
	# the key will be Run1vsRun2, and the value will be a dictionary containing the error metrics for these two run's comparisons
	json_out['QC_comparisons'][json1['name'] + 'vs' + json2['name']] = change_counts

# dump the json out file
with open(options.json_out, 'w') as newJSONFile:
	json.dump(json_out, newJSONFile, sort_keys=True, indent=4)
	
vcf1.close()
vcf2.close()
outCSV.close()
