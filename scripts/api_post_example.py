import json
import requests

__author__ = 'mattdyer'





#start here when the script is launched
if (__name__ == "__main__"):
    url = "http://127.0.0.1:8000/api/v1/analysis/"
    data = {'name': 'api_test123', 'date':'June 4, 2014', 'description':'testing the api', 'type':'Transposon Screen', 'status':'Pending', 'parameters':'{\"param1\":\"value1\"}'}
    headers = {'Content-type': 'application/json'}
    r = requests.post(url, data=json.dumps(data), headers=headers)
    print r


    json_string = "{u'analysis_type': u'transposon_single_sample', u'files': {u'/Volumes/HD/mattdyer/Downloads/Experiment3-NEP-286-IonXpress_001_rawlib_mapped_to_genes-2014-05-22.txt': u'on', u'/Volumes/HD/mattdyer/Downloads/Experiment2-NEP285-IonXpress_005_rawlib_mapped_to_genes-2014-05-22.txt': u'on'}, u'settings': {u'read_coverage_minimum': u'50', u'read_size_minimum': u'40', u'maximum_distance': u'10000'}}"
    json_string = json_string.replace("u'", "\"")
    json_string = json_string.replace("'", "\"")

    try:
        print json_string
        decoded = json.loads(json_string)

        # pretty printing of json-formatted string
        print json.dumps(decoded, sort_keys=True, indent=4)

    except (ValueError, KeyError, TypeError):
        print "JSON format error "

