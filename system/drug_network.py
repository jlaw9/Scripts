# this script manages parsing all the drug bank data and mapping to OMIM

from optparse import OptionParser
import xml.etree.ElementTree as ET

__author__ = 'mattdyer'

## this class manages a network
class Network:
    ## The constructor
    # @param self The object pointer
    def __init__(self):
        self.__interactions = 0
        self.__proteins = {}

    ## Add an interaction
    # @param self The object pointer
    # @param protein1 The first protein
    # @param protein2 The second protein
    def addInteraction(self, protein1, protein2):
        #if protein 1 has not been seen then add it
        if not protein1 in self.__proteins:
            self.__proteins[protein1] = {}

        #if protein 2 has not been seen then add it
        if not protein2 in self.__proteins:
            self.__proteins[protein2] = {}

        #see if the interaction is already known
        elif not protein2 in self.__proteins[protein1]:
            self.__proteins[protein1][protein2] = 1
            self.__proteins[protein2][protein1] = 1
            self.__interactions += 1

    ## load an interaction file
    # @param self The object pointer
    # @param file The file to be parsed
    def loadInteractions(self, file):
        #open the file
        file = open(file, 'r')

        #loop over the file and build the network
        for line in file:
            tokens = line.split('\t')
            protein1 = tokens[0]
            protein2 = tokens[2]

            #skip self interactions
            if not protein1 == protein2:
                self.addInteraction(protein1, protein2)

        #close the file
        file.close()

    ## Get total interactions
    # @param self The object pointer
    # @return The number of interactions
    def getNumberOfInteractions(self):
        return(self.__interactions)

    ## Get total proteins
    # @param self The object pointer
    # @return The number of protein
    def getNumberOfProteins(self):
        return(len(self.__proteins))

    ## See how many proteins from a dictionary are in the network
    # @param self The object pointer
    # @param proteins The dictionary of proteins to check
    # @returns count The count of proteins in the network
    def countHowManyInNetwork(self, proteins):
        count = 0

        #loop over each protein
        for protein in proteins:
            #see if in network
            if protein in self.__proteins:
                count += 1

        #return the count
        return(count)

    ## Get the neighbors in a network from a set of proteins
    # @param self The object pointer
    # @param proteins The set to expand on
    # @return The dictionary of proteins and neighbors
    def getNeighbors(self, proteins):
        #store the neighbors
        neighbors = {}

        for protein in proteins:
            neighbors[protein] = 1

            #grab the neighbors if there are any
            if protein in self.__proteins:
                #add each neighbor
                for neighbor in self.__proteins[protein]:
                    neighbors[neighbor] = 1

        #return the dictionary
        return(neighbors)

## this class manages the annotation map objects
class AnnotationMap:
    ## The constructor
    # @param self The object pointer
    def __init__(self):
        self.__map = {}

    ## load a two column tab-delimited file
    # @param self The object pointer
    # @param file The file to parse
    def parseTwoColumnTab(self, file):
        fileHandle = open(file, 'r')

        for line in fileHandle:
            line = line.strip()
            tokens = line.split('\t')
            id1 = tokens[0]
            id2 = tokens[1]

            #create the dictionary if it isn't there
            if not id1 in self.__map:
                self.__map[id1] = {}

            #add the term
            self.__map[id1][id2] = 1

        #close the file
        fileHandle.close()

    ## get the map
    # @param self The object pointer
    # @returns The dictionary of map terms
    def getMap(self):
        return(self.__map)

    ## get the map for an item
    # @param self The object pointer
    # @param id The id to grab map terms for
    # @returns The dictionary of map terms
    def getMappings(self, id):
        if id in self.__map:
            return(self.__map[id])
        else:
            #return an empty dictionary
            temp = {}
            temp['Not Listed'] = 1
            return(temp)

    ## get the number of terms covered by a set of ids
    # @param self The object pointer
    # @param The dictionary of terms to search
    # @returns The number of terms covered
    def getHowManyTerms(self, list):
        terms = {}

        #loop over the list
        for term in list:
            #loop over ids linked to that term
            if term in self.__map:
                for id in self.__map[term]:
                    terms[term] = 1

        #return the count
        return(len(terms))

