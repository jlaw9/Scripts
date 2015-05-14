#! /bin/bash

# Goal:  Merge and run coverage analysis on the two Samples generated.
# Output:  A mered bam file, and coverage analysis on the merged bam file.

# PARAMETERS:
#USAGE="USAGE: bash merge2bams.sh <Sample_Dir> <Output Directory> <Name_of_merged_bam.bam>"
USAGE="USAGE: bash merger.sh <Sample_Dir>"

if [ $# -gt 0 ];
then
	SAMPLE_DIR=$1
else
	echo $USAGE
	exit 8
fi

if [ ! -d $SAMPLE_DIR ]
then 
	echo "ERROR: $SAMOLE_DIR not found"
	exit 4
fi
if [ ! -f $SAMPLE_DIR/*.bam ]
then
	echo "ERROR: $SAMPLE_DIR has no bam file"
	exit 4
else
	RUN1BAM=`find ${SAMPLE_DIR}/*.bam -maxdepth 0`
fi

# Checks to make sure the new header for the merged.bam file is correct.
# $1: the merged_dir
function checkHeader {
	headerCheck=`grep -Eo 'SM:[a-zA-Z0-9_&/-]*' ${1}/merged.headerCorrected.sam`
	# First maek sure grep found at least two SM: lines (there should be one for each run merged)
	if [ "${#headerCheck}" -lt "2" ]
	then
		echo "ERROR: Fixing the header for $SAMPLE_DIR/Merged/merged_badHeader.bam did not work."
		exit 1
	fi
	# Next, check to make sure everything found by grep matches. If anything doesn't match, quit with an error.
	for check in headerCheck;
	do
		for check2 in headerCheck;
		do
			if [ "$check" != "$check2" ]
			then
				echo "ERROR: Fixing the header for $SAMPLE_DIR/Merged/merged_badHeader.bam did not work."
				exit 1
			fi
		done
	done
}


echo "$SAMPLE_DIR Beginning merging at: `date`"

runs=`find ${SAMPLE_DIR}/Run[0-9] -maxdepth 0 -type d 2>/dev/null`
if [ "${#runs}" -lt "1" ]
then
	echo "There is only one run in $SAMPLE_DIR. Exiting"
	exit 0
fi

echo "java -jar /opt/picard/picard-tools-current/MergeSamFiles.jar \\" > mergeJob.sh
echo "	INPUT=$RUN1BAM \\" >> mergeJob.sh

# Add each run's bam file to mergeJob.sh
for run in $runs;
do
	if [ ! -f ${run}/*.bam ]
	then
		echo "ERROR: $run has no bam file"
		rm mergeJob.sh
		exit 4
	elif [ "`find ${run}/*.bam -maxdepth 0 | wc -l`" -gt "1" ]
	then
		echo "ERROR: $run has more than one bam file. There can only be one bam file in each run's dir"
		rm mergeJob.sh
		exit 4
	else
		RUN_BAM=`find ${run}/*.bam -maxdepth 0`
	fi
		
	echo "	INPUT=$RUN_BAM \\" >> mergeJob.sh
done
echo "	OUTPUT=$SAMPLE_DIR/Merged/merged_badHeader.bam " >> mergeJob.sh
mkdir $SAMPLE_DIR/Merged 2>/dev/null

bash mergeJob.sh 1>/dev/null 2>>errors.txt
if [ "$?" != "0" ]
then
	echo "ERROR: $SAMPLE_DIR something went wrong with merging. Look at mergeJob.sh to see what the command was."
	rm -r $SAMPLE_DIR/Merged 2>/dev/null
	exit 1
fi

merged_dir="$SAMPLE_DIR/Merged"
# Now correct the header and such
#echo "fixing header for ${merged_dir}/merged_badHeader.bam"
samtools view -H ${merged_dir}/merged_badHeader.bam > ${merged_dir}/merged.header.sam 2>&1

# Get just the name of the current sample to write to the header
sample_name=`basename $SAMPLE_DIR`
# Change the SM: tag so that it matches for every run merged. (There should be one SM tag for each run merged)
sed "s/SM:[a-zA-Z0-9_&/-]*/SM:${sample_name}/" ${merged_dir}/merged.header.sam > ${merged_dir}/merged.headerCorrected.sam #2>&1

# Double check that the header is correct.
checkHeader $merged_dir
# If everything checks out, write the new header to merged.bam
samtools reheader ${merged_dir}/merged.headerCorrected.sam ${merged_dir}/merged_badHeader.bam > ${merged_dir}/merged.bam #2>&1

rm ${merged_dir}/merged_badHeader.bam mergeJob.sh 2>/dev/null
echo "$merged_dir finished merging at: `date`"
