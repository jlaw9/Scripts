#! /usr/bin/env python2.7
__author__ = 'durrantmm'

from pymongo import MongoClient

"""
mongoDAOs.mongotools.mongo

This module contains basic mongo methods.
"""

def get_connection():
    client = MongoClient()
    db = client['varman']

    return client, db

def delete_collection(collection):
    client = MongoClient()
    db = client['varman']

    db.drop_collection(collection)

def wait_for_few_connections(num_connections, db=None):
    if db is None:
        client, db = get_connection()

    client_count = db.command("serverStatus")["connections"]['current']
    while client_count > num_connections:
        client_count = db.command("serverStatus")["connections"]['current']

    if db is None:
        client.close()