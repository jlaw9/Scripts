#! /bin/bash

# Goal: Navigate a project Dir by plate, then by sample.
# Get Coverage Metrics for each run of each sample.
# QC all of the multiple run bam files in each sample with each other (i.e. Run1 vs Run2, Run1 vs Run3, Run2 vs Run3)

#$ -S /bin/bash
#$ -cwd
#$ -N QC_Sample
#$ -o qc_sample_out.log
#$ -e qc_sample_out.log
#$ -q all.q
#$ -V


# Default file paths:
SOFTWARE_DIR="/rawdata/software"
QC_SCRIPTS="${SOFTWARE_DIR}/scripts/QC"
BED_DIR="/rawdata/software/BED"
# PROJECT_BED="$BED_DIR/AmpliSeq-Exome.bed"
# CDS_BED='/home/ionadmin/jeff/QC/BED/Wales_CDS.bed'
# PLUS10_BED='/home/ionadmin/jeff/QC/BED/Wales_plus10.bed'
# MINUS10_BED='/home/ionadmin/jeff/QC/BED/Wales_minus10.bed'

function checkFiles {
	files=$1
	for file in ${files[@]}; 
	do
		if [ ! -r ${file} ];
		then
			echo "-- ERROR -- '${file}' not found or not readable" 1>&2
			exit 4
		fi
	done
}

