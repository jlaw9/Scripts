## @package Variant
#
# This class is responsible for managing a variant object
import unittest

__author__ = 'mattdyer'

class Variant:
    #set up some of the class variables
    __chromosome = ""
    __position = 0
    __id = ""
    __referenceAllele = ""
    __alternativeAllele = ""
    __qualityScore = 0
    __filterFlag = ""
    __flags = {}

    ## The constructor
    # @param self The object pointer
    # @param chromosome The chromosome the variant was found on
    # @param position The position of the variant
    # @param id The variant id
    # @param referenceAllele The reference allele
    # @param alternativeAllele The alternative allele
    # @param qualityScore The quality score of the variant
    # @param filterFlag The pass / fail filter flag of the variant
    # @param infoField The info field of parameter=value pairs
    # @param formatField The field containing just flags (generate in TVC)
    # @param noneField The field containing the values for the flags (generate in TVC)
    def __init__(self, chromosome, position, id, referenceAllele, alternativeAllele, qualityScore, filterFlag, infoField, formatField, noneField):
        self.__chromosome = chromosome
        self.__position = position
        self.__id = id
        self.__referenceAllele = referenceAllele
        self.__alternativeAllele = alternativeAllele
        self.__qualityScore = qualityScore
        self.__filterFlag = filterFlag

        #now we need to parse the info field
        infoTokens = infoField.split(";")

        for token in infoTokens:
            pair = token.split("=")
            self.__flags[pair[0]] = pair[1]

        #now we need to do a similar thing for the format / none fields only need to parse them together
        #since the none field has the data for the format field flags
        formatTokens = formatField.split(";")
        noneTokens = noneField.split(";")

        for i in range(0, len(formatTokens)):
            self.__flags[formatTokens[i]] = noneTokens[i]

    ## See if variant has a flag
    # @param self The object pointer
    # @param flag The flag to search
    # @returns True if the variant has the flag, False otherwise
    def hasFlag(self, flag):
        if(flag in self.__flags):
            return(True)
        else:
            return(False)

    ## Get the value of a flag
    # @param self The object pointer
    # @param flag The flag to search
    # @returns The value of the flag
    def getFlag(self, flag):
        if(flag in self.__flags):
            return(self.__flags[flag])
        else:
            return(Null)

    ## Get the variant chromosome
    # @param self The object pointer
    # @returns The chromosome of the variant
    def getChromosome(self):
        return(self.__chromosome)

    ## Get the variant position
    # @param self The object pointer
    # @returns The position of the variant
    def getPosition(self):
        return(self.__position)

    ## Get the variant ID
    # @param self The object pointer
    # @returns The ID of the variant
    def getID(self):
        return(self.__id)

    ## Get the variant reference allele
    # @param self The object pointer
    # @returns The reference allele of the variant
    def getReferenceAllele(self):
        return(self.__referenceAllele)

    ## Get the variant alternative allele
    # @param self The object pointer
    # @returns The alternative allele of the variant
    def getAlternativeAllele(self):
        return(self.__alternativeAllele)

    ## Get the variant quality score
    # @param self The object pointer
    # @returns The quality score of the variant
    def getQualityScore(self):
        return(self.__qualityScore)

    ## Get the variant filter flag
    # @param self The object pointer
    # @returns The quality score of the variant
    def getFilterFlag(self):
        return(self.__filterFlag)

## @package VariantTest
#
# This class is responsible for unit testing the TransposonSite class
class VariantTest(unittest.TestCase):
    #set up a dummy variant object
    variant = Variant("chr13", 1, ".", "G", "A", 10, "PASS", "AO=3372;DP=3382;FAO=1994;FDP=1994;FR=.;FRO=0;FSAF=1237;FSAR=757;FSRF=0;FSRR=0;FWDB=0.017642;FXX=0.00299998;HRUN=1;LEN=1;MLLD=248.455;QD=64.0228;RBI=0.0201118;REFB=0;REVB=0.00965646;RO=6;SAF=2067;SAR=1305;SRF=2;SRR=4;SSEN=0;SSEP=0;SSSB=0.00100081;STB=0.5;TYPE=snp;VARB=7.46822e-06;OID=.;OPOS=32890572;OREF=G;OALT=A;OMAPALT=A", "GT:GQ:DP:FDP:RO:FRO:AO:FAO:SAR:SAF:SRF:SRR:FSAR:FSAF:FSRF:FSRR", "1/1:99:3382:1994:6:0:3372:1994:1305:2067:2:4:757:1237:0:0")

    def test_basic_variables(self):
        self.assertEqual(self.variant.getChromosome(), "chr13")
        self.assertEqual(self.variant.getPosition(), 1)
        self.assertEqual(self.variant.getID(), ".")
        self.assertEqual(self.variant.getReferenceAllele(), "G")
        self.assertEqual(self.variant.getAlternativeAllele(), "A")
        self.assertEqual(self.variant.getQualityScore(), 10)
        self.assertEqual(self.variant.getFilterFlag(), "PASS")

    def test_has_flag(self):
        self.assertEqual(self.variant.hasFlag("FooBar"), False)
        self.assertEqual(self.variant.hasFlag("AO"), True)

    def test_flag_value(self):
        self.assertEqual(self.variant.getFlag("FAO"), "1994")

#if run directly from command-line, just execute test cases
if (__name__ == "__main__"):
    unittest.main()



