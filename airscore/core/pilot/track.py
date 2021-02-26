"""
Track Library
Use:    import track
        par_id = compUtils.get_track_pilot(filename)

This module reads IGC files using igc_lib library
and creates an object containing all info about the flight

Antonio Golfari, Stuart Mackintosh - 2019
"""

# This library is not used at the moment.
# I decided to leave the code here as in the future we could decide to use it,
# especially is we need to use different tracks formats.
# At the moment we use igc_lib library, and just IGC format.

import json
from pathlib import Path
from shutil import copyfile

from calcUtils import epoch_to_date
from db.conn import db_session
from db.tables import TblTaskResult
from Defines import track_formats
from igc_lib import Flight
from trackUtils import find_pilot, get_task_fullpath, create_igc_filename

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

    def __init__(self, track_file=None, track_id=None, par_id=None, track_type=None, flight=None):
        self.track_file = track_file
        self.track_id = track_id
        self.track_type = track_type
        self.notifications = []
        self.flight = flight  # igc_lib.Flight object
        self.par_id = par_id  # TblParticipant ID # could delete?
        # self.comment = comment  # should be a list?

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
    def comment(self):
        if len(self.notifications) > 0:
            return '; '.join([f'[{n.notification_type}] {n.comment}' for n in self.notifications])
        else:
            return ''

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

    def get_notes(self):
        """flight notifications list"""
        from pilot.notification import Notification

        if self.flight:
            self.notifications = [Notification(notification_type='track', comment=i) for i in self.flight.notes]
        else:
            return []

    def get_pilot(self):
        """Get pilot associated to a track from its filename
        should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc
        """
        # TODO Update workflow using CIVL database / new Participant obj.
        # TODO in the new workflow we should have a Pilot obj, with Track as attr. so get_pilot should be in Pilot
        if self.par_id is None:
            """Get string"""
            self.par_id = find_pilot(Path(self.filename).stem)

    def to_db(self, task_id):
        """Imports track to db"""
        # TODO in the new workflow we should have a Pilot obj, with Track as attr. so we should add() in Pilot
        # TODO G record check
        result = ''

        # add track as result in TblTaskResult table
        with db_session() as db:
            # TODO: g-record still to implement
            track = TblTaskResult(par_id=self.par_id, task_id=task_id, track_file=self.filename, g_record=1)
            self.track_id = db.add(track)
            db.commit()
            result += f"track for pilot with id {self.par_id} correctly stored in database"
        return result

    @classmethod
    def read_file(cls, filename, track_id=None, par_id=None, config=None, print=print):
        """Reads track file and creates a track object"""
        track = cls(track_file=filename, track_id=track_id, par_id=par_id)
        track.get_type()
        if track.track_type in track_formats:
            """file is a valid track format"""
            if track.track_type == "igc":
                """using IGC reader from aerofile library"""
                if config:
                    track.flight = Flight.create_from_file(filename, config_class=config)
                else:
                    track.flight = Flight.create_from_file(
                        filename,
                    )
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
                if not par_id:
                    track.get_pilot()
                # track.get_glider()
                # track.flight = flight
                # track.date = epoch_to_date(track.flight.date_timestamp)
                return track
            else:
                data = {'par_id': par_id, 'track_id': track_id, 'Result': 'Not Yet Processed'}
                print(f'IGC does not meet quality standard set by igc parsing config. Notes:{track.flight.notes}')
                print(json.dumps(data) + '|result')
        else:
            print(f"File {filename} (pilot ID {par_id}) is NOT a valid track file.")

    @classmethod
    def read_db(cls, track_id):
        """Creates a Track Object from a DB Track entry"""
        from db.tables import TrackObjectView as T

        track = cls(track_id=track_id)
        """Read general info about the track"""
        with db_session() as db:
            # get track details.
            q = db.query(T).get(track_id)
            q.populate(track)
            """Creates the flight obj with fixes info"""
            # task_id = q.task_id
            full_path = get_task_fullpath(q.task_id)
            track.flight = Flight.create_from_file(Path(full_path, track.track_file))
        return track

    @staticmethod
    def from_dict(d):
        track = Track()
        for key, value in d.items():
            if hasattr(track, key):
                try:
                    setattr(track, key, value)
                except AttributeError as e:
                    continue
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

    def copy_track_file(self, task_path, pname=None, pid=None):
        """copy track file in the correct folder and with correct name
        name could be changed as the one XContest is sending, or rename that one, as we wish
        if path or pname is None will calculate. note that if bulk importing it is better to pass these values
        rather than query DB for each track"""
        from db.tables import TblParticipant as P

        src_file = self.filename
        if pname is None:
            # get pilot details.
            pilot = P.get_by_id(self.par_id)
            pname = pilot.name
            pid = pilot.ID
        if task_path:
            fullname = create_igc_filename(task_path, self.date, pname, pid)
            print(f'path to copy file: {fullname}')
            """copy file"""
            try:
                copyfile(src_file, fullname)
                self.track_file = fullname.name
                print(f'file successfully copied to : {self.filename}')
                return fullname
            except:
                print('Error copying file:', fullname)
        else:
            print('error, no path given')
        return None
