#! /usr/bin/env python

# Goal: Now that all of the variants from all files that successsfully ran annovar.

import os
import sys
import subprocess
import re
import json
import fnmatch
import gc # for garbage collecting 
import numpy # for calculating stats
import math
from scipy.stats import mode
from optparse import OptionParser

# Paths
REF_FASTA = "/results/referenceLibrary/tmap-f3/hg19/hg19.fasta"
BAM_INDEXER = '/opt/picard/picard-tools-current/BuildBamIndex.jar'
VARIANT_CALLER_DIR = '/results/plugins/variantCaller'
SOFTWARE_ROOT = "/home/ionadmin/software"

# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------
total_vars = 0
ten_17_reads = 0
not_slam_dunk = 0
	
def main(project_dir, hotspot, out_file, var_info_out_file):
	# This global dictionary will be used to get all of the variant stats for the variant info file.
	global all_vars_info
	all_vars_info = {}

	global total_vars
	global ten_17_reads
	global not_slam_dunk
	total_vars += 1

	# First get all of the JSON files
	json_files = getJsonFiles(project_dir)

	dict_all_vars, list_all_vars = loadHotspot(hotspot)
	#print "gathered set_all_vars: ",set_all_vars

	#print dict_all_vars
	# Now pool the variants from the annovar files and generate the data matrix
	writeDataMatrix(dict_all_vars, list_all_vars, json_files, out_file)

	print 'Finished writing the datamatrix: %s. Now writing the variant info file: %s'%(out_file, var_info_out_file)

	# remove these variables to free up python's memory.
	dict_all_vars = ''
	list_all_vars = ''
	# garbage collector
	gc.collect()

	# If the user specified to write the variant info file, write it here.
	if var_info_out_file != None:
		# Now write the info and stats about all of the variants
		writeVarInfo(hotspot, all_vars_info, var_info_out_file)

	print 'total_vars:', total_vars
	print 'ten_17_reads:', ten_17_reads
	print 'not_slam_dunk:', not_slam_dunk
	print "Finished"


# @param project_dir the dir in which to find the json files used to find the vcf files to pool the variants
# @param hotspot the output hotspot file
def getJsonFiles(project_dir):
	json_files = [] # list of all of the json files found
	# first, find all of the sample's json files
	for root, dirnames, filenames in os.walk(project_dir):
		for filename in fnmatch.filter(filenames, "*.json"):
			json_files.append(os.path.join(root, filename))
	return json_files

def getJsonData(json_file):
	# load the json file
	jsonData = json.load(open(json_file))
	anno_vcf = ''
	if jsonData['sample_status'] == "merged_filtered":
		anno_vcf = "%s/Analysis_files/Wales_HS/anno_Post_HS.hg19_multianno.vcf"%jsonData['sample_folder']
			#print "loading the variants of " + anno_vcf
			#vcfFile = open(anno_vcf, 'r')
			#project_variants = addVars2Set(vcfFile, project_variants)
	return anno_vcf