function usage {
cat << EOF
USAGE: bash QC_sample.sh 
	-h | --help
	-s | --sample_dir <path/to/Sample_Dir>
	-g | --germline <path/to/TVC/parameters.json> <Depth Cutoff> <WT Cutoff> <HOM Cutoff>
	-all | --all_tumor_normal <Json_Normal> <Depth_N> <WT_N> <HOM_N> <Json_T> <Depth_T> <WT_T> <HOM_T>
	-tn | --tumor_normal <Json_Normal> <Depth_N> <WT_N> <HOM_N> <Json_T> <Depth_T> <WT_T> <HOM_T>
	-tt | --tumor_tumor <TVC Json_T> <Depth_T> <WT_T> <HOM_T>
	-nn | --normal_normal <TVC Json_Normal> <Depth_N> <WT_N> <HOM_N> 
	-b | --bed <path/to/bed> 
	-cb | --cds_bed <path/to/CDS_bed> (This option should only be used if the user wants to run TVC using the Project bed, and then intersect the results with the CDS bed.)
	-sb | --subset_bed <path/to/subset_bed> (If the user want to subset out certain genes from the Project_Bed)
	-a | --amp_cov_cutoff (Cutoff for # of amplicon reads.) 
	-rgc | --run_gatk_cds (Normally, GATK is run using the subset of the beds specified above. If the cds_bed is specified, and this option is specified, GATK will be run twice.)
	-chr | --subset_chr <chr#> (The chromosome specified here (for example: chr1) will be used to subset the VCF and BAM files)
	-nr | --no_run_info (If this option is specified, no need to supply the plus and minus 10 beds)
	-pb | --plus10bed (bed file with only the 10th pos of the amplicons)
	-mb | --minus10bed (bed file with only the 10th pos from the end of the amplicons)
	-cl | --cleanup (This option is not yet available. Will delete temporary files used to generate the QC metrics)
EOF
exit 8
}

#for arguments
if [ $# -lt 5 ]; then
	usage
fi

# Default Options
GERMLINE="False" # Treat the file system as germline and generate QC tables for them. 
TUMOR_NORMAL="False" # Treat the file system as Tumor / Normal pairs and generate QC tables for them. 
TUMOR_TUMOR="False" # Treat the file system as Tumor / Tumor pairs and generate QC tables for them. 
NORMAL_NORMAL="False" # Treat the file system as Normal / Normal pairs and generate QC tables for them. 
RUN_INFO="True" # Option to generate run information about each sample
CLEANUP="False" # Option to delete the temporary files. Not yet implemented.
AMP_COV_CUTOFF=30 # The minimum amount of coverage each amplicon needs to have. Default is 30

RUNNING="Starting QC using these option: "
while :
do
	case $1 in
		-h | --help)
			usage
			;;
		-s | --sample_dir)
			SAMPLE_DIR=$2
			RUNNING="$RUNNING --sample_dir: $2, "
			shift 2
			;;
		-g | --germline)
			if [ "$5" == "" ]; then
				echo "ERROR: all 5 options are needed for --germline"
				exit 8
			fi			
			JSON_PARAS=$2
			DEPTH_CUTOFF=$3
			WT_CUTOFF=$4
			HOM_CUTOFF=$5
			RUNNING="$RUNNING --germline: Json_paras: $2, Depth_cutoff: $2, WT_cutoff:$3, HOM_cutoff:$4, "
			GERMLINE="True"
			shift 5
			;;
		-all | --all_tumor_normal)
			if [ "$9" == "" ]; then
				echo "ERROR: all 8 options are needed for --all_tumor_normal"
				exit 8
			fi
			JSON_PARAS_NORMAL=$2
			DEPTH_CUTOFF_NORMAL=$3
			WT_CUTOFF_NORMAL=$4
			HOM_CUTOFF_NORMAL=$5
			JSON_PARAS_TUMOR=$6
			DEPTH_CUTOFF_TUMOR=$7
			WT_CUTOFF_TUMOR=$8
			HOM_CUTOFF_TUMOR=$9
			RUNNING="$RUNNING --all_tumor_normal: Json_parasN: $2, Depth_cutoffN: $3 WT_N:$4 HOM_N:$5 Json_parasT: $6, Depth_cutoffT: $7 WT_T:$8 HOM_T:$9, "
			TUMOR_NORMAL="True"
			TUMOR_TUMOR="True"
			NORMAL_NORMAL="True"
			shift 9
			;;
		-tn | --tumor_normal)
			if [ "$9" == "" ]; then
				echo "ERROR: all 8 options are needed for --tumor_normal"
				exit 8
			fi			
			JSON_PARAS_NORMAL=$2
			DEPTH_CUTOFF_NORMAL=$3
			WT_CUTOFF_NORMAL=$4
			HOM_CUTOFF_NORMAL=$5
			JSON_PARAS_TUMOR=$6
			DEPTH_CUTOFF_TUMOR=$7
			WT_CUTOFF_TUMOR=$8
			HOM_CUTOFF_TUMOR=$9
			RUNNING="$RUNNING --tumor_normal: Json_parasN: $2, Depth_cutoff1: $3 WT_N:$4 HOM_N:$5 Json_parasT: $6, Depth_cutoffT: $7 WT_T:$8 HOM_T:$9, "
			TUMOR_NORMAL="True"
			shift 9
			;;
		-tt | --tumor_tumor)
			if [ "$5" == "" ]; then
				echo "ERROR: all 5 options are needed for --tumor_tumor"
				exit 8
			fi			
			JSON_PARAS_TUMOR=$3
			DEPTH_CUTOFF_TUMOR=$3
			WT_CUTOFF_TUMOR=$4
			HOM_CUTOFF_TUMOR=$5
			RUNNING="$RUNNING --tumor_tumor: Json_paras: $2, Depth_cutoff: $2 WT_cutoff:$3 HOM_cutoff:$4, "
			TUMOR_TUMOR="True"
			shift 5
			;;
		-nn | --normal_normal)
			if [ "$5" == "" ]; then
				echo "ERROR: all 5 options are needed for --normal_normal"
				exit 8
			fi			
			JSON_PARAS_NORMAL=$2
			DEPTH_CUTOFF_NORMAL=$3
			WT_CUTOFF_NORMAL=$4
			HOM_CUTOFF_NORMAL=$5
			RUNNING="$RUNNING --normal_normal: Json_paras: $2, Depth_cutoff: $2 WT_cutoff:$3 HOM_cutoff:$4, "
			NORMAL_NORMAL="True"
			shift 5
			;;

		-nr | --no_run_info)
			RUN_INFO="False"
			RUNNING="$RUNNING --no_run_info, "
			shift
			;;
		-b | --bed)
			PROJECT_BED=$2
			RUNNING="$RUNNING --bed: $2, "
			shift 2
			;;
		-cb | --cds_bed)
			CDS_BED=$2
			RUNNING="$RUNNING --cds_bed: $2, "
			shift 2
			;;
		-pb | --plus10)
			PLUS10_BED=$2
			RUNNING="$RUNNING --plus10: $2, "
			shift 2
			;;
		-mb | --minus10)
			MINUS10_BED=$2
			RUNNING="$RUNNING --minus10: $2, "
			shift 2
			;;
		-a | --amp_cov_cutoff)
			AMP_COV_CUTOFF=$2
			RUNNING="$RUNNING --amp_cov_cutoff: $2, "
			shift 2
			;;
		-sb | --subset_bed)
			SUBSET_BED=$2
			RUNNING="$RUNNING --subset_bed: $2, "
			shift 2
			;;
		-rgc | --run_gatk_cds)
			RUN_GATK_CDS="True"
			RUNNING="$RUNNING --run_gatk_cds, "
			shift 
			;;
		-chr | --subset_chr)
			CHR=$2
			RUNNING="$RUNNING --subset_chr: $2, "
			shift 2
			;;
		-cl | --cleanup)
			CLEANUP="True"
			RUNNING="$RUNNING --cleanup "
			shift
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

# RUNNING contains all of the specified options
echo "$RUNNING"

#files=("$SAMPLE_DIR" "$PROJECT_BED" "$PLUS10_BED" "$MINUS10_BED" "$CDS_BED")
#checkFiles $files


