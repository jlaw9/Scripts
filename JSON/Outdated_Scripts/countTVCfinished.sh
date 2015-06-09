#! /bin/bash

# Script to make the QC json files

if [ $# -lt 1 ]; then
	echo "USAGE: bash mkQC_json.sh /path/to/project"
	exit 8
fi

PROJECT_DIR="$1"

samples=`find ${PROJECT_DIR}/* -maxdepth 0 -type d`

for sample in $samples; do
	sample_name=`basename $sample`

	runs=`find ${sample}/Run* -maxdepth 0 -type d`
	for run in $runs; do
		run_name=`basename $run`
	if [  "`find ${run}/4.2*.vcf -maxdepth 0 -type f 2>/dev/null`" -a ! "`find ${run}/tvc*out/TSVC_variants.vcf -maxdepth 0 -type f 2>/dev/null`" ]; then
				echo "$run did attempt tvc"
	fi
            
	#we checked based on *.vcf file, now let's check the json file content

	#echo "check for vcf is fine"
	echo "$run"
	#cd $run 
	#file=`find -name *.json_read  -type f`
	file=`find ${run}/*.json_read  -type f`
	echo $file 

    if [ "`grep "finished" $file`" ]; then
            echo "finished TVC_COV"
	else
		echo "did not finish TVC_COV"
	fi

    done

done
