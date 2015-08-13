__author__ = 'matt'

from mongotools import config_mongo, sampleinfo_mongo, variants_mongo, hotspot_mongo, annotate_mongo, hotspothist_mongo

def set_project_name(name):

    config_mongo.set_project_name(name)
    sampleinfo_mongo.set_project_name(name)
    variants_mongo.set_project_name(name)
    hotspot_mongo.set_project_name(name)
    annotate_mongo.set_project_name(name)
    hotspothist_mongo.set_project_name(name)
