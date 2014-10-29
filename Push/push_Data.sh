#! /bin/bash

#Qsub arguments:

#$ -S /bin/bash
#$ -cwd
#$ -N Push_Data
#$ -o push_results.log
#$ -e push_results.log
#$ -V


#This script is a tool that copies BAM, amplicon.cov.xls and the TSVC_variants.vcf files of a run specified by the user.
# All of the std_out is written to a csv by start_Push.sh. all std_err is written to the screen.

#-----------------------------  FUNCTIONS DEFINED HERE -----------------------------------
#-----------------------------------------------------------------------------------------
function usage {
cat << EOF
USAGE: bash push_Data.sh 
All of the std_out is written to a csv by start_Push.sh. all std_err is written to the screen.
	-h | --help
	-u | --user_server <ionadmin@ip_address>
	-p | --project_path <path/to/project>	 (Destination on the other server of the files to push.)
	-s | --sample <sample_name>		(The sample's name)
	-i | --run_id <run_id> 			(The run's id. Will be used to find the file)
	-r | --run <run> 			(Files will be pushed to project_path/sample/run)
	-P | --proton_name <proton_name> 	(i.e. PLU or MER or NEP. Will be used to find the location of the bam file and such)
	-bp | --backup_path <backup_path> 	(for pluto: /mnt/Charon/archivedReports 	for mercury: /mnt/Triton/archivedReports)
	-b | --barcode <barcode>		(if this run is barcoded)
EOF
exit 8
}

# creates the output path we are pushing the files to
function create_ssh_Dir {
	ssh ${USER_SERVER} mkdir -p $1 </dev/null
}

#Find the version TS was run to generate the original BAM file.
# $1: The Run_Path/version.txt
function check_TS_Version {
	if [ "`find $1 -maxdepth 0 2>/dev/null`" ]; then
		TS_version=`grep -oE "version.*" $1 -m 1 2>/dev/null | grep -oe "[0-9]\.[0-9]" | perl -ne "chomp and print"`
		if [ "$TS_version" == "" ]; then
			TS_version=`grep -oE "Torrent_Suite=.*" $1 -m 1 2>/dev/null | grep -oe "[0-9]\.[0-9]" | perl -ne "chomp and print"`
		else
			TS_version="not_found"
		fi
	fi
	printf "${TS_version},"	
}
#find the version and parameters TVC was run on the original BAM file.
# $1: The Run_Path/plugin_out/variantCaller_out/drmaa_stdout.txt
function check_TVC_Version {
	if [ "`find $1 -maxdepth 0 2>/dev/null`" ]; then
		TVC_version=`grep -oE "version.*" $1 -m 1 2>/dev/null | \
			grep -oe "[0-9]\.[0-9]" | perl -ne "chomp and print"`
		TVC_parameters=`grep -oiE "results[/_.a-z]+\.json" $1 2>/dev/null | \
			grep -oiE "[_.a-z]+\.json" | perl -ne "chomp and print"`
		printf "${TVC_version}, ${TVC_parameters},"
	else
#		printf ",,"
		printf ""
	fi
}

#Takes as input the relative path/to/file.
#Writes to output the result of finding and pushing the file
function find_and_Push_File {
	# this variable will only be set to True if the file was actually copied.
	COPIED="False"
	if [ "`find $1 -maxdepth 0 2>/dev/null`" ]; then
		FILE_NAME=`find $1 -type f -printf "%f\n"`
		if ssh ${USER_SERVER} stat ${OUT_PATH}/${FILE_NAME} \> /dev/null 2\>\&1; then
			printf "File already copied,"
#			echo "$1 already copied" 1>&2
		else
			echo "${OUT_PATH}/${FILE_NAME} starting to copy at `date`" 1>&2
			COUNTER=0
			until [ "$COUNTER" == "10" ]; do
				rsync -avz --progress ${1} ${USER_SERVER}:${OUT_PATH}/${FILE_NAME} > /dev/null 2>&1 </dev/null
				if [ "$?" -ne "0" ]; then
					echo "Connection lost... will retry in 30 seconds." 1>&2
					let "COUNTER+=1"
					sleep 30
					#printf "ERROR: $1 was not copied,"
				else
					COUNTER=10
					COPIED="True"
					printf "Copied,"
					echo "${OUT_PATH}/${FILE_NAME} copied successfully `date`" 1>&2
				fi
			done
		fi
	else
		echo "--- File not found: $1 ---" 1>&2 
	#	echo "${OUT_PATH}/${FILE_NAME}" >> files_not_found.txt
		printf "not found," 
	fi
}



#for arguments
if [ $# -lt 14 ]; then # Technically there should be at least 14 arguments
	usage
	echo "ERROR: Not enough arguments provided"
fi

RUNNING="Starting push with options: "
counter=0
while :
do
	let "counter+=1"
	# If not enough inputs were given for an option, the while loop will just keep going. Stop it and print this error if it loops more than 100 times
	if [ $counter -gt 100 ]; then
		echo "USAGE ERROR: not all required inputs were given for options." 1>&2
		#echo "$RUNNING"
		exit 8
	fi
	case $1 in
		-h | --help)
			usage
			;;
		-u | --user_server)
			USER_SERVER=$2
			RUNNING="$RUNNING --user_server: $2 "
			shift 2
			;;
		-p | --project_path)
			DEST_PATH=$2
			RUNNING="$RUNNING --project_path: $2 "
			shift 2
			;;
		-s | --sample)
			SAMPLE=$2
			RUNNING="$RUNNING --sample: $2 "
			shift 2
			;;
		-i | --run_id)
			RUN_ID=$2
			RUNNING="$RUNNING --run_id: $2 "
			shift 2
			;;
		-r | --run)
			RUN=$2
			RUNNING="$RUNNING --output_dir: $2 "
			shift 2
			;;
		-P | --proton_name)
			PROTON_NAME=$2
			RUNNING="$RUNNING --proton_name: $2 "
			shift 2
			;;
		-bp | --backup_path)
			BACKUP_PATH=$2
			RUNNING="$RUNNING --backup_path: $2 "
			shift 2
			;;
		-b | --barcode) 
			BARCODE=$2
			RUNNING="$RUNNING --barcode: $2 "
			shift 2
			;;
		-*)
			printf >&2 'WARNING: Unknown option (ignored): %s\n' "$1"
			shift
			;;
		*)  # no more options. Stop while loop
			if [ "$1" != "" ]; then
				printf >&2 'WARNING: Unknown argument (ignored): %s\n' "$1"
				shift
			else
				break
			fi
			;;
	esac
