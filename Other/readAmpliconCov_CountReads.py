#! /usr/bin/python

# Script for generating the amplicon table to differentiate between amplicon reads < 30x and > 30x

import sys
import os
import subprocess
import re
try:
	import xlsxwriter
	from xlsxwriter.utility import xl_rowcol_to_cell
except ImportError:
	print "Use python2.7 to run this script"
	sys.exit(1)
import argparse


# Function used to ensure the user specifies a .xlsx ending if the -o/--output option is used
def ensure_xlsx(file_name):
	if file_name[-5:] != ".xlsx":
		error = "%s does not end with .xlsx" %file_name
		raise argparse.ArgumentTypeError(error)
	return file_name

# All of the arguments are specified here.
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description='Gereates a spreadsheet containing coverage information about all of the samples in a project.')
parser.add_argument('-d', '--project_dir', required=True, help='Specify the path/to/projectDirectory')
parser.add_argument('-o', '--output', default='All_Samples.amplicon.cov.xlsx', type=ensure_xlsx, help='Specify the path/to/.xlsx file (default: %(default)s)')
parser.add_argument('-b', '--write_binary', action='store_true', help='write in binary (0 if read depth < cov-cutoff, 1 if read depth >= cov-cutoff)')
parser.add_argument('-c', '--cutoff', type=int, default=30, help='The cell will turn red (and set to 0 if -b option is used) if coverage is < cutoff (default: %(default)s)')

# Gets all of the command line arguments specified and puts them into the dictionary args
args = vars(parser.parse_args())

# Place the arguemts into variables
Project_Dir = args['project_dir'] # The directory that holds all of the project data
OutFile = args['output'] # Default: All_Samples.amplicon.cov.xlsx
binary = args['write_binary'] # Default: False
cov_cutoff = args['cutoff'] # Default: 30
# done parsing args"


#os.chdir(Project_Dir)

# Check first to see if there are .amplicon.cov.xls files in the Project_Dir specified 
#command = "find %s/*/*/*.amplicon.cov.xls -type f | head -n 1" %Project_Dir
command = 'find %s -name "*.amplicon.cov.xls" -type f -print -quit' %Project_Dir
anAmplicon = subprocess.check_output(command, shell=True).strip()
if anAmplicon == "":
	print "No .amplicon.cov.xls files were found in %s" %Project_Dir
	sys.exit()

# Create the xlsx file, and add some formatting options that will be used later when actually adding the values to the cells
workbook = xlsxwriter.Workbook(OutFile)
red = workbook.add_format()
red.set_bg_color('#FF0000')
red.set_bottom(1)
green = workbook.add_format()
green.set_bg_color('509050')
green.set_bottom(1)
percent_format = workbook.add_format({'num_format': '0.00%'})

# Add the different sheets to the workbook
Amp_Sheet = workbook.add_worksheet("Amplicon Data")
Amp_Sheet.freeze_panes(1, 4)
Binary_Sheet = workbook.add_worksheet("Binary Amplicon Data")
Binary_Sheet.freeze_panes(1, 5)
MetaData_Sheet = workbook.add_worksheet("Metadata")
#write the header line
col = 0
Amp_Sheet.write(0,0, "plate")
Amp_Sheet.set_column(col,col, 5)
Binary_Sheet.write(0,0, "plate")
Binary_Sheet.set_column(col,col, 5)
col += 1
Amp_Sheet.set_column(col,col+2, 3)
Binary_Sheet.set_column(col,col+2, 3)
Amp_Sheet.write(0,1, "sample")
Binary_Sheet.write(0,1, "sample")
col += 1
Amp_Sheet.write(0,2, "row")
Binary_Sheet.write(0,2, "row")
col += 1
Amp_Sheet.write(0,3, "column")
Binary_Sheet.write(0,3, "column")
col += 1
Amp_Sheet.write(0,4, "% Covered")
Binary_Sheet.write(0,4, "% Covered")
MetaData_Sheet.write(0,0, "Chromosome")
MetaData_Sheet.write(1,0, "Start")
MetaData_Sheet.write(2,0, "End")
MetaData_Sheet.write(3,0, "Amplicon")
row = 0
col = 5

print "Started"
 #This command gets all but the first line of the "firstAmplicon" file, sorts it by amplicon, keeps only the 4th columns (the amplicon list), and then puts that into the OutFile
command = "tail -n +2 " + anAmplicon + " | sort -k4 | cut -f 1,2,3,4"
ampList = subprocess.check_output(command, shell=True).strip().split("\n")
for amp in ampList:
	Data = amp.split("\t")
	for data in Data:
		if row == 3:
			Amp_Sheet.write(0, col, data)
