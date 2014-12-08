import networkx as nx
import matplotlib.pyplot as plt
from optparse import OptionParser

__author__ = 'mattdyer'

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-d', '--drug', dest='drugs', help='The drug info file from LAM')
    parser.add_option('-g', '--gene', dest='genes', help='Gene List')
    parser.add_option('-n', '--network', dest='network', help='Protein interaction network file')
    parser.add_option('-o', '--output', dest='output', help='The output directory')
    parser.add_option('-u', '--uniprot', dest='uniprot', help='The uniprot map file')
    (options, args) = parser.parse_args()

    #build a graph
    graph = nx.Graph()

    #load the uniprot map
    uniprotMap = {}
    file = open(options.uniprot, 'r')

    for line in file:
        line = line.strip('\n\r')
        tokens = line.split('\t')

        #store uniprot to gene
        uniprotMap[tokens[0]] = tokens[1]

        #store gene to uniprot
        uniprotMap[tokens[1]] = tokens[0]

    #close the file
    file.close()

    #load the drug file
    file = open(options.drugs, 'r')
    drugTargets = {}

    #loop over and store the targeted proteins
    for line in file:
        line = line.strip('\n\r')
        tokens = line.split('\t')
        drug = tokens[0]
        proteins = tokens[6]

        #see if we had multiple
        proteinArray = []

        if not ';' in proteins:
            proteinArray.append(proteins)
        else:
            #tokenize and add
            tokens = proteins.split(';')

            for token in tokens:
                token = token.replace(' ','')
                proteinArray.append(token)

        #now for each protein store the drug info
        for protein in proteinArray:
            if not protein in drugTargets:
                drugTargets[protein] = drug
            else:
                drugTargets[protein] += '; %s' % drug

    #close the file
    file.close()

    #load the gene list
    targetProteins = {}
    mappingNotFound = {}
    file = open(options.genes, 'r')

    for gene in file:
        gene = gene.strip('\n\r')

        #if we have the mapping then store it
        if gene in uniprotMap:
            targetProteins[uniprotMap[gene]] = 1
        else:
            mappingNotFound[gene] = 1;

    #close the file
    file.close()

    #parse the file now
    file = open(options.network, 'r')

    #loop over the file and build the network
    for line in file:
        line = line.rstrip('\n\r')
        tokens = line.split('\t')
        protein1 = tokens[0]
        protein2 = tokens[2]

        #exclude self interactions and see if the graph already has the edge or not
        if not protein1 == protein2 and not graph.has_edge(protein1, protein2) and not graph.has_edge(protein2, protein1):
            graph.add_edge(protein1, protein2)

    #close the file
    file.close()

    #now lets start the real analysis
    directDruggable = {}
    directNotDruggable = {}
    neighborDruggable = {}
    neighborNotDruggable = {}
    notInNetwork = {}

    #loop over the target set of genes and place them into buckets
    for protein in targetProteins:
        #see if druggable or not
        if protein in drugTargets and graph.has_node(protein):
            directDruggable[protein] = 1
        elif not protein in drugTargets and graph.has_node(protein):
            directNotDruggable[protein] = 1
        else:
            notInNetwork[protein] = 1

        #now grab the neighbors of that protein
        if graph.has_node(protein):
            neighbors = graph.neighbors(protein)

            for neighbor in neighbors:
                #only look at it the neighbors wasn't also a target
                if not neighbor in targetProteins:
                    if neighbor in drugTargets:
                        neighborDruggable[neighbor] = 1
                    else:
                        neighborNotDruggable[neighbor] = 1

    #now lets just print out all the info
    file = open('%s/summary.txt' % (options.output), 'w')
    file.write('Gene\tUniprot\tType\tDrug Interactions\tNotes\n')
    proteinsToMap = {}

    for gene in mappingNotFound:
        file.write('%s\tNA\tNA\tNA\t%s\n' % (gene, 'Uniprot ID Unknown'))

    for protein in directDruggable:
        file.write('%s\t%s\tDirect\t%s\t\n' % (uniprotMap[protein], protein, drugTargets[protein]))
        proteinsToMap[protein] = uniprotMap[protein]

    for protein in directNotDruggable:
        file.write('%s\t%s\tDirect\t\t\n' % (uniprotMap[protein], protein))
        proteinsToMap[protein] = uniprotMap[protein]

    for protein in neighborDruggable:
        file.write('%s\t%s\tNeighbor\t%s\t\n' % (uniprotMap[protein], protein, drugTargets[protein]))
        proteinsToMap[protein] = uniprotMap[protein]

    #close the file
    file.close()

    #rebuild the graph just looking at the proteins of interest now (make this better, just a quick hack, not done optimally)
    subgraph = graph.subgraph(proteinsToMap.keys())

    #layout the graph
    plt.figure(figsize=(11, 8), dpi=150)
    pos=nx.spring_layout(subgraph) # positions for all nodes

    # nodes
    nx.draw_networkx_nodes(subgraph,pos,node_size=45,node_color='blue',nodelist=list(directNotDruggable.keys()))
    nx.draw_networkx_nodes(subgraph,pos,node_size=45,node_color='yellow',nodelist=list(neighborDruggable.keys()))
    nx.draw_networkx_nodes(subgraph,pos,node_size=45,node_color='green',nodelist=list(directDruggable.keys()))

    # edges
    nx.draw_networkx_edges(subgraph,pos,alpha=.4,edge_color='grey')

    # labels
    nx.draw_networkx_labels(subgraph,pos,font_size=8,font_family='sans-serif', labels=proteinsToMap, horizontalalignment='center', verticalalignment='top')


    plt.axis('off')
    plt.savefig("%s/graph.png" % (options.output)) # save as png
    plt.show() # display

