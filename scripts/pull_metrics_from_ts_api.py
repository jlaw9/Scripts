from optparse import OptionParser
import sys
import requests

__author__ = 'mattdyer'

## Make an API call and return the request object
# @param url The url to call
# @returns The JSON request object
def makeAPICall(url):
    headers = {'Content-type': 'application/json'}
    r = requests.get(url, headers=headers, auth=('ionadmin', 'ionadmin'))

    #see if the call was good
    if(not r.status_code == 200):
        print "Error: invalid API call, %i status code returned" % (r.status_code)
        sys.exit(1)

    jsonRequest = r.json()

    #now lets pull our data
    #print json.dumps(jsonRequest, sort_keys=True, indent=4)

    return(jsonRequest)


#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-u', '--url', dest='url', help='The Torrent Suite URL including the http:// part')
    parser.add_option('-i', '--id', dest='id', help='The Torrent Suite run ID')
    parser.add_option('-n', '--name', dest='name', help='The Torrent Suite run name')
    (options, args) = parser.parse_args()

    #check to make sure either ID or name was provided
    if(not options.id and not options.name):
        print "Error: must provide either run ID (--id) or name (--name)"
        sys.exit(1)

    #check to make sure URL was provided
    if(not options.url):
        print "Error: must provide URL (--url)"
        sys.exit(1)

    #create the connection to Torrent Suite API
    url = options.url + '/rundb/api/v1/results/'

    #if we have an id, use that
    if(options.id):
        url += '?id=%s&format=json' % (options.id)
    #otherwise use the run name
    else:
        url += '?resultsName=%s&format=json' % (options.name)

    #make the request and get the JSON String
    jsonRequest = makeAPICall(url)

    #grab the 30X number from the coverageAnalysisLite plugin
    if(jsonRequest['objects'][0]['pluginStore']['coverageAnalysisLite']['Target base coverage at 30x']):
        print '30x Coverage: %s' % (jsonRequest['objects'][0]['pluginStore']['coverageAnalysisLite']['Target base coverage at 30x'])

    #grab the links
    libMetricsLink = options.url + jsonRequest['objects'][0]['libmetrics'][0] + '?format=json'
    analysisMetricsLink = options.url + jsonRequest['objects'][0]['analysismetrics'][0] + '?format=json'
    qualityMetricsLink = options.url + jsonRequest['objects'][0]['qualitymetrics'][0] + '?format=json'

    #grab the basecaller.json file for the run, if the id was not provided then we will need to grab it
    if(not options.id):
        options.id = jsonRequest['objects'][0]['id']

    #now build the url to pull
    basecallerLink = ('/report/%s/metal/basecall_results/BaseCaller.json' % (options.id))
    basecallerLink = options.url + basecallerLink
    print basecallerLink

    #it's not a real API call, but should still work
    jsonRequest = makeAPICall(basecallerLink)

    #grab the polyclonal number
    if(jsonRequest['BeadSummary']['lib']['polyclonal']):
        print "Polyclonal Reads: %s" % jsonRequest['BeadSummary']['lib']['polyclonal']





