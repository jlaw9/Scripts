#this script is responsible for managing / driving the execution of jobs for Atlas

import psycopg2
import json
import os
from runner import Runner

__author__ = 'mattdyer'

#a couple of global variables that we will use
BASE_OUTPUT_DIRECTORY = "/Volumes/HD/mattdyer/Desktop"
UNIPROT_FILE = "/Volumes/HD/mattdyer/Documents/Work/LAM/Data/sprot_uniprot_seq.txt"
BACKGROUND_FILE = "/Volumes/HD/mattdyer/Documents/Work/LAM/programming/10000_background.txt"


class JobManager:
    __databaseName = ""
    __databaseURL = ""
    __databaseUser = ""
    __databasePassword = ""

    ## The constructor
    # @param self The object pointer
    # @param databaseName The database name
    # @param databaseURL The database URL
    # @param databaseUser The user to connect to the database as
    # @param databasePassword The user password to use while connecting to the db
    def __init__(self, databaseName, databaseURL, databaseUser, databasePassword):
        self.__databaseName = databaseName
        self.__databaseURL = databaseURL
        self.__databaseUser = databaseUser
        self.__databasePassword = databasePassword

    ## Manage the job by parsing the json and finding which analysis to kick off
    # @param self The object pointer
    # @param json The json analysis string pulled from the database
    # @returns The SGE job id
    def manageJob(self, id, name, jsonString):
        #we will want to capture the process exit code and SGE number
        jobNumberSGE = -1
        exitStatus = 1

        #parse the json string
        parameters = json.loads(jsonString)

        #determine which type of job we are running
        analysisType = parameters["analysis_type"]

        #build the command-line call
        commandLine = ""

        #see if output directory exists, if not create it
        output_directory = "%s/%s" %  (BASE_OUTPUT_DIRECTORY, id)
        if(not os.path.exists(output_directory)):
            os.makedirs(output_directory)

        #single sample transposon
        if(analysisType == "transposon_single_sample"):
            read_coverage_minimum = parameters["settings"]["read_coverage_minimum"]
            read_size_minimum = parameters["settings"]["read_size_minimum"]
            maximum_distance = parameters["settings"]["maximum_distance"]
            output_file = "%s.xls" % (name)

            commandLine = "/Volumes/HD/mattdyer/Documents/Work/LAM/programming/transposon_single_sample.pl -uniprot_file \"%s\" -background_file \"%s\" -min_coverage %s -min_size %s -max_distance %s -output_directory \"%s\" -output_file \"%s\"" % (UNIPROT_FILE, BACKGROUND_FILE, read_coverage_minimum, read_size_minimum, maximum_distance, output_directory, output_file)

            #now add the files
            for file in parameters["files"]:
                commandLine += " -file=\"%s\"" % (file)

        #now we can pass the job to be executed over to the job runner
        runner = Runner("CommandLine")
        self.setStatus(id, "Running", jobNumberSGE)
        exitStatus = runner.runCommandLine(commandLine)

        #will update this when we cut over to SGE on the Torrent Server
        if(not exitStatus == 0):
            self.setStatus(id, "Failed", jobNumberSGE)
        else:
            self.setStatus(id, "Complete", jobNumberSGE)

    ## Set the status of a job
    # @param self The object pointer
    # @param status The status of the job
    def setStatus(self, id, status, jobNumberSGE):
        #create the connection
        databaseConnection = psycopg2.connect(host=self.__databaseURL, database=self.__databaseName, user=self.__databaseUser, password=self.__databasePassword)

        #create the cursor so we can database operations
        databaseCursor = databaseConnection.cursor()

        #change what we need to change
        databaseCursor.execute("UPDATE analysis_analysis SET sge_job_number=\'%d\' WHERE id=\'%d\'" % (int(jobNumberSGE), int(record[0])))
        databaseCursor.execute("UPDATE analysis_analysis SET status=\'%s\' WHERE id=\'%d\'" % (status, int(record[0])))
        databaseConnection.commit()

        #close the db cursor and connection
        databaseCursor.close()
        databaseConnection.close()

    ## Get the list of pending jobs
    # @param self The object pointer
    # @returns An array of pending jobs
    def getPendingJobs(self):
        #create the connection
        databaseConnection = psycopg2.connect(host=self.__databaseURL, database=self.__databaseName, user=self.__databaseUser, password=self.__databasePassword)

        #create the cursor so we can database operations
        databaseCursor = databaseConnection.cursor()

        #run a query
        databaseCursor.execute("SELECT * FROM analysis_analysis")
        records = databaseCursor.fetchall()

        #close the db cursor and connection
        databaseCursor.close()
        databaseConnection.close()

        #return the records
        return(records)

#start here when the script is launched
if (__name__ == "__main__"):
    #create the job manager
    jobManager = JobManager("Atlas", "127.0.0.1", "admin", "temp123")
    records = jobManager.getPendingJobs()

    #loop of the results
    for record in records:
        #check the status as we are only interested in jobs that are pending
        if (record[6] == "Pending"):
            #strip the unicode stuff from teh json string
            jsonString = record[5].replace("u'", "\"")
            jsonString = jsonString.replace("'", "\"")

            #strip out white spaces in the name
            name = record[1].replace("\s+", "_")

            #pass the parameters over to the job manager to start the job
            jobManager.manageJob(record[0], name, jsonString)




