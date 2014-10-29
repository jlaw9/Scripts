#! /bin/bash

#Qsub arguments:

#$ -S /bin/bash
#$ -cwd
#$ -N Push_Data
#$ -o Files/push_results.log
#$ -e Files/push_results.log
#$ -V


# This script takes a Comma Separated file and calls the push script for each run of each sample.

#Arguments
USAGE="USAGE: bash start_Push.sh <ionadmin@ipaddress> </destination/path> <pushFiles.csv> <push_results.csv>"
USER_SERVER=''
DEST_PATH=''
PROJECT_FILE=''
OUT=''
BACKUP_PATH="/mnt/Charon/archivedReports"

if [ $# -lt 4 ];
then
	echo $USAGE
	exit 8
else
	#first, check the connection of the server.
	ssh -q ${1} exit
	if [ "$?" != "0" ];
	then
	    echo "ERROR: Cannot connect to ${USER_SERVER}" 
	    exit 1
	else
		USER_SERVER=$1
	fi
	# Now check if the input file exists
	if [ ! -r $3 ];
	then
		echo $USAGE
		echo "ERROR: $3 not found or not readable"
		echo
		exit 4
	else
		DEST_PATH=$2
		PROJECT_FILE=$3
		OUT=$4
	fi
fi

# $1: sample, $2 runID, $3 Run# $4: Proton name
function pushData {
	# Normal output will be put into the output csv. Error output will be printed to the screen
	bash push_Data.sh \
		--user_server $USER_SERVER \
		--project_path $DEST_PATH \
		--sample $1 \
		--run_id $2 \
		--run $3 \
		--proton_name $4 \
		--backup_path $BACKUP_PATH \
		>> $OUT </dev/null &

	pushPID=$!
	# sleepAndMaybeKill.sh is a bash command that sleeps for the given amount of time, then kills the ProcessID passed to it.
	seconds_to_wait=7200
	bash sleepAndMaybeKill.sh $seconds_to_wait $pushPID >/dev/null 2>&1 &  
    SLEEP_AND_MAYBE_KILL_PID=$!   
    wait $pushPID > /dev/null 2>&1
    if [ $? -eq 0 ]; then
		# If push_Data.sh succeeded, then stop the sleep and maybe kill script. 
        kill $SLEEP_AND_MAYBE_KILL_PID >/dev/null 2>&1
    else
		echo "push_Data.sh froze for 2 hours at `date`. Restarting it."
		bash push_Data.sh \
			--user_server $USER_SERVER \
			--project_path $DEST_PATH \
			--sample $1 \
			--run_id $2 \
			--run $3 \
			--proton_name $4 \
			--backup_path $BACKUP_PATH \
			>> $OUT </dev/null &
		wait $!
	fi
}

mkdir Json_Files 2>/dev/null

echo "Copying the files listed in $PROJECT_FILE to $USER_SERVER:$DEST_PATH"

# write the header to the output file
echo "Sample,Run,Proton,Rot-ID,Dir Containing Data,TSv,BAM,BAM.bai,Cov,TVC, pdf, Json" > $OUT
#echo "Sample,Run,Proton,RUN-ID,BAM,BAM.bai,Cov,TVC,pdf, Json" > $OUT

no_spaces_file=`tail -n +2 $PROJECT_FILE | sed "s/ //g"` #| sed "s/Neptune/Mercury/g"`

# If everything checks out, then read the csv file line by line, and call push_Data.sh
echo "$no_spaces_file" |
while IFS=',' read sample run server runID flag other; do
	# We'll just copy neptune's info from neptune.
	if [ "$server" == "Pluto" -a "$runID" != "" ]; then
		printf "${sample},$run,$server,${runID}," >> $OUT
		# For every rotid listed in the runID column, copy the needed data.
		pushData $sample $runID Run$run "PLU"

		echo >> $OUT </dev/null
	fi
done

echo "Finished copying samples listed in $PROJECT_FILE"