## this class manages the annotation objects
class AnnotationList:
    ## The constructor
    # @param self The object pointer
    def __init__(self):
        self.__annotations = {}

    ## load a two column tab-delimited file
    # @param self The object pointer
    # @param file The XML file to parse
    def parseTwoColumnTab(self, file):
        fileHandle = open(file, 'r')

        for line in fileHandle:
            line = line.strip()
            tokens = line.split('\t')
            id = tokens[0]
            name = tokens[1]
            term = Annotation(id, name)
            self.__annotations[id] = term

        #close the file
        fileHandle.close()

    ## get the annotation list
    # @param self The object pointer
    # @returns The dictionary of annotation terms
    def getAnnotations(self):
        return(self.__annotations)

    ## get a specific annotation
    # @param self The object pointer
    # @param id The id to search for
    # @returns The annotation object
    def getAnnotation(self, id):
        if id in self.__annotations:
            return(self.__annotations[id])
        else:
            #return an empty dictionary
            temp = {}
            temp['Not Listed'] = 1
            return(temp)

## this class manages the annotations
class Annotation:
    ## The constructor
    # @param self The object pointer
    # @param id The annotation ID
    # @param name The drug name
    def __init__(self, id, name):
        self.__name = name
        self.__id = id

    ## Get the name
    # @param self The object pointer
    # @returns The annotation name
    def getName(self):
        return(self.__name)

    ## Get the id
    # @param self The object pointer
    # @returns The annotation id
    def getID(self):
        return(self.__id)

## this class manages the drugs objects
class DrugList:
    ## The constructor
    # @param self The object pointer
    def __init__(self):
        self.__drugs = {}

    ## load the drug bank XML file
    # @param self The object pointer
    # @param file The XML file to parse
    # @param file The list of CAS number for our library
    # @returns The total number of DrugBank drugs and number in our library
    def parseDrugBankXML(self, file, casList):
        #parse the DrugBank XML file
        drugRecords = ET.parse(file)
        drugRoot = drugRecords.getroot()
        totalDrugs = 0
        drugsWithCAS = 0
        drugsInLibrary = 0

        #loop over all the drug entries
        for drug in drugRoot.findall('drug'):
            id = drug.find('drugbank-id').text
            name = drug.find('name').text
            indication = drug.find('indication').text
            cas = drug.find('cas-number').text
            totalDrugs += 1

            #store only if cas was provided
            if not cas is None:
                drugsWithCAS += 1

            #only want things in our library
            if cas in casList:
                drugsInLibrary += 1
                casList[cas] = 1

                #create the drug object and store it in our hash
                drugObject = Drug(name, id, indication, cas)
                self.__drugs[id] = drugObject

        return(totalDrugs, drugsWithCAS, drugsInLibrary)

    ## get the drug list
    # @param self The object pointer
    # @returns The dictionary of drug terms
    def getDrugs(self):
        return(self.__drugs)

    ## get a specific drug
    # @param self The object pointer
    # @param id The drug ID
    # @returns The drug object
    def getDrug(self, id):
        #see if the drug exists and return it if it does
        if id in self.__drugs:
            return(self.__drugs[id])

