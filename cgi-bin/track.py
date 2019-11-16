"""
Module for operations on tracks
Use:    import track
        pilPk = compUtils.get_track_pilot(filename)

This module reads IGC files using igc_lib library
and creates an object containing all info about the flight

Antonio Golfari, Stuart Mackintosh - 2019
"""

from calcUtils import epoch_to_date, sec_to_time
from igc_lib import Flight
# Use your utility module.
from myconn import Database
import os


class Track():
    """
    Create an object Track and
    a collection of functions to handle tracks.

    var: filename, pilot
    """

    def __str__(self):
        return "Track Object"

    def __init__(self, filename = None, track_id = None, pil_id = None, task_id = None, glider = None, cert = None, type = None):
        self.filename = filename
        self.track_id = track_id
        self.type = type
        self.pil_id = pil_id
        self.task_id = task_id
        self.glider = glider
        self.cert = cert
        self.flight = None      # igc_lib.Flight object
        self.date = None        # in datetime.date format

    def to_dict(self):
        return self.__dict__

    def get_pilot(self):
        """Get pilot associated to a track from its filename
        should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc
        """
        if self.pil_id is None:

            """Get string"""
            fields = os.path.splitext(os.path.basename(self.filename))
            if fields[0].isdigit():
                """Gets name from FAI n."""
                fai = 0 + int(fields[0])
                query = ("SELECT `pilPk` FROM `PilotView` WHERE `pilFAI` = {}".format(fai))
            else:
                names = fields[0].replace('.', ' ').replace('_', ' ').replace('-', ' ').split()
                """try to find xcontest user in filename
                otherwise try to find pilot name from filename"""

                s = []
                t = []
                u = []
                for i in names:
                    s.append(" `pilLastName` LIKE '%%{}%%' ".format(i))
                    t.append(" `pilFirstName` LIKE '%%{}%%' ".format(i))
                    u.append(" `pilXContestUser` LIKE '{}' ".format(i))
                cond = ' OR '.join(s)
                cond2 = ' OR '.join(t)
                cond3 = ' OR '.join(u)
                query =(""" SELECT
                                `pilPk`
                            FROM
                                `PilotView`
                            WHERE
                                ({})
                            UNION ALL
                            SELECT
                                `pilPk`
                            FROM
                                `PilotView`
                            WHERE
                                ({})
                            AND
                                ({})
                            LIMIT 1""".format(cond3, cond, cond2))

            print ("get_pilot Query: {}  \n".format(query))

            """Get pilot"""
            with Database() as db:
                try:
                    self.pil_id = db.fetchone(query)['pilPk']
                except:
                    self.pil_id = None

            if self.pil_id is None:
                """No pilot infos in filename"""

    def add(self):
        import datetime
        from compUtils import get_class, get_offset
        """Imports track to db"""
        result = ''
        g_record = int(self.flight.valid)

        """add track as result in tblTaskResult table"""
        query = """ INSERT INTO `tblTaskResult`(
                        `pilPk`,
                        `tasPk`,
                        `traFile`,
                        `traGRecordOk`,
                    )
                    VALUES(
                        %s, %s, %s, %s
                    )
                    """
        params = [self.pil_id, self.task_id, self.filename, g_record]
        with Database() as db:
            try:
                self.track_id = db.execute(query, params)
                result += ("track for pilot with id {} correctly stored in database".format(self.pil_id))
            except:
                print('Error Inserting track into db:')
                print(query)
                result = ('Error inserting track for pilot with id {}'.format(self.pil_id))

        return result

    @classmethod
    def read_file(cls, filename, track_id = None, pil_id = None):
        """Reads track file and creates a track object"""
        track = cls(filename=filename, track_id=track_id, pil_id=pil_id)
        track.get_type()
        print('type ', track.type)
        if track.type is not None:
            """file is a valid track format"""
            if track.type == "igc":
                """using IGC reader from aerofile library"""
                print('reading flight')
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
                print('flight valid')
                if not pil_id:
                    track.get_pilot()
                # track.get_glider()
                track.flight    = flight
                track.date      = epoch_to_date(track.flight.date_timestamp)
                return track
            else: print(f'** ERROR: {flight.notes}')
        else:
            print(f"File {filename} (pilot ID {pil_id}) is NOT a valid track file.")

    @classmethod
    def read_db(cls, track_id):
        """Creates a Track Object from a DB Track entry"""

        track = cls(track_id=track_id)

        """Read general info about the track"""

        query = """ SELECT
                        `pil_id`,
                        `task_id`,
                        `track_file` AS `filename`
                    FROM
                        `TaskResultView`
                    WHERE
                        `track_id` = %s
                    LIMIT 1 """

        with Database() as db:
            # get the formula details.
            t = db.fetchone(query, [track_id])

        if t:
            track.to_dict().update(t)

            """Creates the flight obj with fixes info"""
            track.flight = Flight.create_from_file(track.filename)

        return track

    def to_geojson(self, filename = None, mintime=0, maxtime=86401):
        """Dumps the flight to geojson format
            If a filename is given, it write the file, otherwise returns the string"""

        from geojson import Feature, FeatureCollection, MultiLineString, dump

        features = []
        route = []
        for fix in self.flight.fixes:
            if mintime <= fix.rawtime < maxtime:
                route.append((fix.lon, fix.lat))

        route_multilinestring = MultiLineString([route])
        features.append(Feature(geometry=route_multilinestring, properties={"Track": "Track"}))
        feature_collection = FeatureCollection(features)

        if filename is None:
            return feature_collection
        else:
            with open(filename, 'w') as f:
                dump(feature_collection, f)

    def get_type(self):
        """determine if igc / kml / live / ozi"""
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

    def get_glider(self):
        """Get glider info for pilot, to be used in results"""

        if self.pil_id is not None:
            query = """    SELECT
                                CONCAT( IFNULL(`pilGlider`, ''),
                                        ' ',
                                        IFNULL(`pilGliderBrand`, '')
                                        ) AS `glider`,
                                ,
                                `gliGliderCert` AS `cert`
                            FROM
                                `PilotView`
                            WHERE
                                `pilPk` = %s
                            LIMIT 1"""
            #print ("get_glider Query: {}  \n".format(query))
            with Database() as db:
                row = db.fetchone(query, [self.pil_id])
            if row is not None:
                self.__dict__.update(row)
                # brand = '' if row['pilGliderBrand'] is None else row['pilGliderBrand']
                # glider = '' if row['pilGlider'] is None else ' ' + row['pilGlider']
                # self.glider = brand + glider
                # self.cert = row['gliGliderCert']

    def copy_track_file(self, task_path=None, pname=None):
        """copy track file in the correct folder and with correct name
        name could be changed as the one XContest is sending, or rename that one, as we wish
        if path or pname is None will calculate. note that if bulk importing it is better to pass these values
        rather than query DB for each track"""

        from shutil import copyfile
        import glob
        from compUtils import get_task_file_path
        from os import path

        src_file = self.filename
        if task_path is None:
            task_path = get_task_file_path(self.task_id)

        if pname is None:
            query = "SELECT " \
                    "   CONCAT_WS('_', LOWER(P.`pilFirstName`), LOWER(P.`pilLastName`) ) AS pilName " \
                    "   FROM `PilotView` P " \
                    "   WHERE P.`pilPk` = %s" \
                    "   LIMIT 1"
            param = self.pil_id

            with Database() as db:
                # get the task details.
                t = db.fetchone(query, params=param)
                if t:
                    pname = t['pilName']

        if task_path:
            """check if directory already exists"""
            if not path.isdir(task_path):
                os.makedirs(task_path)
            """creates a name for the track
            name_surname_date_time_index.igc
            if we use flight date then we need an index for multiple tracks"""

            index = str(len(glob.glob(task_path+'/'+pname+'*.igc')) + 1).zfill(2)
            filename = '_'.join([pname, str(self.date), index]) + '.igc'
            fullname = path.join(task_path, filename)
            # print(f'path to copy file: {fullname}')
            print('path to copy file:',fullname)
            """copy file"""
            try:
                copyfile(src_file, fullname)
                self.filename = fullname
                # print(f'file succesfully copied to : {self.filename}')
                print('file succesfully copied to :', self.filename)
            except:
                print('Error copying file:', fullname)
        else:
            print('error, path not created')

    @staticmethod
    def is_flying(p1, p2):
        """check if pilot is flying between 2 gps points"""
        dist = quick_distance(p2, p1)
        altdif = abs(p2['gps_alt'] - p1['gps_alt'])
        timedif = time_diff(p2['time'], p1['time'])
