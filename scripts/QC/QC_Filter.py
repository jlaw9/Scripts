#! /bin/usr/env python

# Goal: Remove the variants that have Multi Allelic calls, and the variants where FRO + FAO < 30 (or a specified input) from a merged vcf file.


import sys
import re
import os
import subprocess

# @param Takes in a dictionary with the key as the description of a variant, and the value as the value of that description.
# @return Returns the amount of variants that were filtered (depth was not > cutoff in either vcf file).
def check_depth(vcfInfo):
	if vcfInfo['GT'] != '.':
		alt_depth = ''
		ref_depth = ''
		try: 
			if 'FAO' in vcfInfo and vcfInfo['FAO'] != '.':   # Ozlem said that the frequency depth score is better than the regular depth score, so use that if we can.
				alt_depth = vcfInfo['FAO']
				ref_depth = vcfInfo['FRO']
			elif 'AO' in vcfInfo:
				alt_depth = vcfInfo['AO']
				ref_depth = vcfInfo['RO']
			elif 'AD' in vcfInfo: # For older vcf files (3.2), the format is different.
				alt_depth = vcfInfo['AD'].split(',')[1]
				ref_depth = vcfInfo['AD'].split(',')[0]
			total_depth = int(alt_depth) + int(ref_depth)
			return total_depth
		except KeyError:
			print "KEY ERROR: in the vcf file. Leaving this variant."
			return -1
	else:
		# If there is no GT (genotype) information available about this variant from this vcf file, then just leave it.
		return -1

def usage():
	print "USAGE: python QC_Filter_Var.py <vcf_file.vcf> <filtered_vcf_output.vcf> [--single cutoff] [--merged cutoff1 cutoff2]\
			\t Only variants with FRO+FAO > cutoff number will be kept.\
			\n\t\tUse --single option for a single vcf. \
			\n\t\tUse --merged option for a vcf file that has been merged. (cutoff1 corresponds to the first columns values, and cutoff2 to the second)"
#	print "Tumor/Normal pair filtering not yet implemented."
	sys.exit(8)

merged = False
# input files for the program.
try:
	if len(sys.argv) == 6 and sys.argv[3] == "--merged":
		merged = True
		vcf = open (sys.argv[1], 'r') # input file1 vcf 
		filtered_vcf = open(sys.argv[2], 'w') # Output vcf that has the variants filtered.
		cutoff1 = int(sys.argv[4])
		cutoff2 = int(sys.argv[5])
	elif len(sys.argv) == 5 and sys.argv[3] == "--single":
		vcf = open (sys.argv[1], 'r') # input file1 vcf 
		filtered_vcf = open(sys.argv[2], 'w') # Output vcf that has the variants filtered.
		cutoff1 = int(sys.argv[4])
	else:
		usage()
except IOError, ValueError:
	print "ERROR: Check file path's and that cutoff values given are integers"
	sys.exit(1)

last_chr_pos = "" # This variable will be set to the chr, and pos of the line immediately before the current line.
duplicate_variants_removed = 0
multiple_variants_removed = 0
total_variants_filtered= 0
for line in vcf:
	if line[0] == "#": # Write the header lines first
		filtered_vcf.write(line)
	else: # Then do the filtering
		line = line.strip()
		line_arr = line.split('\t')
		chr_pos = line_arr[0] + "_" + line_arr[1]
		# If the current chr and pos are equal to the chr and pos of the line immediately before this line, this is a duplicate entry. This line will be skipped.
		if chr_pos != last_chr_pos:
			last_chr_pos = chr_pos
			if not re.search(",", line_arr[4]): # Don't keep variants that have a Multi allelic call. Bonnie thinks they're a sequencing artifact
				# Now filter the FRO + FAO values.
				if not merged:
					vcfInfo = dict(zip(line_arr[8].split(":"), line_arr[9].split(":")))   # Creates a dictionary with the description as the key, and the actual value as the value.
					depth = check_depth(vcfInfo)
					if depth >= cutoff1 or depth == -1:
						# The line will only be written if the variant passes all of the filters and checks.
						filtered_vcf.write(line + "\n")
					else:
						total_variants_filtered += 1
				else:
					# Because this vcf file is merged from two runs, it has two information columns, column 10 is from the first vcf file, and column 11 is from the second.
					vcf1Info = dict(zip(line_arr[8].split(":"), line_arr[9].split(":")))   # Creates a dictionary with the description as the key, and the actual value as the value.
					vcf2Info = dict(zip(line_arr[8].split(":"), line_arr[10].split(":")))   # Creates a dictionary with the description as the key, and the actual value as the value.
					depth1 = check_depth(vcf1Info)
					depth2 = check_depth(vcf2Info)
					if (depth1 >= cutoff1 or depth1 == -1) and (depth2 >= cutoff2 or depth2 == -1):
						filtered_vcf.write(line + "\n")
					else:
						total_variants_filtered += 1
			# Don't keep the variant if it doesn't meet this criteria
			else:
				multiple_variants_removed += 1
		else:
			duplicate_variants_removed += 1

print "# of duplicate variants removed: " + str(duplicate_variants_removed)
print "# of multiple variants removed: " + str(multiple_variants_removed)
try:
	print "# of variants removed that had coverage < %s in VCF1 and < %s in VCF2: %s"%(cutoff1, cutoff2, total_variants_filtered)
except NameError:
	print "# of variants removed that had coverage < " + str(cutoff1) + ": " + str(total_variants_filtered)


vcf.close()
filtered_vcf.close()
