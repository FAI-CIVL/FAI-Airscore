"""
Module for operations on tracks
Use:    import track
        pilPk = compUtils.get_track_pilot(filename)

This module reads IGC files using igc_lib library
and creates an object containing all info about the flight

Antonio Golfari, Stuart Mackintosh - 2019
"""

from calcUtils import *
from igc_lib import *
# Use your utility module.
from myconn import Database


class Track():
    """
    Create an object Track and
    a collection of functions to handle tracks.

    var: filename, pilot
    """

    def __str__(self):
        return "Track Object"

    def __init__(self, filename = None, pilot = None, task = None, glider = None, cert = None, type = None, test = 0):
        self.filename = filename
        self.traPk = None
        self.type = type
        self.pilPk = pilot
        self.tasPk = task
        self.glider = glider
        self.cert = cert
        self.flight = None      # igc_lib.Flight object
        self.date = None        # in datetime.date format

    def get_pilot(self, test = 0):
        """Get pilot associated to a track from its filename
        should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc
        """

        if self.pilPk is None:
            message = ''
            names = []

            """Get string"""
            fields = os.path.splitext(os.path.basename(self.filename))
            if fields[0].isdigit():
                """Gets name from FAI n."""
                fai = 0 + int(fields[0])
                message += ("file {} contains FAI n. {} \n".format(fields[0], fai))
                query = ("SELECT pilPk FROM tblPilot WHERE pilFAI = {}".format(fai))
            else:
                names = fields[0].replace('.', ' ').replace('_', ' ').replace('-', ' ').split()
                """try to find xcontest user in filename
                otherwise try to find pilot name from filename"""
                message += ("file {} contains pilot name \n".format(fields[0]))

                s = []
                t = []
                u = []
                for i in names:
                    s.append(" pilLastName LIKE '%%{}%%' ".format(i))
                    t.append(" pilFirstName LIKE '%%{}%%' ".format(i))
                    u.append(" pilXContestUser LIKE '{}' ".format(i))
                cond = ' OR '.join(s)
                cond2 = ' OR '.join(t)
                cond3 = ' OR '.join(u)
                query =(""" SELECT
                                pilPk
                            FROM
                                tblPilot
                            WHERE
                                ({})
                            UNION ALL
                            SELECT
                                pilPk
                            FROM
                                tblPilot
                            WHERE
                                ({})
                            AND
                                ({})
                            LIMIT 1""".format(cond3, cond, cond2))

            print ("get_pilot Query: {}  \n".format(query))

            """Get pilot"""
            with Database() as db:
                try:
                    self.pilPk = db.fetchone(query)['pilPk']
                except:
                    self.pilPk = None

            if self.pilPk is None:
                """No pilot infos in filename"""
                message += ("{} does NOT contain any valid pilot info \n".format(fields[0]))

        if test == 1:
            """TEST MODE"""
            message += ("pilPk: {}  \n".format(self.pilPk))
            print (message)

    def add(self, test = 0):
        from datetime import datetime
        from compUtils import get_class
        """Imports track to db"""
        result = ''
        message = ''
        message += ("track {} will be imported for pilot with ID {} and task with ID {} \n".format(self.filename, self.pilPk, self.tasPk))

        """get time of first fix of the track"""
        trastart = datetime.combine(datetime.strptime(self.date, "%Y-%m-%d"), datetime.strptime(sec_to_str(self.flight.fixes[0].rawtime),"%H:%M:%S").time())
        traclass = get_class(self.tasPk)
        traduration = self.flight.fixes[-1].rawtime - self.flight.fixes[0].rawtime

        """add track entry into tblTrack table"""
        query = ("""INSERT INTO `tblTrack`(
                        `pilPk`,
                        `traClass`,
                        `traGlider`,
                        `traDHV`,
                        `traDate`,
                        `traStart`,
                        `traDuration`,
                        `traFile`
                    )
                    VALUES(
                        '{}','{}','{}','{}','{}','{}','{}','{}'
                    )
                    """.format(self.pilPk, traclass, self.glider, self.cert, self.date, trastart, traduration, self.filename))
        message += query
        if not test:
            with Database() as db:
                try:
                    db.execute(query)
                    self.traPk = db.lastrowid()
                except:
                    print('Error Inserting track into db:')
                    print(query)
                finally:
                    result += ("track for pilot with id {} correctly stored in database".format(self.pilPk))
        else:
            print(message)

        return result

    @classmethod
    def read_file(cls, filename, pilot_id = None, test = 0):
        """Reads track file and creates a track object"""
        message = ''
        track = cls(filename)
        track.get_type(test)
        if track.type is not None:
            """file is a valid track format"""
            message += ("File Type: {} \n".format(type))
            if track.type == "igc":
                """using IGC reader from aerofile library"""
                flight = Flight.create_from_file(filename)
            #if track.type == "kml":
                """using KML reader created by Antonio Golfari
                To be rewritten for igc_lib"""
                #with open(track.filename, 'r', encoding='utf-8') as f:
                    #flight = kml.Reader().read(f)
            """Check flight is valid
            I'm not creating a track without a valid flight because it would miss date property.
            We could change this part if we find a way to gen non-valid flight with timestamp property
            '"""
            if flight.valid:
                if not pilot_id:
                    track.get_pilot(test)
                else:
                    track.pilPk = 0 + pilot_id
                track.get_glider(test)
                track.flight = flight
                track.date = epoch_to_date(track.flight.date_timestamp)
                if test == 1:
                    """TEST MODE"""
                    print (message)
                return track
        else:
            message += ("File {} (pilot ID {}) is NOT a valid track file. \n".format(track, pilPk))

    @classmethod
    def read_db(cls, traPk, test = 0):
        """Creates a Track Object from a DB Track entry"""

        track = cls()

        """Read general info about the track"""
        query = "select unix_timestamp(T.traDate) as udate," \
                "   T.*," \
                "   CTT.* " \
                "from tblTrack T " \
                "left outer join " \
                "tblComTaskTrack CTT on T.traPk=CTT.traPk " \
                "where T.traPk=%s"

        with Database() as db:
            # get the formula details.
            t = db.fetchone(query, [traPk])

        if t:
            track.pilPk = t['pilPk']
            track.filename = t['traFile'] if t['traFile'] is not None else None
            track.tasPk = t['tasPk'] if t['tasPk'] is not None else None
            track.glider = t['traGlider'] if t['traGlider'] is not (None or 'Unknown') else None
            track.cert = t['traDHV'] if t['traGlider'] is not (None or 'Unknown') else None
        if test == 1:
            print("read_db: pilPk: {} | filename: {}".format(track.pilPk, track.filename))

        """Creates the flight obj with fixes info"""
        track.flight = Flight.create_from_file(track.filename)

        return track

    def to_geojson(self, filename = None, test = 0):
        """Dumps the flight to geojson format
            If a filename is given, it write the file, otherwise returns the string"""

        from geojson import Point, Feature, FeatureCollection, MultiPoint, MultiLineString, dump

        #assert self.flight.valid

        #TODO write objects to the geojson form the flight object