# All of the variants in the final hotspot file should have been filtered previously, so this correctly represents the set of all variants
# @param the annotated hotspot file containing the pooled variants
# @returns a set of the gene_pos of all variants
def loadHotspot(hotspot):
	list_all_vars = [] # the list of all variants will be used to ensure that every VCF file has all of the correct variants. It will also serve to sort all of the vars.
	dict_all_vars = {} # the dict of all variants will be used to shortcut the step of annotating each sample's variants. All of the annotation will be done using the hotspot file
	# regex for parsing out the AA listed by Annovar
	getAA = re.compile('([a-zA-Z]*)(\d+)([a-zA-Z]*)')
	with open(hotspot, 'r') as HSFile:
		for line in HSFile:
			if line[0] != '#':
				line = line.strip().split("\t")
				# This if statement is so that you can generate a data matrix with only the multi-var calls. 
				if not options.multi_var_only or len(line[4].split(',')) > 1:
					chr_pos = '_'.join(line[0:2])
					alleles = {} # Dict that will hold the AA changes for each allele listed at each chr_pos. If there is no AA change, the regular nucleotide will be held instead.
					# Get annovar's annotation part of the vcf file and load it into the dictionary varInfo
					varInfo = getAnnoDict(line, 0) # we can just assume that the first alt allele is the correct one because here we're just getting the gene name and var type (i.e. exonic vs intronic)
					# We aren't looking at the UTR 5 or 3 variants here, so remove those
					var_type = varInfo['Func.refGene']
					geneName = varInfo['Gene.refGene']
					# Get the AA information for exonic variants
					if var_type == 'exonic':
						AAChange = getAAChange(line, 0) # get the gene name and the AA change
						m = getAA.match(AAChange)
						REF_Change = m.group(1)
						REF_Pos = m.group(2)
						list_all_vars.append((geneName, line[1], '%s%s'%(REF_Change,REF_Pos), chr_pos))
						alleles[line[3]] = REF_Change
						for i in range(0, len(line[4].split(','))):
							AAChange = getAAChange(line, i) # get the gene name and the AA change
							m = getAA.match(AAChange)
							ALT_Change = m.group(3)
							alleles[line[4].split(',')[i]] = ALT_Change
					else:
						list_all_vars.append((geneName, line[1], '%s%s'%(line[3],line[1]), chr_pos))
						alleles[line[3]] = line[3]
						for nuc in line[4].split(','):
							alleles[nuc] = nuc
	
					dict_all_vars[chr_pos] = alleles
					#list_all_vars.append('_'.join([varInfo['Gene.refGene'], line[0], line[1]]))

					# here is the all_vars_info addition
					# It would be more time and memory efficient to not store all of this into memory. I could probably just loop through the Hotspot file again.
					if chr_pos not in all_vars_info:
						all_vars_info[chr_pos] = {'WT':0, 'HET':0, 'HOM':0, 'freq':[]}

	# Last we need to sort the list_all_vars
	list_all_vars = my_sort(list_all_vars)

	return dict_all_vars, list_all_vars


# all_vars_info is a global dictionary containing all of the variants and their counts and GT frequencies.
# @param GT_Info the information about this sample's variant
def add_var_info(chr_pos, GT, freq):
	# Add a count to this positions GT.
	all_vars_info[chr_pos][GT] += 1
	# add the freq of this variant to be used for statistics later
	all_vars_info[chr_pos]['freq'].append(float(freq))


# @param allele_freqs is a list of allele frequencies for each chr_pos. The frequency is calculated this way: allele_depth / total_depth.
# If the reference allele's depth frequency is > .8, then 1 - ref_freq is printed.
# Otherwise the % of alt allele is printed. This is done to compare the % of alt allele accross the population.
def getVarStats(allele_freqs):
	allele_freqs.sort(key=float)
	rounded_list = []
	HETs = []
	HOMs = []
	# The mode is the value that most often appears in a dataset
	# round the frequencies to help find a mode
	for freq in allele_freqs:
		rounded_list.append(float(str(freq)[0:4]))
		if freq >= .2 and freq < .8:
			HETs.append(float(freq))
		elif freq > .8:
			HOMs.append(freq)
	
	# calc the mode of the rounded list of frequencies
	freq_mode, mode_count = mode(rounded_list)
	# calc the median of the HET values
	median_het = numpy.median(HETs) 	
	
	# Now the Interquartile range
	# For percentile to work, I had to upgrade numpy using this command: sudo pip install numpy==1.7.1 --upgrade
	# Didn't work...
	#q75, q25 = numpy.percentile(allele_freqs, [75,25])
	# I'll use my own IQR function instead.
	IQR = calc_IQR(allele_freqs)
	IQR_HET = '.'
	if len(HETs) > 2:
		IQR_HET = calc_IQR(HETs)
	
	
	return '\t'.join([str(median_het), str(IQR_HET), str(IQR), str(freq_mode[0]) + ', ' + str(mode_count[0])])


