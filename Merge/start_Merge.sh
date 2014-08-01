#! /bin/bash

# Goal: Navigate a project Dir by plate, then by sample. Merge all of the multiple runs for each sample

USAGE='USAGE: bash start_Merge.sh <path/to/Project_Dir>'

#for arguments
if [ $# -gt 0 ];
then
	PROJECT_DIR=$1
	PROJECT_BED='/rawdata/project_data/BED_files/Wales/IAD000004_Amplicons.bed'
	MERGED_BED='/rawdata/project_data/BED_files/Wales/Merged/IAD000004_Amplicons_mergedDetail.bed'
	UNMERGED_BED='/rawdata/project_data/BED_files/Wales/Unmerged/IAD000004_Amplicons_unmergedDetail.bed'
else
	echo $USAGE
	exit 1
fi

# Now check the files to see if they exist
if [ ! -d $PROJECT_DIR ]
then
	echo "ERROR: Project Dir: $PROJECT_DIR not found"
	exit 4
elif [ ! -r $PROJECT_BED -o ! -r $MERGED_BED -o ! -r $UNMERGED_BED ]
then
	echo "ERROR: Problem with BED file paths."
	exit 4
fi

# ---------------------------------------
# ------ PROGRAM STARTS HERE ------------
# ---------------------------------------


echo "Merging multiple runs of $PROJECT_DIR"
# find all of the plates in the given project_dir. (case1, control1, etc.)
plates=`find ${PROJECT_DIR}/[a-z]*[0-9] -maxdepth 0 -type d 2>/dev/null`

# Search through the different plates and samples to find the samples with multiple runs. 
for plate in $plates;
do
	# find all of the samples within that plate (A01, A02 etc)
	samples=`find ${plate}/[A-Z][0-9][0-9] -maxdepth 0 -type d 2>/dev/null`

	# Now loop through the different samples
	for sample in $samples;
	do
		if [ ! -d ${sample}/Merged ]
		then
			num_runs=`find ${sample}/Run[0-9] -maxdepth 0 -type d 2>/dev/null | wc -l`
			if [ "$num_runs" -gt "0" ]
			then
				# Merge all of the runs for this sample. merger.sh also prepares the bam file's headers and such for coverage analysis and tvc
#				rm -r ${sample}/Merged 2>/dev/null
				bash merger.sh $sample
				if [ "$?" != "0" ]
				then
					echo "ERROR: $sample had a problem merging. Not running TVC or Cov Analysis."
				else
					#run Coverage Analysis and TVC on the merged bam file
					bash ~/software/Tools/runTVC_and_CovAnalysis.sh \
						--bam_dir ${sample}/Merged \
						--cov $MERGED_BED $UNMERGED_BED \
						--tvc $PROJECT_BED \
						--cleanup

					if [ "$?" == "0" ]
					then
						# Cleanup the temp files used to fix the header.
						rm ${sample}/Merged/*.sam 2>/dev/null
					fi
				fi
			fi
		else
			echo "$sample runs have already been merged"
		fi
	done
done

echo "Finished merging BAM files for $PROJECT_DIR"
