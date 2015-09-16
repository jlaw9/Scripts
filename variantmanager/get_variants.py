#!/usr/bin/env python2.7

from pymongo import MongoClient

client = MongoClient()
db = client['varman']

coll = db['Wales_variants']

for var in coll.find({"TYPE": "orig"}):
	# if var['GT_calc'] == "0/1" and len(var['ALT']) == 1:
		# print var['CHROM'], var['POS'], var['REF'], var['ALT'][0], var['AF_calc']
	if var['GT_orig'] == "0/1" and len(var['ALT']) == 1:
		print var['CHROM'], var['POS'], var['REF'], var['ALT'][0], var['AF_calc']
