#! /usr/bin/env python2.7

# Goal: Create pretty 3x3 tables comparing mulitple runs, or Tumor/Normal pairs 

import sys
import os
import re
import subprocess
import argparse
try:
	import xlsxwriter
	from xlsxwriter.utility import xl_rowcol_to_cell
except ImportError:
	print "xlsxwriter is installed on python2.7 on triton. Use python2.7", sys.argv[0]
	sys.exit(1)

# Function to check if a value is greater than the maximum value (i.e. WT to HET is greater than 10 or something), then write it in red
def check_max_and_write(row, col, value, Max):
	if int(value) > int(Max):
		# write this cell in red
		MRsheet.write(row, col, value, red)
	else:
		MRsheet.write(row, col, value)
		# write this cell in normal white

# Complex function to write cells. 
# @param write_format is the format to write the cell in. 
# @param Max will be the maximum threshold for writing in red, unless it's 0. If max if negative, it will be treated as a minimum threshold
# MAx is not yet implemented.
# @return returns 1 so there will be one less line of code (to incrament col). Maybe it could just incrament col, I would just rather not have global variables
def check_to_write(row, col, key, write_format, write_azure):
	if key in qcDict:
		if write_azure:
			try:
				if write_format == "num_format":
						QCsheet.write_number(row, col, int(qcDict[key].replace(',','')), num_format_azure)
				elif write_format == "perc_format":
					QCsheet.write_number(row, col, float(qcDict[key]), perc_format_azure)
				elif write_format == "dec3_format":
					QCsheet.write_number(row, col, float(qcDict[key]), dec3_format_azure)
				elif re.search("=", write_format):
					cell1 = xl_rowcol_to_cell(row, col-2)
					cell2 = xl_rowcol_to_cell(row, col-1)
					QCsheet.write_formula(row, col, "=(%s-%s)/%s"%(cell1, cell2, cell1), perc_format_azure)
				elif write_format == "":
					QCsheet.write(row, col, qcDict[key], azure)
			except ValueError:
				QCsheet.write(row, col, qcDict[key], azure)
		else:
			try:
				if write_format == "num_format":
					QCsheet.write_number(row, col, int(qcDict[key].replace(',','')), num_format)
				elif write_format == "perc_format":
					QCsheet.write_number(row, col, float(qcDict[key]), perc_format)
				elif write_format == "dec3_format":
					QCsheet.write_number(row, col, float(qcDict[key]), dec3_format)
				elif re.search("=", write_format):
					cell1 = xl_rowcol_to_cell(row, col-2)
					cell2 = xl_rowcol_to_cell(row, col-1)
					QCsheet.write_formula(row, col, "=(%s-%s)/%s"%(cell1, cell2, cell1), perc_format)
				elif write_format == "":
					QCsheet.write(row, col, qcDict[key])
			except ValueError:
				QCsheet.write(row, col, qcDict[key])
	return 1


