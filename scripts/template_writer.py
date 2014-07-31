__author__ = 'mattdyer'

#This class is responsible for writing the different job wrappers use at TRI
class TemplateWriter:

    ## The constructor
    # @param self The object pointer
    # @params outputDirectory The output directory
    # @param softwareDirectory The software root directory
    def __init__(self, outputDirectory, softwareDirectory):
        #save the output directories
        self.__outputDirectory = outputDirectory
        self.__softwareDirectory = softwareDirectory

    ## Write the analysis template
    # @param self The object pointer
    # @param job The json job object
    # @returns A string to the shell script file to be run
    def writeTemplate(self, job):
        #create the output file
        outputFile = '%s/job.sh' % (self.__outputDirectory)
        fileHandle = open(outputFile, 'w')

        #now depending on the analysis time, add the content we need
        if job['analysis']['type'] == 'qc_tvc':
            #we want to merge, QC, then call variants
            self.__writeHeader(job, fileHandle)
            self.__writeStatusChange('running', job['json_file'], fileHandle, False)
            self.__writeCovTVCTemplate(job, fileHandle)
            self.__writeStatusChange('finished', job['json_file'], fileHandle, True)
        elif job['analysis']['type'] == 'qc_compare':
            print 'hit'
            self.__writeHeader(job, fileHandle)
            self.__writeStatusChange('running', job['json_file'], fileHandle, False)
            self.__writeQCCompareTemplate(job, fileHandle)
            self.__writeStatusChange('finished', job['json_file'], fileHandle, True)

        #close the file handle
        fileHandle.close()

        #return the file string
        return(outputFile)

    ## Write the header stuff for a job
    # @param self The object pointer
    # @param job The json job object
    # @param file The file handle
    def __writeHeader(self, job, fileHandle):
        #this is just a dummy holder for now
        fileHandle.write('#! /bin/bash\n')
        fileHandle.write('#$ -wd %s\n' % self.__outputDirectory)
        fileHandle.write('#$ -N %s.%s.%s\n' % (job['project'], job['sample'], job['name']))
        fileHandle.write('#$ -V\n')
        fileHandle.write('#$ -S /bin/bash\n\n')

    ## Write the code for merging BAM files
    # @param self The object pointer
    # @param job The json job object
    # @param file The file handle
    def __writeMergeTemplate(self, job, fileHandle):
        #create a seperate job for each file in the directory
        print ''

    ## Write the code for updating the status in the JSON file
    # @param self The object pointer
    # @param status The json job object
    # @param jsonFile The json file to update the status in
    # @param file The file handle
    # @param wrap Boolean of whether or not to wrap the status
    def __writeStatusChange(self, status, jsonFile, fileHandle, wrap):
        #set the status and wrap if requested
        if not wrap:
            fileHandle.write('python %s/scripts/update_json.py -j %s -s %s\n' % (self.__softwareDirectory, jsonFile, status))
        else:
            fileHandle.write('if [ $? -ne 0 ]; then\n')
            fileHandle.write('\tpython %s/scripts/update_json.py -j %s -s %s\n' % (self.__softwareDirectory, jsonFile, "failed"))
            fileHandle.write('else\n')
            fileHandle.write('\tpython %s/scripts/update_json.py -j %s -s %s\n' % (self.__softwareDirectory, jsonFile, status))
            fileHandle.write('fi\n')


    ## Write the code for running coverage analysis and tvc
    # @param self The object pointer
    # @param job The json job object
    # @param file The file handle
    def __writeCovTVCTemplate(self, job, fileHandle):
        #default is to not flag dups
        dupFlag = '--remove_dup_flags'

        #see if settings want to mark dups though
        if 'mark_dups' in job['analysis']['settings']:
            #if it is set to true, then we change the flag
            if job['analysis']['settings']['mark_dups'] == 'true':
                print 'here'
                dupFlag = '--flag_dups'

        #default is AmpliSeq for coverage analysis
        coverageAnalysisFlag = '--cov_ampliseq'

        #see if the settings say targetseq
        if 'capture_type' in job['analysis']['settings']:
            #if it is set to true, then we change the flag
            if job['analysis']['settings']['capture_type'].lower() == 'targetseq' or job['analysis']['settings']['capture_type'].lower() == 'target_seq':
                coverageAnalysisFlag = '--cov_targetseq'

        for file in job['analysis']['files']:
            fileHandle.write('bash %s/scripts/runTVC_COV.sh --ptrim PTRIM.bam --cleanup %s %s --cov %s %s --tvc %s --tvc %s --output_dir %s %s/%s\n' % (self.__softwareDirectory, dupFlag, coverageAnalysisFlag, job['analysis']['settings']['qc_merged_bed'], job['analysis']['settings']['qc_unmerged_bed'], job['analysis']['settings']['tvc_bed'], job['analysis']['settings']['tvc_parameter_json'], job['output_folder'], job['output_folder'], file))

    ## Write the code for running qc comparisons
    # @param self The object pointer
    # @param job The json job object
    # @param file The file handle
    def __writeQCCompareTemplate(self, job, fileHandle):
        #default is to analyze all chromsomes
        chrFlag = '-chr chr1'

        if job['analysis']['settings']['analyze_all_chromosomes'] == 'true':
            chrFlag = ''

        #let's check the type
        if job['analysis']['settings']['type'] == 'germline':
            #germline run
            fileHandle.write('bash %s/scripts/QC/QC_sample.sh --beg_bed %s --end_bed %s -cl -s %s/%s/%s -g %s %s %s %s -a %s -b %s %s\n' % (self.__softwareDirectory, job['analysis']['settings']['beg_bed'], job['analysis']['settings']['end_bed'], job['sample_folder'], job['project'], job['sample'], job['analysis']['settings']['tvc_parameter_json'], job['analysis']['settings']['min_base_coverage'], job['analysis']['settings']['wt_cutoff'], job['analysis']['settings']['hom_cutoff'], job['analysis']['settings']['min_amplicon_coverage'], job['analysis']['settings']['cds_bed'], chrFlag))
        #add other types later



    ## Write the code for running TVC
    # @param self The object pointer
    # @param job The json job object
    # @param file The file handle
    def __writeTVCTemplate(self, job, fileHandle):
        #this is just a dummy holder for now
        print ''