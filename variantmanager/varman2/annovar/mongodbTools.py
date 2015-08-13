#! /usr/bin/env python2.7
__author__ = 'durrantmm'

from pymongo import MongoClient


class MongoDBTools:
    @staticmethod
    def write_annovar_vcf(vcf_path, collection_name, logger=None):
        client = MongoClient()
        db = client['variants']
        proj_collection = db[collection_name]

        aggregate_command = {"$group": {"_id": {CHROM: "$CHROM", POS: "$POS", ID: "ID", REF: "$REF", ALT: "$ALT"}}}
        distinct_snps = proj_collection.aggregate(aggregate_command)
        for result in distinct_snps:
            print result
