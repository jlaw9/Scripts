#! /bin/bash

# Goal: Run coverage analysis and TVC on a BAM file 
# It would be great to allow you to either specify a sample, plate, or project, or a csv.

# Parameters for Qsub:
#$ -S /bin/bash
#$ -N TVC
#$ -o tvc.log
#$ -e tvc.log
#$ -q all.q
#$ -cwd
#$ -V


# Default parameters
REF_FASTA="/results/referenceLibrary/tmap-f3/hg19/hg19.fasta"
VARIANT_CALLER_DIR="/results/plugins/variantCaller"
TVC_VERSION="4.2"

function usage {
cat << EOF
USAGE: bash runtvc.sh <path/to/BAM_File.bam> [OPTIONS]
Quick script to get only the HS positions for the Wales Data Matrix
Options:
	-t | --tvc <path/to/Project_BED> <path/to/tvc_json> 	(region bed file and parameter settings file which will be used by TVC.)
	-th | --tvc_hotspot <path/to/Hotspot.vcf> 	(The hotspot file used to run TVC)
	-o | --output_dir <path/to/Output_Dir>	(Output files will be placed here. Default is the Bam File's directory)
EOF
exit 8
}

#for arguments
if [ $# -lt 3 ]; then # Technically there should be more than 20 arguments specified by the user, but more useful error messages can be displayed below
	usage
fi

RUNNING="Starting using these options: "
counter=0
while :
do
	let "counter+=1"
	# If not enough inputs were given for an option, the while loop will just keep going. Stop it and print this error if it loops more than 100 times
	if [ $counter -gt 100 ]; then
		echo "USAGE: not all required inputs were given for options." 1>&2
		echo "$RUNNING"
		exit 8
	fi
	case $1 in
		*.bam)
			BAM_FILE=$1
			RUNNING="$RUNNING BAM: $1 "
			shift 
			;;
		-t | --tvc)
			RUN_TVC="True"
			BED=$2
			TVC_JSON=$3
			RUNNING="$RUNNING --tvc bed: $2 json: $3 "
			shift 3
			;;
		-th | --tvc_hotspot)
			TVC_HOTSPOT=$2
			RUNNING="$RUNNING --tvc_hotspot: $2 "
			shift 2
			;;
		-o | --output_dir)
			OUTPUT_DIR=$2
			RUNNING="$RUNNING --output_dir: $2 "
			shift 2
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


# Runs TVC, then copies the .vcf file needed, and deletes the rest of the files generated.
mkdir -p ${OUTPUT_DIR}/tvc_out 2>/dev/null
log="${OUTPUT_DIR}/tvc_out/tvc.log"

echo "$BAM_FILE beginning TVC v4.2 w/o the wrapper script at: `date`"
#now run TVC v4.2. 
tvc \
	--output-dir ${OUTPUT_DIR}/tvc_out \
	--output-vcf wo_wrapper_4.2_TSVC_variants.vcf \
	--reference $REF_FASTA \
   	--input-bam $BAM_FILE \
    --target-file $BED \
    --trim-ampliseq-primers \
    --target-file $BED \
    --input-vcf $TVC_HOTSPOT \
    --process-input-positions-only \
    --use-input-allele-only \
	--parameters-file $TVC_JSON \
	>> $log



if [ $? -eq 0 ]; then
	#TVC was successful.
	echo "$BAM_FILE TVC v${TVC_VERSION} finished successfully at: `date`"
	mv ${OUTPUT_DIR}/tvc_out/wo_wrapper_4.2_TSVC_variants.vcf ${OUTPUT_DIR}
	rm -r ${OUTPUT_DIR}/tvc_out
	grep "HEALED" ${OUTPUT_DIR}/wo_wrapper_4.2_TSVC_variants.vcf
else
	# Something went wrong with TVC. Not copying the data.
	echo 1>&2
	echo "--- ERROR: $BAM_FILE TVC v${TVC_VERSION} had a problem. Not copying data ---" 1>&2
	echo "--- See tvc${TVC_VERSION}_out/log.out for details of what happened ---" 1>&2
fi

