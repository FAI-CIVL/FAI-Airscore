"""
Module for operations on tracks
Use:    import trackUtils
        pilPk = compUtils.get_track_pilot(filename)

Antonio Golfari - 2018
"""

# Use your utility module.
import kml
from myconn import Database
from calcUtils import *

import sys, os, aerofiles, json
from datetime import date, time, datetime

class Track():
    """
    Create an object Track and
    a collection of functions to handle tracks.

    var: filename, pilot
    """
    def __init__(self, filename = None, pilot = None, task = None, glider = None, cert = None, type = None, test = 0):
        self.filename = filename
        self.type = type
        self.pilPk = pilot
        self.task_id = task
        self.glider = glider
        self.cert = cert

    def get_pilot(self, test = 0):
        """Get pilot associated to a track from its filename"""
        """should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc"""
        if self.pilPk is None:
            message = ''
            names = []

            """Get string"""
            fields = os.path.splitext(os.path.basename(self.filename))
            if fields[0].isdigit():
                """Gets name from FAI n."""
                fai = 0 + int(fields[0])
                message += ("file {} contains FAI n. {} \n".format(fields[0], fai))
                query = ("SELECT pilPk FROM PilotView WHERE pilFAI = {}".format(fai))
            else:
                """Gets name from string"""
                message += ("file {} contains pilot name \n".format(fields[0]))
                names = fields[0].replace('.', ' ').replace('_', ' ').replace('-', ' ').split()
                s = []
                t = []
                for i in names:
                    s.append(" pilLastName LIKE '%%{}%%' ".format(i))
                    t.append(" pilFirstName LIKE '%%{}%%' ".format(i))
                cond = ' OR '.join(s)
                cond2 = ' OR '.join(t)
                query = ("""    SELECT
                                    pilPk
                                FROM
                                    PilotView
                                WHERE
                                    ({})
                                AND
                                    ({})""".format(cond, cond2))

            print ("get_pilot Query: {}  \n".format(query))

            """Get pilot"""
            with Database() as db:
                self.pilPk = db.fetchone(query)['pilPk']

#               db = myconn.getConnection()
#               query = ("SELECT pilPk FROM PilotView WHERE pilFAI = {}".format(fai))
#               message += ("Query: {}  \n".format(query))
#               try:
#                   c = db.cursor()
#                   c.execute(query)
#                   row = c.fetchone()
#               except Exception:
#                   message += ("Error while connecting to MySQL \n")
#               else:
#                   if row is not None:
#                       self.pilPk = 0 + row['pilPk']
#               finally:
#                   c.close()
#           else:
#               """Try to Get pilPk from name"""
#               cond = "', '".join(names)
#               db = myconn.getConnection()
#               query = ("""    SELECT
#                                   pilPk
#                               FROM
#                                   PilotView
#                               WHERE
#                                   pilLastName IN ( '{0}' )
#                               AND
#                                   pilFirstName IN ( '{0}' )""".format(cond))
#               message += ("Query: {}  \n".format(query))
#               try:
#                   c = db.cursor()
#                   c.execute(query)
#                   row = c.fetchone()
#               except Exception:
#                   message += ("Error while connecting to MySQL \n")
#               else:
#                   if row is not None:
#                       self.pilPk = 0 + row['pilPk']
#               finally:
#                   c.close()

            if self.pilPk is None:
                """No pilot infos in filename"""
                message += ("{} does NOT contain any valid pilot info \n".format(fields[0]))

        if test == 1:
            """TEST MODE"""
            message += ("pilPk: {}  \n".format(pilPk))
            print (message)

