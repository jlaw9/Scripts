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

class Compare_VCFs:
	def __init__(self, options):
		self.vcf1 = open(options.vcfs[0], 'r')
		self.vcf2 = open(options.vcfs[1], 'r')
		self.WT1_Cutoff = options.gt_cutoffs[0]
		self.HOM1_Cutoff = options.gt_cutoffs[1]
		self.WT2_Cutoff = options.gt_cutoffs[2]
		self.HOM2_Cutoff = options.gt_cutoffs[3]
		self.total_eligible_bases = options.bases[0]
		self.total_possible_bases = options.bases[1]
		self.outCSV = open(options.outCSV, 'w')
		# a dictionary to keep track of the allele types of the two different files compared..
		self.change_counts = {'WT_WT':0, 'WT_HET':0, "WT_HOM":0,'HET_WT':0, 'HET_HET':0, "HET_HOM":0, \
				'HOM_WT':0, 'HOM_HET':0, "HOM_HOM":0,} 
		self.reassigned_GTs = 0
		
	# main function
	def main(self):
		# add the header lines to the csv file
		self.outCSV.write("chr\tpos\tRef\tAlt\tRun1 GT\tRun1 AF\tRun1 Alternate Depth\tRun1 Ref Depth\t " + \
				"Run2 GT\tRun2 AF\tRun2 Alternate Depth\tRun2 Ref Depth\n")
		
		line1 = self.vcf1.readline().strip()
		line2 = self.vcf2.readline().strip()
		# Because the two vcf files were created from the same HotSpot file, they should have the same chromosome positions listed in the same order.
		# Therefore, I am reading the two vcf files line by line at the same time.
		while line1 != '' and line1[0] == '#':
			line1 = self.vcf1.readline().strip()
			line2 = self.vcf2.readline().strip()
		while line1 != '' or line2 != '':
			line1arr = line1.split('\t')
			line2arr = line2.split('\t')
			# If I make it a while loop rather than an if statement, this will handle if there are more than one mismatches. If the error rate is really high, the vcf files given were probably not from the same hotspot file.
			# Rather than load the variants into memory, handle mismatches this way.
			while line1arr[0:2] != line2arr[0:2]:
				# A variant must have been filtered from one of the VCF files. We should just skip over it in the other one.
				#print 'line1:', line1arr[0:2], '\t', 'line2:',line2arr[0:2]
				if line2 == '':
					line1 = self.skipVar(line1, 1)
					line1arr = line1.split('\t')
				elif line1 == '':
					line2 = self.skipVar(line2, 2)
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
								line1 = self.skipVar(line1, 1)
								line1arr = line1.split('\t')
							else:
								line2 = self.skipVar(line2, 2)
								line2arr = line2.split('\t')
						# Check the positions if they are on the same chromosome..
						elif var1Pos < var2Pos:
							line1 = self.skipVar(line1, 1)
							line1arr = line1.split('\t')			
						else:
							line2 = self.skipVar(line2, 2)
							line2arr = line2.split('\t')
					# There could be a case where the x chromosome or the y chromosome has the extra variant. I'll have to figure that out later.
					except ValueError:
						self.matchTheRest(line1, line2)
						break
		
			# If the chr and positions match, then we're good to go.
			if line1 != '' and line2 != '': # If the while loop hit the end of the file, then don't do anything here.
				GT1Info = self.getGTInfo(line1, self.WT1_Cutoff, self.HOM1_Cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth
				GT2Info = self.getGTInfo(line2, self.WT2_Cutoff, self.HOM2_Cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth 
				GT1Info, GT2Info = self.reAssignGT(GT1Info, GT2Info)
				# Write the chr, pos, ref Allele, alt Allele, vcf1 info, vcf2 info.
				self.outCSV.write('\t'.join([line1arr[0], line1arr[1], line1arr[3], line1arr[4], GT1Info[0], GT1Info[1], GT1Info[2], GT1Info[3], GT2Info[0], GT2Info[1], GT2Info[2], GT2Info[3]]) + '\n')
				GT1_GT2 = GT1Info[0] + "_" +  GT2Info[0]
				if GT1_GT2 in self.change_counts: # unknown (i.e ._.) will be skipped.
					self.change_counts[GT1_GT2] += 1
				line1 = self.vcf1.readline().strip()
				line2 = self.vcf2.readline().strip()
			
		# get the sample and run info from each run's json files.
		json1 = self.getJsonData(options.jsons[0])
		json2 = self.getJsonData(options.jsons[1])
		
		# Now that we have all of GT info for each variant listed in both VCFs, get the error metrics, and write the json output.
		total_vars = 0
		# get the WT_WT bases
		for key in self.change_counts:
			if key != 'WT_WT':
				total_vars += int(self.change_counts[key])
		self.change_counts['WT_WT'] = self.total_eligible_bases - total_vars
		
		self.change_counts['run1_type'] = self.getRunType(json1, self.WT1_Cutoff)
		self.change_counts['run2_type'] = self.getRunType(json2, self.WT2_Cutoff)
		
		# Get the error_counts
		if self.change_counts['run1_type'] == "normal" and self.change_counts['run2_type'] == 'tumor':
			# If you are comparing Tumor Normal pairs, the error count should only include the Normal side
			error_count =  int(self.change_counts['HET_WT'])  +  int(self.change_counts['HOM_WT']) + int(self.change_counts['HOM_HET'])
		else:
			# If you are comparing Germline Germline  or Tumor Tumor, the error count should be everything off diagonal
			error_count =  int(self.change_counts['WT_HET']) + int(self.change_counts['WT_HOM']) + int(self.change_counts['HET_HOM']) + int(self.change_counts['HET_WT']) +  int(self.change_counts['HOM_WT']) + int(self.change_counts['HOM_HET'])
		
		# Calc the error_rate
		self.change_counts['error_count'] = error_count
		try:
			self.change_counts['error_rate'] = (float(error_count) / self.total_eligible_bases)
		except ZeroDivisionError:
			self.change_counts['error_rate'] = 0
		self.change_counts['total_eligible_bases'] = self.total_eligible_bases
		self.change_counts['perc_avail_bases'] = self.total_eligible_bases / self.total_possible_bases
		self.change_counts['reassigned_GTs'] = self.reassigned_GTs
		
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
		if options.chr:
			self.change_counts['chr'] = True
			# the key will be CDS:Run1vsRun2, and the value will be a dictionary containing the error metrics for these two run's comparisons
			json_out['QC_comparisons']['%s:%svs%s'%(options.chr, json1['name'], json2['name'])] = self.change_counts
		# if this is a cds specific comparison, append that to the key
		elif options.cds:
			self.change_counts['CDS'] = True
			# the key will be CDS:Run1vsRun2, and the value will be a dictionary containing the error metrics for these two run's comparisons
			json_out['QC_comparisons']['CDS:' + json1['name'] + 'vs' + json2['name']] = self.change_counts
		else:
			# the key will be Run1vsRun2, and the value will be a dictionary containing the error metrics for these two run's comparisons
			json_out['QC_comparisons'][json1['name'] + 'vs' + json2['name']] = self.change_counts
		
		# dump the json out file
		with open(options.json_out, 'w') as newJSONFile:
			json.dump(json_out, newJSONFile, sort_keys=True, indent=4)
			
		self.vcf1.close()
		self.vcf2.close()
		self.outCSV.close()

	# (if flow-space values are present FAO/FRO values will be reported, if not then will use AO/RO values instead)
	# based on FAO/FRO (or AO/RO) determine the total depth and allele frequency
	# assign GT to each normal variant based on the determined thresholds: 
	# anything < 0.2 will be WT, anything >= 0.8 and anything in between will be HOM
	#@param Takes as input the line from a vcf file and the WT and HOM allele frequency cutoffs. (Could be different for Tumor / Normal pairs)
	#@return Returns a tuple with 1. the GT, 2. alternate allele frequency, 3. the alt depth, and 4. the ref depth
	def getGTInfo(self, line, WT_cutoff, HOM_cutoff):
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
		return [GT, str(alt_freq)[0:5], alt_depth, ref_depth] # returns the GT, and first three decimal points of the alt frequencies, and the alt and ref depth.

	# Ozlem made this update originally in another file named reAssignGT.py. I brought that scripts functionality as a function here.
	def reAssignGT(self, GT1Info, GT2Info):
	   # check to see how close normal AF is to the GT thresholds
		if abs(float(GT1Info[1]) - self.WT1_Cutoff) < 0.01:
			GT1Info[0]="HET" # assign HET as GT
			GT1Info[1]=str(self.WT1_Cutoff)
		elif abs(float(GT1Info[1]) - self.HOM1_Cutoff) < 0.01: #assign HOM
			GT1Info[0]="HOM"
			GT1Info[1]=str(self.HOM1_Cutoff)
				
		# now do the same check for tumor AF
		if abs(float(GT2Info[2]) - self.WT2_Cutoff) < 0.01:
			GT2Info[0]="HET" # assign HET as GT
			GT2Info[1]=str(self.WT2_Cutoff)
		elif abs(float(GT2Info[2]) - self.HOM2_Cutoff) < 0.01: #assign HOM
			GT2Info[0]="HOM"
			GT2Info[1]=str(self.HOM2_Cutoff)

		# compare the Allele frequencies between the two runs. If the difference between the two runs is < .1, then make them the same GT.
		if abs(float(GT1Info[1]) - float(GT2Info[1])) < 0.10:
			if GT1Info[0] != GT2Info[0]:
				self.reassigned_GTs += 1
			# 0.1 is hard cut-off
			#check which run ahs the higher frequency, and keep that one.
			if float(GT1Info[1]) > float(GT2Info[1]):
				GT2Info[0]=GT1Info[0] # keep normal GT
			else:
				GT1Info[0]=GT2Info[0]

		return GT1Info, GT2Info 


	# @param line is the line of the current variant that is found in one vcf file but not the other. 
	# File_num is the number of the vcf file line is from.
	# @return returns the line after whichever variant was mismatched.
	def skipVar(self, line, file_num):
		line1arr = line2arr = line.split('\t')
		if file_num == 1:
			GT1Info = self.getGTInfo(line, self.WT1_Cutoff, self.HOM1_Cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth
			self.outCSV.write('\t'.join([line1arr[0], line1arr[1], line1arr[3], line1arr[4], GT1Info[0], GT1Info[1], GT1Info[2], GT1Info[3], '.', '.', '.', '.']) + '\n')
			# I'm not sure if Bonnie wants variants only found in one vcf file to be counted as a WT change.
	#		self.change_counts[GT1Info[0] + '_WT'] += 1
			# read another line in vcf1 to get vcf1 and 2 back in sync.		
			line1 = self.vcf1.readline().strip()
			return line1
		else:
			# Skip over this variant in self.vcf2.
			GT2Info = self.getGTInfo(line, self.WT2_Cutoff, self.HOM2_Cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth
			self.outCSV.write('\t'.join([line2arr[0], line2arr[1], line2arr[3], line2arr[4], '.', '.', '.', '.', GT2Info[0], GT2Info[1], GT2Info[2], GT2Info[3]]) + '\n')
			# I'm not sure if Bonnie wants variants only found in one vcf file to be counted as a WT change.
	#		self.change_counts['WT_' + GT2Info[0]] += 1
			# read another line from vcf2 to get vcf1 and 2 back in sync.		
			line2 = self.vcf2.readline().strip()
			return line2

	# Match the rest of the variants in the file. The rest should be like chrX, Y, chrM or other stuff
	def matchTheRest(self, line1, line2):
		vcf1_leftovers = {}
		while line1 != '':
			vcf1_leftovers["_".join(line1.split('\t')[0:3])] = line1
			line1 = self.vcf1.readline().strip()
		vcf2_leftovers = {}
		while line2 != '':
			vcf2_leftovers["_".join(line2.split('\t')[0:3])] = line2
			line2 = self.vcf2.readline().strip()

		for chr_pos in vcf1_leftovers:
			line1arr = vcf1_leftovers[chr_pos].split('\t')
			GT1Info = self.getGTInfo(vcf1_leftovers[chr_pos], self.WT1_Cutoff, self.HOM1_Cutoff)
			if chr_pos in vcf2_leftovers:
				line2arr = vcf2_leftovers[chr_pos].split('\t')
				# this variant is found in both.
				GT2Info = self.getGTInfo(vcf2_leftovers[chr_pos], self.WT2_Cutoff, self.HOM2_Cutoff)
				self.outCSV.write('\t'.join([line1arr[0], line1arr[1], line1arr[3], line1arr[4], GT1Info[0], GT1Info[1], GT1Info[2], GT1Info[3], GT2Info[0], GT2Info[1], GT2Info[2], GT2Info[3]]) + '\n')
				GT1_GT2 = GT1Info[0] + "_" +  GT2Info[0]
				if GT1_GT2 in self.change_counts: # unknown (i.e ._.) will be skipped.
					self.change_counts[GT1_GT2] += 1
				# remove this variant from self.vcf2.
				vcf2_leftovers.pop(chr_pos, None)
			else:
				self.outCSV.write('\t'.join([line1arr[0], line1arr[1], line1arr[3], line1arr[4], GT1Info[0], GT1Info[1], GT1Info[2], GT1Info[3], '.', '.', '.', '.']) + '\n')
	
		for chr_pos in vcf2_leftovers:
			line2arr = vcf2_leftovers[chr_pos].split('\t')
			GT2Info = self.getGTInfo(vcf2_leftovers[chr_pos], self.WT2_Cutoff, self.HOM2_Cutoff)
			self.outCSV.write('\t'.join([line2arr[0], line2arr[1], line2arr[3], line2arr[4], '.', '.', '.', '.', GT2Info[0], GT2Info[1], GT2Info[2], GT2Info[3]]) + '\n')

	# If the json file exists, get the dictionary from it. If not, then make it
	def getJsonData(self, jsonFile):
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
	def getRunType(self, jsonData, WT_Cutoff):
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

if __name__ == "__main__":
	
	# set up the option parser
	parser = OptionParser()
	
	# add the options to parse
	parser.add_option('-v', '--vcfs', dest='vcfs', nargs=2, help='The two VCF files generated from the two runs combined Hotspot file')
	parser.add_option('-j', '--jsons', dest='jsons', nargs=2, help='The json files in each VCFs sample dir. These are used to get each runs type (i.e., tumor or normal). Normal should come before Tumor. They will not be altered by this script')
	parser.add_option('-g', '--gt_cutoffs', dest='gt_cutoffs', nargs=4, type="float", help='WT1_Cutoff, HOM1_Cutoff, WT2_Cutoff, HOM2_Cutoff. Variant filtering should already have been done before this step.')
	parser.add_option('-b', '--bases', dest='bases', nargs=2, type="float", help='1. total_eligible_bases (total bases available with good depth in each bam file) 2. Total possible bases (total baess available in the bed file)')
	parser.add_option('-o', '--out_csv', dest='outCSV', help='Output csv file to summarize the matched variants')
	parser.add_option('-t', '--json_out', dest='json_out',  help='This json file will hold the QC error metrics for this comparison. QC_generateSheets.py will use this json file to generate the master spreadsheet')
	parser.add_option('-c', '--cds', dest='cds', action="store_true", help='Optional. Add "CDS" to the title of the 3x3 table. This option should be used if the --run_gatk_twice option is specified in QC_2Runs.sh.')
	parser.add_option('-r', '--chr', dest='chr', help='Optional. Add the specified chromosome to the title of the 3x3 table. This option should be used if only chr1 is being QCd')
	
	(options, args) = parser.parse_args()
	
	#check to make sure either ID or name was provided
	if(not options.vcfs or not options.jsons or not options.gt_cutoffs or not options.bases or not options.outCSV or not options.json_out):
		print "USAGE ERROR: --vcfs, --jsons, --gt_cutoffs, --total_bases, --out_csv, and --json_out are all required. Only --cds and --chr are optional."
		print "Options given: --vcf %s --jsons %s --gt_cutoffs %s --total_bases %s --out_csv %s --json_out %s"%(options.vcfs, options.jsons, options.gt_cutoffs, options.bases, options.outCSV, options.json_out)
		print "Args given: %s"%args
		print "use -h for help"
		sys.exit(8)

	compare_vcfs = Compare_VCFs(options)
	compare_vcfs.main()
	
