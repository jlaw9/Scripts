## @package PG_Database
#
# This class is responsible for managing interaction with a postgres database

import unittest
import psycopg2

__author__ = 'mattdyer'

class PG_Database:
    #set up some class object
    __host = ""
    __name = ""
    __user = ""
    __password = ""
    __connection = ""
    __cursor = ""


    ## The constructor
    # @param self The object pointer
    # @param host The host name of the database
    # @param name The name of the database
    # @param user The user to login as
    # @param password The password to login with
    def __init__(self, host, name, user, password):
        #set up the new object
        self.__host = host
        self.__name = name
        self.__password = password
        self.__user = user

        #create the connection
        self.__connection = psycopg2.connect(host=databaseURL, database=databaseName, user=databaseUser, password=databasePassword)

        #create the cursor so we can database operations
        self.__cursor = db_connection.cursor()

    ## Execute a query and return the result
    # @param self The object pointer
    # @param query The query to be executed
    # @returns An array containing the query results
    def queryDatabase(self, query):
        #probably a better way to do this
        self.__cursor.execute(query)
        return(self.__cursor)

    ## Kill the connection
    # @param self The object pointer
    def disconnect(self):
        #close both cursor and connection
        self.__cursor.close()
        self.__connection.close()