#       return pilPk

    def add(self, test = 0):
        """Imports track to db"""
        message = ''
        message += ("track {} will be imported for pilot with ID {} and task with ID {} \n".format(self.filename, self.pilPk, self.task_id))

        print(self)
        """Get info on glider"""
        self.get_glider(test)
        #glider = info['glider']
        #cert  = info['cert']

        """read track file"""
        """IGC, KML, OZI, LIVE"""
        result = self.read(test)

        """creates a JSON data"""
        j = json.dumps(result, cls=DateTimeEncoder)

        """writes a JSON file"""
        with open('json_data.json', 'wb') as fp:
            fp.write(j.encode("utf-8"))

        if test == 1:
            """TEST MODE"""
            print (message)

        return result

    def read(self, test = 0):
        """Reads track file and creates a dict() object"""
        message = ''
        if self.type is None:
            self.get_type(test)
        if self.type is not None:
            """file is a valid track format"""
            message += ("File Type: {} \n".format(type))
            if self.type == "igc":
                """using IGC reader from aerofile library"""
                with open(self.filename, 'r', encoding='utf-8') as f:
                    result = aerofiles.igc.Reader().read(f)
            if self.type == "kml":
                """using KML reader created by Antonio Golfari"""
                with open(self.filename, 'r', encoding='utf-8') as f:
                    result = kml.Reader().read(f)

        else:
            Message += ("File {} (pilot ID {}) is NOT a valid track file. \n".format(track, pilPk))

        if test == 1:
            """TEST MODE"""
            print (message)

        return result

    def get_type(self, test = 0):
        """determine if igc / kml / live / ozi"""
        message = ''
        if self.filename is not None:
            """read first line of file"""
            with open(self.filename) as f:
                first_line = f.readline()

            if first_line[:1] == 'A':
                """IGC: AXCT7cea4d3ae0df42a1"""
                self.type = "igc"
            elif first_line[:3] == '<?x':
                """KML: <?xml version="1.0" encoding="UTF-8"?>"""
                self.type = "kml"
            elif first_line.contains("B  UTF"):
                self.type = "ozi"
            elif first_line[:3] == 'LIV':
                self.type = "live"
            else:
                self.type = None
            print ("  ** FILENAME: {} TYPE: {} \n".format(self.filename, self.type))

    def get_glider(self, test = 0):
        """Get glider info for pilot, to be used in results"""
        message = ''
#       info = dict()
#       info['glider'] = 'Unknown'
#       info['cert'] = None

        if self.pilPk is not None:
            query = ("""    SELECT
                                pilGlider, pilGliderBrand, gliGliderCert
                            FROM
                                PilotView
                            WHERE
                                pilPk = {}""".format(self.pilPk))
            #print ("get_glider Query: {}  \n".format(query))
            with Database() as db:
                row = db.fetchone(query)
            if row is not None:
                self.glider = " ".join((row['pilGliderBrand'], row['pilGlider']))
                self.cert = row['gliGliderCert']
                #print ("Glider: {} - Certification: {} \n".format(self.glider, self.cert))
#           db = myconn.getConnection()
#           query = ("""    SELECT
#                               pilGlider, pilGliderBrand, gliGliderCert
#                           FROM
#                               PilotView
#                           WHERE
#                               pilPk = {}""".format(self.pilPk))
#           message += ("Query: {}  \n".format(query))
#           try:
#               c = db.cursor()
#               c.execute(query)
#               row = c.fetchone()
#           except Exception:
#               print ("get_glider - Error while connecting to MySQL")
#           else:
#               if row is not None:
#                   self.glider = " ".join(row['pilGliderBrand'], row['pilGlider'])
#                   self.cert = row['gliGliderCert']
#           finally:
#               c.close()
        else:
            message += ("get_glider - Error: NOT a valid Pilot ID \n")

        if test == 1:
            """TEST MODE"""
            message += ("Glider Info: \n")
            message += ("{}, cert. {} \n".format(self.glider, self.cert))
            print (message)

        #return (info)

    @staticmethod
    def is_flying(p1, p2, test = 0):
        """check if pilot is flying between 2 gps points"""
        message = ''
        dist = quick_distance(p2, p1, test)
        altdif = abs(p2['gps_alt'] - p1['gps_alt'])
        timedif = time_diff(p2['time'], p1['time'], test)

def get_pil_result(pilPk, tasPk, test):
    """Get pilot result in a given task"""
    message = ''
    traPk = 0
    with Database() as db:
        query = ("""    `SELECT`
                            `T`.`traPk`
                        FROM
                            `tblTaskResult` `TR`
                            JOIN `tblTrack` `T` USING (`traPk`)
                        WHERE
                            `T`.`pilPk` = {}
                            AND `TR`.`tasPk` = {}
                        LIMIT
                            1""".format(pilPk, tasPk))
        message += ("Query: {}  \n".format(query))
        if db.rows(query) > 0:
            traPk = 0 + db.fetchone(query)['traPk']
        else:
            """No result found"""
            message += ("Pilot with ID {} has not been scored yet on task ID {} \n".format(pilPk, tasPk))

    if test == 1:
        """TEST MODE"""
        message += ("traPk: {}  \n".format(traPk))
        print (message)

    return traPk
