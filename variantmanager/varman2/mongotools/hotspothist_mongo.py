#! /usr/bin/env python2.7
__author__ = 'durrantmm'

from pymongo import MongoClient
import mongo

"""
mongoDAOs.mongotools.sampleinfo_mongo

This module is contains mongo database access functions that are not tied to a specific instance of a class.
"""
project_name = None
variants_name = None


def set_project_name(name):
    global project_name, variants_name
    project_name = name
    variants_name = '%s_variants' % name

def add_new_hist(number, db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    new_hist = {"PROJECT": project_name, "NUMBER": number}
    hotspothist_coll = db['hotspot_history']
    hotspothist_coll.update_one(new_hist, {'$set': new_hist}, upsert=True)

    if db is None:
        client.close()

def get_next_number(db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    hotspothist_coll = db['hotspot_history']
    total_count = hotspothist_coll.find({"PROJECT": project_name}).count()

    if db is None:
        client.close()

    return total_count + 1

def is_hotspot_hist(number, db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    hotspothist_coll = db['hotspot_history']
    hotspot_hist = hotspothist_coll.find_one({"PROJECT": project_name, "NUMBER": number})

    if db is None:
        client.close()

    if hotspot_hist is None:
        return False
    else:
        return True

def has_loaded_hotspots(number, db=None):
    global project_name, variants_name
    if db is None:
        client, db = mongo.get_connection()

    variants_coll = db[variants_name]
    var_match = variants_coll.find_one({"PROJECT": project_name, "TYPE": "hotspot", "NUMBER": number})

    if db is None:
        client.close()

    if var_match is None:
        return False
    else:
        return True


