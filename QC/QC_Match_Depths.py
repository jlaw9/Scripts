#! /usr/bin/env python

# TEMP script to get the corrected depths for Einstein and SEGA

import sys
import os.path
import re
from optparse import OptionParser
# ----------------------------------------------------
# ------------- PROGRAM STARTS HERE ------------------
# ----------------------------------------------------

if __name__ == "__main__":
	
	if len(sys.argv) < 4:
		print "USAGE %s <Run1_depths> <Run2_depths> <depth_cutoff1> <depth_cutoff2>"
		sys.exit(8)
	Run1_depths = open(sys.argv[1], 'r')
	Run2_depths = open(sys.argv[2], 'r')
	depth1_cutoff = int(sys.argv[3])
	depth2_cutoff = int(sys.argv[4])
	
	total_depth = 0
	last_chr = ''
	line1 = Run1_depths.readline().strip()
	line2 = Run2_depths.readline().strip()
	# Because the two vcf files were created from the same HotSpot file, they should have the same chromosome positions listed in the same order.
	# Therefore, I am reading the two vcf files line by line at the same time.
	while line1 != '' or line2 != '':
		line1arr = line1.split('\t')
		line2arr = line2.split('\t')
		# If I make it a while loop rather than an if statement, this will handle if there are more than one mismatches. If the error rate is really high, the vcf files given were probably not from the same hotspot file.
		# Rather than load the variants into memory, handle mismatches this way.
		while line1arr[0:2] != line2arr[0:2]:
			# A variant must have been filtered from one of the VCF files. We should just skip over it in the other one.
			#print 'line1:', line1arr[0:2], '\t', 'line2:',line2arr[0:2]
			if line2 == '':
				line1 = Run1_depths.readline()
				print ' end of Run2'
				break
			elif line1 == '':
				line2 = Run2_depths.readline()
				print ' end of Run1'
				break
			else:
				var1Chr = line1arr[0]
				var2Chr = line2arr[0]
				var1Pos = int(line1arr[1])
				var2Pos = int(line2arr[1])
				# Check first to see if the chromosomes match. IF they don't, then whichever file has an extra variant should write that var.
				if var1Chr != var2Chr:
					if var1Chr == last_chr:
						line1 = Run1_depths.readline()
						line1arr = line1.split('\t')
					else:
						line2 = Run2_depths.readline()
						line2arr = line2.split('\t')
				# Check the positions if they are on the same chromosome..
				elif var1Pos < var2Pos:
					line1 = Run1_depths.readline()
					line1arr = line1.split('\t')
				else:
					line2 = Run2_depths.readline()
					line2arr = line2.split('\t')

		last_chr = line1arr[0]
		# If the chr and positions match, then we're good to go.
		if line1 != '' and line2 != '': # If the while loop hit the end of the file, then don't do anything here.
			try:
				if int(line1arr[2]) >= depth1_cutoff and int(line2arr[2]) >= depth2_cutoff:
					total_depth += 1
			except ValueError:
				sys.exit("this must be a depth file from GATK")
			line1 = Run1_depths.readline().strip()
			line2 = Run2_depths.readline().strip()
		
print total_depth