#         min_lat = self.flight.takeoff_fix.lat
#         min_lon = self.flight.takeoff_fix.lon
#         max_lat = self.flight.takeoff_fix.lat
#         max_lon = self.flight.takeoff_fix.lon

        features = []
        #features.append(Feature(geometry=point, properties={"country": "Spain"}))

#         takeoff = Point((self.flight.takeoff_fix.lon,self.flight.takeoff_fix.lat))
#         features.append(Feature(geometry=takeoff, properties={"TakeOff": "TakeOff"}))
#         landing = Point((self.flight.landing_fix.lon,self.flight.landing_fix.lat))
#         features.append(Feature(geometry=landing, properties={"Landing": "Landing"}))

#         thermals = []
#         for i, thermal in enumerate(self.flight.thermals):
#     #        add_point(name="thermal_%02d" % i, fix=thermal.enter_fix)
#             thermals.append( (thermal.enter_fix.lon,thermal.enter_fix.lat) )
#     #        add_point(name="thermal_%02d_END" % i, fix=thermal.exit_fix)
#             thermals.append( (thermal.exit_fix.lon,thermal.exit_fix.lat) )
#
#         thermals_multipoint = MultiPoint(thermals)
#         features.append(Feature(geometry=thermals_multipoint))

        route = []
        for fix in self.flight.fixes:
            route.append((fix.lon, fix.lat))

        route_multilinestring = MultiLineString([route])
        features.append(Feature(geometry=route_multilinestring, properties={"Track": "Track"}))
        feature_collection = FeatureCollection(features)

        if filename is None:
            return feature_collection
        else:
            with open(filename, 'w') as f:
                dump(feature_collection, f)

    def get_type(self, test = 0):
        """determine if igc / kml / live / ozi"""
        message = ''
        if self.filename is not None:
            """read first line of file"""
            with open(self.filename, encoding="ISO-8859-1") as f:
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

        if self.pilPk is not None:
            query = ("""    SELECT
                                pilGlider, pilGliderBrand, gliGliderCert
                            FROM
                                tblPilot
                            WHERE
                                pilPk = {}
                            LIMIT 1""".format(self.pilPk))
            #print ("get_glider Query: {}  \n".format(query))
            with Database() as db:
                row = db.fetchone(query)
            if row is not None:
                brand = '' if row['pilGliderBrand'] is None else row['pilGliderBrand']
                glider = '' if row['pilGlider'] is None else ' ' + row['pilGlider']
                self.glider = brand + glider
                self.cert = row['gliGliderCert']

        else:
            message += ("get_glider - Error: NOT a valid Pilot ID \n")

        if test == 1:
            """TEST MODE"""
            message += ("Glider Info: \n")
            message += ("{}, cert. {} \n".format(self.glider, self.cert))
            print (message)

    def copy_track_file(self, test=0):
        """copy track file in the correct folder and with correct name
        name could be changed as the one XContest is sending, or rename that one, as we wish"""
        from shutil import copyfile
        from Defines import FILEDIR
        import glob

        message = ''
        src_file = self.filename

        """get comp and task info"""
        query = ("""  SELECT
                            LOWER(T.`comCode`) AS comCode,
                            LOWER(T.`tasCode`) AS tasCode,
                            YEAR(C.`comDateFrom`) AS comYear,
                            DATE_FORMAT(T.`tasdate`, '%%Y%%m%%d') AS tasDate,
                            CONCAT_WS(
                                '_',
                                LOWER(P.`pilFirstName`),
                                LOWER(P.`pilLastName`)
                            ) AS pilName
                        FROM
                            `tblPilot` P,
                            `tblTaskView` T
                        JOIN `tblCompetition` C USING(`comPk`)
                        WHERE
                            T.`tasPk` = '{}' AND P.`pilPk` = '{}'
                        LIMIT 1""".format(self.tasPk, self.pilPk))

        message += query

        with Database() as db:
            # get the task details.
            if db.rows(query) > 0:
                t = db.fetchone(query)
                cname = str(t['comCode'])
                tname = str(t['tasCode'])
                pname = str(t['pilName'])
                year  = str(t['comYear'])
                tdate = str(t['tasDate'])
                taskdir = FILEDIR + ('/'.join([year,cname,('_'.join([tname,tdate]))]))
                """check if directory already exists"""
                if not os.path.isdir(taskdir):
                    os.makedirs(taskdir)
                """creates a name for the track
                name_surname_date_time_index.igc
                if we use flight date then we need an index for multiple tracks"""
                #filename = pname+'_'+datetime.today().strftime('%Y%m%d-%H%M%S')+'.igc'
                index = str(len(glob.glob(taskdir+'/'+pname+'*.igc')) + 1).zfill(2)
                filename = '_'.join([pname,self.date,index]) + '.igc'
                fullname = '/'.join([taskdir,filename])
                message += "path to copy file: {}".format(fullname)
                """copy file"""
                try:
                    copyfile(src_file, fullname)
                except:
                    print('Error copying file')
                finally:
                    self.filename = fullname
                    message += "file succesfully copied to : {}".format(self.filename)
            else:
                print('Error: track copy query to find comp info failed')

    @staticmethod
    def is_flying(p1, p2, test = 0):
        """check if pilot is flying between 2 gps points"""
        message = ''
        dist = quick_distance(p2, p1, test)
        altdif = abs(p2['gps_alt'] - p1['gps_alt'])
        timedif = time_diff(p2['time'], p1['time'], test)
