#! /usr/bin/env python

from optparse import OptionParser
import os
import os.path
import sys
import re
import json
import numpy as np
from numpy.random import normal
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.append("/rawdata/legos/scripts/QC")
import tools

class Allele_Histo:
	def __init__(self, options):
		self.options = options
		self.count = 0
		self.change_counts = {'WT_WT':0, 'WT_HET':0, "WT_HOM":0,'HET_WT':0, 'HET_HET':0, "HET_HOM":0, \
				'HOM_WT':0, 'HOM_HET':0, "HOM_HOM":0,} 
		#gaussian_numbers = normal(size=1000)
		#print type(gaussian_numbers)
		#plt.hist(gaussian_numbers, bins=20, normed=True, cumulative=True)
		#plt.hist(gaussian_numbers, bins=(-10,-1,1,10))
		#plt.hist(gaussian_numbers, bins=20, histtype='step')
		#plt.title("Gaussian Histogram")
		#plt.xlabel("Value")
		#plt.ylabel("Frequency")
		#plt.show()
	
	def create_histogram(self, matched_var_file):
		with open(matched_var_file, 'r') as var_file:
			normal = []
			tumor = []
			var_file.readline()
			for line in var_file:
				line = line.split('\t')
				if line[5] != '.':
					normal.append(float(line[5]))
				if line[9] != '.':
					tumor.append(float(line[9]))
				# now get the cell changes
				GT1_GT2 = line[4] + "_" + line[8]
				#if GT1_GT2 in self.change_counts: # unknown (i.e ._.) will be skipped.
				#	self.change_counts[GT1_GT2].append([line[5], line[9]])
			# now use matplotlib to generate a histogram
			#print normal
			normal_arr = np.array(normal)
			sample = os.path.abspath(matched_var_file).split('/')[-4]
			run1 = os.path.abspath(matched_var_file).split('/')[-2].split('vs')[0][4:]
			self.make_histo(normal_arr, title="%s %s Allele Frequencies"%(sample, run1), fig_name="%s_%s_histogram_JL_%s.png"%(sample, run1, tools.getDate()))
			tumor_arr = np.array(tumor)
			run2 = os.path.abspath(matched_var_file).split('/')[-2].split('vs')[-1]
			self.make_histo(tumor_arr, title="%s %s Allele Frequencies"%(sample, run2), fig_name="%s_%s_histogram_JL_%s.png"%(sample, run2, tools.getDate()))

	def make_histo(self, array, title, fig_name):
		plt.figure(self.count)
		self.count += 1
		plt.hist(array, bins=100)
		plt.title(title)
		plt.xlabel("Allele Frequency")
		plt.xticks(np.arange(0, 1, 0.1))
		plt.ylabel("Count")
		plt.savefig(fig_name)


if __name__ == '__main__':

	# set up the option parser
	parser = OptionParser()
	
	# add the options to parse
	parser.add_option('-c', '--csv', dest='csv', action='append', help='The matched variants csv that has the allele frequencies used in making the histogram')
	parser.add_option('-o', '--output', dest='output', help='The output file. If no output file is specified, output will be written to the screen')
	parser.add_option('-d', '--debug', dest='debug', action='store_true', help='Option to debug or include print statements in code')

	(options, args) = parser.parse_args()

	if not options.csv:
	#	print "USAGE_ERROR: json file %s not found"%options.json
		parser.print_help()
		sys.exit(1)

	ex = Allele_Histo(options)
	for csv in options.csv:
		ex.create_histogram(csv)

