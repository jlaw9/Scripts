## @package TransposonSiteSet
#
# This class is responsible for managing data for a TransposonSiteSet which is a bunch of TransposonSite objects

import unittest
from transposonSite import TransposonSite

__author__ = 'mattdyer'

class TransposonSiteSet:
    __upstreamSites = {}
    __downstreamSites = {}
    __exonSites = {}
    __intronSites = {}
    __name = ""

    ## The constructor
    # @param self The object pointer
    # @param name The name of the set, e.g. gene name
    def __init__(self, name):
        #set up the new object
        self.__upstreamSites = {}
        self.__downstreamSites = {}
        self.__exonSites = {}
        self.__intronSites = {}
        self.__name = name

    ## Get the name of the set
    # @param self The object pointer
    # @returns The name of the set
    def getName(self):
        return(self.__name)

    ## Add a new site to the set
    # @param self The object pointer
    # @param sample The sample the site was observed in
    # @param position The position of the insertion
    # @param coverage The coverage of the site
    # @param orientation The orientation of the site (coding or reverse)
    # @param location The location of the site (upstream, downstream, exon, or intron)
    # @param distance The distance of the site from start / stop of the region
    def addSite(self, sample, position, coverage, orientation, location, distance):
        #grab the correct hash depending on what our location is
        sites = self.__upstreamSites;

        if(location == "downstream"):
            sites = self.__downstreamSites
        elif(location == "exon"):
            sites = self.__exonSites
        elif(location == "intron"):
            sites = self.__intronSites

        #now see if this site has been seen or not
        transposonSite = ""
        if position in sites:
            #grab the TransposonSite object
            transposonSite = sites[position]
        else:
            #create a new TransposonSite object
            transposonSite = TransposonSite(distance)
            sites[position] = transposonSite

        #add coverage and sample info
        if(orientation == "coding"):
            transposonSite.addCodingCoverage(sample, coverage)
        else:
            transposonSite.addReverseCoverage(sample, coverage)

    ## Get the hash of upstream sites
    # @param self The object pointer
    # @returns A hash of the upstream sites
    def getUpstreamSites(self):
        return(self.__upstreamSites)

    ## Get the hash of downstream sites
    # @param self The object pointer
    # @returns A hash of the downstream sites
    def getDownstreamSites(self):
        return(self.__downstreamSites)

    ## Get the hash of exon sites
    # @param self The object pointer
    # @returns A hash of the exon sites
    def getExonSites(self):
        return(self.__exonSites)

    ## Get the hash of intron sites
    # @param self The object pointer
    # @returns A hash of the intron sites
    def getIntronSites(self):
        return(self.__intronSites)

    ## Get the number of upstream sites
    # @self The object pointer
    # @returns The number of upstream sites
    def getUpstreamSiteCount(self):
        return(len(self.__upstreamSites))

    ## Get the number of downstream sites
    # @self The object pointer
    # @returns The number of downstream sites
    def getDownstreamSiteCount(self):
        return(len(self.__downstreamSites))

    ## Get the number of exon sites
    # @self The object pointer
    # @returns The number of exon sites
    def getExonSiteCount(self):
        return(len(self.__exonSites))

    ## Get the number of intron sites
    # @self The object pointer
    # @returns The number of intron sites
    def getIntronSiteCount(self):
        return(len(self.__intronSites))

    ## See if a specific site is defined in the set
    # @self The object pointer
    # @position The position
    # @returns True if the site is in the set, false otherwise
    def hasSite(self, position):
        if(position in self.__upstreamSites or position in self.__downstreamSites or position in self.__exonSites or position in self.__downstreamSites):
            return(True)
        else:
            return(False)

    ## Get a specific site based on location
    # @self The object pointer
    # @position The position
    # @returns The TransposonSite object
    def getSite(self, position):
        #technically a site should only belong to single group so we can get away with this approach
        if(position in self.__upstreamSites):
            return(self.__upstreamSites[position])
        elif(position in self.__downstreamSites):
            return(self.__downstreamSites[position])
        elif(position in self.__exonSites):
            return(self.__exonSites[position])
        elif(position in self.__intronSites):
            return(self.__intronSites[position])
        else:
            return(Null)

## @package TransposonSiteTest
#
# This class is responsible for unit testing the TransposonSite class
class TransposonSiteTest(unittest.TestCase):
    #set up a dummy gene object
    siteSet = TransposonSiteSet("gene1")
    siteSet.addSite("sample1", 100, 10, "coding", "upstream", 100)
    siteSet.addSite("sample2", 101, 10, "coding", "upstream", 100)
    siteSet.addSite("sample1", 200, 30, "reverse", "downstream", 100)
    siteSet.addSite("sample1", 150, 40, "coding", "exon", 1)
    siteSet.addSite("sample1", 150, 60, "reverse", "exon", 1)
    siteSet.addSite("sample1", 160, 50, "coding", "intron", 2)

    def test_name(self):
        self.assertEqual(self.siteSet.getName(), "gene1")

    def test_upstream_count(self):
        self.assertEqual(self.siteSet.getUpstreamSiteCount(), 2)

    def test_downstream_count(self):
        self.assertEqual(self.siteSet.getDownstreamSiteCount(), 1)

    def test_exon_count(self):
        self.assertEqual(self.siteSet.getExonSiteCount(), 1)

    def test_intron_count(self):
        self.assertEqual(self.siteSet.getIntronSiteCount(), 1)

    def test_has_site(self):
        self.assertEqual(self.siteSet.hasSite(180), False)
        self.assertEqual(self.siteSet.hasSite(150), True)

    def test_get_site(self):
        site = self.siteSet.getSite(150)
        self.assertEqual(site.getCodingCoverage(), 40)
        self.assertEqual(site.getReverseCoverage(), 60)
        self.assertEqual(site.getTotalCoverage(), 100)

#if run directly from command-line, just execute test cases
if (__name__ == "__main__"):
    unittest.main()