#			Amp_Sheet.set_column(col,col, 2.5)
			Binary_Sheet.write(0, col, data)
			Binary_Sheet.set_column(col,col, 2.5)
		MetaData_Sheet.write(row, col-4, data)
		row += 1
	row = 0
	col += 1
row = 0
col = 0
# lists all of the directories in the Project_Dir
plates = subprocess.check_output('ls ' + Project_Dir, shell=True).strip()
plates = plates.split("\n")

for plate in plates:
	plate = plate.strip()
	#if statement checks to ensure that only the directories that are either a case, control, or old plate will be used
	if re.search(r"case\d",plate) or re.search(r'control\d', plate) or re.search(r'old\d', plate):
		plateDir = Project_Dir + "/" + plate
		samples = subprocess.check_output('ls ' + plateDir, shell=True).strip()
		samples = samples.split("\n")

		#this for loop will loop through the different files within the plate
		for sample in samples:
			if re.search('\w\d\d',sample):
				sample = sample.strip()
				sampleDir = plateDir + '/' + sample 
				# If this sample has multiple runs that have been merged, use them. 
				command = "find %s/Merged -type d 2>/dev/null | wc -l"%sampleDir
				merged = subprocess.check_output(command, shell=True).strip()
				if int(merged) > 0:
#					print plate, sample, "has a merged run"
					sampleDir += "/Merged"
				# Each plate should only have one amplicon
				amplicon = subprocess.check_output('ls ' + sampleDir + '/*.amplicon.cov.xls', shell=True).strip()
#				amplicons = amplicons.split("\n")
				# remove the header from the amplicon with tail, sort the file by amplicon names (in the 4th column),
				# and then keep only the coverage of that amplicon (in the 10th column)
				command = "tail -n +2 " + amplicon + " | sort -k4 | cut -f 10"
				readValues = subprocess.check_output(command, shell=True).strip()
				readValues = readValues.split("\n")
				# split the amplicons path by "/" to get just the name of the amplicon file. 
#				forHeader = amplicon.split("/")[-1][:3]
				# ------ WRITE THE HEADER -----------
#				# The 'header' or first item on the row will be the plate_sample (i.e. case1_A01)
#				header = plate + "_" + sample 
				col = 0
				row += 1
				Amp_Sheet.write(row, col, plate)
				Binary_Sheet.write(row, col, plate)
				col += 1
				Amp_Sheet.write(row, col, sample)
				Binary_Sheet.write(row, col, sample)
				col += 1
				Amp_Sheet.write(row, col, sample[0]) # Write the sample row 
				Binary_Sheet.write(row, col, sample[0])
				col += 1
				Amp_Sheet.write(row, col, sample[1:]) # Write the sample column
				Binary_Sheet.write(row, col, sample[1:])
				col += 1
#				Amp_Sheet.write_formula(row, col, "=SUM(F%s:FFF%s)/804"%(row,row), percent_format)
				# write the % amplicons covered. Use row+1 for the sum because row, col start at zero, but using letters (ie. F1:ff1) starts at one.
				Binary_Sheet.write_formula(row, col, "=SUM(F%s:FFF%s)/804"%(row+1,row+1), percent_format)
				col += 1

				# --------- WRITE THE DATA ---------
				for value in readValues:
					if int(value) < cov_cutoff:
					#	if binary:
						Binary_Sheet.write_number(row, col, 0, red)
					#	else:
						Amp_Sheet.write_number(row, col, int(value), red)
					else:
					#	if binary:
						Binary_Sheet.write_number(row, col, 1, green)
					#	else:
						Amp_Sheet.write_number(row, col, int(value), green)
					col += 1
		print "finished plate", plate


col = 4
row += 1
Binary_Sheet.write(row, col, "SUM: ")
Binary_Sheet.write(row+1, col, "% Amplicons")
Binary_Sheet.write(row+1, col, "GC: ")

# Now write the GC content
command = "tail -n +2 " + anAmplicon + " | sort -k4 | cut -f 6"
GCs = subprocess.check_output(command, shell=True).strip().split("\n")
for gc in GCs:
	col += 1
	top = xl_rowcol_to_cell(1, col) # A1
	bottom = xl_rowcol_to_cell(row-1, col) # A1
	Binary_Sheet.write_formula(row, col, "=SUM(%s:%s)"%(top,bottom))
	Sum = xl_rowcol_to_cell(row, col) # Cell of the SUM cell
	Binary_Sheet.write_formula(row+1, col, "=%s/1235"%Sum, percent_format)
	Binary_Sheet.write_number(row+2, col, int(gc)) # Write the GC content
workbook.close()
print 'done'
