#! /bin/bash

# GOAL: Run annovar on all of the vcf files in the project, and generate a list of variants

#$ -S /bin/bash
#$ -cwd
#$ -N Get_All_Variants
#$ -o results.txt
#$ -e errors.txt
#$ -V

PROJECT_DIR='/rawdata/project_data/Wales_Archived_data2' # This is the directory where I'm still QC multiple runs
# There shouldn't normally be two different project directoreis, so I won't make that a parameter
PROJECT_METADATA_CSV='/home/ionadmin/jeff/Wales_data/WalesPlates_5_23_14.csv'

USAGE='USAGE: bash get_list_of_all_variants.sh <path/to/Project_Dir> <path/to/Project_Metadata_CSV> <Amplicon Coverage Cutoff> <Depth Cutoff>'

#for arguments
if [ $# -eq 4 ];
then
	PROJECT_DIR=$1
	PROJECT_METADATA_CSV=$2
	AMP_COV_CUTOFF=$3 # The minimum amount of coverage each amplicon needs to have
	DEPTH_CUTOFF=$4 # The minimum depth for each base.
else
	echo $USAGE
	exit
fi

# Now check the files to see if they exist
if [ ! -d $PROJECT_DIR ]
then
	echo "$PROJECT_DIR not found"
	exit
elif [ ! -r $PROJECT_METADATA_CSV ]
then
	echo "$PROJECT_METADATA_CSV not found"
	exit
fi

#PROJECT_DATA=$(tail -n +2 ${PROJECT_FILE}) # This didn't work to remove the header line, so looks like I'll just have to write to a file
tail -n +2 $PROJECT_METADATA_CSV > noheader.csv
PROJECT_FILE_WO_HEADER="noheader.csv"

echo "sample_dir;id;plate;sample;case_ctr;rotID_col;barcode" > successful_samples.txt

# If everything checks out, then read the csv file line by line, and call push_Data.sh
while IFS=',' read id plate sample case_ctr rotID_col barcode status leftovers
do
	status=`echo "$status" | sed "s/^ *//g" | sed "s/ *$//g"`
	sample_dir=''
	IFS="&" read -a rotIDs <<< "${rotID_col}"
	# If there is only one run for this sample, then take the data from the normal place.
	if [ "${#rotIDs[@]}" == "1" -a "$status" != 'Fail' ]
	then
		# Normal output will be put into the output csv. Error output will be printed to the screen
		if [ "`find ${PROJECT_DIR}/${plate}/${sample} -maxdepth 0 2>/dev/null`" ]
		then
			sample_dir=`find ${PROJECT_DIR}/${plate}/${sample} -maxdepth 0`
		else
			echo "ERROR: $plate/$sample not found in $PROJECT_DIR"
			echo "ERROR: $plate/$sample not found in $PROJECT_DIR" 1>&2
		fi
	# If there are multiple runs, then use the data that ozlem already merged and such.
	elif [ "${#rotIDs[@]}" -gt "1" -a "$status" != 'Fail' ]
	then
		if [ "`find ${PROJECT_DIR}/${plate}/${sample}/Merged -maxdepth 0 2>/dev/null`" ]
		then
			sample_dir=`find ${PROJECT_DIR}/${plate}/${sample}/Merged -maxdepth 0`
		else
			echo "ERROR: $plate/$sample not found in $PROJECT_DIR"
			echo "ERROR: $plate/$sample not found in $PROJECT_DIR" 1>&2
		fi
	fi

	# if the plate/sample was found, then call_filter_and_run_annovar.sh
	if [ "$sample_dir" != '' ]
	then
		# If annovar was already run, then don't run it again.
		if [ ! -f "${sample_dir}/Analysis_files/filtered.vcf" ]
		then
			bash filter_and_run_annovar.sh $sample_dir $AMP_COV_CUTOFF $DEPTH_CUTOFF
			error_code=$?
			if [ "$error_code" == "0" ]
			then
				# script was successful. Adding this sample_dir to the list
				echo "${plate}_${sample} finished running Annovar without errors"
				echo "$sample_dir;$id;$plate;$sample;$case_ctr;$rotID_col;$barcode" >> successful_samples.txt
			elif [ "$error_code" == "4" ]
			then
				# one of the files was not found.
				echo "ERROR: ${sample_dir} did not have the necessary files"
				echo "ERROR: ${sample_dir} did not have the necessary files" 1>&2
			else
				# Something went wrong...
				echo "ERROR: ${sample_dir} failed. See sample_dir's log.txt file"
				echo "ERROR: ${sample_dir} failed. See sample_dir's log.txt file" 1>&2
			fi
		else
			echo "$sample_dir;$id;$plate;$sample;$case_ctr;$rotID_col;$barcode" >> successful_samples.txt
		fi
	fi
done < ${PROJECT_FILE_WO_HEADER}
echo "Finished generating the annovar data."

echo "Generating the list of all variants"
python2.7 generate_sheets_allvars.py successful_samples.txt -d data_matrix.xls -s varsPerSample.xls -v varInfo.xls
#head -1 all_vars.xls > sorted_all_vars.xls 
#tail -n +2 all_vars2.xls | sort -k 1 >>sorted_all_vars.xls

rm $PROJECT_FILE_WO_HEADER


