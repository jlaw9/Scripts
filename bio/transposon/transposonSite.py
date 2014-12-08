## @package TransposonSite
#
# This class is responsible for managing data for a transposon site

import unittest

__author__ = 'mattdyer'

class TransposonSite:
    __codingCoverage = {}
    __reverseCoverage = {}
    __samples = {}
    __distance = 0

    ## The constructor
    # @param self The object pointer
    # @param distance The distance of the site from the gene, or if in an exon or intron, the exon / intron number
    def __init__(self, distance):
        #set up the new object
        self.__codingCoverage = {}
        self.__reverseCoverage = {}
        self.__distance = distance

    ## Get the distance information
    # @param self The object pointer
    # @returns The distance of the site from the gene, or if in an exon or intron, the exon / intron number
    def getDistance(self):
        return(self.__distance)

    ## Add coverage for coding direction
    # @param self The object pointer
    # @param sample The sample where the coverage was seen
    # @param coverage The amount of coverage to add
    def addCodingCoverage(self, sample, coverage):
        #see if sample exists
        if sample in self.__codingCoverage:
            #add to the coverage if it does
            self.__codingCoverage[sample] += coverage
        else:
            #create the entry if it doesn't
            self.__codingCoverage[sample] = coverage

        #store the sample in the hash too
        self.__samples[sample] = 1

    ## Add coverage for reverse direction
    # @param self The object pointer
    # @param sample The sample where the coverage was seen
    # @param coverage The amount of coverage to add
    def addReverseCoverage(self, sample, coverage):
        #see if sample exists
        if sample in self.__reverseCoverage:
            #add to the coverage if it does
            self.__reverseCoverage[sample] += coverage
        else:
            #create the entry if it doesn't
            self.__reverseCoverage[sample] = coverage

        #store the sample in the hash too
        self.__samples[sample] = 1

    ## Get the coding coverage for a sample
    # @param self The object pointer
    # @param sample The sample where the coverage was seen
    # @returns The total coverage in the coding direction
    def getSampleCodingCoverage(self, sample):
        #see if the sample exists
        if(sample in self.__codingCoverage):
            #return the coverage
            return(self.__codingCoverage[sample])
        else:
            #not found return 0
            return(0)

    ## Get the reverse coverage for a sample
    # @param self The object pointer
    # @param sample The sample where the coverage was seen
    # @returns The total coverage in the reverse direction
    def getSampleReverseCoverage(self, sample):
        #see if sample exists
        if(sample in self.__reverseCoverage):
            #return the coverage
            return(self.__reverseCoverage[sample])
        else:
            #not found return 0
            return(0)

    ## Get the total coverage for a sample
    # @param self The object pointer
    # @param sample The sample where the coverage was seen
    # @returns The total coverage at this site
    def getSampleTotalCoverage(self, sample):
        return(self.getSampleCodingCoverage(sample) + self.getSampleReverseCoverage(sample))

    ## Get the coding coverage
    # @param self The object pointer
    # @returns The total coverage in the coding direction
    def getCodingCoverage(self):
        #sum up across each sample
        sum = 0

        #loop over each sample
        for sample in self.__codingCoverage:
            sum += self.getSampleCodingCoverage(sample)

        return(sum)

    ## Get the reverse coverage
    # @param self The object pointer
    # @returns The total coverage in the reverse direction
    def getReverseCoverage(self):
        #sum up across each sample
        sum = 0

        #loop over each sample
        for sample in self.__reverseCoverage:
            sum += self.getSampleReverseCoverage(sample)

        return(sum)

    ## Get the total coverage for a sample
    # @param self The object pointer
    # @returns The total coverage at this site
    def getTotalCoverage(self):
        return(self.getCodingCoverage() + self.getReverseCoverage())

    ## Get the list of samples at this site
    # @param self The object pointer
    # @returns A comma-separated list of samples that had this site
    def getSampleList(self):
        #build the string
        sampleList = ""

        for sample in sorted(self.__samples):
            sampleList += sample + ", "

        return(sampleList)

    ## Get the number of samples at this site
    # @param self The object pointer
    # @returns The number samples that had this site
    def getSampleCount(self):
        return(len(self.__samples))

## @package TransposonSiteTest
#
# This class is responsible for unit testing the TransposonSite class
class TransposonSiteTest(unittest.TestCase):
    #set up a dummy gene object
    site = TransposonSite(10);
    site.addCodingCoverage("A", 10)
    site.addCodingCoverage("B", 20)
    site.addReverseCoverage("A", 40)

    def test_distance(self):
        self.assertEqual(self.site.getDistance(), 10)

    def test_sample_coding_coverage(self):
        self.assertEqual(self.site.getSampleCodingCoverage("B"), 20)

    def test_sample_reverse_coverage(self):
        self.assertEqual(self.site.getSampleReverseCoverage("A"), 40)

    def test_total_coding_coverage(self):
        self.assertEqual(self.site.getCodingCoverage(), 30)

    def test_total_reverse_coverage(self):
        self.assertEqual(self.site.getReverseCoverage(), 40)

    def test_total_coverage(self):
        self.assertEqual(self.site.getTotalCoverage(), 70)

    def test_number_of_samples(self):
        self.assertEqual(self.site.getSampleCount(), 2)

    def test_sample_list(self):
        self.assertEqual(self.site.getSampleList(), "A, B, ")

#if run directly from command-line, just execute test cases
if (__name__ == "__main__"):
    unittest.main()
