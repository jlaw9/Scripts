from pymongo import MongoClient

client = MongoClient()

db = client['varman']
collection = db['Wales_hotspot']

for doc in collection.find():
	print doc
