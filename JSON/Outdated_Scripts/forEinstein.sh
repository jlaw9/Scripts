#! /bin/bash

# Goal: go through each Einstein sample dir, create QC sub-dir and then QC json file 

USAGE='USAGE: bash forEinstein.sh <path/to/Project_Dir> <example json file>'

PROJECT_DIR=$1

exampleJson=$2

samples=`find ${PROJECT_DIR}/E* -maxdepth 0 -type d 2>/dev/null`


for sample in $samples 
do
	if [ ! -d ${sample}/QC ]
    then 
		mkdir ${sample}/QC
	fi
    
	echo ${sample}

    python /home/ionadmin/TRI_Scripts/JSON/writeQCJson.py ${sample} $2 
	#exit
done