# function for calculating the Interquarile range. This function uses the linear interpolation method.
def calc_IQR(freqs):
	# If there is an odd number of items, the bottom and top half of the data should be split around the middle value
	Q1 = float(len(freqs) + 1) / 4
	Q1_left = freqs[int(math.floor(Q1)) -1] # subract 1 because computers start at 0
	Q1_right = freqs[int(math.ceil(Q1)) -1] # subract 1 because computers start at 0
	Q1 = Q1_left + (.75 * (Q1_right - Q1_left))
	Q3 = float(3*(len(freqs) + 1)) / 4
	Q3_left = freqs[int(math.floor(Q3)) -1] # subract 1 because computers start at 0
	#print len(freqs), str(math.ceil(Q3) -1)
	Q3_right = freqs[int(math.ceil(Q3)) -1] # subract 1 because computers start at 0
	Q3 = Q3_left + (.25 * (Q3_right - Q3_left))
	return Q3 - Q1


## function for calculating the Interquarile range
#def calc_IQR(freqs):
#	# If there is an odd number of items, the bottom and top half of the data should be split around the middle value
#	bottom_half = ''
#	top_half = ''
#	if len(freqs) % 2 != 0:
#		bottom_half = freqs[:((len(freqs) - 1)/2)]
#		top_half = freqs[((len(freqs) + 1)/2):]
#	else:
#		bottom_half = freqs[:(len(freqs) / 2)]
#		top_half = freqs[(len(freqs) / 2):]
#	q75 = numpy.median(top_half)
#	q25 = numpy.median(bottom_half)
#	return q75 - q25

# @param all_vars_info dictionary containing the info and stats for all of the variants of the project.
# @param list_all_vars a sorted list of all of the variants containing the chr_pos, gene and other info
# @param out_file the file to write the variant info to.
def writeVarInfo(hotspot, all_vars_info, out_file):
	out = open(out_file, 'w')

	# List of variant scores for understanding a variant's importance
	score_list = ['1000g2012apr_all', 'snp129NonFlagged', 'snp137NonFlagged', 'LJB23_SIFT_score', 'LJB23_SIFT_pred', 'LJB23_Polyphen2_HDIV_score', 
			'LJB23_Polyphen2_HDIV_pred', 'LJB23_Polyphen2_HVAR_score', 'LJB23_Polyphen2_HVAR_pred', 'LJB23_GERP++', 'LJB23_PhyloP', 
			'LJB23_SiPhy', 'LJB23_MutationTaster_score', 'LJB23_MutationTaster_pred']
	# First write the header line
	out.write('\t'.join(['Gene', 'chr', 'pos', 'Ref', 'Alt', '# WT', '# HET', '# HOM', 'Medain_HET', 'IQR HETs', 'IQR', 'Mode, Mode Count', 'Variant Function', 'Variant Exonic Function', 'AA change']) + 
			'\t' + '\t'.join(score_list) + '\n')
 
	# regex for parsing out the AA listed by Annovar
	getAA = re.compile('([a-zA-Z]*)(\d+)([a-zA-Z]*)')
	# Loop through all of the variants in the Hotspot file and write it along with all it's info.
	with open(hotspot, 'r') as HSFile:
		for line in HSFile:
			if line[0] != '#':
				line = line.strip().split("\t")
				# This if statement is so that you can generate a data matrix with only the multi-var calls. 
				if not options.multi_var_only or len(line[4].split(',')) > 1:
					chr_pos = '_'.join(line[0:2])
					varInfo = getAnnoDict(line, 0) # we can just assume that the first alt allele is the correct one because here we're just getting the gene name and var type (i.e. exonic vs intronic)
					# We aren't looking at the UTR 5 or 3 variants here, so remove those
					var_type = varInfo['Func.refGene']
					geneName = varInfo['Gene.refGene']
					# Write the first var info
					out.write('\t'.join([geneName, line[0], line[1], line[3], line[4], str(all_vars_info[chr_pos]['WT']), str(all_vars_info[chr_pos]['HET']),
						str(all_vars_info[chr_pos]['HOM'])]))

					# Now write the Variant statistics
					out.write('\t'.join(['', getVarStats(all_vars_info[chr_pos]['freq'])]))

					# write the exonic function and the AA change if this is an exonic variant
					if var_type == 'exonic':
					 	out.write('\t'.join(['', var_type, varInfo['ExonicFunc.refGene'], '']))
						for i in range(0, len(line[4].split(','))):
							AAChange = getAAChange(line, i) # get the gene name and the AA change
							if i > 0:
								out.write(', ')
							out.write(AAChange)
					else:
						out.write('\t'.join(['', var_type, '.','.']))
	
					for score in score_list:
						if varInfo[score] == '':
							out.write('\t.') 
						else:
							out.write('\t' + varInfo[score])
					out.write('\n')
	
	out.close()


