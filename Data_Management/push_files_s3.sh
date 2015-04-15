#!/bin/bash

## QSUB variables
## job name
#$ -N job
## log files. -o is output, -e is error
#$ -o job.log
#$ -e job.log
## use the queue all.q. Options: plugin.q, 
#$ -q all.q
## use the current shell variables
#$ -V
## use /bin/bash for the script
#$ -S /bin/bash
## current working dir
#$ -cwd

if [ $# -lt 1 ]; then
	echo "USAGE: bash push_sample_s3.sh /path/to/file /path/for/s3 [/path/to/file  /path/for/s3]+"
	echo "Script to push files to the amazon s3 server. Push as many files as you like."
	exit 8
fi

SAMPLE_DIR="$1"

# Script to push files to the amazon s3 server. This script is called by push_sample_s3.sh
status="pass"
files=("${@}")
i=0
# first loop through the files to make sure they all exist
while [ $i -lt ${#files[@]} ]; do
	echo ${files[${i}]}
	if [ "${files[${i}]}" != "" ]; then
		if [ ! "`find ${files[${i}]} -maxdepth 0 2>/dev/null`" ]; then
			status="failed: ${files[${i}]} was not found!"
			echo $status
		fi
	else
		status="failed: There's a blank file!"
		echo $status
	fi
	let i+=2
done
i=0
if [ "$status" == "pass" ]; then
	# now actually push the files
	while [ $i -lt ${#files[@]} ]; do
		# push the file to the specified location and name on the s3 childhooddiseases bucket. Folders and directories are autmotically created.
		aws s3 cp ${files[${i}]} s3://childhooddiseases/${files[$((i+1))]} 
		#echo "aws s3 cp ${files[${i}]} s3://childhooddiseases/${files[$((i+1))]}" 
		if [ "$?" != "0" ]; then
			status="ERROR: command aws s3 cp ${files[$i]} s3://childhooddiseases/${files[$((i+1))]} failed!!"
		fi
		let i+=2
	done
fi

echo "Files ${files[@]} finished with a status of $status"
echo "Files ${files[@]} finished with a status of $status" | ssmtp -vvv jlaw@childhooddiseases.org  2>&1 1>/dev/null
