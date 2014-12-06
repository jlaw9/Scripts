#! /usr/bin/env python

# Goal: Now that all of the variants from all files that successsfully ran annovar.

import os
import sys
import subprocess
import re
import json
import fnmatch
from optparse import OptionParser

# Paths
REF_FASTA = "/results/referenceLibrary/tmap-f3/hg19/hg19.fasta"
BAM_INDEXER = '/opt/picard/picard-tools-current/BuildBamIndex.jar'
VARIANT_CALLER_DIR = '/results/plugins/variantCaller'
SOFTWARE_ROOT = "/home/ionadmin/software"

# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------
	
def main(project_dir, hotspot, out_file):
	# First get all of the JSON files
	json_files = getJsonFiles(project_dir)

	dict_all_vars, list_all_vars = loadHotspot(hotspot)
	#print "gathered set_all_vars: ",set_all_vars

	# Now pool the variants from the annovar files and generate the data matrix
	writeDataMatrix(dict_all_vars, list_all_vars, json_files, out_file)

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
	getAA = re.compile('([A-Z]*)(\d+)([A-Z]*)')
	with open(hotspot, 'r') as HSFile:
		for line in HSFile:
			if line[0] != '#':
				line = line.strip().split("\t")
				chr_pos = '_'.join(line[0:2])
				alleles = {} # Dict that will hold the AA changes for each allele listed at each chr_pos. If there is no AA change, the regular nucleotide will be held instead.
				# Get annovar's annotation part of the vcf file and load it into the dictionary varInfo
				varInfo = getAnnoDict(line, 0) # we can just assume that the first alt allele is the correct one because here we're just getting the gene name and var type (i.e. exonic vs intronic)
				# We aren't looking at the UTR 5 or 3 variants here, so remove those
				var_type = varInfo['Func.refGene']
				geneName = varInfo['Gene.refGene']
				# I'm not sure what to do with splicing variants right now, so don't worry about those yet..
				if var_type == 'exonic':
					AAChange = getAAChange(line, 0) # get the gene name and the AA change
					m = getAA.match(AAChange)
					REF_Change = m.group(1)
					REF_Pos = m.group(2)
					list_all_vars.append((geneName, line[1], '%s%s'%(REF_Change,REF_Pos), chr_pos))
					alleles[line[3]] = REF_Change
					for i in range(0, len(line[4].split(','))):
						AAChange = getAAChange(line, i) # get the gene name and the AA change
						m = p.match(AAChange)
						ALT_Change = m.group(2)
						alleles[line[4].split(',')[i]] = ALT_Change
				else:
					list_all_vars.append((geneName, line[1], '%s%s'%(line[3],line[1]), chr_pos))
					for nuc in line[4].split(','):
						alleles[nuc] = nuc

				dict_all_vars[chr_pos] = alleles
				#list_all_vars.append('_'.join([varInfo['Gene.refGene'], line[0], line[1]]))
	return dict_all_vars, list_all_vars


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
		# First we need to sort the dict_all_vars
		list_all_vars = my_sort(list_all_vars)
		total_num_vars = len(list_all_vars)
		# First loop through the set of all variants and write them as the header to the output file
		for var_list in list_all_vars:
			# The variant was stored like this: Gene_AAPos_AAChange (Nuc Change)
			# We want the output to be: Gene_AAChange (Nuc Change)
			data_matrix.write("\t%s_%s"%(var_list[0],var_list[2])
		
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
		print "Finished generating data matrix of all the variants."

# These files should all match the hotspot file exactly because of the options used to run tvc.
# @param anno_vcf an annotated vcf file post hotspot
# @returns a string containing the info to be written to the data matrix file
def writeVarsInVCF(anno_vcf, dict_all_vars):
	vars_to_write = {}
	with open(anno_vcf, 'r') as anno_vcf_file:
		for line in anno_vcf_file:
			if line[0] != '#':
				line = line.strip().split("\t")
				chr_pos = line[0] + '_' + line[1]
				if len(line[4].split(',')) > 1:
					varInfo = getAnnoDict(line, 0)
					# returns a tuple containing 1st the total_depth and second, either two variants (if the depths reported only two) or however many variants were found.
					total_depth, num_alleles, GT_Info = getGTInfo(line, .2, .8)
					# Now check to see if the variant has enough depth
					if total_depth < DEPTH_CUTOFF:
						vars_to_write[chr_pos] = 'LOW_DEPTH: %d'%(total_depth)
					elif num_alleles > 2:
						# This is a multi-allelic sequencing error.
						vars_to_write[chr_pos] = '%s (%s)'%(GT_Info[0][0], GT_Info[0][1])
						for i in range(1,len(GT_Info[1:])):
							vars_to_write[chr_pos] += '/ %s (%s)'%(GT_Info[0][0], GT_Info[0][1])
					else:
						allele1 = dict_all_vars[chr_pos][GT_Info[0]]	
						allele2 = dict_all_vars[chr_pos][GT_Info[1]]	
						freq = GT_Info[2]
						vars_to_write[chr_pos] = "%s/%s (%s)"%(allele1, allele2, freq)
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
		depths = {} # dict of depths. key is the allele, value the depth 
		freqs = {} # dict of depths. key is the allele, value the depth 
		# Loop through the variants to grap the alternate depths.
		if 'FAO' in info and info['FAO'] != '.': # the flow depth score is better than the base space depth score, so use that if we can.
			depths.append((ref, int(info['FRO']))) # first get the ref_depth
			total_depth = int(info['FRO']) 
			for i in range(0, len(alternates)): # if there is only one alternate allele, then this for loop will run only once
				depths.append(alternates[i], int(info['FAO'].split(',')[i]))
				total_depth += int(info['FAO'].split(',')[i])
		elif 'AO' in info:
			depths.append((ref, int(info['RO'])))
			total_depth = int(info['RO']) 
			for i in range(0, len(alternates)):
				depths.append(alternates[i], int(info['AO'].split(',')[i]))
				total_depth += int(info['AO'].split(',')[i])
		if total_depth != 0:
			for allele, depth in depths:
				freq = depth / float(total_depth)
				if freq > .1: # use .1 as a temporary threshold for multi-allelic calls
					freqs.append((allele, freq))
			# First check if there are too many variants to be real (sequencing artifact)
			if len(freqs) > 2:
				# if this doesn't look real, then return all of the frequencies to be printed out.	
				return total_depth, len(freqs), freqs
			else:
				if freqs[0][1] > HOM_cutoff:
					# This should be WT/WT. change the freq to be the percentage of variant calls
					return total_depth, 2, [freqs[0][0], freqs[0][0], str((1-freqs[0][1]))[0:5]]
					#return '%s/%s (%s)' %(freqs[0][0],freqs[0][0],str(freqs[0][1])[0:5])
				elif freqs[1][1] > HOM_cutoff:
					# If this allele's frequency is greaty then the hom cutoff, then return something like A/A (.85)
					return total_depth, 2, [freqs[1][0], freqs[1][0], str(freqs[1][1])[0:5]]
					#return '%s/%s (%s)' %(freqs[1][0],freqs[1][0],str(freqs[1][1])[0:5])
				else:
					# This must be a heterozygous variant. Print the two alleles, with the frequency of the second (because the first is most often the ref allele)
					return total_depth, 2, [freqs[0][0], freqs[1][0], str(freqs[1][1])[0:5]]
					#return '%s/%s (%s)' %(freqs[0][0],freqs[1][0],str(freqs[1][1])[0:5])

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
				currentPos = sorted_vars[i].split('_')[1]
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
	parser.add_option('-a', '--anno_hotspot', dest='hotspot', help='The name of the master hotspot file used to re-run TVC on all of the samples')
	parser.add_option('-o', '--datamatrix', default="datamatrix.csv", dest='datamatrix', help='The output Data Matrix [Default: %default]')
	parser.add_option('-m', '--min_base_cutoff', default=10, type="int", dest='min_base_cutoff', help='The minimum depth each variant must have to be considered. [Default: %default]')

	options, args = parser.parse_args()

	if not options.project_dir or not options.hotspot:
		print "USAGE ERROR: both -p (--project_dir) and -a (--anno_hotspot) are required"
		parser.print_help()
		#print "Use -h for help"
		sys.exit(8)

	# make the depth cutoff global so other functions can use it.
	global DEPTH_CUTOFF
	DEPTH_CUTOFF = options.min_base_cutoff

	main(options.project_dir, options.hotspot, options.datamatrix)

