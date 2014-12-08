#generate all the plots for the market project
from optparse import OptionParser
import matplotlib.pyplot as plt
import prettyplotlib as ppl
import numpy as np

__author__ = 'mattdyer'


# add labels to a plot
# @param points The plot object
# @param axis The axis object
def autolabel(points, axis):
    # attach some text labels
    for point in points:
        height = point.get_height()
        axis.text(point.get_x()+point.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-o', '--output', dest='output', help='The output directory')
    (options, args) = parser.parse_args()

    ############
    #Figure 1, platform services
    ############
    fig, ax1 = plt.subplots()
    revenues = [77, 93, 110, 131, 155, 181, 210]
    cagr = [None, 20.8, 18.6, 18.5, 18.4, 17.2, 15.8]
    labels = ['2010', '2011', '2012', '2013', '2014', '2015', '2016']

    #axis 1 revenue
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, revenues, align='center', alpha=0.4, color='b', label='Revenue')
    ax1.set_ylabel('Revenue (Billions USD)')

    #axis 2, CAGR
    ax2 = ax1.twinx()
    plot2 = ax2.plot(xPos, cagr, linewidth=2, marker='o', label='CAGR', color='r', alpha=0.4)
    ax2.set_ylabel('CAGR (%)')

    #final additions and then plot
    plt.xticks(xPos, labels)
    plt.title('Cloud Services Market')
    plt.legend(plot1, ['Revenue'], loc='upper left')
    plt.legend(plot2, ['CAGR'], loc='upper right')
    plt.savefig('%s/figure1.png' % (options.output))
    #plt.show()

    ############
    #Figure 2, market breakdown by submarket
    ############
    plt.subplots()
    markets = ['Security Services', 'IaaS', 'SaaS', 'PaaS', 'Advertising']
    data = [
        [1,1,1,1,1,2,3],
        [3,4,6,9,13,18,24],
        [11,13,16,20,24,28,33],
        [27,29,31,36,40,45,50],
        [34,43,53,61,71,83,95]
    ]

    #set the colors
    colors = ['r', 'y', 'g', 'b', 'c']

    #plot the data
    index = np.arange(len(labels))
    offset = np.array([0.0] * len(labels))
    for row in range(len(data)):
        plt.bar(index, data[row], label=markets[row], align='center', alpha=0.4, bottom=offset, color=colors[row])
        offset += data[row]

    plt.xticks(xPos, labels)
    plt.ylabel('Revenue (Billions USD)')
    plt.legend(loc='upper left')
    plt.title('Cloud Services Submarkets')
    plt.savefig('%s/figure2.png' % (options.output))

    ############
    #Figure 3, CAGR by submarket
    ############
    plt.subplots()
    markets = ['Security\nServices', 'IaaS', 'SaaS', 'PaaS', 'Advertising', 'Cloud\nServices\nTotal']
    data = [26.7, 41.3, 19.5, 27.7, 17.0, 17.7]

    #plot the data
    index = np.arange(len(markets))
    plot = plt.barh(index, data, color='b', align='center', alpha=0.4)

    #set the individual colors now
    plot[0].set_color('r')
    plot[1].set_color('y')
    plot[2].set_color('g')
    plot[3].set_color('b')
    plot[4].set_color('c')
    plot[5].set_color('k')

    plt.yticks(xPos, markets)
    plt.xlabel('5-Year CAGR (2011-2016) (%)')
    plt.title('Cloud Services CAGR by Submarket' )
    plt.savefig('%s/figure3.png' % (options.output))
    plt.show()

    #http://stackoverflow.com/questions/5147112/matplotlib-how-to-put-individual-tags-for-a-scatter-plot