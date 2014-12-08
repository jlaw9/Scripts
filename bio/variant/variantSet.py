## @package VariantSet
#
# This class is responsible for managing a VariantSet object

import unittest
from variant import Variant

__author__ = 'mattdyer'

class VariantSet:
    __variants = []

    ## The constructor
    # @param self The object pointer
    def __init__(self):
        self.__variants = []

    ## Parse a VCF file and store all the variant information
    # @param self The object pointer
    # @param file The VCF file to be parsed
    def parseVCF(self, file):
        #load the file to be parsed
        fileReader = open(file, "r")

        #loop over the file
        for line in fileReader:
            #see if line starts with # and skip
            if line.startswith("#"):
                continue

            #tokenize the line
            lineTokens = line.split("\t")

            #set up the variables just so it clear what we are using
            chromosome = lineTokens[0]
            position = int(lineTokens[1])
            id = lineTokens[2]
            referenceAllele = lineTokens[3]
            alternateAllele = lineTokens[4]
            qualityScore = float(lineTokens[5])
            filterFlag = lineTokens[6]
            infoGroup = lineTokens[7]
            formatGroup = lineTokens[8]
            noneGroup = lineTokens[9]

            #create the variant and add it
            variant = Variant(chromosome, position, id, referenceAllele, alternateAllele, qualityScore, filterFlag, infoGroup, formatGroup, noneGroup)
            self.__variants.append(variant)

    ## Get the number of variants
    # @param self The object pointer
    # @returns The number of variants
    def getNumberOfVariants(self):
        return(len(self.__variants))

## @package VariantSetTest
#
# This class is responsible for unit testing the VariantSet class
class VariantSetTest(unittest.TestCase):
    #set up a dummy VariantSet object
    variantSet = VariantSet()
    variantSet.parseVCF("test.vcf")

    def test_variant_count(self):
        self.assertEqual(self.variantSet.getNumberOfVariants(), 20)

#if run directly from command-line, just execute test cases
if (__name__ == "__main__"):
    unittest.main()

