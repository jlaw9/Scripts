from optparse import OptionParser
import sys
import requests
import json
import base64

__author__ = 'mattdyer'

## Print something out formatted nicely
# @param title The title of what you are printing
# @param content The string to print
# @returns The JSON request object
def printBlock(title, content):
    #create a simple json document
    print '#########################'
    print '# %s' % title
    print '#########################'
    print content
    print ''

## Push a document to TrueVault
# @param url The url to push the document too
# @param document The base64 encoded document
# @param token The API token
# @param label The label of the type we are posting (e.g. document or schema)
# @returns The TrueVault API response JSON object
def pushDocument(url, document, token, label):
    params = {label : document}

    #make the request and store the results
    r = requests.post(url, data=params, auth=(token, ''))

    jsonRequest = r.json()
    return(jsonRequest)

## Get a list of documents from a search
# @param url The url to push the document too
# @param search The base64 encoded search
# @param token The API token
# @returns The TrueVault API response JSON object
def getDocuments(url, search, token):
    params = {"search_option" : search}
    #make the request and store the results
    r = requests.get(url, auth=(token, ''), params=params)

    jsonRequest = r.json()
    return(jsonRequest)

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-n', '--state', dest='state', help='State to search (e.g. Utah, New York, etc)')
    (options, args) = parser.parse_args()

    #wouldn't want to hardcode these, but since I am just testing things out it is ok for now
    token = 'cf5e1ca2-ee0c-48c6-9c81-63289e39a350'
    url = 'https://api.truevault.com/v1'
    vaultName = 'test'
    vaultID = '0f43d968-ba68-45b3-b79a-01d5d173efac'

    #if a name wasn't provided then just use matt
    if(not options.state):
        options.state = 'Utah'

    #build the search schema
    #commenting this out since schemas have to be unique and I already ran this, but leaving it hear as an example

    #schema = {
    #    'name':'user',
    #    'fields':[
    #        {
    #            'name':'name',
    #            'index':True,
    #            'type': 'string'
    #        },
    #        {
    #            'name':'lives_in',
    #            'index':True,
    #            'type': 'string'
    #        }
    #    ]
    #}

    #print out the schema
    #printBlock('Our Schema - JSON String', json.dumps(schema, sort_keys=True, indent=4))

    #base64 encode the json string and print it out
    #encodedSchema = base64.b64encode(json.dumps(schema, sort_keys=True, indent=4))
    #printBlock('Our Schema - base64 Encoded', encodedSchema)

    #publish the doc to TrueVault
    #response = pushDocument('%s/vaults/%s/schemas' % (url, vaultID), encodedSchema, token, 'schema')
    #schemaID = response['schema']['id']
    #printBlock('Schema POST Response', json.dumps(response, sort_keys=True, indent=4))

    #schemas have to be unique so after the first time of running this script the above won't work so just hardcoding the schema id for now
    schemaID = 'd3db444b-d402-45ee-b7cb-2bf09c02d256'

    # now build the document

    doc = {
        'schema_id' : schemaID,
        'users':[
            {
                'name':'Matt',
                'lives_in':'Utah'
            },
            {
                'name':'Ian',
                'lives_in':'Illinois'
            },
            {
                'name':'Alex',
                'lives_in':'New York'
            },
        ]
    }

    #print out the doc
    printBlock('Our Document - JSON String', json.dumps(doc, sort_keys=True, indent=4))

    #base64 encode the json string and print it out
    encodedDoc = base64.b64encode(json.dumps(doc, sort_keys=True, indent=4))
    printBlock('Our Document - base64 Encoded', encodedDoc)

    #publish the doc to TrueVault
    response = pushDocument('%s/vaults/%s/documents' % (url, vaultID), encodedDoc, token, 'document')
    documentID = response['document_id']
    printBlock('Document POST Response', json.dumps(response, sort_keys=True, indent=4))
    printBlock('Docuemnt ID', documentID)

    #now run a search
    search = {
        'filter':{
            'lives_in':options.state
        },
        'page':1,
        "per_page":10
    }

    #print out the search
    printBlock('Our Search - JSON String', json.dumps(search, sort_keys=True, indent=4))

    #base64 encode the json string and print it out
    encodedSearch = base64.b64encode(json.dumps(search, sort_keys=True, indent=4))
    printBlock('Our Search - base64 Encoded', encodedSearch)

    #publish the search request
    #response = getDocuments('%s/vaults/%s/?search_option=%s' % (url, vaultID, encodedSearch), token)
    response = getDocuments('%s/vaults/%s/' % (url, vaultID), encodedSearch, token)
    printBlock('Search POST Response', json.dumps(response, sort_keys=True, indent=4))