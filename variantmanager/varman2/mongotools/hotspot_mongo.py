#! /usr/bin/env python2.7
__author__ = 'durrantmm'

from pymongo import ASCENDING
import mongo, variants_mongo
from varman2 import genotypetools
import sys

"""
mongoDAOs.mongotools.variants_mongo

This module is contains mongo database access functions that are not tied to a specific instance of a class.
"""
project_name = None
hotspot_name = None

def set_project_name(name):
    global project_name, hotspot_name
    project_name = name
    hotspot_name = '%s_hotspot' % name

def get_collection(db=None):
    global hotspot_name
    if db is None:
        client, db = mongo.get_connection()

    hotspot_coll = db[hotspot_name]

    if db is None:
        client.close()

    return hotspot_coll

def add_variant(variant, db=None):
    global hotspot_name
    if db is None:
        client, db = mongo.get_connection()

    variants_coll = db[hotspot_name]

    final_qc_inc = 0
    cov_qc_inc = 0
    af_qc_inc = 0
    multi_allele_inc = 0

    if variant['FINAL_QC'] == 'PASS':
        final_qc_inc = 1
    if variant['COV_QC'] == 'PASS':
        cov_qc_inc = 1
    if variant['AF_QC'] == 'PASS':
        af_qc_inc = 1
    if variant['MULTI_ALLELE_QC'] == 'PASS':
        multi_allele_inc = 1

    wt_inc = 0
    het_alt_inc = 0
    het_inc = 0
    hom_inc = 0
    nocall_inc = 0

    zygos = genotypetools.get_zygosity(variant['GT_calc'])

    if 'NOCALL' in variant['FILTER']:
        nocall_inc = 1
    elif zygos == 'wt':
        wt_inc = 1
    elif zygos == 'het_alt':
        het_alt_inc = 1
    elif zygos == 'het':
        het_inc = 1
    elif zygos == 'hom':
        hom_inc = 1
    elif zygos == 'nocall':
        nocall_inc = 1

    entry = {'CHROM': variant['CHROM'], 'POS': variant['POS'], 'REF': variant['REF'], 'ALT': variant['ALT']}

    variants_coll.update_one(entry, {'$inc': {'orig_stats.qc.total_count': 1,
                                              'orig_stats.qc.final_qc_count': final_qc_inc,
                                              'orig_stats.qc.cov_qc_count': cov_qc_inc,
                                              'orig_stats.qc.af_qc_count': af_qc_inc,
                                              'orig_stats.qc.multi_allele_qc_count': multi_allele_inc,
                                              'orig_stats.zygosity.wt_count': wt_inc,
                                              'orig_stats.zygosity.het_count': het_inc,
                                              'orig_stats.zygosity.het_alt_count': het_alt_inc,
                                              'orig_stats.zygosity.hom_count': hom_inc,
                                              'orig_stats.zygosity.nocall_count': nocall_inc},
                                     '$addToSet': {'orig_samples': variant['SAMPLE']}},
                             upsert=True)

    if db is None:
        client.close()

def add_hotspot_variant(variant, db=None):
    global hotspot_name
    if db is None:
        client, db = mongo.get_connection()

    hotspot_coll = db[hotspot_name]

    final_qc_inc = 0
    cov_qc_inc = 0
    af_qc_inc = 0
    multi_allele_inc = 0

    if variant['FINAL_QC'] == 'PASS':
        final_qc_inc = 1
    if variant['COV_QC'] == 'PASS':
        cov_qc_inc = 1
    if variant['AF_QC'] == 'PASS':
        af_qc_inc = 1
    if variant['MULTI_ALLELE_QC'] == 'PASS':
        multi_allele_inc = 1

    wt_inc = 0
    het_inc = 0
    het_alt_inc = 0
    hom_inc = 0
    nocall_inc = 0

    zygos = genotypetools.get_zygosity(variant['GT_calc'])

    if 'NOCALL' in variant['FILTER']:
        nocall_inc = 1
    elif zygos == 'wt':
        wt_inc = 1
    elif zygos == 'het_alt':
        het_inc = 1
    elif zygos == 'het':
        het_inc = 1
    elif zygos == 'hom':
        hom_inc = 1
    elif zygos == 'nocall':
        nocall_inc = 1

    chrom, pos, ref, alt = variant['CHROM'], variant['POS'], variant['REF'], variant['ALT']
    entry = {'CHROM': chrom, 'POS': pos, 'REF': ref, 'ALT': alt}
    update = {'$inc': {'hotspot_stats.qc.total_count': 1,
                          'hotspot_stats.qc.final_qc_count': final_qc_inc,
                          'hotspot_stats.qc.cov_qc_count': cov_qc_inc,
                          'hotspot_stats.qc.af_qc_count': af_qc_inc,
                          'hotspot_stats.qc.multi_allele_qc_count': multi_allele_inc,
                          'hotspot_stats.zygosity.wt_count': wt_inc,
                          'hotspot_stats.zygosity.het_count': het_inc,
                          'hotspot_stats.zygosity.het_alt_count': het_alt_inc,
                          'hotspot_stats.zygosity.hom_count': hom_inc,
                          'hotspot_stats.zygosity.nocall_count': nocall_inc}
                 }
    modified_count = hotspot_coll.update_one(entry, update).modified_count

    if modified_count != 1:
        pass

    if db is None:
        client.close()

