#this script is responsible for managing / driving the execution of jobs for Atlas

import os
import logging
import time
import datetime
import shutil
import glob
from optparse import OptionParser

__author__ = 'mattdyer'

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

    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-f', '--folder', dest='folder', help='The folder to clean up')
    parser.add_option('-s', '--sample', dest='sample', help='The sample name')
    parser.add_option('-r', '--run', dest='run', help='The run name')
    (options, args) = parser.parse_args()

    # now lets clean things up
    logging.debug('%s - Cleaning up %s' % (getTimestamp(), options.folder))

    #create a temp folder that we can store
    tempFolder = '%s/%s' % (options.folder, '.temp')
    if(os.path.isdir(tempFolder)):
        shutil.rmtree(tempFolder)

    os.mkdir(tempFolder)

    #now we can move things there that we want to keep
    #first lets move the VCF
    #if(os.path.isfile('%s/tvc_out/TSVC_variants.vcf' % (options.folder))):
        #logging.debug('%s - Copying %s to temp' % (getTimestamp(), '%s/tvc_out/TSVC_variants.vcf' % (options.folder)))
        #shutil.move('%s/tvc_out/TSVC_variants.vcf' % (options.folder), tempFolder)

    #now the PDF report
    if(os.path.isfile('%s/backupPDF.pdf' % (options.folder))):
        logging.debug('%s - Copying %s to temp' % (getTimestamp(), '%s/backupPDF.pdf' % (options.folder)))
        shutil.move(('%s/backupPDF.pdf') % (options.folder), tempFolder)

    #now the BAM file
    if(os.path.isfile('%s/rawlib.bam' % (options.folder))):
        logging.debug('%s - Copying %s to temp' % (getTimestamp(), '%s/cov_full/rawlib.bam' % (options.folder)))
        shutil.move(('%s/rawlib.bam') % (options.folder), tempFolder)

    #now the coverage XLS, need to check two locations
    #first see if we have the cov_full folder
    #if(os.path.isfile('%s/cov_full/rawlib.amplicon.cov.xls' % (options.folder))):
    #    logging.debug('%s - Copying %s to temp' % (getTimestamp(), '%s/cov_full/rawlib.amplicon.cov.xls' % (options.folder)))
    #    shutil.move(('%s/cov_full/rawlib.amplicon.cov.xls') % (options.folder), tempFolder)
    #else:
        #other wise, just grab any XLS that may be floating around
        #files = glob.glob('%s/*.xls' % (options.folder))

        #there should be only one
        #if len(files) == 1:
            #move the file
            #logging.debug('%s - Copying %s to temp' % (getTimestamp(), files[0]))
            #shutil.move(files[0], tempFolder)

        #else:
            #print warning
            #logging.warning('%s - Multiple XLS files found in %s' % (getTimestamp(), options.folder))

    #finally grab the json file
    files = glob.glob('%s/*.json*' % (options.folder))

    for file in files:
        logging.debug('%s - Copying %s to temp' % (getTimestamp(), file))

        if '_read' in file:
            tokens = file.split('/')
            fileNew = tokens[len(tokens)-1]
            fileNew = fileNew.replace('_read','')
            shutil.move(file, '%s/%s' % (tempFolder, fileNew))
        else:
            shutil.move(file, tempFolder)

    #now just delete everything else
    files = glob.glob('%s/*' % (options.folder))

    for file in files:
        logging.debug('%s - Deleting %s' % (getTimestamp(), file))

        if(os.path.isfile(file)):
            os.remove(file)
        else:
            shutil.rmtree(file)

    #move the hidden folder contents back
    files = glob.glob('%s/*' % (tempFolder))

    for file in files:
        logging.debug('%s - Copying %s to folder' % (getTimestamp(), file))
        shutil.move(file, options.folder)

    #remove the hidden dir
    shutil.rmtree(tempFolder)






