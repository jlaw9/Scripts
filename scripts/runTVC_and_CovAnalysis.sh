#! /bin/bash

# Goal: Run coverage analysis and TVC on a BAM file 
# It would be great to allow you to either specify a sample, plate, or project, or a csv.

# Parameters for Qsub:
#$ -S /bin/bash
#$ -N TVC_Cov
#$ -o tvc_results.log
#$ -e tvc_results.log
#$ -cwd
#$ -V

SOFTWARE_ROOT="/rawdata/legos"
PICARD_TOOLS_DIR="/opt/picard/picard-tools-current"
COV_ANALYSIS_DIR="/results/plugins/coverageAnalysis"
VARIANT_CALLER_DIR="/results/plugins/variantCaller"

# Default parameter settings JSON file for running TVC
TVC_JSON="${SOFTWARE_ROOT}/parameter_sets/germline_high_stringency_pgm.json"
REF_FASTA="/results/referenceLibrary/tmap-f3/hg19/hg19.fasta"

function usage {
cat << EOF
USAGE: bash runTVC_and_CovAnalysis.sh <path/to/BAM_File.bam> [OPTIONS]
Options:
	-c | --cov <path/to/Merged_BED> <path/to/Unmerged_BED>   (If no .cov.xls file is present in the bam file's directory, use this option to run Coverage Analysis)
	-ca | --cov_ampliseq 	(Default. Will run coverage analysis with Ampliseq options)
	-ct | --cov_targetseq	(Will run coverage analysis with Targetseq options)
	-t | --tvc <path/to/Project_BED> 	(If no .vcf file is present in the bam file's dir, use this option to run TVC)
	-tj | --tvc_json <path/to/TVC_parameters.json file>	(Parameter settings file which will be used by TVC. Defaut is germline_high_stringency.json)
	-o | --output_dir <path/to/Output_Dir>	(Output files will be placed here. Default is the Bam File's directory)
	-rdf | --remove_dup_flags	(Will use samtools to check if there are duplicate flags. If there are, remove the duplicate flags from the bam file using Picard tools)
	-fd | --flag_dups		(Will place the duplicate flag in the bam file)
	-cl | --cleanup		(Use this option to delete the temporary files generated to run TVC and Coverage Analysis. If there are any errors, the temp files are not deleted.)
	-f | --forced			(Use this option to run tvc/cov even if there is a .vcf/.cov.xls file already present)
EOF
exit 8
}


# Default options
RUNNING="Starting using these options: "
RUN_COV="False"
COV_AMPLISEQ="True"
RUN_TVC="False"
TVC_VERSION='4.2'
CLEANUP="False"
NOERRS="True"
FORCED="False"
#for arguments
if [ $# -lt 3 ];
then
	usage
fi
while :
do
	case $1 in
		*.bam)
			BAM_FILE=$1
			RUNNING="$RUNNING BAM: $1 "
			shift 
			;;
		-c | --cov)
			RUN_COV="True"
			MERGED_BED=$2
			UNMERGED_BED=$3
			RUNNING="$RUNNING --cov merged_bed: $2, unmerged_bed: $3 "
			shift 3
			;;
		-ca | --cov_ampliseq)
			COV_AMPLISEQ="True"
			RUNNING="$RUNNING --cov_ampliseq "
			shift 
			;;
		-ct | --cov_targetseq)
			COV_TARGETSEQ="True"
			COV_AMPLISEQ="False"
			RUNNING="$RUNNING --cov_targetseq "
			shift 
			;;
		-t | --tvc)
			RUN_TVC="True"
			PROJECT_BED=$2
			RUNNING="$RUNNING --tvc bed: $2 "
			shift 2
			;;
		-tj | --tvc_json)
			TVC_JSON=$2
			RUNNING="$RUNNING --tvc_json: $2 "
			shift 2
			;;
		-o | --output_dir)
			OUTPUT_DIR=$2
			RUNNING="$RUNNING --output_dir: $2 "
			shift 2
			;;

		-rdf | --remove_dup_flags)
			REMOVE_DUP_FLAGS="True"
			RUNNING="$RUNNING --remove_dup_flags: $2 "
			shift
			;;
		-fd | --flag_dups)
			FLAG_DUPS="True"
			RUNNING="$RUNNING --flag_dups: $2 "
			shift
			;;
		-cl | --cleanup)
			CLEANUP="True"
			RUNNING="$RUNNING --cleanup "
			shift
			;;
		-f | --forced)
			FORCED="True"
			RUNNING="$RUNNING --forced"
			shift
			;;
		-*)
			printf >&2 'WARNING: Unknown option (ignored): %s\n' "$1"
			shift
			;;
		 *)  # no more options. Stop while loop
			if [ "$1" != '' ]; then
					printf >&2 'WARNING: Unknown option (ignored): %s\n' "$1"
					shift
			else    
				break
			fi  
			;;  
	esac