done

# the options used
echo "$RUNNING at `date`" 1>&2

#-----------------------------  BEGIN PUSHING HERE -----------------------------------
#--------------------------------------------------------------------------------------

# The path to push the files to
# Example /rawdata/projects/Einstein/E0001/Run1
OUT_PATH=${DEST_PATH}/${SAMPLE}/${RUN}
PROJECT_PATH="/results/analysis/output/Home"

#Find the path of the directory that has the specified ROT-ID
# there must be a - before and after the RUN_ID as to ensure the proper run ID is found. 
# For example. With proton MER and Run_ID 21, without the - before and after, it could match MER-210 or MER-218 or MER-213 and so on. With the dash, only MER-21- will be found.
if [ "`find ${PROJECT_PATH}/*${PROTON_NAME}-${RUN_ID}[-_]*/${BARCODE}*rawlib*.bam -type f | grep -v "_tn_" 2>/dev/null`" ]; then
	# head -n 1 shouldn't be necessary, but there are times where there are more than one dir with the same RUN_ID...
	RUN_PATH=`find ${PROJECT_PATH}/*${PROTON_NAME}-${RUN_ID}[-_]* -maxdepth 0 -type d | head -n 1`
#If the directory is not found, check in the backup.
elif [ "`find ${BACKUP_PATH}/*${PROTON_NAME}-${RUN_ID}[-_]*/${BARCODE}*rawlib*.bam -type f 2>/dev/null`" ]; then
	RUN_PATH=`find ${BACKUP_PATH}/*${PROTON_NAME}-${RUN_ID}[-_]* -maxdepth 0 -type d | head -n 1` 
