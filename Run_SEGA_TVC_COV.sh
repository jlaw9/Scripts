#! /bin/bash

#Qsub arguments:

#$ -S /bin/bash
#$ -cwd
#$ -N TVC_Cov_SEGA
#$ -o run_SEGA_tvc_results.txt
#$ -e run_SEGA_tvc_results.txt
#$ -q all.q
#$ -V


# GOAL: Run TVC and Coverage analysis on all of the BAM files in Radiogenomics.

USAGE='USAGE: bash runRadiogenomics_TVC_Cov.sh <path/to/Project_Dir>'

#for arguments
if [ $# -eq 1 ]; then
	PROJECT_DIR=$1
else
	echo $USAGE
	exit 1
fi

# Now check the files to see if the dir exists
if [ ! -d $PROJECT_DIR ]; then
	echo "Project dir: $PROJECT_DIR not found"
	exit 1
fi

# Paths to bed files and JSON parameter settings files are specified here
BED_DIR="/rawdata/project_data/BED_files/"
MERGED_BED="$BED_DIR/AmpliSeqExome.20131001.designed_merged_detail.bed"
UNMERGED_BED="$BED_DIR/AmpliSeqExome.20131001.designed_unmerged_detail.bed"
PROJECT_BED="$BED_DIR/AmpliSeqExome.20131001.designed.bed"
NORMAL_JSON="/rawdata/project_data/parameter_files/ampliseqexome_germline_highstringency_p1_4.0_20130920_parameters.json"
TUMOR_JSON="/rawdata/project_data/parameter_files/ampliseqexome_somatic_highstringency_p1_4.0_20130920_parameters.json"

echo "$PROJECT_DIR running TVC and Cov analysis on all of the bam files"

# Search through the different directories, and if there is a directory that doesn't have a .cov.xls or .vcf, run Coverage analysis and/or TVC
pairs=`find ${PROJECT_DIR}/* -maxdepth 0 -type d`

for pair in $pairs; do
	# Now loop through the different samples
	normal_bams=`find ${pair}/Normal/N-*/rawlib.bam -maxdepth 0`
	for normal_bam in $normal_bams; do
		bam_dir=`dirname $normal_bam`
		# call the runTVC_and_Cov_Analysis.sh script giving the normal json parameters
		qsub -N "TVC_SEGA" runTVC_and_CovAnalysis.sh \
			$normal_bam \
			--cov $MERGED_BED $UNMERGED_BED \
			--tvc $PROJECT_BED \
			--tvc_json $NORMAL_JSON \
			--output_dir $bam_dir \
			--cleanup \
			--forced
		#exit
	done

	tumor_bams=`find ${pair}/Tumor/T-*/rawlib.bam -maxdepth 0`
	for tumor_bam in $tumor_bams; do
		bam_dir=`dirname $tumor_bam`
		# call the runTVC_and_Cov_Analysis.sh script giving the tumor json parameters
		qsub -N "TVC_SEGA" runTVC_and_CovAnalysis.sh \
			$tumor_bam \
			--cov $MERGED_BED $UNMERGED_BED \
			--tvc $PROJECT_BED \
			--tvc_json $TUMOR_JSON \
			--output_dir $bam_dir \
			--cleanup \
			--forced
	done
done

echo "$PROJECT_DIR Finished"
