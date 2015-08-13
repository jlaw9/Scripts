from pymongo import MongoClient

client = MongoClient()
db = client['varman']
coll = db['Wales']

with open('tmp.out', 'w') as out:
	for result in db.Wales.aggregate(
			[{"$group": {"_id": {"CHROM": "$CHROM", "POS": "$POS", "ALT": "$ALT", "REF": "$REF"}}}]):
		result = result['_id']
		alt = ",".join([str(val) for val in result['ALT']])

		out_line = [str(val) for val in [result['CHROM'], result['POS'], result['REF'], alt]]

		out.write("\t".join(out_line) + "\n")
