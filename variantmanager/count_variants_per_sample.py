#! /usr/bin/env python2.7

import pymongo

client = pymongo.MongoClient()
db = client['varman']
col = db['Wales_variants']

samples = col.distinct('SAMPLE')
num_samples = len(samples)
total_count = 0
for sample in samples:
	count = col.find({'SAMPLE': sample}).count()
	print sample, count
	total_count += count

print "Total Samples: ", num_samples
print "Total Variants: ", total_count

client.close()