# @param line a split vcf annotated line
# @returns the correct output for the data matrix
def getAAChange(line, index):
		varInfo = getAnnoDict(line, index)
		# find the correct splice (separated by ,)
		# sample AAChange.refGene part: AAChange.refGene=ADORA3:NM_001081976:exon6:c.T786C:p.P262P,ADORA3:NM_020683:exon6:c.T1029C:p.P343P;
		try:
			alt_splicings = varInfo['AAChange.refGene'].split(',')
		except KeyError:
			print 'alt_allele doesnt match annovar: ', line, varInfo
			return ''
			sys.exit(1)
		matching_splice = ''
		# This is the list of the longest transcripts for all of the genes in the Wales dataset. 
		canonTranscripts=set(['NM_004996', 'NM_020683', 'NM_199460', 'NM_001190455', 'NM_000754', 'NM_001004019', 'NM_144600', 'NM_004481', 'NM_000834', 'NM_003483', 'NM_005501', 'NM_001184998', 'NM_001128423', 'NM_001040114', 'NM_017668', 'NM_000281', 'NM_003901', 'NM_033517', 'NM_001172504', 'NM_003105', 'NM_006772', 'NM_001244', 'NM_001007471', 'NM_000368', 'NM_000548', 'NM_018117', 'NM_032642'])
		for splice in alt_splicings:
			info = splice.split(':')
			transcript = info[1]
			if transcript in canonTranscripts:
				matching_splice = splice
				break
		# If none of the transcripts match what we have, then just take the last one.
		if matching_splice == '':
			matching_splice = alt_splicings[-1]
	
		splice_info = matching_splice.split(':')
		AAChange = splice_info[4][2:]
		
		return AAChange


# @param line a split line
# @param index the index of the correct alt allele
# @returns a dict of the annotated variant info
def getAnnoDict(line, index):
	# Here is an example line from a vcf file that has been annotated:
	#Func.refGene=exonic;Gene.refGene=ADORA3;GeneDetail.refGene=;ExonicFunc.refGene=synonymous_SNV;AAChange.refGene=ADORA3:NM_001081976:exon6:c.T786C:p.P262P,ADORA3:NM_020683:exon6:c.T1029C:p.P343P;1000g2012apr_all=;ALLELE_END
	# The alternate alleles are split by 'ALLELE_END', so split by that, get the correct index from GTInfo.
	annoInfo = line[7].split('ALLELE_END')[index].split(";")
	if len(annoInfo) == 0:
		annoInfo = line[7].split('ALLELE_END')[0].split(";")
#		print 'Theres only one ALLELE_END here!', line
#	elif index > 0:
#		print 'Theres more than one ALLELE_END here!', line, index
	annoDict = {}
	for item in annoInfo:
		if len(item.split('=')) > 1:
			annoDict[item.split('=')[0]] = item.split('=')[1]
	return annoDict

