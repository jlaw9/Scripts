#! /bin/bash

# Script to re-run TVC on all of the Wales samples

#Qsub arguments:

#$ -S /bin/bash
#$ -cwd
#$ -N TVC_Cov_SEGA
#$ -o run_SEGA_tvc_results.txt
#$ -e run_SEGA_tvc_results.txt
#$ -q all.q
#$ -V

USAGE='USAGE: bash Run_Wales_TVC.sh <path/to/Project_Dir>'

#for arguments
if [ $# -eq 1 ]; then
	PROJECT_DIR=$1
else
	echo $USAGE
	exit 8
fi

# Now check the files to see if the dir exists
if [ ! -d $PROJECT_DIR ]; then
	echo "Project dir: $PROJECT_DIR not found"
	exit 4
fi

# Paths to bed files and JSON parameter settings files are specified here
SOFTWARE_ROOT="/home/ionadmin/software"
BED_DIR="/rawdata/project_data/BED_files/"
PROJECT_BED="$BED_DIR/Wales/IAD000004_Amplicons.bed"
JSON="/rawdata/project_data/parameter_files/germline_high_stringency_pgm.json"

echo "$PROJECT_DIR running TVC on the bam files"

# Search through the different directories, and if there is a directory that doesn't have a .cov.xls or .vcf, run Coverage analysis and/or TVC
samples=`find ${PROJECT_DIR}/*/* -maxdepth 0 -type d`

for sample in $samples; do
	if [ "`find ${sample}/Merged -maxdepth 0 -type d 2>/dev/null`" ]; then
		bam_file=`find ${sample}/Merged/*.bam -maxdepth 0 -type f`
	else
		bam_file=`find ${sample}/*.bam -maxdepth 0 -type f`
	fi
		# call the runTVC_and_Cov_Analysis.sh script giving the normal json parameters
	bash ${SOFTWARE_ROOT}/scripts/runTVC_COV.sh \
		$bam_file \
		--tvc $PROJECT_BED $JSON \
		--output_dir ${sample}/Analysis_files/Wales_HS/ \
		--tvc_hotspot /rawdata/project_data/Wales/Wales_Hotspot.vcf \
		--forced

		#--cleanup \
	#mv ${sample}/Analysis_files/4.2*.vcf ${sample}/Analysis_files/From_Wales_HS.vcf
	exit
done

echo "$PROJECT_DIR Finished"