# ----------------------------------------------------
# ------------ FUNCTIONS DEFINED HERE ----------------
# ----------------------------------------------------

# THIS FUNCTION IS NOT YET IMPLEMENTED
# $1: Run_Dir $2: The output dir $3 the depth cutoff $4 the WT_Cutoff $5 the HOM_Cutoff
function QC_getRunInfo {
	if [ ! "`find ${1}/*.bam -maxdepth 0 2>/dev/null`" ]
	then
		echo "$1 has no BAM file :("
	elif [ ! "`find ${1}/*.vcf -maxdepth 0 2>/dev/null`" ]
	then
		echo "$1 has no VCF file :("
	else
	# ----- There should be only one .bam in this directory. Otherwise there could be problems. ----------
		# QC_getCoverageInfo runs GATK 3 times using the three different BED files specified to get the three different QC metrics wanted
		#Ts/Tv	# Total variants (single allele)	# HET variants (single allele rates)	# HOM variants (single allele rates)
		BAM="`find ${1}/*.bam -maxdepth 0 2>/dev/null`"
		VCF="`find ${1}/4.0*.vcf -maxdepth 0 2>/dev/null`"
		if [ "$VCF" == "" ]; then
			VCF="`find ${1}/*.vcf -maxdepth 0 2>/dev/null`"
		fi
		bash ${QC_SCRIPTS}/QC_getRunInfo.sh $BAM $VCF $PLUS10_BED $MINUS10_BED $CDS_BED $2 $AMP_COV_CUTOFF $3 $4 $5
	fi
}

# For Tumor / Normal pairs, Run1 should be the normal run, and Run2 should be the tumor run.
# $1 1st Run's dir name (i.e. sample1/Run1), $2: 2nd Run's dir name (i.e. sample1/Run2), 
# $3: JSON_PARAS1, $4: JSON_PARAS2
# $5: Depth1, $6: Depth2, $7: WT1, $8: HOM1, $9: WT2, $10: HOM2
# Output will be put into a dir like: sample1/QC/Run1vsRun2
function QC_2Runs {
	if [ "$1" != "$2" ]; then
		run1_name="`find $1 -maxdepth 0 -type d -printf "%f\n" 2>/dev/null`"
		run2_name="`find $2 -maxdepth 0 -type d -printf "%f\n" 2>/dev/null`"
		QCd="${SAMPLE_DIR}/QC/${run1_name}vs${run2_name}"
		# QC these two runs. QC_2Runs.sh takes the two run dirs and finds a .bam, .vcf, and .cov.xls file in the same dir as the .bam file
		qc2runs="bash ${QC_SCRIPTS}/QC_2Runs.sh --run_dirs $1 $2 --output_dir $QCd --project_bed $PROJECT_BED -a $AMP_COV_CUTOFF -j $3 $4 -d $5 $6 -gt $7 $8 $9 ${10} "
		if [ "$CDS_BED" != "" ]; then
			qc2runs="$qc2runs -cb $CDS_BED "
		fi
		if [ "$SUBSET_BED" != "" ]; then
			qc2runs="$qc2runs --subset_bed $SUBSET_BED "
		fi
		if [ "$RUN_GATK_CDS" == "True" ]; then
			qc2runs="$qc2runs --run_gatk_cds "
		fi
		if [ "$CHR" != "" ]; then
			qc2runs="$qc2runs --subset_chr $CHR "
		fi
		if [ "$CLEANUP" == "True" ]; then
			qc2runs="$qc2runs --cleanup "
		fi

		# now run QC_2Runs
		$qc2runs
		status="$?"
		if [ $status -eq 1 ]; then
			echo "$QCd QC_2Runs.sh had an error!! moving it to ${QCd}_Error" 1>&2
			mv $QCd ${QCd}_Error
		elif [ $status -eq 4 ]; then
			echo "$QCd got a file not found error..." 1>&2
		elif [ $status -eq 8 ]; then
			echo "$QCd got a usage error..." 1>&2
		fi
	fi
}

# ---------------------------------------
# ------ PROGRAM STARTS HERE ------------
# ---------------------------------------

echo "$SAMPLE_DIR is starting QC"

# ---------------------------------- START GERMLINE ---------------------------------------
if [ "$GERMLINE" == "True" ]; then
	# Find all of the runs in this sample. The printf option makes it so only the name of the dir is printed
	runs="`find ${SAMPLE_DIR}/Run[0-9]* -maxdepth 0 -type d 2>/dev/null`"
	# QC the Multiple Runs
	for run1 in $runs; do
		run1_num=`echo "$run1" | grep -Eo "[0-9]$"`
		# If the user did not specify to get this run's info, then get this run's info.