# @param list_all_vars a sorted list of all of the chr_pos_ref_alt variants
# @param json_files a list of all of the json_files
# @param out_file the name of the file to write the data matrix to.
# @returns a written data matrix
def writeDataMatrix(dict_all_vars, list_all_vars, json_files, outFile):
	with open(outFile, 'w') as data_matrix:
		#data_matrix.write("GeneName_REFchrposALT (Amino Acid Change)")
		data_matrix.write("GeneName_Ref_Pos")
		total_num_vars = len(list_all_vars)
		# First loop through the set of all variants and write them as the header to the output file
		for var_list in list_all_vars:
			# The variant was stored like this: Gene_AAPos_AAChange (Nuc Change)
			# We want the output to be: Gene_AAChange (Nuc Change)
			data_matrix.write("\t%s_%s"%(var_list[0],var_list[2]))
		
		data_matrix.write('\n')
		# Now loop through all of the samples, and print out their GT for each variant in the all_vars list. (If no GT info is present, simply leave the cell blank)
		# sample is the current sample (i.e. case1_A01) and sampleVars is the list of all of the variants of that sample
		for json_file in json_files:
			# get the annotated vcf file from the json_file
			jsonData = json.load(open(json_file))
			if 'sample_status' in jsonData and jsonData['sample_status'] == "merged_filtered":
				# First write the sample name to the output file
				# TEMP WALES fix
				sample_name = '_'.join(jsonData['name'].split('_')[0:2])
				data_matrix.write(sample_name)
				# The variants should be in the same order as the hotspot file used to create them, so write all of the variants in the annotated vcf file
				anno_vcf = "%s/Analysis_files/Wales_HS/anno_Post_HS.hg19_multianno.vcf"%jsonData['sample_folder']
				if not os.path.isfile(anno_vcf):
					print "WARNING: %s was not found! Skipping this samle"%anno_vcf
				else:
					sample_vars = writeVarsInVCF(anno_vcf, dict_all_vars)	
					for var_list in list_all_vars:
						chr_pos = var_list[-1]
						data_matrix.write('\t' + sample_vars[chr_pos])
					#if len(sample_vars.split('\t')) - 1 != total_num_vars:
					#if len(sample_vars.split('\t')) != total_num_vars:
					#	print "ERROR: %s has %d vars. there should be %d vars"%(sample_name, len(sample_vars.split('\t')) - 1,total_num_vars)
					#	print sample_vars
					#	sys.exit(1)
					#data_matrix.write(sample_vars)
				data_matrix.write('\n')

# These files should all match the hotspot file exactly because of the options used to run tvc.
# @param anno_vcf an annotated vcf file post hotspot
# @returns a string containing the info to be written to the data matrix file
def writeVarsInVCF(anno_vcf, dict_all_vars):
	vars_to_write = {}
	with open(anno_vcf, 'r') as anno_vcf_file:
		for line in anno_vcf_file:
			if line[0] != '#' and line[0:3] == "chr" :
				line = line.strip().split("\t")
				# This if statement is so that you can generate a data matrix with only the multi-var calls. 
				if not options.multi_var_only or len(line[4].split(',')) > 1:
					chr_pos = line[0] + '_' + line[1]
					varInfo = getAnnoDict(line, 0)
					# returns a tuple containing 1st the total_depth and second, either two variants (if the depths reported only two) or however many variants were found.
					total_depth, num_alleles, GT_Info = getGTInfo(line, .2, .8)
					# Now check to see if the variant has enough depth
					global total_vars
					global ten_17_reads
					global not_slam_dunk
					total_vars += 1
					if total_depth >= 10 and total_depth <= 17:
						ten_17_reads += 1
						#print GT_Info[2]
						if num_alleles < 3:
							freq = float(GT_Info[2])
							if (freq >= .11 and freq <= .3) or (freq >= .7 and freq <= .9):
								not_slam_dunk += 1
						else:
							not_slam_dunk += 1
					if total_depth < DEPTH_CUTOFF:
						vars_to_write[chr_pos] = 'LOW_DEPTH: %d'%(total_depth)
					elif num_alleles > 2:
						# This is a multi-allelic sequencing error.
						vars_to_write[chr_pos] = GT_Info[0][0]
						for i in range(1,len(GT_Info)):
							vars_to_write[chr_pos] += '/%s'%GT_Info[i][0]
						vars_to_write[chr_pos] += ' (%.3f'%GT_Info[0][1]
						for i in range(1,len(GT_Info)):
							vars_to_write[chr_pos] += '/%.3f'%GT_Info[i][1]
						vars_to_write[chr_pos] += ')'
					else:
						allele1 = dict_all_vars[chr_pos][GT_Info[0]]	
						allele2 = dict_all_vars[chr_pos][GT_Info[1]]	
						freq = GT_Info[2]
						vars_to_write[chr_pos] = "%s/%s (%s)"%(allele1, allele2, freq)
						add_var_info(chr_pos, GT_Info[3], freq)
	return vars_to_write


