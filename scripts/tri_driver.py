#this script is responsible for managing / driving the execution of jobs for Atlas

import glob
import json
import shutil
import os
import logging
import time
import datetime
import fnmatch
from runner import Runner
from template_writer import TemplateWriter

__author__ = 'mattdyer'

#a couple of global variables that we will use
BASE_SAMPLE_DIRECTORY = "/Volumes/HD/mattdyer/Desktop/temp"
BASE_SOFTWARE_DIRECTORY = "/rawdata/software"

class JobManager:

    ## The constructor
    # @param self The object pointer
    # @param outputDirectory The output directory path
    # @param sampleDirectory The sample directory path
    def __init__(self, softwareDirectory, sampleDirectory):
        if(softwareDirectory == ''):
            self.__softwareDirectory = BASE_SOFTWARE_DIRECTORY
        else:
            self.__softwareDirectory = softwareDirectory

        if(sampleDirectory == ''):
            self.__sampleDirectory = BASE_SAMPLE_DIRECTORY
        else:
            self.__sampleDirectory = sampleDirectory

    ## Manage the job by parsing the json and finding which analysis to kick off
    # @param self The object pointer
    # @param json The json analysis string pulled from the database
    # @returns The SGE job id
    def manageJob(self, jobFile):
        #we will want to capture the process exit code and SGE number
        jobNumberSGE = -1

        #load the job file
        jsonData = open(jobFile)
        fileData = json.load(jsonData)
        logging.debug('%s - %s' % (getTimestamp(), fileData))

        #create the output folder
        outputFolder = '%s/%s/%s/%s' %(self.__sampleDirectory, fileData['project'], fileData['sample'], fileData['name'])
        logging.debug('%s - Creating output folder %s' % (getTimestamp(), outputFolder))
        fileData['output_folder'] = outputFolder

        #see if it exists first
        if not os.path.exists(outputFolder):
            os.makedirs(outputFolder)

        #write the job template
        templateWriter = TemplateWriter(outputFolder, self.__softwareDirectory)
        analysisFile = templateWriter.writeTemplate(fileData)

        #now we can pass the job to be executed over to the job runner
        runner = Runner("CommandLine")
        logging.info('%s - Starting %s' % (getTimestamp(), analysisFile))
        fileData['status'] = 'submitted'
        fileData['output_folder'] = outputFolder
        fileData['json_file'] = jobFile

        #update the json
        self.__updateJSON(jobFile, fileData)

        #submit the job to SGE
        sgeJobID = runner.submitToSGE('%s/job.sh' % (outputFolder), fileData)
        fileData['status'] = 'queued'
        fileData['sge_job_id'] = sgeJobID
        logging.info('%s - Submitted to SGE (%i)' % (getTimestamp(), sgeJobID))

        #update the json
        self.__updateJSON(jobFile, fileData)

    ## Update the json file
    # @param self The object pointer
    # @param jobFile The input json job file
    # @param job The json job object
    def __updateJSON(self, jobFile, job):
        #now overwrite the old file
        with open(jobFile, 'w') as newJobFile:
            json.dump(job, newJobFile, sort_keys=True, indent=4)

    ## Get the list of pending jobs
    # @param self The object pointer
    # @returns An array of pending job json files
    def getPendingJobs(self):
        #get all the json files that are in in the sample directories
        logging.debug("%s - Looking for JSON job files in %s/*/*/" % (getTimestamp(), self.__sampleDirectory))
        files = []
        jobsToProcess = []

        #recurse through and find the json files
        for root, dirnames, filenames in os.walk(self.__sampleDirectory):
            for filename in fnmatch.filter(filenames, '*.json'):
                files.append(os.path.join(root, filename))

        #process each of the json files
        for file in files:
            #rename the json file so it won't get picked up by the next thread
            logging.debug('%s - Found %s' % (getTimestamp(), file))
            #shutil.move(file, '%s_read' % file)
            shutil.copy(file, '%s_read' % (file))

            #add the file to the array
            jobsToProcess.append('%s_read' % (file))

        #return the array
        return(jobsToProcess)

## simple method to get a time stamp
# @returns A timestamp
def getTimestamp():
    #get the time / timestamp
    currentTime = time.time()
    timeStamp = datetime.datetime.fromtimestamp(currentTime).strftime('%Y-%m-%d_%H-%M-%S')

    #return the stamp
    return(timeStamp)

#start here when the script is launched
if (__name__ == "__main__"):
    #set up the logging
    logging.basicConfig(level=logging.DEBUG)

    #create the job manager
    jobManager = JobManager('', '')

    #find the pending jobs
    jobsToProcess = jobManager.getPendingJobs()
    logging.info('%s - Found %i analyses to process' % (getTimestamp(), len(jobsToProcess)))

    #process the jobs now
    for job in jobsToProcess:
        logging.info('%s - Working on %s' % (getTimestamp(), job))

        #process the job
        jobManager.manageJob(job)

        #send an email?



