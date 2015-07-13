#! /usr/bin/env python

# Script to intersect VCF files and then generate Venn Diagrams for them.
# Generates either 2, 3, or 4 set Venn Diagrams depending on how many files are passed in

from optparse import OptionParser
import os
import os.path
import sys
import re
import json

__author__ = "jlaw"

class Venns:
	def __init__(self, vcfs, categories, output, output_dir, title, subtitle):
		self.vcfs = vcfs
		self.categories = categories
		if not self.categories:
			self.categories = []
			for vcf in self.vcfs:
				vcf_name = vcf.split('/')[-1].split('.vcf')[0]
				self.categories.append(vcf_name)
		self.output = output
		self.output_dir = output_dir
		self.title = title
		self.subtitle = subtitle
		if len(self.vcfs) == 2:
			self.intersections = ['0','1', '0_1']
		elif len(self.vcfs) == 3:
			self.intersections = ['0','1','2','0_1','0_2','1_2','0_1_2']
		elif len(self.vcfs) == 4:
			self.intersections = ['0','1','2','3','0_1','0_2','0_3','1_2','1_3','2_3','0_1_2','0_1_3','0_2_3','1_2_3','0_1_2_3']
	
	def intersect_vcfs(self):
		# first use bgip and tabix to prepare the VCFs for vcf-isec to run on them
		for vcf in self.vcfs:
			if not os.path.isfile("%s.gz.tbi"%vcf):
				command = "bgzip -c %s > %s.gz; tabix -p vcf %s.gz"%(vcf, vcf, vcf)
				if self.runCommandLine(command) != 0:
					sys.stderr.write("ERROR: bgzip and/or tabix failed!\n")
					sys.exit(1)
		for intersection in self.intersections:
			if len(intersection.split('_')) == 1:
				vcf = self.vcfs[int(intersection)]
				# copy the vcf file to the output directory
				command = "cp %s %s/%s%s.vcf"%(vcf, self.output_dir, self.output, intersection)
				self.runCommandLine(command)
			else:
				#if not os.path.isfile("%s/%s%s.vcf"%(self.output_dir, self.output, intersection)):
				# create the vcfs_to_intersect string
				vcfs_to_intersect = [] 
				for i in xrange(len(intersection.split('_'))):
					vcfs_to_intersect.append(self.vcfs[int(intersection.split('_')[i])] + ".gz")
				vcfs_to_intersect = ' '.join(vcfs_to_intersect)
				# use vcf-isec to intersect the vcf files for creating the venn diagrams
				# can't use the -p option because R requires the full sums.
				command = "vcf-isec -f %s > %s/%s%s.vcf 2>/dev/null"%(vcfs_to_intersect, self.output_dir, self.output, intersection)
				if self.runCommandLine(command) != 0:
					sys.stderr.write("ERROR: vcf-isec failed!\n")
					sys.exit(1)
		# now run vcf-isec with the -p option to get the variants unique to each set. Pretty cool!
		#command = "vcf-isec -f -p %s_unique %s"%(self.output, ' '.join([s + ".gz" for s in self.vcfs]))
		#self.runCommandLine(command)

	# function to count the number of variants in each intersection
	def count_vars(self):
		if os.path.isfile("%s/%s.txt"%(self.output_dir, self.output)):
			self.runCommandLine("rm %s/%s.txt"%(self.output_dir, self.output))
		# now loop through and count the number of variants in each intersection
		for intersection in self.intersections:
			# create the category string
			category = [] 
			for i in xrange(len(intersection.split('_'))):
				category.append(self.categories[int(intersection.split('_')[i])])
			category = '_'.join(category)
			command = "printf \"%s\t\" >> %s/%s.txt; "%(category, self.output_dir, self.output)
			# unzip the vcf-isec output, and count the number of variants
			vcf = "%s%s.vcf"%(self.output, intersection)
			command += "grep -v \"^#\" %s | wc -l | sed 's/ //g' >> %s/%s.txt" %(vcf, self.output_dir, self.output)
			self.runCommandLine(command)

	def create_venns(self):
		command = "Rscript Venn.R %s/%s '%s' '%s'"%(self.output_dir, self.output, self.title, self.subtitle)
		if self.runCommandLine(command) != 0:
			sys.stderr.write("ERROR: Venn.R failed!\n")
			sys.exit(1)

	# @param systemCall command to run from bash
	# @returns the exit code or status of the bash command
	def runCommandLine(self, systemCall):
		#run the call and return the status
		print 'Starting %s' % (systemCall)
		status = os.system(systemCall)
		return(status)

if __name__ == '__main__':

	# set up the option parser
	parser = OptionParser()
	
	# add the options to parse
	parser.add_option('-v', '--vcfs', dest='vcfs', action="append", help='The VCF files to intersect. Generates either 2, 3, or 4 set Venn Diagrams depending on how many files are passed in')
	parser.add_option('-c', '--categories', dest='categories', action="append", help='The category title for each VCF file. Default: VCF names')
	parser.add_option('-o', '--output', dest='output', help='The output prefix')
	parser.add_option('-O', '--output_dir', dest='output_dir', help='The output directory to hold all of the output files')
	parser.add_option('-t', '--title', dest='title', help='The Title of the Venn Diagram')
	parser.add_option('-s', '--subtitle', dest='subtitle', help='The sub-Title of the Venn Diagram')

	(options, args) = parser.parse_args()

	# check options specified
	if not options.vcfs or len(options.vcfs) < 2 or len(options.vcfs) > 4:
		sys.stderr.write("ERROR: Must specify 2-4 VCF files to intersect\n")
		parser.print_help()
		sys.exit(1)
	if options.categories and len(options.vcfs) != len(options.categories):
		sys.stderr.write("ERROR: Must specify the same number of categories as VCFs\n")
		parser.print_help()
		sys.exit(1)
	for vcf in options.vcfs:
		if not os.path.isfile(vcf):
			print "USAGE_ERROR: vcf file %s not found"%vcf
			parser.print_help()
			sys.exit(1)
	if not options.output_dir:
		options.output_dir = '.'

	venn = Venns(options.vcfs, options.categories, options.output, options.output_dir, options.title, options.subtitle)
	venn.intersect_vcfs()
	venn.count_vars()
	venn.create_venns()
