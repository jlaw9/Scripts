#! /bin/bash

#Qsub arguments:

#$ -S /bin/bash
#$ -cwd
#$ -N QC_all_SEGA_samples
#$ -o QC/QC_Out_Files/run_sega_qc_results.txt
#$ -e QC/QC_Out_Files/run_sega_qc_results.txt
#$ -q all.q
#$ -V


# GOAL: Run TVC and Coverage analysis on all of the BAM files in Radiogenomics.

USAGE='USAGE: bash runRadiogenomics_TVC_Cov.sh <path/to/Project_Dir>'

#for arguments
if [ $# -eq 1 ];
then
	PROJECT_DIR=$1
else
	echo $USAGE
	exit 1
fi

# Now check the files to see if the dir exists
if [ ! -d $PROJECT_DIR ]
then
	echo "Project dir: $PROJECT_DIR not found"
	exit 1
fi

# Paths to bed files and JSON parameter settings files are specified here
SOFTWARE_DIR="/home/ionadmin/software"
QC_SCRIPTS="${SOFTWARE_DIR}/scripts/QC/SEGA_QC"
PROJECT_BED="/rawdata/project_data/BED_files/AmpliSeqExome.20131001.designed.bed"
CDS_BED="/rawdata/project_data/BED_files/CDSonly.bed"
NORMAL_JSON="/rawdata/project_data/parameter_files/ampliseqexome_germline_highstringency_p1_4.0_20130920_parameters.json"
TUMOR_JSON="/rawdata/project_data/parameter_files/ampliseqexome_somatic_highstringency_p1_4.0_20130920_parameters.json"

echo "$PROJECT_DIR running QC on all of the samples "
echo

# Search through the different directories, and if there is a directory that doesn't have a .cov.xls or .vcf, run Coverage analysis and/or TVC
samples=`find ${PROJECT_DIR}/ES2 -maxdepth 0 -type d`

for sample in $samples; do
	sample_name=`basename $sample`

	#bash ${QC_SCRIPTS}/QC_sample.sh \
	qsub -N QC_$sample_name ${QC_SCRIPTS}/QC_sample.sh \
		--sample_dir $sample \
		--all_tumor_normal $NORMAL_JSON 13 .2 .8 $TUMOR_JSON 30 .1 .7 \
		--bed $PROJECT_BED \
		--amp_cov_cutoff 30 \
		--cds_bed $CDS_BED \
		--subset_chr chr1 \
		--no_run_info

done

echo
echo "$PROJECT_DIR Finished running QC"