def get_hotspot_vars(db=None):
    global hotspot_name
    if db is None:
        client, db = mongo.get_connection()

    hotspot_coll = db[hotspot_name]

    sortby = [('CHROM', ASCENDING), ('POS', ASCENDING)]
    hotspot_cursor = hotspot_coll.find().sort(sortby)

    if db is None:
        client.close()

    return hotspot_cursor

def get_variant(chrom, pos, ref, alt, db=None):
    global hotspot_name
    if db is None:
        client, db = mongo.get_connection()

    hotspot_coll = db[hotspot_name]

    hotspot = hotspot_coll.find_one({"CHROM": chrom, "POS": pos, "REF": ref, "ALT": alt})

    if db is None:
        client.close()

    return hotspot

def has_annotation(chrom, pos, ref, alt, db=None):
    global hotspot_name
    if db is None:
        client, db = mongo.get_connection()

    hotspot_coll = db[hotspot_name]

    hotspot = hotspot_coll.find_one({"CHROM": chrom, "POS": pos, "REF": ref, "ALT": alt})

    if db is None:
        client.close()

    if 'ANNOTATION' in hotspot.keys():
        return True
    else:
        return False

def get_valid_hotspot_vars(db=None):
    global hotspot_name
    if db is None:
        client, db = mongo.get_connection()

    hotspot_coll = db[hotspot_name]

    sortby = [('CHROM', ASCENDING), ('POS', ASCENDING)]

    search_query = {'orig_stats.qc.final_qc_count': {'$gt': 0},
                    '$or': [
                        {'orig_stats.zygosity.het_count': {'$gt': 0}},
                        {'orig_stats.zygosity.hom_count': {'$gt': 0}}]
                    }

    hotspot_cursor = hotspot_coll.find(search_query).sort(sortby)

    if db is None:
        client.close()

    return hotspot_cursor

def get_final_hotspot_vars(db=None):
    global hotspot_name
    if db is None:
        client, db = mongo.get_connection()

    hotspot_coll = db[hotspot_name]

    sortby = [('CHROM', ASCENDING), ('POS', ASCENDING)]

    search_query = {'ANNOTATION': {'$exists': True}, 'hotspot_stats': {'$exists': True}}

    hotspot_cursor = hotspot_coll.find(search_query).sort(sortby)

    if db is None:
        client.close()

    return hotspot_cursor

def index_hotspot(db=None):
    global project_name, hotspot_name

    index = [("CHROM", ASCENDING), ("POS", ASCENDING)]

    if db is None:
        client, db = mongo.get_connection()

    hotspot_coll = db[hotspot_name]
    hotspot_coll.create_index(index)

    if db is None:
        client.close()

def is_hotspot(chrom, pos, ref, alt, db=None):
    global hotspot_name
    if db is None:
        client, db = mongo.get_connection()

    query = {'CHROM': chrom, 'POS': pos, 'REF': ref, 'ALT': alt}
    hotspot_coll = db[hotspot_name]
    match = hotspot_coll.find_one(query)

    if db is None:
        client.close()

    if match:
        return True
    else:
        return False