# @param line a split vcf annotated line
# @returns the correct output for the data matrix
def getGTChange(line):
	GT, highest_alt_freq, total_alt_depth, ref_depth, index = getGTInfo(line, .2, .8) # Because this is a germline script, just pass the WT and HOM cutoffs hardcoded here
	# Now check to see if the variant has enough depth
	if total_alt_depth + ref_depth < DEPTH_CUTOFF:
		return 'LOW_DEPTH: %d'%(total_alt_depth + ref_depth)
	else:
		GTChange = "%s%s%s"%(line[3], line[1], line[4].split(',')[index])
		return "%s (%s) %s"%(GT, highest_alt_freq, GTChange)


#def runAnnovar(inVCF, outVCF):
#	if os.isfile(outVCF):
		# Annovar has already been run on this file. Get the variants
#@param Takes as input the line from a vcf file and the WT and HOM allele frequency cutoffs. (Could be different for Tumor / Normal pairs)
#@return Returns a tuple with 1. the GT, 2. alternate allele frequency, 3. the alt depth, and 4. the ref depth, 5. the index of the best alt allele. (I did not consider the sample having two alternate alleles!!!!)
def getGTInfo(line, WT_cutoff, HOM_cutoff):
	#line = line.split("\t") # the line should've already been split
	alternates = line[4].split(",")
	try:
		info = dict(zip(line[8].split(":"), line[9].split(":"))) #Creates a dictionary with the description as the key, and the actual value as the value.
		depths = [] # list of depth tuples. 1st is the allele, 2nd the depth 
		freqs = [] # list of frequencies 
		ref = line[3]
		# Loop through the variants to grap the alternate depths.
		if 'FAO' in info and info['FAO'] != '.': # the flow depth score is better than the base space depth score, so use that if we can.
			ref_allele = (ref, int(info['FRO'])) # first get the ref_depth
			depths.append(ref_allele)
			total_depth = int(info['FRO']) 
			for i in range(0, len(alternates)): # if there is only one alternate allele, then this for loop will run only once
				depths.append((alternates[i], int(info['FAO'].split(',')[i])))
				total_depth += int(info['FAO'].split(',')[i])
		elif 'AO' in info:
			ref_allele = (ref, int(info['RO']))
			depths.append(ref_allele)
			total_depth = int(info['RO']) 
			for i in range(0, len(alternates)):
				depths.append((alternates[i], int(info['AO'].split(',')[i])))
				total_depth += int(info['AO'].split(',')[i])
		if total_depth == 0:
			return 0,0,0
		else:
			for allele, depth in depths:
				freq = depth / float(total_depth)
				if freq > .1: # use .1 as a temporary threshold for multi-allelic calls
					freqs.append((allele, freq))
			# First check if there are too many variants to be real (sequencing artifact)
			if len(freqs) > 2:
				# if this doesn't look real, then return all of the frequencies to be printed out.	
				return total_depth, len(freqs), freqs
			else:
				# first check the WT status
				if freqs[0][0] == ref_allele[0]:
					if freqs[0][1] > HOM_cutoff:
						# This should be WT/WT. change the freq to be the percentage of variant calls
						return total_depth, 2, [freqs[0][0], freqs[0][0], str((1-freqs[0][1]))[0:5], 'WT']
				if freqs[0][1] > HOM_cutoff:
					# This should be HOM mutant. 
					return total_depth, 2, [freqs[0][0], freqs[0][0], str((freqs[0][1]))[0:5], 'HOM']
				elif freqs[1][1] > HOM_cutoff:
					# This should be HOM mutant. 
					# If this allele's frequency is greaty then the hom cutoff, then return something like A/A (.85)
					return total_depth, 2, [freqs[1][0], freqs[1][0], str(freqs[1][1])[0:5], 'HOM']
				else:
					# This must be a heterozygous variant. Print the two alleles, with the frequency of the second (because the first is most often the ref allele)
					if freqs[0][1] > freqs[1][1] and freqs[0][0] != ref_allele[0]:
						# If this is a ALT/ALT HET rather than a regular WT/ALT HET, then the greater of the two allele frequencies should be output to the screen. 
						return total_depth, 2, [freqs[0][0], freqs[1][0], str(freqs[0][1])[0:5], 'HET']
					else:
						# Otherwise, just print the second allele's frequency.
						return total_depth, 2, [freqs[0][0], freqs[1][0], str(freqs[1][1])[0:5], 'HET']

	except KeyError, ValueError:
		#print "Leaving GT as . for this variant:", line
		traceback.print_exc()
		sys.exit(1)
		#pass

	return freqs # returns a list of tuples of alleles and their frequencies

