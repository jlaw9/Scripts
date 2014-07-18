
from optparse import OptionParser
import json

__author__ = 'mattdyer'

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-i', '--in', dest='infile', help='Input JSON file')
    parser.add_option('-o', '--out', dest='outfile', help='The output JSON file')
    parser.add_option('-s', '--status', dest='status', help='The status to update it to')
    (options, args) = parser.parse_args()

    #read in the json file
    jsonData = open(options.infile)
    fileData = json.load(jsonData)

    #set the status
    fileData['status'] = options.status

    #dump the file
    with open(options.outfile, 'w') as newJSONFile:
            json.dump(fileData, newJSONFile, sort_keys=True, indent=4)