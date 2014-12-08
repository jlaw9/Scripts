from optparse import OptionParser
import json
import requests
import logging
import time
import datetime

__author__ = 'mattdyer'

urlRoot = 'http://127.0.0.1:8000/api/v1/analysis'

## simple method to get a time stamp
# @returns A timestamp
def getTimestamp():
    #get the time / timestamp
    currentTime = time.time()
    timeStamp = datetime.datetime.fromtimestamp(currentTime).strftime('%Y-%m-%d_%H-%M-%S')

    #return the stamp
    return(timeStamp)

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #set up the logging
    logging.basicConfig(level=logging.DEBUG)

    #add the options to parse
    parser.add_option('-j', '--job', dest='job', help='The job id')
    parser.add_option('-s', '--status', dest='status', help='The status to update it to')
    (options, args) = parser.parse_args()

    message = {'status':options.status}
    headers = {'Content-type': 'application/json'}
    url = '%s/%s/' % (urlRoot, options.job)
    logging.debug('%s - %s' % (getTimestamp(), message))
    logging.debug('%s - %s' % (getTimestamp(), url))

    r = requests.patch(url, data=json.dumps(message), headers=headers)
    logging.debug('%s - %s' % (getTimestamp(), r.status_code))



