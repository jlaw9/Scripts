#generate all the plots for the market project
from optparse import OptionParser
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import matplotlib as mpl
import cartopy.io.shapereader as shpreader
import numpy as np

__author__ = 'mattdyer'


# add labels to a plot
# @param points The plot object
# @param axis The axis object
def autolabel(points, axis, data):
    # attach some text labels
    for i, point in enumerate(points):
        height = float(point.get_height())

        axis.text(point.get_x()+point.get_width()/2., 1.05*height, '%.1f'%data[i],
                ha='center', va='bottom')

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-o', '--output', dest='output', help='The output directory')
    (options, args) = parser.parse_args()

    ############
    #Figure 1a, imaging markets revenue
    ############
    fig, ax1 = plt.subplots()
    revenues = [1.5, 4.0, 4.2, 4.5, 7.3]
    labels = ['Nuclear Medicine', 'MRI', 'CT', 'Ultrasound', 'X-Ray']

    #axis 1 revenue
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, revenues, align='center', alpha=0.4, color='b', label='Revenue')
    ax1.set_ylabel('Revenue (Billions USD)')

    #final additions and then plot
    autolabel(plot1, ax1, revenues)
    plt.xticks(xPos, labels)
    plt.savefig('%s/figure1a.png' % (options.output))
    #plt.show()

    ############
    #Figure 1b, imaging markets cagr
    ############
    fig, ax1 = plt.subplots()
    cagr = [5.8, 4.5, 4.5, 6.2, 5.4]

    #axis 1 revenue
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, cagr, align='center', alpha=0.4, color='r', label='CAGR')
    ax1.set_ylabel('CAGR (%)')

    #final additions and then plot
    autolabel(plot1, ax1, cagr)
    plt.xticks(xPos, labels)
    plt.savefig('%s/figure1b.png' % (options.output))


    ############
    #Figure 2
    ############


    ############
    #Figure 3a - CON states
    ############
    #start to build the map
    states = {
        'Arkansas':'g',
        'Connecticut':'g',
        'Hawaii':'g',
        'Kentucky':'g',
        'Maine':'g',
        'Massachusetts':'b',
        'Michigan':'g',
        'Mississippi':'b',
        'Missouri':'g',
        'New Hampshire':'g',
        'New York':'g',
        'North Carolina':'g',
        'Rhode Island':'g',
        'South Carolina':'g',
        'Tennessee':'b',
        'Vermont':'g',
        'Virginia':'g',
        'West Virginia':'g',
        'District of Columbia':'g'
    }
    plt.figure()
    statesShape = shpreader.natural_earth(resolution='110m', category='cultural', name='admin_1_states_provinces_shp')
    ax = plt.axes([0.01, 0.01, 0.98, 0.98], projection=ccrs.PlateCarree())
    ax.set_xlim([-175, -66.5])
    ax.set_ylim([15, 80])
    cmap = mpl.cm.Blues

    # finish the map

    for state in shpreader.Reader(statesShape).records():
        name = state.attributes['name']
        #print '%s\t%s' % (name, state.attributes['name_alt'])

        #see if key exists
        if name in states:
            ax.add_geometries(state.geometry, ccrs.PlateCarree(), facecolor='b', alpha=0.4, label=name)
        else:
            ax.add_geometries(state.geometry, ccrs.PlateCarree(), facecolor='#FAFAFA', label=name)

    plt.title('States with C.O.N. Policy')
    plt.savefig('%s/figure3a.png' % (options.output))

    ############
    #Figure 4
    ############

    ############
    #Figure 5 - MRI application scatter plot
    ############
    fig, ax1 = plt.subplots()
    data1 = [2500, 2900, 2400, 800, 700, 400, 400, 100]
    data2 = [25.0, 29.0, 24.0, 8.0, 7.0, 4.0, 4.0, 1.0]
    data3 = [97.0, 89.0, 99.5, 99.0, 91.0, 55.0, 19.0, 5.0]
    colors = ['b', 'b', 'b', 'y', 'y', 'r', 'r', 'r']

    labels = ['Spine', 'Brain & Head', 'Extremity', 'Vascular', 'Pelvic & Abdominal', 'Breast', 'Chest, other Cardiac', 'Other' ]
    plt.subplots_adjust(bottom = 0.1)
    plt.scatter(data2, data3, marker = 'o', c =colors, alpha=0.4, s = data1, cmap = plt.get_cmap('Spectral'))
    for label, x, y in zip(labels, data2, data3):
        if label == 'Brain & Head':
            plt.annotate(
                label,
                xy = (x, y), xytext = (60, 30),
                textcoords = 'offset points', ha = 'right', va = 'bottom',
                bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))
        elif label == 'Spine':
            plt.annotate(
                label,
                xy = (x, y), xytext = (-20, -60),
                textcoords = 'offset points', ha = 'right', va = 'bottom',
                bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))
        elif label == 'Chest, other Cardiac':
            plt.annotate(
                label,
                xy = (x, y), xytext = (60, 20),
                textcoords = 'offset points', ha = 'right', va = 'bottom',
                bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))
        else:
            plt.annotate(
                label,
                xy = (x, y), xytext = (-20, 20),
                textcoords = 'offset points', ha = 'right', va = 'bottom',
                bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))

    ax1.set_xlabel('Percent of Procedures (%)')
    ax1.set_ylabel('Percent of Sites Performing (%)')
    plt.savefig('%s/figure5.png' % (options.output))

    ############
    #Figure 6 - Market share MRI
    ############
    fig, ax1 = plt.subplots()
    ax1.axis('equal')
    data = [30, 30, 20, 12, 5, 3]
    labels = ['GE', 'Siemens', 'Philips', 'Toshiba', 'Hitachi', 'Other']
    pie_wedge_collection = plt.pie(data, labels=labels,autopct='%1.1f%%', startangle=90)

    for pie_wedge in pie_wedge_collection[0]:
        pie_wedge.set_edgecolor('white')

    plt.title("MRI Market Share")
    plt.savefig('%s/figure6.png' % (options.output))
    plt.show()