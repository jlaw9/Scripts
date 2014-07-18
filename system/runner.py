## @package Runner
#
# This class is responsible for running jobs on the command line

import subprocess
import os
import time

__author__ = 'mattdyer'

class Runner:
    ## The constructor
    # @param self The object pointer
    # @param mode The mode in which jobs will be run (CommandLine or SGE)
    def __init__(self, mode):
        self.__mode = mode

    ## Run a job on the command-line
    # @param self The object pointer
    # @param systemCall The system call to executed
    # @returns The exit status and the output
    def runCommandLine(self, systemCall):
        #run the call and return the status
        returnCode = subprocess.call(systemCall, shell=True)
        return(returnCode)

    ## Run a job on via SGE
    # @param self The object pointer
    # @param systemCall The system call to executed
    # @returns The SGE job number
    def submitToSGE(self, systemCall):
        #submit to SGE and grab the job id
        jobString = subprocess.check_output(systemCall, shell=True)
        tokens = jobString.split(' ')
        return(int(tokens[2]))
