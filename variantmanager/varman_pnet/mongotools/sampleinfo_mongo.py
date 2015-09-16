#! /usr/bin/env python2.7
__author__ = 'durrantmm'

from pymongo import MongoClient
import mongo

"""
mongoDAOs.mongotools.sampleinfo_mongo

This module is contains mongo database access functions that are not tied to a specific instance of a class.
"""
project_name = None


def set_project_name(name):
    global project_name
    project_name = name

def add_new_sample(new_sample, db=None):
    if db is None:
        client, db = mongo.get_connection()

    sampleinfo_coll = db['sample_info']
    sampleinfo_coll.update_one(new_sample, {'$set': new_sample}, upsert=True)

    if db is None:
        client.close()

def delete_sample(sample, db=None):
    if db is None:
        client, db = mongo.get_connection()

    sampleinfo_coll = db['sample_info']
    sampleinfo_coll.remove_one({"project_name": project_name, "SAMPLE": sample})

    if db is None:
        client.close()

def get_sample_info(db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    proj_collection = db['sample_info']
    results = proj_collection.find({"PROJECT": project_name})
    info = {}

    for result in results:
        info.update({result['SAMPLE']: {field: result[field] for field in result.keys() if field != "SAMPLE"}})

    if db is None:
        client.close()

    return info

def is_sample(sample, db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    proj_collection = db['sample_info']
    result = proj_collection.find_one({"PROJECT": project_name, "SAMPLE": sample})

    if result is not None:
        return True
    else:
        return False

def is_fully_annotated(sample, db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    proj_collection = db['sample_info']
    result = proj_collection.find_one({"PROJECT": project_name, "SAMPLE": sample})

    if "FULLY_ANNOTATED" in result.keys() and result['FULLY_ANNOTATED'] is True:
        return True
    else:
        return False

def get_vcf_files():
    sample_info = get_sample_info()

    vcf_files = {}
    for id in sample_info:
        vcf_files.update({id: sample_info[id]['VCF']})

    return vcf_files

def get_samples(db=None):
    if db is None:
        client, db = mongo.get_connection()

    sample_info = get_sample_info(db)

    samples = []
    for id in sample_info:
        samples.append(id)

    if db is None:
        client.close()

    return samples


def get_bam_files():
    sample_info = get_sample_info()

    vcf_files = []
    for id in sample_info:
        vcf_files.append((id, sample_info[id]['BAM']))

    return vcf_files


def has_sample_info(db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    sample_info_coll = db['sample_info']
    info_doc = sample_info_coll.find_one({"PROJECT": project_name})

    if db is None:
        client.close()

    if info_doc is not None:
        return True
    else:
        return False

def get_affected(sample_name, db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    sample_info_coll = db['sample_info']
    info_doc = sample_info_coll.find_one({"project_name": project_name, "SAMPLE": sample_name})

    if db is None:
        client.close()

    return info_doc['AFFECTED']

def get_affected_dict(db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    sample_info_coll = db['sample_info']
    cursor = sample_info_coll.find({"PROJECT": project_name})
    out_dict = {}

    for doc in cursor:
        try:
            out_dict.update({doc['SAMPLE']: doc['AFFECTED']})
        except KeyError:
            out_dict.update({doc['SAMPLE']: None})

    if db is None:
        client.close()

    return out_dict

def change_sample_field(sample, field, value, db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    sample_info_coll = db['sample_info']

    sample_info_coll.update_one({'PROJECT': project_name, 'SAMPLE': sample}, {'$set': {field: value}})

    if db is None:
        client.close()