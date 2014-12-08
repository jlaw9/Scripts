## @package Gene
#
# This class is responsible for managing a gene object
import unittest

__author__ = 'mattdyer'

class Gene:

    #set up some class variables
    __name = ""
    __transcriptID = ""
    __chromosome = ""
    __strand = ""
    __startPosition = 0
    __endPosition = 0
    __exonStarts = []
    __exonEnds = []
    __sequence = ""

    ## The constructor
    # @param self The object pointer
    # @param name The name of the gene
    # @param chromosome The name of the chromosome (e.g. chr1)
    # @param strand The strand of the gene (e.g. F or R)
    # @param startPosition The start position
    # @param endPosition The end position
    def __init__(self, name, chromosome, strand, startPosition, endPosition):
        #set up the new object
        self.__name = name
        self.__chromosome = chromosome
        self.__strand = strand
        self.__startPosition = startPosition
        self.__endPosition = endPosition
        self.__exonStarts = []
        self.__exonEnds = []
        self.__sequence = ""

    ## Add a transcript ID
    # @param self The object pointer
    # @param transcriptID The transcript ID
    def addTranscriptID(self, transcriptID):
        self.transcriptID = transcriptID

    ## Get the name of the gene
    # @param self The object pointer
    # @return Returns the name of the gene
    def getName(self):
        return(self.__name)

    ## Get the size of the gene
    # @param self The object pointer
    # @return Returns the size of the gene
    def getSize(self):
        return(self.__endPosition - self.__startPosition)

    ## Get the transcript ID
    # @param self The object pointer
    # @return Returns the transcript ID of the gene
    def getTranscriptID(self):
        return(self.transcriptID)

    ## Get the chromosome
    # @param self The object pointer
    # @return Returns the chromosome of the gene
    def getChromosome(self):
        return(self.__chromosome)

    ## Get the strand
    # @param self The object pointer
    # @return Returns the strand of the gene
    def getStrand(self):
        return(self.__strand)

    ## Get the start position
    # @param self The object pointer
    # @return Returns the start position of the gene
    def getStartPosition(self):
        return(self.__startPosition)

    ## Get the end position
    # @param self The object pointer
    # @return Returns the end position of the gene
    def getEndPosition(self):
        return(self.__endPosition)

    ## Get the number of exons
    # @param self The object pointer
    # @return Returns the number of exons in the gene
    def getNumberOfExons(self):
        return(len(self.__exonStarts))

    ## Add exons to the gene 
    # @param self The object pointer
    # @param starts A comma-separated string of start coordinates    
    # @param ends A comma-separated string of end coordinates
    def addExonsToGene(self, starts, ends):
        #split the two strings into arrays
        startCoordinates = starts.split(",")
        endCoordinates = ends.split(",")

        #the two lists should always be the same length
        if(len(startCoordinates) != len(endCoordinates)):
            print "WARNING: " , self.__name , " has a different number of start and stop coordinates - skipping"
        else:
            #add the coordinates
            for i in range(0, len(startCoordinates)):
                if(startCoordinates[i] != "" and endCoordinates[i] != ""):
                    self.__exonStarts.append(int(startCoordinates[i]))
                    self.__exonEnds.append(int(endCoordinates[i]))
            
    ## Given a coordinate position this will return the location of the coordinate 
    # (upstream, downstream, exon, or intron) and the distance from the gene. If the 
    # coordinate is in the gene then it will return the exon or intron number
    # @param self The object pointer
    # @param position The position to test
    # @return Returns the location of the intron (upstream, downstream, exon, intron) and the distance from the gene or exon / intron number if within gene
    def getLocation(self, position):
        #set up the two variables we will return
        distance = 0
        location = "upstream"

        #if position is less than gene start
        if(position < self.__startPosition):
            #find the difference
            distance = self.__startPosition - position
            
            #if the gene was on the reverse strand then it would be downstream so update location
            if(self.__strand == "R"):
                location = "downstream"

        #if position is greater than gene start
        elif (position > self.__endPosition):
            #find the difference
            distance = position - self.__endPosition

            #if the gene was on the forward strand then it would be downstream so update location
            if(self.__strand == "F"):
                location = "downstream"

        #the position is somewhere in the gene itself
        else:
            #loop over each exon and see if we are in an exon or intron
            for i in range(0, len(self.__exonStarts)):
                #grab the coordinate for this exon
                start = self.__exonStarts[i]
                end = self.__exonEnds[i]

                #check if in exon
                if (position >= start and position <= end):
                    location = "exon"
                    distance = i + 1

                    #see if on the reverse strand then we need to switch the numbering
                    if(self.__strand == "R"):
                        distance = len(self.__exonStarts) - i

                    #break the for loop
                    break
                #check if intron
                elif (position < start):
                    location = "intron"
                    distance = i

                    #see if on the reverse strand then we need to switch the numbering
                    if(self.__strand == "R"):
                        distance = len(self.__exonStarts) - i

                    #break the for loop
                    break

        #return the location and distance
        return(location, distance)

## @package GeneTest
#
# This class is responsible for unit testing the gene class
class GeneTest(unittest.TestCase):
    #set up a dummy gene object
    geneForward = Gene("test", "chr1", "F", 500, 1000)
    geneReverse = Gene("test", "chr1", "R", 1500, 2000)
    geneForward.addExonsToGene("500,700,900,", "600,800,1000,")
    geneReverse.addExonsToGene("1500,1700,1900,", "1600,1800,2000,")

    def test_number_of_exons(self):
        self.assertEqual(self.geneForward.getNumberOfExons(), 3)
        self.assertEqual(self.geneReverse.getNumberOfExons(), 3)

    def test_location_exon_forward(self):
        location, distance = self.geneForward.getLocation(550)
        self.assertEqual(location, "exon")
        self.assertEqual(distance, 1)

        location, distance = self.geneForward.getLocation(950)
        self.assertEqual(location, "exon")
        self.assertEqual(distance, 3)

    def test_location_intron_forward(self):
        location, distance = self.geneForward.getLocation(650)
        self.assertEqual(location, "intron")
        self.assertEqual(distance, 1)

    def test_location_upstream_forward(self):
        location, distance = self.geneForward.getLocation(450)
        self.assertEqual(location, "upstream")
        self.assertEqual(distance, 50)

    def test_location_downstream_forward(self):
        location, distance = self.geneForward.getLocation(1050)
        self.assertEqual(location, "downstream")
        self.assertEqual(distance, 50)

    def test_location_exon_reverse(self):
        location, distance = self.geneReverse.getLocation(1550)
        self.assertEqual(location, "exon")
        self.assertEqual(distance, 3)

        location, distance = self.geneReverse.getLocation(1950)
        self.assertEqual(location, "exon")
        self.assertEqual(distance, 1)

    def test_location_intron_reverse(self):
        location, distance = self.geneReverse.getLocation(1650)
        self.assertEqual(location, "intron")
        self.assertEqual(distance, 2)

    def test_location_upstream_reverse(self):
        location, distance = self.geneReverse.getLocation(1450)
        self.assertEqual(location, "downstream")
        self.assertEqual(distance, 50)

    def test_location_downstream_reverse(self):
        location, distance = self.geneReverse.getLocation(2050)
        self.assertEqual(location, "upstream")
        self.assertEqual(distance, 50)

#if run directly from command-line, just execute test cases
if (__name__ == "__main__"):
    unittest.main()