# Sort by gene and pos
def my_sort(list_all_vars):
	sorted_vars = []
	current_gene = ''
	current_len = 0
	# loop through the dict of all vars ordered by Gene.
#	for variant in sorted(dict_all_vars, key=dict_all_vars.get):
	for variant in sorted(list_all_vars):
		gene = variant[0]
		pos = variant[1]
		if current_gene != gene:
			current_len = len(sorted_vars)
			current_gene = gene
			sorted_vars.append(variant)
		# Start putting the variants in by position
		else:
			i = current_len
			inserted = False
			while i < len(sorted_vars) and not inserted:
				currentPos = sorted_vars[i][1]
				if int(pos) < int(currentPos):
					sorted_vars.insert(i, variant)
					inserted = True
				else:
					i += 1
			if not inserted:
				sorted_vars.append(variant)
	return sorted_vars


# --------------------------------------------------------
# ----------- PROGRAM STARTS HERE ------------------------
# --------------------------------------------------------

if (__name__ == "__main__"):
	# set up the parser
	parser = OptionParser()

	parser.add_option('-p', '--project_dir', dest='project_dir', help="The project dir for which you want to generate the master hotspot file")
#	parser.add_option('-r', '--run_annovar', dest='annovar', help="run annovar on all of the Wales samples")
	parser.add_option('-a', '--ah', dest='hotspot', help='The name of the master hotspot file used to re-run TVC on all of the samples')
	parser.add_option('-o', '--datamatrix', default="datamatrix.csv", dest='datamatrix', help='The output Data Matrix [Default: %default]')
	parser.add_option('-i', '--write_var_info', default="var_info.csv", dest='var_info', help='Write a variant info file containing stats' + 
			'about each variant in the population and their annotated importance (dbSNP #, sift, polyphen, etc.) [Default: %default]')
	parser.add_option('-m', '--min_base_cutoff', default=10, type="int", dest='min_base_cutoff', help='The minimum depth each variant must have to be considered. [Default: %default]')
	parser.add_option('-j', '--multi_var_only', dest='multi_var_only', action="store_true", default=False, help='write the data matrix for only places with multiple alternate alleles')

	options, args = parser.parse_args()

	if not options.project_dir or not options.hotspot:
		print "USAGE ERROR: both -p (--project_dir) and -a (--anno_hotspot) are required"
		parser.print_help()
		#print "Use -h for help"
		sys.exit(8)

	# make the depth cutoff global so other functions can use it.
	global DEPTH_CUTOFF
	DEPTH_CUTOFF = options.min_base_cutoff

	main(options.project_dir, options.hotspot, options.datamatrix, options.var_info)

