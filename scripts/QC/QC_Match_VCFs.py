#! /usr/bin/env python

#script to QC the VCF files of two different runs before merging them.

#  Goal: Run QC on all of the BAM files that have multiple runs (after filtering and matching with the hotspot file).
#  Because the two different runs are of the same genes of the same person, the VCF files are supposed to be the same.
#  Match the variant entries among the two different vcf files of the two runs. Report the corresponding freq and depths
#  Report any variant not matched in both files.

import sys
import re
import os
import subprocess

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
		GT1Info = getGTInfo(line, WT1_cutoff, HOM1_cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth
		outCSV.write('\t'.join([line1arr[0], line1arr[1], line1arr[3], line1arr[4], GT1Info[0], GT1Info[1], GT1Info[2], GT1Info[3], '.', '.', '.', '.']) + '\n')
		# I'm not sure if Bonnie wants variants only found in one vcf file to be counted as a WT change.
#		change_counts[GT1Info[0] + '_WT'] += 1
		# read another line in vcf1 to get vcf1 and 2 back in sync.		
		line1 = file1_vcf.readline().strip()
		return line1
	else:
		# Skip over this variant in vcf2.
		GT2Info = getGTInfo(line, WT2_cutoff, HOM2_cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth
		outCSV.write('\t'.join([line2arr[0], line2arr[1], line2arr[3], line2arr[4], '.', '.', '.', '.', GT2Info[0], GT2Info[1], GT2Info[2], GT2Info[3]]) + '\n')
		# I'm not sure if Bonnie wants variants only found in one vcf file to be counted as a WT change.
#		change_counts['WT_' + GT2Info[0]] += 1
		# read another line from vcf2 to get vcf1 and 2 back in sync.		
		line2 = file2_vcf.readline().strip()
		return line2

# Match the rest of the variants in the file. The rest should be like chrX, Y, chrM or other stuff
def matchTheRest(line1, line2):
	vcf1_leftovers = {}
	while line1 != '':
		vcf1_leftovers["_".join(line1.split('\t')[0:3])] = line1
		line1 = file1_vcf.readline().strip()
	vcf2_leftovers = {}
	while line2 != '':
		vcf2_leftovers["_".join(line2.split('\t')[0:3])] = line2
		line2 = file2_vcf.readline().strip()

	for chr_pos in vcf1_leftovers:
		line1arr = vcf1_leftovers[chr_pos].split('\t')
		GT1Info = getGTInfo(vcf1_leftovers[chr_pos], WT1_cutoff, HOM1_cutoff)
		if chr_pos in vcf2_leftovers:
			line2arr = vcf2_leftovers[chr_pos].split('\t')
			# this variant is found in both.
			GT2Info = getGTInfo(vcf2_leftovers[chr_pos], WT2_cutoff, HOM2_cutoff)
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
		GT2Info = getGTInfo(vcf2_leftovers[chr_pos], WT2_cutoff, HOM2_cutoff)
		outCSV.write('\t'.join([line2arr[0], line2arr[1], line2arr[3], line2arr[4], '.', '.', '.', '.', GT2Info[0], GT2Info[1], GT2Info[2], GT2Info[3]]) + '\n')
	

# ----------------------------------------------------
# ------------- PROGRAM STARTS HERE ------------------
# ----------------------------------------------------

# Example usage: python QC_wales.py TD04_finalIntersect_update.vcf LD04_finalIntersect_update.vcf match.csv 
# input files for the program.
if len(sys.argv) >= 10:
	file1_vcf = open (sys.argv[1], 'r') # input file1 vcf (with hotspot call)
	WT1_cutoff = float(sys.argv[2])
	HOM1_cutoff = float(sys.argv[3])
	file2_vcf = open (sys.argv[4], 'r') # input file2 vcf (with hotspot call)
	WT2_cutoff = float(sys.argv[5])
	HOM2_cutoff = float(sys.argv[6])
	total_eligible_bases = int(sys.argv[7]) # This value is generated by GATK using the Overlap subset Bed file
	if total_eligible_bases == 0:
		print "ERROR: total_eligible_bases cannot be 0"
		sys.exit(8)
	outCSV = open (sys.argv[8], 'w') # output csv file to summarize the matched variants
	# the master sheet has a line per outCSV_File with the info to generate the 3x3 QC table.
	master_table = open (sys.argv[9], 'a') # This script APPENDS to the master list
else:
	# If there are any problems with the arguments, print this usage error
	print "USAGE: python QC_wales.py <Run1.vcf> WT1_cutoff HOM1_cutoff <Run2.vcf> WT2_cutoff HOM2_cutoff <total_eligible_bases> \
			<output_matched_variants.csv> <master_sheet.csv>"
	sys.exit(8)


# add the header lines to the csv file
outCSV.write("chr\tpos\tRef\tAlt\tRun1 GT\tRun1 AF\tRun1 Alternate Depth\tRun1 Ref Depth\t " + \
		"Run2 GT\tRun2 AF\tRun2 Alternate Depth\tRun2 Ref Depth\n")
change_counts = {'WT_WT':0, 'WT_HET':0, "WT_HOM":0,'HET_WT':0, 'HET_HET':0, "HET_HOM":0, \
		'HOM_WT':0, 'HOM_HET':0, "HOM_HOM":0,} # a dictionary to keep track of the allele types of the two different files compared..

line1 = file1_vcf.readline().strip()
line2 = file2_vcf.readline().strip()
# Because the two vcf files were created from the same HotSpot file, they should have the same chromosome positions listed in the same order.
# Therefore, I am reading the two vcf files line by line at the same time.
while line1 != '' and line1[0] == '#':
	line1 = file1_vcf.readline().strip()
	line2 = file2_vcf.readline().strip()
while line1 != '' or line2 != '':
	line1arr = line1.split('\t')
	line2arr = line2.split('\t')
	# If I make it a while loop rather than an if statement, this will handle if there are more than one mismatches. If the error rate is really high, the vcf files given were probably not from the same hotspot file.
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
	# If the while loop hit the end of the file, then don't do anything here.
	if line1 != '' and line2 != '':
		GT1Info = getGTInfo(line1, WT1_cutoff, HOM1_cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth
		GT2Info = getGTInfo(line2, WT2_cutoff, HOM2_cutoff) # Will return a tuple with 1. the GT, 2. alternate allele frequency, 3.the alt depth, and 4. the ref depth 
		# Write the chr, pos, ref Allele, alt Allele, vcf1 info, vcf2 info.
		outCSV.write('\t'.join([line1arr[0], line1arr[1], line1arr[3], line1arr[4], GT1Info[0], GT1Info[1], GT1Info[2], GT1Info[3], GT2Info[0], GT2Info[1], GT2Info[2], GT2Info[3]]) + '\n')
		GT1_GT2 = GT1Info[0] + "_" +  GT2Info[0]
		if GT1_GT2 in change_counts: # unknown (i.e ._.) will be skipped.
			change_counts[GT1_GT2] += 1
		line1 = file1_vcf.readline().strip()
		line2 = file2_vcf.readline().strip()
	

# If you are comparing Normal Normal or Tumor Tumor, the error count should be everything off diagonal
if WT1_cutoff == WT2_cutoff:
	error_count =  int(change_counts['WT_HET']) + int(change_counts['WT_HOM']) + int(change_counts['HET_HOM']) + int(change_counts['HET_WT']) +  int(change_counts['HOM_WT']) + int(change_counts['HOM_HET'])
	change_counts['WT_WT'] += total_eligible_bases - error_count
# If you are comparing Tumor Normal pairs, the error count should only include the Normal side
else:
	error_count =  int(change_counts['HET_WT'])  +  int(change_counts['HOM_WT']) + int(change_counts['HOM_HET'])
	change_counts['WT_WT'] += total_eligible_bases - error_count - int(change_counts['WT_HET']) - int(change_counts['WT_HOM']) - int(change_counts['HET_HOM'])
# If the error rate is really low, floats give a 4.567e^4 or something like that. *100 to get percentages.... ?
error_rate = (float(error_count) / float(total_eligible_bases))
change_counts['error_count'] = error_count
change_counts['error_rate'] = str(error_rate)
change_counts['total_eligible_bases'] = str(total_eligible_bases)


# Write the gathered info to the master_table output file.
# The file path should look like this: sample01/QC/Run1vsRun2/VCF1_Final.vcf
file1 = sys.argv[1].split("/")
file2 = sys.argv[2].split("/")
sample = file1[-4] # i.e. sample01
runs = file1[-2] # i.e. Run1vsRun2
#run1 = file1[-2].split("vs")[0] # i.e. sample1_Run1
#run2 = file1[-2].split("vs")[1] # i.e. samples1_Run2
#ver1 = file1[-1][0:3] # i.e. 3.4TSVC.vcf
#ver2 = file2[-1][0:3] # i.e. 4.0TSVC.vcf
# If the bam files are not the same version vcf1 and vcf2 will include the name of the vcf file indicating the bam's TS version
#if ver1 != ver2:
#	run1 += '_TSv' + ver1 # i.e. QCRun1_TSv3.4
#	run2 += '_TSv' + ver2 # i.e. Run2_TSv4.0

# First write the case_sample_run:case_sample_run (i.e. case1_A02_run1_TSv3.4:case1_A02_run2_TSv4.0)
#master_table.write('%s_%s_%s'%(file1[-4],file1[-3],vcf1) + ":" + '%s_%s_%s\t'%(file2[-4],file2[-3],vcf2))
master_table.write("%s:%s\t"%(sample, runs))
for key in change_counts:
	master_table.write(key + ':' + str(change_counts[key]) + "\t")
master_table.write('\n')
	
file1_vcf.close()
file2_vcf.close()
outCSV.close()
master_table.close()