# start here
if (__name__ == "__main"):
	mr = False # default is false for using multiple run settings
	tn = False # default is false for using tumor/normal settings
	hetMax = 5
	homMax = 2
	het_wtMax = 70
	hom_wtMax = 10
	hom_hetMax = 70
	# Function used to ensure the user specifies a .xlsx ending if the -o/--output option is used
	def ensure_xlsx(file_name):
		if file_name[-5:] != ".xlsx":
			error = "%s does not end with .xlsx" %file_name
			raise argparse.ArgumentTypeError(error)
		return file_name
	
	# All of the arguments are specified here.
	parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description='Gereates a spreadsheet containing all of the QC metrics contained in -r option and all of the 3x3 tables in the -m option.')
	parser.add_argument('-r', '--run_info', help='tab delimited file containing the run info \n(default: %(default)s)')
	parser.add_argument('-m', '--multi_run_info', help='Contains the multi_run_info used to generate the 3x3 tables and other error rate statistics \n(default: %(default)s)')
	parser.add_argument('-o', '--output', default='QC.xlsx', type=ensure_xlsx, help='Specify the path/to/.xlsx file (default: %(default)s)')
	#parser.add_argument('-mr', '--germline', action='store_true', help='write in binary (0 if read depth < cov-cutoff, 1 if read depth >= cov-cutoff)')
	#parser.add_argument('-mr', '--germline', action='store_true', help='write in binary (0 if read depth < cov-cutoff, 1 if read depth >= cov-cutoff)')
	# I'll have to add --tumor_normal, --tumor_tumor, and --normal_normal
	
	# Gets all of the command line arguments specified and puts them into the dictionary args
	args = vars(parser.parse_args())
	
	if len(sys.argv) < 3:
		print "USAGE ERROR: Must specify at least one option. Use -h for help"
		sys.exit(8)
	
	runInfoFile = args['run_info']
	multiRunInfoFile = args['multi_run_info']
	workbook = xlsxwriter.Workbook(args['output'])
	
	# Adding formats for red cells, and the borders for the table.
	header_format = workbook.add_format()
	header_format.set_bold()
	header_format.set_font_size(12)
	header_format.set_align('center')
	header_format.set_text_wrap()
	header_format2 = workbook.add_format()
	header_format2.set_bold()
	header_format2.set_font_size(14)
	
	
	center = workbook.add_format()
	center.set_align('center')
	
	azure = workbook.add_format()
	azure.set_bg_color('#d5e8f8')
	azure.set_align('center')
	
	red = workbook.add_format()
	red.set_bg_color('#FF0000')
	red.set_align('center')
	
	num_format = workbook.add_format({'num_format': '#,##0'})
	num_format.set_align('center')
	perc_format = workbook.add_format({'num_format': '0.00%'})
	perc_format.set_align('center')
	dec3_format = workbook.add_format({'num_format': '0.000'})
	dec3_format.set_align('center')
	num_format_azure = workbook.add_format({'num_format': '#,##0'})
	num_format_azure.set_align('center')
	num_format_azure.set_bg_color('#d5e8f8')
	perc_format_azure = workbook.add_format({'num_format': '0.00%'})
	perc_format_azure.set_align('center')
	perc_format_azure.set_bg_color('#d5e8f8')
	dec3_format_red = workbook.add_format({'num_format': '0.000'})
	dec3_format_red.set_align('center')
	dec3_format_red.set_bg_color('#FF0000')
	dec3_format_azure = workbook.add_format({'num_format': '0.000'})
	dec3_format_azure.set_align('center')
	dec3_format_azure.set_bg_color('#d5e8f8')
	
	top = workbook.add_format()
	top.set_top(2)
	right = workbook.add_format()
	right.set_right(2)
	bottom = workbook.add_format()
	bottom.set_bottom(2)
	left = workbook.add_format()
	left.set_left(2)
	
	
	if runInfoFile != None:
		# Infosheet is where all of the metrics about each run will be written
		QCsheet = workbook.add_worksheet("QC Metrics")
		QCsheet.freeze_panes(1,2)
		
		# First write the QC metrics for each run of each sample.
		# Write the header
		col = 0
		QCsheet.write(0,col, "Sample #", header_format)
		QCsheet.set_column(col,col,None,center)
		col += 1
		QCsheet.write(0,col, "Plate, row and column", header_format)
		QCsheet.set_column(col,col,10,center)
		col += 1
		QCsheet.write(0,col, "Library prep date", header_format)
		QCsheet.set_column(col,col,10,center)
		col += 1
		QCsheet.write(0,col, "Barcode used", header_format)
		QCsheet.set_column(col,col,12,center)
		col += 1
		QCsheet.write(0,col, "Library concentration (ng/ul)", header_format)
		QCsheet.set_column(col,col,None,center)
		col += 1
		QCsheet.write(0,col, "Run #", header_format)
		QCsheet.set_column(col,col,5,center)
		col += 1
		QCsheet.write(0,col, "Rot ID", header_format)
		QCsheet.set_column(col,col,None,center)
		col += 1
		QCsheet.write(0,col, "Run Date", header_format)
		QCsheet.set_column(col,col,12,center)
		col += 1
		QCsheet.write(0,col, "Total Basepairs", header_format)
		QCsheet.set_column(col,col,12,center)
		col += 1
		QCsheet.write(0,col, "% Polyclonal", header_format)
		QCsheet.set_column(col,col,12,center)
		col += 1
		QCsheet.write(0,col, "Mean Read Length", header_format)
		QCsheet.set_column(col,col,None,center)
		col += 1
		QCsheet.write(0,col, "Median Read Length", header_format)
		QCsheet.set_column(col,col,None,center)
		col += 1
		QCsheet.write(0,col, "% expected read length (out of 120 bp)", header_format)
		QCsheet.set_column(col,col,12,center)
		col += 1
		QCsheet.write(0,col, "% amplicons > 30x covered at bp +10", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "% amplicons > 30x covered at bp -10", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "(%covered at bp(10) - bp(n-10))/bp(10)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "total number of bases covered at 30x (the # of bases covered in the 'covered_bases region' region.)", header_format)
		QCsheet.set_column(col,col,18,center)
		col += 1
		QCsheet.write(0,col, "% covered bases (n/83046)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "% targeted bases (n/84447)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "Ts/Tv", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "# Total variants (single allele)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "# HET variants (single allele rates)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "# HOM variants (single allele rates)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "HET/HOM ratio (single allele rates)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "3x3 N-N pair (whole amplicon)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "Total bases evaluated (>=30x in both runs) (whole amplicon)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "% Available Bases (whole amplicon)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "3x3 qc observed error counts  (whole amplicon)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "3x3 qc error rate  (whole amplicon)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "Z-Score error rate (whole amplicon)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "Total bases evaluated (>=30x in both runs) (cds only)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "% Available Bases (cds only)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "3x3 qc observed error counts  (cds only)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "3x3 qc error rate  (cds only)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "Z-Score error rate (cds only)", header_format)
		QCsheet.set_column(col,col,13,center)
		col += 1
		QCsheet.write(0,col, "run status (does it pass qc?)", header_format)
		QCsheet.set_column(col,col,None,center)
		col += 1
		QCsheet.set_column(col,col+20,12,center)
		
		QCsheet.set_row(0,100,header_format)
		
		row = 1
		qcDict = {}
		write_azure = False
		last_sample = ""
	
		runInfoFile = open(runInfoFile, 'r')
		for line in runInfoFile:
			line = line.strip().split('\t')
			qcDict = {}
			for item in line:
				item = item.split(':')
				qcDict[item[0]] = item[1]
			col = 0
			col += check_to_write(row, col, 'sample_num', "", write_azure)
			col += check_to_write(row, col, 'sample', "", write_azure)
			col += check_to_write(row, col, 'lib_prep_date', "", write_azure)
			col += check_to_write(row, col, 'barcode', "", write_azure)
			col += check_to_write(row, col, 'lib_conc', "", write_azure)
			col += check_to_write(row, col, 'run_num', "", write_azure)
			col += check_to_write(row, col, 'rotID', "", write_azure)
			col += check_to_write(row, col, 'run_date', "", write_azure)
			col += check_to_write(row, col, 'total_bases', "num_format", write_azure)
			col += check_to_write(row, col, 'polyclonal', "perc_format", write_azure)
			col += check_to_write(row, col, 'mean', "num_format", write_azure)
			col += check_to_write(row, col, 'median', "", write_azure)
			col += check_to_write(row, col, 'expected_length', "", write_azure)
			col += check_to_write(row, col, 'plus10', 'perc_format', write_azure)
			col += check_to_write(row, col, 'minus10', 'perc_format', write_azure)
			# give it the dummy 'minus10' key because it doesn't have a key
			col += check_to_write(row, col, 'minus10', "=", write_azure)
			col += check_to_write(row, col, 'total_covered', 'num_format', write_azure)
			col += check_to_write(row, col, 'perc_expected', 'perc_format', write_azure)
			col += check_to_write(row, col, 'perc_targeted', 'perc_format', write_azure)
			col += check_to_write(row, col, 'ts_tv', 'num_format', write_azure)
			col += check_to_write(row, col, 'total_vars', 'num_format', write_azure)
			col += check_to_write(row, col, 'total_het', 'num_format', write_azure)
			col += check_to_write(row, col, 'total_hom', 'num_format', write_azure)
			col += check_to_write(row, col, 'het_hom', 'dec3_format', write_azure)
			#run_num = int(qcDict['run_num'])
			#runs = int(qcDict['runs'])
	
			# Now write the N-N pair and the T-T pairs
			col += check_to_write(row, col, 'same_pair', "", write_azure)
			col += check_to_write(row, col, 'same_total_evaluated', 'num_format', write_azure)
			col += check_to_write(row, col, 'same_perc_available_bases', 'perc_format', write_azure)
			col += check_to_write(row, col, 'same_error_count', 'num_format', write_azure)
			col += check_to_write(row, col, 'same_error_rate', 'perc_format', write_azure)
			try:
				if 'same_zscore' in qcDict and float(qcDict['same_zscore']) > 3:
					QCsheet.write_number(row, col, float(qcDict['same_zscore']), dec3_format_red)
					qcDict['same_status'] = 'Fail'
					col += 1
				else:
					col += check_to_write(row, col, 'same_zscore', 'dec3_format', write_azure)
			except ValueError:
				col += check_to_write(row, col, 'tn_zscore', '', write_azure)
			col += check_to_write(row, col, 'same_status', "", write_azure)
	
		# Now write the T-N pairs
			col += check_to_write(row, col, 'tn_pair', "", write_azure)
			col += check_to_write(row, col, 'tn_total_evaluated', 'num_format', write_azure)
			col += check_to_write(row, col, 'tn_perc_available_bases', 'perc_format', write_azure)
			col += check_to_write(row, col, 'tn_error_count', 'num_format', write_azure)
			col += check_to_write(row, col, 'tn_error_rate', 'perc_format', write_azure)
			try:
				if 'tn_zscore' in qcDict and float(qcDict['tn_zscore']) > 3:
					QCsheet.write_number(row, col, float(qcDict['tn_zscore']), dec3_format_red)
					qcDict['tn_status'] = 'Fail'
					col += 1
				else:
					col += check_to_write(row, col, 'tn_zscore', 'dec3_format', write_azure)
			except ValueError:
				col += check_to_write(row, col, 'tn_zscore', '', write_azure)
			col += check_to_write(row, col, 'tn_status', "", write_azure)
		
			sample = qcDict['sample']
			# Write every other sample as azure
			if last_sample == sample:
				if write_azure:
					QCsheet.set_row(row, None, azure)
			else:
				last_sample = sample
				if write_azure:
					write_azure = False
				else:
					write_azure = True
				QCsheet.set_row(row, None, azure)
	
	#		# Write every other sample as azure
	#		if run_num < runs:
	#			if write_azure:
	#				QCsheet.set_row(row, None, azure)
	#		elif run_num == runs:
	#			if write_azure:
	#				QCsheet.set_row(row, None, azure)
	#				write_azure = False
	#			else:
	#				write_azure = True
			row += 1
	
	
	if multiRunInfoFile != None:
		# MRsheet is the sheet where all of the 3x3 tables for each of the multiple runs of each sample will be written
		MRsheet = workbook.add_worksheet("3x3 tables")
		multiRunInfoFile = open(multiRunInfoFile, 'r')
		
		row = 2
		col = 2
		last_sample = ''
		# now write the 3x3 tables on the mr sheet
		for line in multiRunInfoFile:
			line = line.strip()
			line = line.split("\t")
			sample = line[0].split(":")[0]
			runs = line[0].split(":")[1].split('vs')
			if last_sample == "":
				last_sample = sample
			else:
				if last_sample == sample: # if there are more than two runs for this sample, add another table to the right.
					col += 8
				else: # else, move back to the left and down.
					last_sample = sample
					row += 8
					col = 2
		#first make the header for each table.
			header = "%s_%s    -  vs  -    %s_%s"%(sample, runs[0], sample, runs[1]) # i.e. sample1_Run1  -  vs  - sample1_Run2
	#		header = runs[0] + "   -  vs  -   " + runs[1] # i.e. case1_a01_qcrun1 vs case1_a01_run2
			MRsheet.write(row-1, col, header, header_format2)
			#print "generating the qc tables for: " + header
			
			#now write the table headers
			MRsheet.write(row+1, col, "WT", right)
			MRsheet.write(row+2, col, "HET", right)
			MRsheet.write(row+3, col, "HOM", right)
			MRsheet.write(row+4, col, "Sum:")
			MRsheet.write(row, col+1, "WT", bottom)
			MRsheet.write(row, col+2, "HET", bottom)
			MRsheet.write(row, col+3, "HOM", bottom)
			MRsheet.write(row, col+4, "Sum:")
		
			#now write the actual values
			line = line[1:]
			#create the output dictionary
			table_values = {}
			total = 0
			for item in line:
				item = item.split(':')
				table_values[item[0]] = item[1]
			total = int(table_values["WT_WT"]) + int(table_values["WT_HET"]) + int(table_values["WT_HOM"]) + \
					int(table_values["HET_WT"]) + int(table_values["HET_HET"]) + int(table_values["HET_HOM"]) + \
					int(table_values["HOM_WT"]) + int(table_values["HOM_HET"]) + int(table_values["HOM_HOM"])
			# If there are less than 10,000 nucleotides to compare on the QC spreadMRsheet, highlight those in red.
		#	if int(table_values['WT_WT']) < 50000:
		#		MRsheet.write(row+1, col+1, table_values["WT_WT"], red)
		#	else:
			MRsheet.write(row+1, col+1, table_values["WT_WT"])
			# add the diagonal and the sums because their formatting won't change.
			MRsheet.write(row+2, col+2, table_values["HET_HET"])
			MRsheet.write(row+3, col+3, table_values["HOM_HOM"])
			# Add the totals for each row and column
			MRsheet.write(row+4, col+1, str(int(table_values["WT_WT"])+int(table_values["HET_WT"])+int(table_values["HOM_WT"])), top)
			MRsheet.write(row+4, col+2, str(int(table_values["WT_HET"])+int(table_values["HET_HET"])+int(table_values["HOM_HET"])), top)
			MRsheet.write(row+4, col+3, str(int(table_values["WT_HOM"])+int(table_values["HET_HOM"])+int(table_values["HOM_HOM"])), top)
			MRsheet.write(row+1, col+4, str(int(table_values["WT_WT"])+int(table_values["WT_HET"])+int(table_values["WT_HOM"])), left)
			MRsheet.write(row+2, col+4, str(int(table_values["HET_WT"])+int(table_values["HET_HET"])+int(table_values["HET_HOM"])), left)
			MRsheet.write(row+3, col+4, str(int(table_values["HOM_WT"])+int(table_values["HOM_HET"])+int(table_values["HOM_HOM"])), left)
			MRsheet.write(row+4, col+4, str(total))
		
			if mr: # set different cells to red if they exceed the threshold specified
				check_max_and_write(row+2, col+1, table_values["HET_WT"], hetMax)
				check_max_and_write(row+3, col+1, table_values["HOM_WT"], homMax)
				check_max_and_write(row+1, col+2, table_values["WT_HET"], hetMax)
				check_max_and_write(row+3, col+2, table_values["HOM_HET"], hetMax)
				check_max_and_write(row+1, col+3, table_values["WT_HOM"], homMax)
				check_max_and_write(row+2, col+3, table_values["HET_HOM"], hetMax)
			elif tn:
				# write normal values
				check_max_and_write(row+2, col+1, table_values["HET_WT"], het_wtMax)
				check_max_and_write(row+3, col+1, table_values["HOM_WT"], hom_wtMax)
				check_max_and_write(row+3, col+2, table_values["HOM_HET"], hom_hetMax)
				# now write the tumor side
				MRsheet.write(row+1, col+2, table_values["WT_HET"])
				MRsheet.write(row+1, col+3, table_values["WT_HOM"])
				MRsheet.write(row+2, col+3, table_values["HET_HOM"])
			else:
				# if no threshold is specified, then everything will stay white.
				MRsheet.write(row+2, col+1, table_values["HET_WT"])
				MRsheet.write(row+3, col+1, table_values["HOM_WT"])
				MRsheet.write(row+1, col+2, table_values["WT_HET"])
				MRsheet.write(row+3, col+2, table_values["HOM_HET"])
				MRsheet.write(row+1, col+3, table_values["WT_HOM"])
				MRsheet.write(row+2, col+3, table_values["HET_HOM"])
	
	print "Finished generating the QC table"
	workbook.close()
