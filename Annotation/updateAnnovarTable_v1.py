#! usr/bin/env python

# goal: read csv file containing both normal and tumor depths 
# read also table annovar output 
# append normal and tumor depths to table output 
# keep only canonical transcript 

import sys
import os
import numpy as np
import string


# required input files: 

inputCSV = open(sys.argv[1], 'r') # let's say somatic.csv 

inputTableAnnovar = open(sys.argv[2], 'r') # table_annovar.pl output corresponding using vcf file corresponding to the input CSV (for instance; somatic.vcf)

inputTranscriptFile = sys.argv[3] #canonical transcript List 


# read transcipt list into an array 

canonicalList = np.loadtxt(inputTranscriptFile, dtype='str')

# need to work on different formatting
#somaticVariants=np.loadtxt(inputCSV,dtype={'names':('chr', 'pos', 'ref', 'alt', 'normalGT', 'normalAF', 'normalAltDepth', 'normalRefdepth','tumorGT', 'tumorAF', 'tumorAltdepth', 'tumorRefdepth'), 'formats': ('S1', 'i4', 'S1', 'S1', 'S1', 'f4', 'i4', 'i4', 'S1', 'f4', 'i4', 'i4')})

# for now read all columns as text 

somaticVariants=np.loadtxt(inputCSV,dtype='str')

# first line is header 
line = inputTableAnnovar.readline()

while line != "":
	line = inputTableAnnovar.readline()
	lineArr=line.split('\t') 

	match_found = ''

	if  lineArr[9] !="." and lineArr[9] !="UNKNOWN" :
		#split column 9 by ":"
		AAchanges=lineArr[9].split(',')
		#print (AAchanges)
		#AAno=len(AAchanges)
		#print (AAno)
        
		for AA in AAchanges:
			AAinfo = AA.split(':')
			transcript = AAinfo[1]
			if transcript in canonicalList: 
				match_found = AA
				break 

		if match_found == '':
			match_found = AAchanges[-1]

		protein_change = match_found.split(':')

		if len(protein_change) > 4:  # sometimes there is no protein change reported for nonframeshift indels in annovar output, need to place "." in that case  
			AA_report=  protein_change[4][2:]
		else:
			AA_report='.'

		print (AA_report)

		break 