done

# RUNNING is a variable containing all of the options specified
echo "$RUNNING"

# Now check the files to see if the bam file exists.
if [ "$BAM_FILE" == '' ]
then
	echo "ERROR: MUST SPECIFY A BAM FILE" 1>&2
#	usage
	exit 4
fi
# If no output dir is specified, default will be the bam file's directory
if [ "$OUTPUT_DIR" == '' ]
then
	OUTPUT_DIR=`dirname $BAM_FILE`
fi

# ------------------------------------------------
# ---------------- FUNCTIONS ---------------------
# ------------------------------------------------

function checkFlags {
	# Remove or flag the duplicates according to what the user specified.
	if [ "$REMOVE_DUP_FLAGS" == "True" ]; then
		bash ${SOFTWARE_ROOT}/scripts/flags.sh \
			$BAM_FILE \
			--remove_dup \
			--cleanup
	elif [ "$FLAG_DUPS" == "True" ]; then
		bash ${SOFTWARE_ROOT}/scripts/flags.sh \
			$BAM_FILE \
			--flag_dups \
			--cleanup
	fi
}

# $1: the bam file to index
function checkBamIndex {
	# If the bam file needs to be indexed, index the bam file
	if [ ! "`find ${1}.bai -maxdepth 0 2>/dev/null`" ]; then
		echo "Indexing $BAM_FILE"
		java -jar ${PICARD_TOOLS_DIR}/BuildBamIndex.jar INPUT=${1} OUTPUT=${1}.bai >/dev/null 2>&1 #hides the output of picard-tools.
	fi	
}

# Runs coverage analysis, then copies the .amplicon.cov.xls file it needs, and deletes the other files generated.
function runCov {
	checkBamIndex $BAM_FILE

	echo "$BAM_FILE beginning Coverage Analysis at: `date`"
	#now run TVC
	mkdir -p ${OUTPUT_DIR}/cov_full 2>/dev/null
	
	# -a is for Ampliseq.  -g option gives the gene name and GC content  -D specifies the output directory, -d is for bam files with flagged duplicates
	# Ozlem had to modify the run_coverage_analysis.sh to include the 30x coverage. She modified the targetReadStats.pl which is being called by run_cv_analysis.sh
	# For some reason, putting the merged BED file for -A and the unmerged BED file for -B with the -g option generated the same .amplicon.cov.xls file as the web browser did. We will use these settings.
	run_cov="${COV_ANALYSIS_DIR}/run_coverage_analysis.sh"
	if [ "$COV_AMPLISEQ" == "True" ]; then
		run_cov="$run_cov -ag"
	elif [ "$COV_TARGETSEQ" == "True" ]; then
		run_cov="$run_cov -c -d"
	fi
	run_cov="""$run_cov -D "${OUTPUT_DIR}/cov_full" -A "${MERGED_BED}" -B "${UNMERGED_BED}" "$REF_FASTA" "$BAM_FILE"""" 	
	echo
	echo "running cov with these options: $run_cov"
	echo
	$run_cov > ${OUTPUT_DIR}/cov_full/log.out 2>&1
	#wait for job to finish. If there is an error in coverage analysis, $? will be 1 and the error message will be displayed 
	if [ $? -eq 0 ];
	then
		# Coverage analysis was successful. Copy the .amplicon.cov.xls file, and Delete the other temporaray files.
		echo "$BAM_FILE Coverage analysis finished successfully at: `date`"
	else
		NOERRS="False"
		# Something went wrong with coverage analysis. Not copying the data.
		echo 1>&2
		echo "--- ERROR: $BAM_FILE Coverage analysis was unsuccessful. Not copying or deleting data ---" 1>&2
		echo "--- See cov_full/log.out for details of what happened ---" 1>&2
	fi
}


