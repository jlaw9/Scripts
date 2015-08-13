#! /usr/bin/env python2.7
__author__ = 'durrantmm'

import mongo

"""
mongoDAOs.mongotools.config

This module contains mongo database access functions that are not tied to a specific instance of a class.
"""

project_name = None


def set_project_name(name):
    global project_name
    project_name = name

def create_project_config(config, db=None):
    if db is None:
        client, db = mongo.get_connection()

    configs_coll = db['configs']

    configs_coll.replace_one(config, config, upsert=True)

    if db is None:
        client.close()

    return config


def has_config(db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    configs_coll = db['configs']

    config_count = configs_coll.find({'project_name': project_name}).count()

    if db is None:
        client.close()

    if config_count > 0:
        return True
    else:
        return False


def get_project_config(db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    configs_coll = db['configs']

    project_config = configs_coll.find_one({'project_name': project_name})

    if db is None:
        client.close()

    return project_config


def change_config_field(field, value, db=None):
    global project_name

    if db is None:
        client, db = mongo.get_connection()

    config_coll = db['configs']

    config_coll.update_one({'project_name': project_name}, {'$set': {field: value}})

    if db is None:
        client.close()