#		if [ "$RUN_INFO" == "True" ]; then
	#		get_Run_Info $sample ${sample}/Analysis_files/gatk_out
#			QC_getRunInfo $run1
#		fi
		# If there are more than two run_bams for this sample, then QC them with each other.
		for run2 in $runs; do
			run2_num=`echo "$run2" | grep -Eo "[0-9]$"`
			if [ $run1_num -lt $run2_num ]; then
				# Make the QC table for this combination.
				QC_2Runs $run1 $run2 \
					$JSON_PARAS $JSON_PARAS \
					$DEPTH_CUTOFF $DEPTH_CUTOFF \
					$WT_CUTOFF $HOM_CUTOFF \
					$WT_CUTOFF $HOM_CUTOFF
			fi
		done
	done
fi
# ---------------------------------- END GERMLINE ---------------------------------------

# $1 1st Run's dir name (i.e. sample1/Run1), $2: 2nd Run's dir name (i.e. sample1/Run2), 
# $3: JSON_PARAS1, $4: JSON_PARAS2
# $3: Depth1, $4: Depth2, $5: WT1, $6: HOM1, $7: WT2, $8: HOM2

# ---------------------------------- Start Somatic ---------------------------------------
if [ "$TUMOR_NORMAL" == "True" ]; then
	# QC the Tumor runs with the normal runs.
	normal_runs="`find ${SAMPLE_DIR}/Normal/N-[0-9_]* -maxdepth 0 -type d 2>/dev/null`"
	tumor_runs="`find ${SAMPLE_DIR}/Tumor/T-[0-9_]* -maxdepth 0 -type d 2>/dev/null`"
	for normal_run in $normal_runs; do
		for tumor_run in $tumor_runs; do
			# Make the QC table for this combination.
			QC_2Runs $normal_run $tumor_run \
				$JSON_PARAS_NORMAL $JSON_PARAS_TUMOR \
				$DEPTH_CUTOFF_NORMAL $DEPTH_CUTOFF_TUMOR \
				$WT_CUTOFF_NORMAL $HOM_CUTOFF_NORMAL \
				$WT_CUTOFF_TUMOR $HOM_CUTOFF_TUMOR
		done		
	done
fi

if [ "$TUMOR_TUMOR" == "True" ]; then
	# QC the Tumor runs with the tumor runs.
	tumor_runs="`find ${SAMPLE_DIR}/Tumor/T-[0-9_]* -maxdepth 0 -type d 2>/dev/null`"
	for tumor_run1 in $tumor_runs; do
		t1_num=`echo "$tumor_run1" | grep -Eo "[0-9]$"`
		for tumor_run2 in $tumor_runs; do
			t2_num=`echo "$tumor_run2" | grep -Eo "[0-9]$"`
			if [ $t1_num -lt $t2_num ]; then
				# Make the QC table for this combination.
				QC_2Runs $tumor_run1 $tumor_run2 \
					$JSON_PARAS_TUMOR $JSON_PARAS_TUMOR \
					$DEPTH_CUTOFF_TUMOR $DEPTH_CUTOFF_TUMOR \
					$WT_CUTOFF_TUMOR $HOM_CUTOFF_TUMOR \
					$WT_CUTOFF_TUMOR $HOM_CUTOFF_TUMOR
			fi
		done		
	done
fi

if [ "$NORMAL_NORMAL" == "True" ]; then
	# QC the Tumor runs with the normal runs.
	normal_runs="`find ${SAMPLE_DIR}/Normal/N-[0-9_]* -maxdepth 0 -type d 2>/dev/null`"
	for normal_run1 in $normal_runs; do
		n1_num=`echo "$normal_run1" | grep -Eo "[0-9]$"`
		for normal_run2 in $normal_runs; do
			n2_num=`echo "$normal_run2" | grep -Eo "[0-9]$"`
			if [ $n1_num -lt $n2_num ]; then
				# Make the QC table for this combination.
				QC_2Runs $normal_run1 $normal_run2 \
					$JSON_PARAS_NORMAL $JSON_PARAS_NORMAL \
					$DEPTH_CUTOFF_NORMAL $DEPTH_CUTOFF_NORMAL \
					$WT_CUTOFF_NORMAL $HOM_CUTOFF_NORMAL \
					$WT_CUTOFF_NORMAL $HOM_CUTOFF_NORMAL
			fi
		done		
	done
fi
# ---------------------------------- END Somatic ---------------------------------------

# Now generate the QC spreadsheet.
het_to_hom_cutoff=6
wt_to_hom_cutoff=3
#python2.7 QC_stats.py QC_Coverage_Info.csv
#python2.7 QC_generateSheets.py master.csv master.xlsx -mr $het_to_hom_cutoff $wt_to_hom_cutoff 
echo "$SAMPLE_DIR Finished QC"

