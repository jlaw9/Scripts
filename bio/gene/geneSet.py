## @package Gene
#
# This class is responsible for managing a set of gene objects

from gene import Gene
import unittest

__author__ = 'mattdyer'

class GeneSet:
    #set up some class variables
    file = ""
    genes = {}

    ## The constructor
    # @param self The object pointer
    def __init__(self):
        #set up the new object
        file = ""
        genes = {}

    ## Load a RefSeq gene model file (UCSC format) and build the gene models
    # @param self The object pointer
    # @param file The RefSeq to be parsed
    def loadGeneModels(self, file):
        #load the file to be parsed
        fileReader = open(file, "r")

        #loop over the file
        for line in fileReader:
            #tokenize the line
            fileTokens = line.split("\t")

            #set up the variables just so it clear what we are using
            geneName = fileTokens[0]
            transcript = fileTokens[1]
            chromosome = fileTokens[2]
            strand = fileTokens[3]
            startPosition = int(fileTokens[4])
            endPosition = int(fileTokens[5])
            exonStarts = fileTokens[9]
            exonEnds = fileTokens[10]

            #update the strand nomenclature
            if(strand == "+"):
                strand = "F"
            else:
                strand = "R"

            #see if gene exists
            if(self.hasGene(geneName)):
                #grab the gene
                gene = self.genes[geneName]

                #see if the new model has a larger coding seqeunce, we take the largest model
                if(endPosition - startPosition > gene.getSize()):
                     self.addGene(geneName, transcript, chromosome, strand, startPosition, endPosition, exonStarts, exonEnds)

            else:
                #gene not seen yet so create it and add it
                self.addGene(geneName, transcript, chromosome, strand, startPosition, endPosition, exonStarts, exonEnds)

        #close the file handle
        fileReader.close()

    ## Add a gene to the gene set
    # @param self The object pointer
    # @param geneName The name of the gene
    # @return Returns true if the gene exist, false if it does not
    def hasGene(self, gene):
        #return true if the gene exists
        return(self.genes.has_key(gene))

    ## Count the number of genes in the gene set
    # @param self The object pointer
    # @return Returns the number of genes in the gene set
    def getNumberOfGenes(self):
        return(len(self.genes.keys()))

    ## Add a gene to the gene set
    # @param self The object pointer
    # @param geneName The name of the gene
    # @param transcript The transcript ID
    # @param chromosome The chromosome the gene is on
    # @param strand The strand of the gene
    # @param startPosition The starting position of the gene
    # @param endPosition The ending position of the gene
    # @param exonStarts The comma-separated list of exon start coordinates
    # @param exonEnds The comma-separated list of exon end coordinates
    def addGene(self, geneName, transcript, chromosome, strand, startPosition, endPosition, exonStarts, exonEnds):
        #create the gene object
        gene = Gene(geneName, chromosome, strand, startPosition, endPosition)
        gene.addTranscriptID(transcript)
        gene.addExonsToGene(exonStarts, exonEnds)

        #add the gene to the hash
        self.genes[geneName] = gene

## @package GeneSetTest
#
# This class is responsible for unit testing the GeneSet class
class GeneSetTest(unittest.TestCase):
    #load the file
    geneSet = GeneSet();
    geneSet.loadGeneModels("test.txt")

    def test_number_of_genes(self):
        self.assertEqual(self.geneSet.getNumberOfGenes(), 2)

    def test_has_gene(self):
        self.assertEqual(self.geneSet.hasGene("BMP4"), True)

    def test_missing_gene(self):
        self.assertEqual(self.geneSet.hasGene("MATT"), False)

#if run directly from command-line, just execute test cases
if (__name__ == "__main__"):
    unittest.main()
