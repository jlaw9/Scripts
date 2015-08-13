#! /usr/bin/env python2.7
__author__ = 'durrantmm'

import mongo
import sys

"""
mongoDAOs.mongotools.annotate_mongo

This module is contains mongo database access functions that are not tied to a specific instance of a class.
"""
project_name = None
hotspot_name = None

def set_project_name(name):
    global project_name, hotspot_name
    project_name = name
    hotspot_name = '%s_hotspot' % name

def save_annotation(chrom, pos, ref, alt, annotations, db=None):
    global hotspot_name
    if db is None:
        client, db = mongo.get_connection()

    hotspot_coll = db[hotspot_name]

    search = {'CHROM': chrom, 'POS': pos, 'REF': ref, 'ALT': alt}
    update = {'$set': {'ANNOTATION': annotations}}
    matched_count = hotspot_coll.update_one(search, update).matched_count

    if matched_count != 1:
        print 'Variant not found in hotspot'

    if db is None:
        client.close()