#this script takes in a CSV file and plots a heat map on an image of the globe

from optparse import OptionParser
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import matplotlib.pyplot as plt
import matplotlib as mpl
import csv
import numpy as np

__author__ = 'mattdyer'

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-c', '--csv', dest='csv', help='The CSV file')
    parser.add_option('-o', '--output', dest='output', help='The output directory')
    (options, args) = parser.parse_args()

    #start to build the map
    countries = {}
    shapeName = 'admin_0_countries'
    countriesShape = shpreader.natural_earth(resolution='110m', category='cultural', name=shapeName)
    plt.figure(figsize=(11, 8), dpi=150)
    ax = plt.axes(projection=ccrs.Robinson())

    #we will build a quick hash to store valid country names to check against input
    for country in shpreader.Reader(countriesShape).records():
        name = country.attributes['name_long']
        print name
        countries[name] = 1

    #read in the CSV data
    max = 0.0;
    values = {}

    fileHandle = open(options.csv, 'r')

    for line in fileHandle:
        line = line.strip('\n')

        #skip comments
        if not line.startswith('#'):
            tokens = line.split(',')

            #see if country name is valid
            if tokens[0] in countries:
                #store the value
                values[tokens[0]] = tokens[1]

                #see if we have a new max
                if float(tokens[1]) > max:
                    max = float(tokens[1])
            else:
                #warn
                print '%s not a known country - skipping it' % (tokens[0])

    print max
    cmap = mpl.cm.Blues

    # finish the map

    for country in shpreader.Reader(countriesShape).records():
        name = country.attributes['name_long']

        #see if key exists
        if name in values:
            value = float(values[name])
            ax.add_geometries(country.geometry, ccrs.PlateCarree(), facecolor=cmap(value / float(max), 1), label=name)
        else:
            ax.add_geometries(country.geometry, ccrs.PlateCarree(), facecolor='#FAFAFA', label=name)

    plt.title('MRI Units per Million Population')
    plt.savefig('%s/map.png' % (options.output))
    plt.savefig('%s/map.svg' % (options.output))
    plt.show()