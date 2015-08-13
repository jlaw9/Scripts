#! /usr/bin/env python2.7

import pymongo

client = pymongo.MongoClient()
db = client['varman']
col = db['sample_info']


info = col.find_one()
samples2 = info['info'].keys()
print len(info['info'].keys())
