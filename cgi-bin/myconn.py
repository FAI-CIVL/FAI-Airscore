"""
Module for mySQL connection
Use:    import myconn
        with Database() as db:
            result = db.fetchone(query)
        
Antonio Golfari - 2018
"""

import Defines as d

try:
    import pymysql as c
    c.install_as_MySQLdb()
except ImportError:
    pass

"""Creates a class for MySQL Connections"""

class Database:

    def __str__(self):
        return "MySQL DB Connection Object"

    def __init__(self):
        self._conn = c.connect(   host=d.MYSQLHOST,
                                        user=d.MYSQLUSER,
                                        passwd=d.MYSQLPASSWORD,
                                        db=d.DATABASE,
                                        charset='utf8mb4',
                                        cursorclass=c.cursors.DictCursor) 
        self._cursor = self._conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.commit()
        self.connection.close()

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        self.connection.commit()

    def rowcount(self):
        return self.cursor.rowcount

    def lastrowid(self):
        return self.cursor.lastrowid

    def execute(self, sql, params=None):
        #print (" ** db.execute - Query: {} \n ".format(sql))
        try:
            self.cursor.execute(sql, params or ())
            return self.cursor.lastrowid
            #print (" ** db.execute Executed query \n ")
        except c.Error as e:
            print(e)
        except:
            print ("execute: Error while connecting to MySQL \n")

    def fetchall(self, sql, params=None):
        self.execute(sql, params)
        try:
            return self.cursor.fetchall()
        except:
            print ("fetchall: Error while connecting to MySQL \n")

    def fetchone(self, sql, params=None):
        self.execute(sql, params)
        try:            
            return self.cursor.fetchone()
        except:
            print ("fetchone: Error while connecting to MySQL \n")

    def rows(self, sql, params=None):
        self.execute(sql, params)
        #print (" ** results found: {} \n ".format(self.cursor.rowcount))
        return self.cursor.rowcount
