"""
Track Library
Use:    import track
        par_id = compUtils.get_track_pilot(filename)

This module reads IGC files using igc_lib library
and creates an object containing all info about the flight

Antonio Golfari, Stuart Mackintosh - 2019
"""

from calcUtils import epoch_to_date, time_difference
from igc_lib import Flight
# Use your utility module.
from myconn import Database
import os

''' Accepted formats list
    When checking tracks, this are formats that will be accepted and processed
'''



class Track(object):
    """
    Create a Track object and
    a collection of functions to handle tracks.

    var: filename, pilot
    """

    def __str__(self):
        return "Track Object"

    def __init__(self, track_file=None, track_id=None, par_id=None, track_type=None, comment=None, flight=None):
        self.track_file = track_file
        self.track_id = track_id
        self.track_type = track_type
        self.comment = comment      #should be a list?
        self.flight = flight  # igc_lib.Flight object
        self.par_id = par_id  # tblParticipant ID # could delete?


    @property
    def date(self):
        """datetime.date format"""
        from calcUtils import epoch_to_date
        if self.flight:
            return epoch_to_date(self.flight.date_timestamp)
        else:
            return None

    @property
    def timestamp(self):
        """epoch format"""
        if self.flight:
            return self.flight.date_timestamp
        else:
            return None

    @property
    def fixes(self):
        """flight fixes list"""
        if self.flight:
            return self.flight.fixes
        else:
            return None

    @property
    def notes(self):
        """flight notes list"""
        if self.flight:
            return self.flight.notes
        else:
            return None

    @property
    def filename(self):
        # compatibility
        return self.fullpath

    @property
    def valid(self):
        if self.flight:
            return self.flight.valid
        else:
            return False

    @property
    def gnss_alt_valid(self):
        if self.flight:
            return self.flight.gnss_alt_valid
        else:
            return False

    @property
    def press_alt_valid(self):
        if self.flight:
            return self.flight.press_alt_valid
        else:
            return False

    @property
    def fullpath(self):
        if not self.track_file:
            return
        from trackUtils import get_task_fullpath
        from os import path as p
        file_path = get_task_fullpath(self.task_id)
        return p.join(file_path, self.track_file)

    def as_dict(self):
        return self.__dict__

    def get_pilot(self):
        """Get pilot associated to a track from its filename
        should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc
        """
        # TODO Update workflow using CIVL database / new Participant obj.
        # TODO in the new workflow we should have a Pilot obj, with Track as attr. so get_pilot should be in Pilot
        from trackUtils import find_pilot
        if self.par_id is None:
            """Get string"""
            fields = os.path.splitext(os.path.basename(self.filename))
            self.par_id = find_pilot(fields[0])

    def add(self):
        """Imports track to db"""
        # TODO in the new workflow we should have a Pilot obj, with Track as attr. so we should add() in Pilot
        from db_tables import tblTaskResult as R
        result = ''

        # add track as result in tblTaskResult table
        with Database() as db:
            try:
                track = R(parPk=self.par_id, tasPk=self.task_id, traFile=self.filename,
                          traGRecordOk=self.filename)  # not sure what g-record has to do with filename??
                self.track_id = db.session.add(track)
                db.session.commit()
                result += ("track for pilot with id {} correctly stored in database".format(self.pil_id))
            except:
                print('Error Inserting track into db:')
                result = ('Error inserting track for pilot with id {}'.format(self.pil_id))
        return result

    @classmethod
    def read_file(cls, filename, track_id=None, par_id=None):
        """Reads track file and creates a track object"""
        track = cls(track_file=filename, track_id=track_id, par_id=par_id)
        track.get_type()
        print('type ', track.type)
        if track.type in accepted_formats:
            """file is a valid track format"""
            if track.type == "igc":
                """using IGC reader from aerofile library"""
                print('reading flight')
                track.flight = Flight.create_from_file(filename)
            # elif track.type == "kml":
            """using KML reader created by Antonio Golfari
            To be rewritten for igc_lib"""
            # TODO update kml reader if we are interested in reading kml track format
            # with open(track.filename, 'r', encoding='utf-8') as f:
                # flight = kml.Reader().read(f)
            '''Check flight is valid
            I'm not creating a track without a valid flight because it would miss date property.'''
            # TODO We could change this part if we find a way to gen non-valid flight with timestamp property
            if track.valid:
                print('track valid')
                if not par_id:
                    track.get_pilot()
                # track.get_glider()
                # track.flight = flight
                # track.date = epoch_to_date(track.flight.date_timestamp)
                return track
            else:
                print(f'** ERROR: {track.notes}')
        else:
            print(f"File {filename} (pilot ID {par_id}) is NOT a valid track file.")

    @classmethod
    def read_db(cls, track_id):
        """Creates a Track Object from a DB Track entry"""
        from db_tables import TrackObjectView as T

        track = cls(track_id=track_id)

        """Read general info about the track"""
        with Database() as db:
            # get track details.
            q = db.session.query(T).get(track_id)
            try:
                db.populate_obj(track, q)
                """Creates the flight obj with fixes info"""
                track.flight = Flight.create_from_file(track.fullpath)
            except:
                print(f'Track Query Error: no result found')

        return track

    @staticmethod
    def from_dict(d):
        track = Track()
        for key, value in d.items():
            if hasattr(track, key):
                setattr(track, key, value)
        return track

    def to_geojson(self, filename=None, mintime=0, maxtime=86401):
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
            print("  ** FILENAME: {} TYPE: {} \n".format(self.filename, self.type))

    def copy_track_file(self, task_path=None, pname=None):
        """copy track file in the correct folder and with correct name
        name could be changed as the one XContest is sending, or rename that one, as we wish
        if path or pname is None will calculate. note that if bulk importing it is better to pass these values
        rather than query DB for each track"""

        from shutil import copyfile
        import glob
        from compUtils import get_task_filepath
        from os import path
        from db_tables import RegistrationView as P

        src_file = self.filename
        if task_path is None:
            task_path = get_task_filepath(self.task_id)

        if pname is None:
            with Database() as db:
                # get pilot details.
                name = db.session.query(P).get(self.par_id).name
            if q:
                pname = name.replace(' ', '_').lower()

        if task_path:
            """check if directory already exists"""
            if not path.isdir(task_path):
                os.makedirs(task_path)
            """creates a name for the track
            name_surname_date_time_index.igc
            if we use flight date then we need an index for multiple tracks"""

            index = str(len(glob.glob(task_path + '/' + pname + '*.igc')) + 1).zfill(2)
            filename = '_'.join([pname, str(self.date), index]) + '.igc'
            fullname = path.join(task_path, filename)
            # print(f'path to copy file: {fullname}')
            print('path to copy file:', fullname)
            """copy file"""
            try:
                copyfile(src_file, fullname)
                self.track_file = fullname
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
        timedif = time_difference(p2['time'], p1['time'])
