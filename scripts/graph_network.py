import networkx as nx
import matplotlib.pyplot as plt
from optparse import OptionParser

__author__ = 'mattdyer'

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-n', '--network', dest='network', help='Protein interaction network file')
    parser.add_option('-o', '--output', dest='output', help='The output directory')
    parser.add_option('-t', '--targets', dest='targets', help='The drug target file')
    (options, args) = parser.parse_args()

    #build a graph
    graph = nx.Graph()

    #load the target file
    file = open(options.targets, 'r')
    targetProteins = {}

    #loop over and store the targeted proteins
    for protein in file:
        protein = protein.strip('\n\r')
        targetProteins[protein] = 1

    #close the file
    file.close()

    #parse the file now
    file = open(options.network, 'r')
    nontargetProteinsInNetwork = {}
    targetProteinsInNetwork = {}

    #loop over the file and build the network
    for line in file:
        line = line.rstrip('\n\r')
        tokens = line.split('\t')
        protein1 = tokens[0]
        protein2 = tokens[2]

        #exclude self interactions and see if the graph already has the edge or not
        if not protein1 == protein2 and not graph.has_edge(protein1, protein2) and not graph.has_edge(protein2, protein1):
            graph.add_edge(protein1, protein2)

            if not protein1 in targetProteins:
                nontargetProteinsInNetwork[protein1] = 1
            else:
                targetProteinsInNetwork[protein1] = 1

            if not protein2 in targetProteins:
                nontargetProteinsInNetwork[protein2] = 1
            else:
                targetProteinsInNetwork[protein2] = 1

    #close the file
    file.close()

    #layout the graph
    pos=nx.spring_layout(graph) # positions for all nodes

    # nodes
    nx.draw_networkx_nodes(graph,pos,node_size=15,node_color='blue',nodelist=list(nontargetProteinsInNetwork.keys()))
    nx.draw_networkx_nodes(graph,pos,node_size=15,node_color='yellow',nodelist=list(targetProteinsInNetwork.keys()))

    # edges
    nx.draw_networkx_edges(graph,pos,alpha=.4,edge_color='grey')

    # labels
    #nx.draw_networkx_labels(G,pos,font_size=4,font_family='sans-serif', horizontalalignment='center', verticalalignment='top')

    plt.axis('off')
    plt.savefig("%s/graph.png" % (options.output)) # save as png
    plt.show() # display

    #plot the degree plots
    degree_sequence = sorted(nx.degree(graph).values(), reverse=True)
    plt.loglog(degree_sequence, 'b-', 'o')
    plt.title('Degree rank plot')
    plt.ylabel('Degree')
    plt.xlabel('Rank')

    plt.savefig('%s/degree_histogram.png' % (options.output))
    plt.show()

