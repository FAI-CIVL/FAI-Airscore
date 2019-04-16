"""
Module for mySQL connection
Use:	import myconn
		db = myconn.getConnection()
		
Antonio Golfari - 2018
"""

import Defines as d

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

import pymysql.cursors

"""Function return a connection"""
def getConnection():

    # You can change the connection arguments.
    connection = pymysql.connect(host=d.MYSQLHOST,
                                 user=d.MYSQLUSER,
                                 password=d.MYSQLPASSWORD,
                                 db=d.DATABASE,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection
