#! /usr/bin/env python2.7
__author__ = 'durrantmm'

from pymongo import ASCENDING
import mongo, hotspot_mongo, sampleinfo_mongo

"""
mongoDAOs.mongotools.variants_mongo

This module is contains mongo database access functions that are not tied to a specific instance of a class.
"""
project_name = None
variants_name = None

def set_project_name(name):
    global project_name, variants_name
    project_name = name
    variants_name = '%s_variants' % name

def get_collection(db=None):
    global variants_name
    if db is None:
        client, db = mongo.get_connection()

    variants_coll = db[variants_name]

    if db is None:
        client.close()

    return variants_coll

def add_variant(variant, db=None):
    global variants_name
    if db is None:
        client, db = mongo.get_connection()

    variants_coll = db[variants_name]
    variants_coll.insert(variant)

    if db is None:
        client.close()


def is_sample_loaded(sample, type, db=None):
    global variants_name
    if db is None:
        client, db = mongo.get_connection()

    variants_coll = db[variants_name]

    sample_var = variants_coll.find_one({'TYPE': type, 'SAMPLE': sample})

    if db is None:
        client.close()

    if sample_var is not None:
        return True
    else:
        return False

def get_sample_vars(sample, type, db=None):
    global variants_name

    if db is None:
        client, db = mongo.get_connection()

    variants_coll = db[variants_name]

    sample_vars = variants_coll.find({'TYPE': type, 'SAMPLE': sample})

    return sample_vars

def count_samples(db=None):
    global variants_name
    if db is None:
        client, db = mongo.get_connection()

    variants_coll = db[variants_name]

    sample_vars = variants_coll.distinct('SAMPLE')

    return len(sample_vars)

def index_variants(db=None):
    global project_name, variants_name

    index = [("TYPE", ASCENDING), ("CHROM", ASCENDING), ("POS", ASCENDING)]

    if db is None:
        client, db = mongo.get_connection()

    variants_coll = db[variants_name]
    variants_coll.create_index(index)

    if db is None:
        client.close()

def drop_variants_index(db=None):
    global project_name, variants_name

    if db is None:
        client, db = mongo.get_connection()

    variants_coll = db[variants_name]
    variants_coll.drop_indexes()

    if db is None:
        client.close()