## this class manages the drug object
class Drug:
    ## The constructor
    # @param self The object pointer
    # @param id The drug ID
    # @param name The drug name
    # @param indication The drug indication
    # @param cas The CAS number
    def __init__(self, name, id, indication, cas):
        self.__name = name
        self.__id = id
        self.__indication = indication
        self.__cas = cas

    ## Get the name
    # @param self The object pointer
    # @returns The drug name
    def getName(self):
        return(self.__name)

    ## Get the id
    # @param self The object pointer
    # @returns The drug id
    def getID(self):
        return(self.__id)

    ## Get the inidication
    # @param self The object pointer
    # @returns The drug indication
    def getIndication(self):
        return(self.__indication)

    ## Get the cas
    # @param self The object pointer
    # @returns The drug cas
    def getCAS(self):
        return(self.__cas)

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-x', '--dbxml', dest='dbxml', help='The drugBank XML file')
    parser.add_option('-g', '--dbgenes', dest='dbgenes', help='The drugBank gene file')
    parser.add_option('-n', '--network', dest='network', help='Protein interaction network file')
    parser.add_option('-t', '--omimterms', dest='omimterms', help='Omim term file')
    parser.add_option('-a', '--goterms', dest='goterms', help='GO term file')
    parser.add_option('-d', '--keggterms', dest='keggterms', help='KEGG term file')
    parser.add_option('-i', '--cosmicterms', dest='cosmicterms', help='COSMIC term file')
    parser.add_option('-b', '--omimmap', dest='omimmap', help='OMIM map file')
    parser.add_option('-j', '--cosmicmap', dest='cosmicmap', help='COSMIC map file')
    parser.add_option('-c', '--gomap', dest='gomap', help='GO map file')
    parser.add_option('-e', '--keggmap', dest='keggmap', help='KEGG map file')
    parser.add_option('-f', '--caslist', dest='caslist', help='CAS list')
    parser.add_option('-o', '--output', dest='output', help='The output directory')
    (options, args) = parser.parse_args()

    #load the cas number from our library
    file = open(options.caslist, 'r')
    casList = {}

    #loop over the file
    for line in file:
        line = line.strip()
        casList[line] = 0

    #close the file
    file.close()

    #load the drugs from drug bank
    drugList = DrugList()
    totalDrugBank, drugsWithCAS, drugBankInLibrary = drugList.parseDrugBankXML(options.dbxml, casList)
    print 'Total Drugs in DrugBank: %i' % (totalDrugBank)
    print 'Total Drugs in DrugBank with CAS: %i' % (drugsWithCAS)
    print 'Total Drugs in DrugBank in Library: %i' % (drugBankInLibrary)

    #print out CAS that aren't in drugbank
    file = open('%s/not_in_drugbank.txt' % (options.output), 'w')

    for cas in casList:
        if casList[cas] == 0:
            file.write('%s\n' % (cas))

    #close the file
    file.close()

    #load the interaction network
    network = Network()
    network.loadInteractions(options.network)
    print 'Total Interactions: %i' % (network.getNumberOfInteractions())
    print 'Total Proteins: %i' % (network.getNumberOfProteins())

    #load the term files
    goTerms = AnnotationList()
    goTerms.parseTwoColumnTab(options.goterms)
    print 'Total GO Terms: %i' % (len(goTerms.getAnnotations()))

    cosmicTerms = AnnotationList()
    cosmicTerms.parseTwoColumnTab(options.cosmicterms)
    print 'Total COSMIC Terms: %i' % (len(cosmicTerms.getAnnotations()))

    keggTerms = AnnotationList()
    keggTerms.parseTwoColumnTab(options.keggterms)
    print 'Total KEGG Terms: %i' % (len(keggTerms.getAnnotations()))

    #load the map files
    omimUniprotMap = AnnotationMap()
    omimUniprotMap.parseTwoColumnTab(options.omimmap)

    omimMorbidMap = AnnotationMap()
    omimMorbidMap.parseTwoColumnTab(options.omimterms)
    print 'Total OMIM Terms: %i' % (len(omimMorbidMap.getMap()))

    goMap = AnnotationMap()
    goMap.parseTwoColumnTab(options.gomap)

    cosmicMap = AnnotationMap()
    cosmicMap.parseTwoColumnTab(options.cosmicmap)

    keggMap = AnnotationMap()
    keggMap.parseTwoColumnTab(options.keggmap)

    #now lets parse the targets CSV file
    file = open(options.dbgenes, 'r')
    output = open('%s/drugs.txt' % options.output, 'w')
    output.write('Protein ID\tSpecies\tDrug Name\tDrugBank ID\tCAS\tIndication\tOMIM ID\tOMIM Mappings\n')
    proteinDrugTargets = {}

    for line in file:
        tokens = line.split(',')
        proteinID = tokens[0]
        species = tokens[11]
        drugs = tokens[12]

        #we only want the human ones
        if species == 'Human':
            #tokenize the drugs
            drugTokens = drugs.split(';')

            #loop over each drug
            for drugID in drugTokens:
                drugID = drugID.strip()

                #now print some info
                if drugID in drugList.getDrugs():
                    #store the proteins covered by our library
                    proteinDrugTargets[proteinID] = 1
                    drugObject = drugList.getDrug(drugID)
                    print '%s\t%s' % (drugObject.getCAS(), proteinID)

                    name = drugObject.getName()
                    id = drugObject.getID()
                    cas = drugObject.getCAS()
                    indication = drugObject.getIndication()

                    #if not None then encode
                    if not indication is None:
                        indication = indication.encode('utf-8')

                    #see if the gene has any known OMIM info
                    if proteinID in omimUniprotMap.getMap():
                        #for each term print out a row
                        for omim in omimUniprotMap.getMappings(proteinID):
                            #print out the entry with omim terms
                            descriptions = '; '.join(list(omimMorbidMap.getMappings(omim).keys())).encode('utf-8')
                            output.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (proteinID, species, name, id, cas, indication, omim, descriptions))

                    else:
                        #print out the entry without omim terms
                        output.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (proteinID, species, name, id, cas, indication, 'N/A', 'N/A'))

    #close the file
    file.close()
    output.close()

    #see what fraction of proteins in the network are targeted by drugs
    print "Drug Targets In Network: %i " % (network.countHowManyInNetwork(proteinDrugTargets))
    print "Go Terms Covered: %i " % (goMap.getHowManyTerms(proteinDrugTargets))
    print "OMIM Terms Covered: %i " % (omimUniprotMap.getHowManyTerms(proteinDrugTargets))
    print "KEGG Terms Covered: %i " % (keggMap.getHowManyTerms(proteinDrugTargets))
    print "COSMIC Terms Covered: %i " % (cosmicMap.getHowManyTerms(proteinDrugTargets))

    #go one step out (make this function recursive at some point
    neighbors1 = network.getNeighbors(proteinDrugTargets)
    print "Drug Targets In Network (1-step): %i " % (network.countHowManyInNetwork(neighbors1))
    print "Go Terms Covered (1-step): %i " % (goMap.getHowManyTerms(neighbors1))
    print "OMIM Terms Covered (1-step): %i " % (omimUniprotMap.getHowManyTerms(neighbors1))
    print "KEGG Terms Covered (1-step): %i " % (keggMap.getHowManyTerms(neighbors1))
    print "COSMIC Terms Covered (1-step): %i " % (cosmicMap.getHowManyTerms(neighbors1))

    #go second step out (make this function recursive at some point
    neighbors2 = network.getNeighbors(neighbors1)
    print "Drug Targets In Network (2-step): %i " % (network.countHowManyInNetwork(neighbors2))
    print "Go Terms Covered (2-step): %i " % (goMap.getHowManyTerms(neighbors2))
    print "OMIM Terms Covered (2-step): %i " % (omimUniprotMap.getHowManyTerms(neighbors2))
    print "KEGG Terms Covered (2-step): %i " % (keggMap.getHowManyTerms(neighbors2))
    print "COSMIC Terms Covered (2-step): %i " % (cosmicMap.getHowManyTerms(neighbors2))

    #go third step out (make this function recursive at some point
    neighbors3 = network.getNeighbors(neighbors2)
    print "Drug Targets In Network (3-step): %i " % (network.countHowManyInNetwork(neighbors3))
    print "Go Terms Covered (3-step): %i " % (goMap.getHowManyTerms(neighbors3))
    print "OMIM Terms Covered (3-step): %i " % (omimUniprotMap.getHowManyTerms(neighbors3))
    print "KEGG Terms Covered (3-step): %i " % (keggMap.getHowManyTerms(neighbors3))
    print "COSMIC Terms Covered (3-step): %i " % (cosmicMap.getHowManyTerms(neighbors3))


