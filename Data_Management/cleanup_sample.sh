#! /bin/bash

# Script to make the QC json files

if [ $# -lt 1 ]; then
	echo "USAGE: bash cleanup_sample.sh /path/to/project"
	exit 8
fi

PROJECT_DIR="$1"

# $1 /path/to/run
function cleanup_run {
	echo "	Cleaning run $1"
	# Cleanup this run
	for file in `ls $1 | grep -v ".vcf" | grep -v "amplicon.cov.xls" | grep -v ".json" | grep -v ".pdf"`; do 
		echo "		rm ${1}/${file}"
		rm -r ${1}/$file
	done
}

# ls -l will list the files in the dir if it's a dir so don't use this.
# $1 /path/to/file
function remove_file {
	space=`ls -l $1 | awk '{print $5}'`
	let total_space+=space
	echo "		rm ${1}"
	rm -r ${1}
}

samples=`find ${PROJECT_DIR}/* -maxdepth 0 -type d`

for sample in $samples; do
	sample_name=`basename $sample`
	if [ "`find /home/ionadmin/jeff/Einstein_passVCF/${sample_name}.vcf -maxdepth 0 -type f 2>/dev/null`" ]; then
		echo "Cleaning sample $sample_name"

		# delete the extra amp.cov.xls if there is one
		runs=`find ${sample}/Run* -maxdepth 0 -type d`
		for run in $runs; do
			num_pdf_files=`find ${run}/*.pdf | wc -l`
			if [ "$num_pdf_files" -gt "1" ]; then
				echo "		rm ${run}/backupPDF.pdf"
				rm ${run}/backupPDF.pdf
			fi
			num_amp_files=`find ${run}/*.amplicon.cov.xls | wc -l`
			if [ "$num_amp_files" -gt "1" ]; then
				echo "		rm ${run}/rawlib.amplicon.cov.xls"
				rm ${run}/rawlib.amplicon.cov.xls
			fi
			if [ "`find ${run}/tvc*_out -maxdepth 0 -type d 2>/dev/null`" ]; then
				mv ${run}/tvc*_out/TSVC_variants.vcf $run 2>/dev/null
				echo "		rm ${run}/tvc*_out"
				rm -r ${run}/tvc*_out
			fi
			if [ "`find ${run}/cov_full -maxdepth 0 -type d 2>/dev/null`" ]; then
				mv ${run}/cov_full/*.amplicon.cov.xls $run 2>/dev/null
				echo "		rm ${run}/cov_full"
				rm -r ${run}/cov_full
			fi
		done

		#cleanup the QC dir
		for file in `ls ${sample}/QC | grep -v ".vcf" | grep -v "amplicon.cov.xls" | grep -v ".json" | grep -v ".pdf"`; do 
			echo "		rm ${sample}/QC/${file}"
			rm -r ${sample}/QC/${file}
		done

		if [ "`find ${sample}/Merged -maxdepth 0 -type d 2>/dev/null`" ]; then
			echo "	$sample_name has a Merged dir"
			# Cleanup the Merged dir
			if [ "`find ${sample}/Merged/tvc*_out -maxdepth 0 -type d 2>/dev/null`" ]; then
				mv ${sample}/Merged/tvc*_out/TSVC_variants.vcf ${sample}/Merged 2>/dev/null
				echo "		rm ${sample}/Merged/tvc*_out"
				rm -r ${sample}/Merged/tvc*_out
			fi
			if [ "`find ${sample}/Merged/cov_full -maxdepth 0 -type d 2>/dev/null`" ]; then
				mv ${sample}/Merged/cov_full/*.amplicon.cov.xls ${sample}/Merged 2>/dev/null
				echo "		rm ${sample}/Merged/cov_full"
				rm -r ${sample}/Merged/cov_full
			fi
			runs=`find ${sample}/Run* -maxdepth 0 -type d`
			for run in $runs; do
				cleanup_run $run
			done
		elif [ "`find ${sample}/BadRuns -maxdepth 0 -type d 2>/dev/null`" ]; then
			echo "	$sample_name has a BadRuns dir"
			runs=`find ${sample}/BadRuns/Run* -maxdepth 0 -type d`
			for run in $runs; do
				cleanup_run $run
				num_pdf_files=`find ${run}/*.pdf | wc -l`
				if [ "$num_pdf_files" -gt "1" ]; then
					echo "		rm ${run}/backupPDF.pdf"
					rm ${run}/backupPDF.pdf
				fi
				# delete the extra amp.cov.xls if there is one
				num_amp_files=`find ${run}/*.amplicon.cov.xls | wc -l`
				if [ "$num_amp_files" -gt "1" ]; then
					echo "		rm ${run}/rawlib.amplicon.cov.xls"
					rm ${run}/rawlib.amplicon.cov.xls
				fi
			done
		else
			echo "	$sample_name no Merged dir"
			runs=`find ${sample}/Run* -maxdepth 0 -type d`
			for run in $runs; do
				# if this is not the final vcf file, clean it up
				if [ "`diff ${run}/*.vcf /home/ionadmin/jeff/Einstein_passVCF/${sample_name}.vcf`" ]; then
					cleanup_run $run
				else
					echo "	$run is the final"
				fi
			done
		fi
	fi
done