else
	#That rotID was not found, so print error, and quit.
	echo "*${PROTON_NAME}-${RUN_ID}-*/${BARCODE}*rawlib.bam not found in ${PROJECT_PATH} or ${BACKUP_PATH}." 1>&2
#	echo "${RUN_ID}/${RUN_NUM}_rawlib.bam" >> files_not_found.txt
	printf "*${PROTON_NAME}-${RUN_ID}-*/${BARCODE}*rawlib.bam not found in ${PROJECT_PATH} or ${BACKUP_PATH}."
	exit 1
fi

printf "$RUN_PATH,"

# Begin the file transfering!
# Finds the TS and TVC versions that were used to compare for QC later.
check_TS_Version "${RUN_PATH}/version.txt"
check_TVC_Version "${RUN_PATH}/plugin_out/variantCaller_out/drmaa_stdout.txt"
# Create the Sample and run path
create_ssh_Dir "${OUT_PATH}"

#push the BAM file
# if the run is not barcoded, then barcode will be empty
find_and_Push_File "${RUN_PATH}/${BARCODE}*rawlib.bam"
if [ "$COPIED" == "True" ]; then
	if [ "$TS_version" == "" ]; then
		TS_version="not_found"
	fi
	# Write the json file which will be used to run TVC, COV analysis, and QC the runs.
	# FILE_NAME should be the name of the file that was pushed
	python writeJson.py \
		--bam $FILE_NAME \
		--run_name $RUN \
		--sample $SAMPLE \
		--proj_path $DEST_PATH \
		--orig_path $RUN_PATH \
		--proton $PROTON_NAME \
		--ip_address 192.168.200.42 \
		--ts_version $TS_version \
		--json "Json_Files/${SAMPLE}_${RUN}.json"
	# push the Json File
	find_and_Push_File "Json_Files/${SAMPLE}_${RUN}.json"
fi

#push the BAM.bai file
find_and_Push_File "${RUN_PATH}/${BARCODE}*rawlib.bam.bai"
#push the amplicon coverage file

# starting with 4.2 coverage analysis plugin output folder gets a number assigned so taht users can run multiple times without over-writing the previous coverage analysis plugin result 
# example: coverageAnalysis_out.2369
# if there are multiple cov results, hopefully they were run with the same BED file! find will grep the first instance
covPath=`find ${RUN_PATH}/plugin_out/coverageAnalysis_out.* -maxdepth 0 2>/dev/null`
find_and_Push_File "${covPath}/*.amplicon.cov.xls"

# find_and_Push_File "${RUN_PATH}/plugin_out/coverageAnalysis_out/*.amplicon.cov.xls"

#push the VCF file
find_and_Push_File "${RUN_PATH}/plugin_out/variantCaller_out/TSVC_variants.vcf"
# push the backupPDF. It is located in the non-archived dir.
#if [ "`find ${PROJECT_PATH}/*${PROTON_NAME}-${RUN_ID}-*/backupPDF.pdf -type f 2>/dev/null`" ]; then
#	pdf=`find ${PROJECT_PATH}/*${PROTON_NAME}-${RUN_ID}-*/backupPDF.pdf -type f 2>/dev/null | head -n 1`
#	find_and_Push_File "$pdf"
#fi

#let's copy report.pdf instead of backup  
if [ "`find ${PROJECT_PATH}/*${PROTON_NAME}-${RUN_ID}-*/report.pdf -type f 2>/dev/null`" ]; then
	pdf=`find ${PROJECT_PATH}/*${PROTON_NAME}-${RUN_ID}-*/report.pdf -type f 2>/dev/null | head -n 1`
	find_and_Push_File "$pdf"
fi

#That should be about it for now.
