#!/bin/bash

# Script to push files to the amazon s3 server

if [ $# -lt 1 ]; then
	echo "USAGE: bash push_sample_s3.sh /path/to/project"
	exit 8
fi

PROJECT_DIR="$1"

samples=`find ${PROJECT_DIR}/* -maxdepth 0 -type d`

for sample in $samples; do
	sample_name=`basename $sample`
	# only push samples that have finished the run or merging process.
	if [ "`find /home/ionadmin/jeff/Einstein_passVCF/${sample_name}.vcf -maxdepth 0 -type f 2>/dev/null`" ]; then
		echo "pushing sample $sample_name"

		final_dir=""
		# check to see if this sample has a merged dir.
		if [ "`find ${sample}/Merged -maxdepth 0 -type d 2>/dev/null`" ]; then
			final_dir="${sample}/Merged"
			echo "	$sample_name has a Merged dir"
		else
			for run in `find ${sample}/Run* -maxdepth 0 -type d`; do
				# if there is no difference between this vcf file and the final file, then push it.
				if [ ! "`diff ${run}/*.vcf /home/ionadmin/jeff/Einstein_passVCF/${sample_name}.vcf`" ]; then
					final_dir="$run"
				fi
			done
		fi

		if [ "$final_dir" != "" ]; then
			# only one file should be matched for each of these commands
			# TODO need to fix the vcf check
			if [ "`find $final_dir/*TSVC_variants.vcf -maxdepth 0 -type f 2>/dev/null`" ]; then
				echo "pushing $final_dir"
				vcf=`find $final_dir/*TSVC_variants.vcf -maxdepth 0 -type f 2>/dev/null | head -n 1`
				vcf2="Einstein/${sample_name}/${sample_name}.vcf"

				cov=`find $final_dir/*.amplicon.cov.xls -maxdepth 0 -type f 2>/dev/null | head -n 1`
				cov_name=`find $final_dir/*.amplicon.cov.xls -type f -printf "%f\n"` 
				cov2="Einstein/${sample_name}/${cov_name}"

				bam=`find $final_dir/*.bam -maxdepth 0 -type f 2>/dev/null | grep -v "PTRIM" | head -n 1`
				bam_name=`find $final_dir/*.bam -type f -printf "%f\n" | grep -v "PTRIM"` 
				bai="$bam.bai"
				bam2="Einstein/${sample_name}/${bam_name}"
				bai2="$bam2.bai"

				json=''
				json2=''
				if [ "`find $final_dir/*.json* -maxdepth 0 -type f 2>/dev/null`" ]; then
					json=`find $final_dir/*.json* -maxdepth 0 -type f 2>/dev/null | head -n 1`
					json2="Einstein/${sample_name}/${sample_name}.json"
				fi
				# now push this sample to s3
				qsub -N push_$sample_name -o push_merged.log -e push_merged.log /home/ionadmin/TRI_Scripts/Data_Management/push_files_s3.sh $vcf $vcf2 $cov $cov2 $bam $bam2 $bai $bai2 $json $json2
				#echo "qsub -N push_$sample_name -o push_merged.log -e push_merged.log /home/ionadmin/TRI_Scripts/Data_Management/push_files_s3.sh $vcf $vcf2 $cov $cov2 $bam $bam2 $bai $bai2 $json $json2"
				# this is a test
				#bash push_files_s3.sh $vcf $vcf2 $cov $cov2 $bam $bam2 $bai $bai2 $json $json2
			fi
		else
			echo "Not pushing $sample"
		fi
	fi
done