# Runs TVC, then copies the .vcf file needed, and deletes the rest of the files generated.
function runTVC {
	checkBamIndex $BAM_FILE

	echo "$BAM_FILE beginning TVC v4.2 at: `date`"
	#now run TVC v4.2. The --primer-trim-bed will trim the reads to matcht the amplicons listed in the BED file
	mkdir -p ${OUTPUT_DIR}/tvc${TVC_VERSION}_out 2>/dev/null
	${VARIANT_CALLER_DIR}/variant_caller_pipeline.py \
		--input-bam $BAM_FILE \
		--reference-fasta $REF_FASTA \
		--output-dir ${OUTPUT_DIR}/tvc${TVC_VERSION}_out \
		--region-bed  ${PROJECT_BED} \
		--parameters-file $TVC_JSON \
		--primer-trim-bed ${PROJECT_BED} \
		--bin-dir  ${VARIANT_CALLER_DIR} \
		> ${OUTPUT_DIR}/tvc${TVC_VERSION}_out/log.out 2>&1
		
	
	if [ $? -eq 0 ];
	then
		#TVC was successful.
		echo "$BAM_FILE TVC v4.2 finished successfully at: `date`"
	else
		# Something went wrong with TVC. Not copying the data.
		NOERRS="False"
		echo 1>&2
		echo "--- ERROR: $BAM_FILE TVC v4.2 had a problem. Not copying data ---" 1>&2
		echo "--- See tvc${TVC_VERSION}_out/log.out for details of what happened ---" 1>&2
	fi
}


# ----------------------------------------------------------
# ---------------- PROGRAM STARTS HERE ---------------------
# ----------------------------------------------------------


if [ "$RUN_COV" == "True" -o "$RUN_TVC" == "True" ]; then
	checkFlags 
fi

if [ "$RUN_COV" == "True" ];
then
	if [ ! -f $MERGED_BED ]
	then
		echo "ERROR: Merged Bed: $MERGED_BED not found. Not running Coverage Analysis."
		NOERRS="False"
	elif [ ! -f $UNMERGED_BED ]
	then
		echo "ERROR: Unmerged Bed: $UNMERGED_BED not found. Not running Coverage Anlysis."
		NOERRS="False"
	elif [ "`find ${OUTPUT_DIR}/*.amplicon.cov.xls 2>/dev/null`" -a "$FORCED" != "True" ];
	then
		echo "$OUTPUT_DIR already has a .amplicon.cov.xls file. Not running Coverage Analysis. (use --forced to have cov analysis run anyway)"
	else
		# If there is no .cov.xls file and the other bed files are found, run coverage analysis
		runCov
	fi
fi
	
if [ "$RUN_TVC" == "True" ]
then
	if [ ! -f $PROJECT_BED ]; then
		echo "ERROR: Project Bed: $PROJECT_BED not found. Not running TVC."
		NOERRS="False"
	elif [ ! -f $TVC_JSON ]; then 
		echo "ERROR: TVC parameters: $TVC_JSON not found. Not running TVC."
		NOERRS="False"
	elif [ "`find ${OUTPUT_DIR}/*.vcf 2>/dev/null`" -a "$FORCED" != "True" ]; then
		echo "$OUTPUT_DIR already has a .vcf file. Not runnning TVC. (use --forced to have tvc run anyway)"
	else
		# If there is no vcf file present for the current run, and the project BED is found, then run TVC.
		runTVC
	fi
fi

# If there were errors in TVC or Cov analysis, then exit here with an exit status of 1.
if [ "$NOERRS" == "False" ]
then
	echo "Finished with problems."
	exit 1
fi

# If the Cleanup option is specified, cleanup the output
if [ "$CLEANUP" == "True" ]
then
	#echo "Copying the output files and removing the temporary files."
	# Copy the output files we want and remove the temporary files.
	mv ${OUTPUT_DIR}/cov_full/*.amplicon.cov.xls ${OUTPUT_DIR}/ 2>/dev/null
	mv ${OUTPUT_DIR}/tvc${TVC_VERSION}_out/TSVC_variants.vcf ${OUTPUT_DIR}/${TVC_VERSION}_TSVC_variants.vcf 2>/dev/null 

	rm -rf ${OUTPUT_DIR}/cov_full 2>/dev/null
	rm -rf ${OUTPUT_DIR}/tvc${TVC_VERSION}_out 2>/dev/null
#	rm ${BAM_FILE}.bai 2>/dev/null
fi
echo "Finished"
exit 0
