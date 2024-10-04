#!/usr/bin/python3
import os
import psycopg2
from python.config_loader import ConfigLoader

class ConnectionError(BaseException):
    """
    Exception raised for errors in the DB connection.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

class QueryError(BaseException):
    """
    Exception raised for errors in the DB Queries.
    
    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

"""
    PostgreSQL client with basic functions.
"""
class PsqlDB:

    def __init__(self, config_path, filename, section):
        """
        Constructor
        To provide the configuration parameters to Postgres service, are two alternatives.
        You can mix over this options.
        
        From environment variables file:

            - POSTGRES_DBNAME, the database name used to connect in the service.
            - POSTGRES_HOST, the host name or IP value used to connect in the service.
            - POSTGRES_PORT, the port number used to connect in the service.
            - POSTGRES_USER, the user name used to authentication in the service.
            - POSTGRES_PASS, the password value used to authentication in the service.

        From configuration file:
            - config_path = 'the/path/to/config/file/'
            - filename = 'db.cfg' (see the README file for format and var names)
            - section = 'session_name_to_db_config'
        
        To support the secrets from swarm mode, you can set the user and password to Geoserver:
            - POSTGRES_USER_FILE, user, the location of secret file on memory in runtime;
            - POSTGRES_PASS_FILE, password, the location of secret file on memory in runtime;
        """
        self.conn = None
        self.cur = None

        try:
            conf = ConfigLoader(config_path, filename, section)
            self.params = conf.get()
            # get user and password for postgres from secrets
            self.db_user = os.getenv("POSTGRES_USER_FILE", self.params["user"])
            if os.path.exists(self.db_user):
                self.db_user = open(self.db_user, 'r').read()
            self.db_pass = os.getenv("POSTGRES_PASS_FILE", self.params["password"])
            if os.path.exists(self.db_pass):
                self.db_pass = open(self.db_pass, 'r').read()
        except Exception as configError:
            raise configError
        
        # read connection parameters
        self.db_user=self.params["user"] if self.params["user"] else os.getenv("POSTGRES_USER", "postgres")
        self.db_pass=self.params["password"] if self.params["password"] else os.getenv("POSTGRES_PASS", "postgres")
        self.db_name=self.params["dbname"] if self.params["dbname"] else os.getenv("POSTGRES_DBNAME", "postgres")
        self.db_host=self.params["host"] if self.params["host"] else os.getenv("POSTGRES_HOST", "localhost")
        self.db_port=self.params["port"] if self.params["port"] else os.getenv("POSTGRES_PORT", 5432)

    def getDBParameters(self):
        """
        Return a dictionary with the database parameter.
        """
        db={
            "drivername":"postgresql+psycopg2",
            "host":self.params["host"],
            "database":self.params["dbname"],
            "port":self.params["port"],
            "username":self.db_user,
            "password":self.db_pass
        }
        return db

    def connect(self):
        try:
            # connect to the PostgreSQL server
            str_conn=f"dbname={self.db_name} user={self.db_user} password={self.db_pass} host={self.db_host} port={self.db_port}"
            self.conn = psycopg2.connect(str_conn)
            self.cur = self.conn.cursor()
        except (Exception, psycopg2.DatabaseError) as error:
            raise ConnectionError('Missing connection:', str(error))
    
    def close(self):
        # close the communication with the PostgreSQL
        if self.cur is not None:
            self.cur.close()
            self.cur = None
        # disconnect from the PostgreSQL server
        if self.conn is not None:
            self.conn.close()

    def commit(self):
        # if is connected
        if self.conn is not None:
            # commit the changes
            self.conn.commit()
    
    def rollback(self):
        # if is connected
        if self.conn is not None:
            # commit the changes
            self.conn.rollback()

    def execQuery(self, query, isInsert=None):
        try:
            
            if self.cur is None:
                raise ConnectionError('Missing cursor:', 'Has no valid database cursor ({0})'.format(query))
            # execute a statement
            self.cur.execute(query)

            if isInsert:
                data=self.cur.fetchone()
                if(data):
                    return data[0]
                else:
                    return None

        except (Exception, psycopg2.DatabaseError) as error:
            self.rollback()
            raise QueryError('Query execute issue', error)
        except (BaseException) as error:
            self.rollback()
            raise QueryError('Query execute issue', error)
            

    def fetchData(self, query):
        data = None
        try:
            # execute a statement
            self.execQuery(query)
            # retrive data
            data = self.cur.fetchall()
            
        except QueryError as error:
            raise error

        return data