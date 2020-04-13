"""
Track Library
Use:    import track
        par_id = compUtils.get_track_pilot(filename)

This module reads IGC files using igc_lib library
and creates an object containing all info about the flight

Antonio Golfari, Stuart Mackintosh - 2019
"""

import glob
from os import path, makedirs
from shutil import copyfile

from sqlalchemy.exc import SQLAlchemyError

from Defines import track_formats, IGCPARSINGCONFIG
from calcUtils import epoch_to_date
from db_tables import TblTaskResult
from igc_lib import Flight, FlightParsingConfig
from myconn import Database
from trackUtils import find_pilot, get_task_fullpath
from notification import Notification

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
        self.comment = comment  # should be a list?
        self.flight = flight  # igc_lib.Flight object
        self.par_id = par_id  # TblParticipant ID # could delete?

    @property
    def date(self):
        """datetime.date format"""
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
    def notifications(self):
        """flight notifications list"""
        if self.flight:
            return [Notification(notification_type='track', comment=i) for i in self.flight.notes]
        else:
            return []


    @property
    def filename(self):
        # compatibility
        return self.track_file

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

    def as_dict(self):
        return self.__dict__

    def get_pilot(self):
        """Get pilot associated to a track from its filename
        should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc
        """
        # TODO Update workflow using CIVL database / new Participant obj.
        # TODO in the new workflow we should have a Pilot obj, with Track as attr. so get_pilot should be in Pilot
        if self.par_id is None:
            """Get string"""
            fields = path.splitext(path.basename(self.filename))
            self.par_id = find_pilot(fields[0])

    def to_db(self, task_id):
        """Imports track to db"""
        # TODO in the new workflow we should have a Pilot obj, with Track as attr. so we should add() in Pilot
        # TODO G record check
        result = ''

        # add track as result in TblTaskResult table
        with Database() as db:
            try:
                # TODO: g-record still to implement
                track = TblTaskResult(par_id=self.par_id, task_id=task_id, track_file=self.filename, g_record=1)
                self.track_id = db.session.add(track)
                db.session.commit()
                result += f"track for pilot with id {self.par_id} correctly stored in database"
            except SQLAlchemyError:
                print('Error Inserting track into db:')
                result += f'Error inserting track for pilot with id {self.par_id}'
        return result

    @classmethod
    def read_file(cls, filename, track_id=None, par_id=None, config=None):
        """Reads track file and creates a track object"""
        track = cls(track_file=filename, track_id=track_id, par_id=par_id)
        track.get_type()
        print('type ', track.track_type)
        if track.track_type in track_formats:
            """file is a valid track format"""
            if track.track_type == "igc":
                """using IGC reader from aerofile library"""
                print('reading flight')
                if config:
                    track.flight = Flight.create_from_file(filename, config_class=config)
                else:
                    track.flight = Flight.create_from_file(filename, )
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
                # task_id = q.task_id
                full_path = get_task_fullpath(q.task_id)
                track.flight = Flight.create_from_file(path.join(full_path, track.track_file))
            except SQLAlchemyError:
                print(f'Track Query Error: no result found')

        return track

    @staticmethod
    def from_dict(d):
        track = Track()
        for key, value in d.items():
            if hasattr(track, key):
                setattr(track, key, value)
        return track

    def get_type(self):
        """determine if igc / kml / live / ozi"""
        if self.filename is not None:
            """read first line of file"""
            with open(self.filename, encoding="ISO-8859-1") as f:
                first_line = f.readline()
            if first_line[:1] == 'A':
                """IGC: AXCT7cea4d3ae0df42a1"""
                self.track_type = "igc"
            elif first_line[:3] == '<?x':
                """KML: <?xml version="1.0" encoding="UTF-8"?>"""
                self.track_type = "kml"
            elif "B  UTF" in first_line:
                self.track_type = "ozi"
            elif first_line[:3] == 'LIV':
                self.track_type = "live"
            else:
                self.track_type = None
            print(f"  ** FILENAME: {self.filename} TYPE: {self.track_type} \n")

    def copy_track_file(self, task_path, pname=None):
        """copy track file in the correct folder and with correct name
        name could be changed as the one XContest is sending, or rename that one, as we wish
        if path or pname is None will calculate. note that if bulk importing it is better to pass these values
        rather than query DB for each track"""
        from db_tables import TblParticipant as P

        src_file = self.filename
        # if task_path is None:
        #     task_path = get_task_filepath(self.task_id)

        if pname is None:
            with Database() as db:
                # get pilot details.
                name = db.session.query(P).get(self.par_id).name
                if name:
                    pname = name.replace(' ', '_').lower()

        if task_path:
            """check if directory already exists"""
            if not path.isdir(task_path):
                makedirs(task_path)
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
            except SQLAlchemyError:
                print('Error copying file:', fullname)
        else:
            print('error, path not created')


def validate_G_record(igc_filename):
    """validates g record by passing the file to a validation server.
    Assumtion is that the protocol is the same as the FAI server (POST)
    :argument igc_filename (full path and filename of igc_file)
    :returns PASSED, FAILED or ERROR"""
    from requests import post
    from Defines import G_Record_validation_Server
    try:
        with open(igc_filename, 'rb') as igc:
            file = {'igcfile': igc}
            r = post(G_Record_validation_Server, files=file)
            if r.json()['result'] in ('PASSED', 'FAILED'):
                return r.json()['result']
            else:
                return 'ERROR'

    except IOError:
        print
        "Could not read file:", igc_filename
        return 'ERROR'


def igc_parsing_config_from_yaml(yaml_filename):
    """reads the settings from a YAML file and creates a
    new FlightParsingConfig object for use when processing track files """

    yaml_config = read_igc_config_yaml(yaml_filename)
    if yaml_config is None:
        return None

    config = FlightParsingConfig()
    yaml_config.pop('editable', None)
    yaml_config.pop('description', None)
    for setting in yaml_config:
        config.yaml_config[setting] = yaml_config['min_fixes']
    return config


def read_igc_config_yaml(yaml_filename):
    import ruamel.yaml
    yaml = ruamel.yaml.YAML()
    full_filename = path.join(IGCPARSINGCONFIG, yaml_filename)
    try:
        with open(full_filename) as fp:
            return yaml.load(fp)
    except IOError:
        return None
    

def save_igc_config_yaml(yaml_filename, yaml_data):
    import ruamel.yaml
    yaml = ruamel.yaml.YAML()
    full_filename = path.join(IGCPARSINGCONFIG, yaml_filename)
    try:
        with open(full_filename, 'w') as fp:
            yaml.dump(yaml_data, fp)
    except IOError:
        return None
    return True
