"""
Flight Result Library

contains FlightResult class.
contains statistics about a flight with regards to a task.

Methods:
    from_fsdb
    check_flight - check flight against task and record results (times, distances and leadout coeff)
    to_db - write result to DB (TblTaskResult) store_result_test - write result to DB in test mode(TblTaskResult_test)
    store_result_json - not needed, think we can delete
    to_geojson_result - create json file containing tracklog (split into preSSS, preGoal and postGoal), Thermals,
                        bounds and result obj
    save_result_file - save the json file.

Functions:
    verify_all_tracks   gets all task pilots and check all flights
    update_all_results  stores all results to database

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019

"""

import json
from collections import Counter
from pathlib import Path
from airspace import AirspaceCheck
from calcUtils import string_to_seconds
from db.conn import db_session
from db.tables import TblTaskResult
from Defines import MAPOBJDIR
from formulas.libs.leadcoeff import LeadCoeff
from .notification import Notification
from .participant import Participant
from .waypointachieved import WaypointAchieved


class FlightResult(Participant):
    """Set of statistics about a flight with respect a task.
    Attributes:
        real_start_time: time the pilot actually crossed relevant start gate.
        SSS_time:       time the task was started . i.e relevant start gate.
        waypoints achieved: the last waypoint achieved by the pilot, SSS, ESS, Goal or a waypoint number (wp1 is first wp after SSS)
        ESS_time:       the time the pilot crossed the ESS (local time)
        fixed_LC:       fixed part of lead_coeff, indipendent from other tracks
        lead_coeff:     lead points coeff (for GAP based systems), sum of fixed_LC and variable part calculated during scoring
    """

    def __init__(
        self,
        first_time=None,
        real_start_time=None,
        SSS_time=0,
        ESS_time=None,
        goal_time=None,
        last_time=None,
        best_waypoint_achieved='No waypoints achieved',
        fixed_LC=0,
        lead_coeff=0,
        distance_flown=0,
        last_altitude=0,
        track_id=None,
        track_file=None,
        **kwargs,
    ):
        """

        :type lead_coeff: int
        """
        self.first_time = first_time
        self.real_start_time = real_start_time
        self.SSS_time = SSS_time
        self.ESS_time = ESS_time
        self.ESS_rank = None
        self.speed = 0
        self.goal_time = goal_time
        self.last_time = last_time
        self.best_waypoint_achieved = best_waypoint_achieved
        self.waypoints_achieved = []
        self.fixed_LC = fixed_LC
        self.lead_coeff = lead_coeff
        self.best_dist_to_ESS = 0
        self.distance_flown = distance_flown  # max distance flown calculated along task route
        self.best_distance_time = 0  # rawtime of fix that gave max distance flown
        self.stopped_distance = 0  # distance at fix that achieve best total distance in stopped tasks
        self.stopped_altitude = 0  # altitude at fix that achieve best total distance in stopped tasks
        self.total_distance = 0  # sum of distance and bonus distance with altitude in stopped tasks
        self.max_altitude = 0
        self.ESS_altitude = 0
        self.goal_altitude = 0
        self.last_altitude = last_altitude
        self.landing_time = 0
        self.landing_altitude = 0
        self.result_type = 'nyp'
        self.score = 0
        self.departure_score = 0
        self.arrival_score = 0
        self.distance_score = 0
        self.time_score = 0
        self.penalty = 0
        self.airspace_plot = []
        self.infringements = []  # Infringement for each space
        self.notifications = []  # notification objects
        self.still_flying_at_deadline = False
        self.track_id = track_id
        self.track_file = track_file

        super().__init__(**kwargs)

    def __setattr__(self, attr, value):
        property_names = [p for p in dir(FlightResult) if isinstance(getattr(FlightResult, p), property)]
        if attr in ('name', 'glider') and type(value) is str:
            self.__dict__[attr] = value.title()
        elif attr in ('nat', 'sex') and type(value) is str:
            self.__dict__[attr] = value.upper()
        elif attr not in property_names:
            self.__dict__[attr] = value

    def as_dict(self):
        return self.__dict__

    @property
    def ss_time(self):
        if self.ESS_time:
            return self.ESS_time - self.SSS_time
        else:
            return None

    @property
    def comment(self):
        if len(self.notifications) > 0:
            return '; '.join([f'[{n.notification_type}] {n.comment}' for n in self.notifications])
        else:
            return ''

    @property
    def flight_time(self):
        if self.landing_time and self.first_time:
            return self.landing_time - self.first_time
        if self.last_time and self.first_time:
            return self.last_time - self.first_time
        else:
            return 0

    @property
    def distance(self):
        try:
            return max(self.distance_flown, self.total_distance)
        except TypeError:
            return None

    @property
    def flat_penalty(self):
        """calculates flat_penalty for the pilot.
            We exclude jtg_penalty entries and sum the others.
            We should have just one anyway. It could be negative value (bonus)"""
        if (
            self.notifications
            and any(n.flat_penalty for n in self.notifications if not n.notification_type == 'jtg')
        ):
            return sum(n.flat_penalty for n in self.notifications if not n.notification_type == 'jtg')
        else:
            return 0

    @property
    def jtg_penalty(self):
        """calculates penalty due to Jump the Gun for the pilot.
            We take the min value.
            We should have just one anyway."""
        if self.notifications and any(n.flat_penalty > 0 for n in self.notifications if n.notification_type == 'jtg'):
            return min(n.flat_penalty for n in self.notifications if n.notification_type == 'jtg')
        else:
            return 0

    @property
    def percentage_penalty(self):
        """calculates percentage_penalty for the pilot.
            At the moment only automatic airspace infringements create percentage penalties, so we take the max value.
            We should have just one anyway."""
        if self.notifications and any(n.percentage_penalty > 0 for n in self.notifications):
            return max(n.percentage_penalty for n in self.notifications)
        else:
            return 0

    @property
    def waypoints_made(self):
        if self.waypoints_achieved:
            return len(Counter(el.name for el in self.waypoints_achieved if not el.name == 'Left Launch'))
        else:
            return 0

    @property
    def before_penalty_score(self):
        """total score before any penalty is applied"""
        return sum([self.distance_score or 0, self.time_score or 0, self.arrival_score or 0, self.departure_score or 0])

    @classmethod
    def from_participant(cls, participant: Participant):
        """Creates FlightResult obj from Participant obj."""
        if isinstance(participant, Participant):
            result = cls()
            result.as_dict().update(participant.as_dict())
            return result

    @staticmethod
    def from_fsdb(elem, task):
        """Creates Results from FSDB FsParticipant element, which is in xml format.
        Unfortunately the fsdb format isn't published so much of this is simply an
        exercise in reverse engineering.
        """
        from pilot.notification import Notification

        offset = task.time_offset
        dep = task.formula.formula_departure
        arr = task.formula.formula_arrival

        result = FlightResult()
        result.ID = int(elem.get('id'))
        fdata = elem.find('FsFlightData')
        fres = elem.find('FsResult')
        if fdata is None:
            '''pilot is abs'''
            result.result_type = 'abs'
            return result

        if not fdata.items() and float(fres.get('distance')) == 0:
            '''pilot is dnf'''
            result.result_type = 'dnf'
            return result

        if fdata.get('tracklog_filename') in [None, '']:
            '''pilot is min dist'''
            result.result_type = 'mindist'
        else:
            result.track_file = fdata.get('tracklog_filename')
            result.result_type = 'lo'
        result.real_start_time = (
            None if not fdata.get('started_ss') else string_to_seconds(fdata.get('started_ss')) - offset
        )
        result.last_altitude = float(fdata.get('last_tracklog_point_alt') or 0)
        result.max_altitude = int(fdata.get('max_alt') if fdata.get('max_alt') is not None else 0)
        result.track_file = fdata.get('tracklog_filename')
        result.lead_coeff = None if fdata.get('lc') is None else float(fdata.get('lc'))
        if not fdata.get('finished_ss') == "":
            result.ESS_altitude = float(fdata.get('altitude_at_ess') or 0)

        if fres is not None:
            '''reading flight data'''
            result.score = float(fres.get('points'))
            result.total_distance = float(fres.get('distance')) * 1000  # in meters
            result.distance_flown = float(fres.get('real_distance')) * 1000  # in meters
            result.SSS_time = None if not fres.get('started_ss') else string_to_seconds(fres.get('started_ss')) - offset
            if result.SSS_time is not None:
                result.ESS_time = (
                    None if not fres.get('finished_ss') else string_to_seconds(fres.get('finished_ss')) - offset
                )
                if task.SS_distance is not None and result.ESS_time is not None and result.ESS_time > 0:
                    result.speed = (task.SS_distance / 1000) / ((result.ESS_time - result.SSS_time) / 3600)
                    result.ESS_rank = None if not fres.get('finished_ss_rank') else int(fres.get('finished_ss_rank'))
                if fdata.get('reachedGoal') == "1" or (result.ESS_time and task.fake_goal_turnpoint):
                    result.goal_time = (
                        None
                        if not fdata.get('finished_task')
                        else string_to_seconds(fdata.get('finished_task')) - offset
                    )
                    result.result_type = 'goal'
            else:
                result.ESS_time = None
            result.last_altitude = int(fres.get('last_altitude_above_goal'))
            result.distance_score = float(fres.get('distance_points'))
            result.time_score = float(fres.get('time_points'))
            result.penalty = 0
            if not fres.get('penalty_reason_auto') == "":
                notification = Notification(
                    notification_type='jtg',
                    flat_penalty=float(fres.get('penalty_points_auto')),
                    comment=(fres.get('penalty_reason_auto')),
                )
                result.notifications.append(notification)
            if dep == 'on':
                result.departure_score = float(fres.get('departure_points'))
            elif dep == 'leadout':
                result.departure_score = float(fres.get('leading_points'))
            else:
                result.departure_score = 0  # not necessary as it it initialized to 0
            result.arrival_score = float(fres.get('arrival_points')) if arr != 'off' else 0
        if elem.find('FsResultPenalty') is not None or fres.get('penalty_reason'):
            '''reading penalties'''
            if elem.find('FsResultPenalty') is not None:
                pen = elem.find('FsResultPenalty')
                percentage_penalty = float(pen.get('penalty'))
                flat_penalty = float(pen.get('penalty_points'))
                reason = pen.get('penalty_reason')
            else:
                percentage_penalty = float(fres.get('penalty'))
                flat_penalty = float(fres.get('penalty_points'))
                reason = fres.get('penalty_reason')
            notification = Notification(
                notification_type='custom',
                percentage_penalty=percentage_penalty,
                flat_penalty=flat_penalty,
                comment=reason,
            )
            result.notifications.append(notification)
            '''calculate points'''
            result.penalty = sum(
                [result.distance_score, result.departure_score, result.arrival_score, result.time_score]
            ) - result.score

        return result

    @staticmethod
    def read(par_id: int, task_id: int):
        """reads result from database"""
        from db.tables import FlightResultView as R
        from db.tables import TblParticipant as P

        result = FlightResult()
        with db_session() as db:
            q = db.query(R).filter_by(par_id=par_id, task_id=task_id).first()
            if not q:
                '''we do not have a result. Creating obj from Participant'''
                q = P.get_by_id(par_id)
            q.populate(result)
        return result

    @staticmethod
    def from_dict(d: dict):
        result = FlightResult()
        for key, value in d.items():
            if key == 'notifications' and value:
                for n in value:
                    result.notifications.append(Notification.from_dict(n))
            elif key == 'waypoints_achieved' and value:
                for n in value:
                    result.waypoints_achieved.append(WaypointAchieved.from_dict(n))
            elif hasattr(result, key):
                setattr(result, key, value)
        return result

    @staticmethod
    def from_result(result):
        """ creates a Pilot obj. from result dict in Task Result json file"""
        return FlightResult.from_dict(result)

    @staticmethod
    def from_flight_check(par_id, flight, task, airspace_obj=None, deadline=None, print=print):
        """ creates a FlightResult obj. from result dict in Task Result json file"""
        result = FlightResult.from_participant(Participant.read(par_id))
        return result.check_flight(flight, task, airspace_obj, deadline, print)

    def reset(self):
        init = FlightResult()
        attr_list = [
            'first_time',
            'real_start_time',
            'SSS_time',
            'ESS_time',
            'ESS_rank',
            'speed',
            'goal_time',
            'last_time',
            'best_waypoint_achieved',
            'waypoints_achieved',
            'fixed_LC',
            'lead_coeff',
            'distance_flown',
            'best_distance_time',
            'stopped_distance',
            'stopped_altitude',
            'total_distance',
            'max_altitude',
            'ESS_altitude',
            'goal_altitude',
            'last_altitude',
            'landing_time',
            'landing_altitude',
            'result_type',
            'score',
            'departure_score',
            'arrival_score',
            'distance_score',
            'time_score',
            'penalty',
            'airspace_plot',
            'infringements',
            'notifications',
            'still_flying_at_deadline',
        ]
        for attr in attr_list:
            setattr(self, attr, getattr(init, attr))

    def check_flight(self, flight, task, airspace_obj=None, deadline=None, print=print):
        """Checks a Flight object against the task.
        Args:
               :param flight: a Flight object
               :param task: a Task
               :param airspace_obj: airspace object to check flight against
               :param deadline: in multiple start or elapsed time, I need to check again track using Min_flight_time
                            as deadline
               :param print: function to overide print() function. defaults to print() i.e. no override. Intended for
                             sending progress to front end
        Returns:
                a list of GNSSFixes of when turnpoints were achieved.
        """
        from flightcheck.flightcheck import calculate_final_results, check_fixes
        from flightcheck.flightpointer import FlightPointer

        '''initialize'''
        if not self.result_type == 'nyp':
            self.reset()
        self.result_type = 'lo'

        if not task.optimised_turnpoints:
            # this should not happen
            task.calculate_optimised_task_length()

        ''' Altitude Source: '''
        alt_source = 'GPS' if task.formula.scoring_altitude is None else task.formula.scoring_altitude
        alt_compensation = 0 if alt_source == 'GPS' or task.QNH == 1013.25 else task.alt_compensation

        '''leadout coefficient'''
        if task.formula.formula_departure == 'leadout':
            lead_coeff = LeadCoeff(task)
        else:
            lead_coeff = None

        '''flight origin'''
        self.first_time = flight.fixes[0].rawtime if not hasattr(flight, 'takeoff_fix') else flight.takeoff_fix.rawtime
        '''flight end'''
        self.landing_time = flight.landing_fix.rawtime
        self.landing_altitude = (
            flight.landing_fix.gnss_alt if alt_source == 'GPS' else flight.landing_fix.press_alt + alt_compensation
        )

        '''Turnpoint managing'''
        tp = FlightPointer(task)

        '''Airspace check managing'''
        if task.airspace_check:
            if not airspace_obj and not deadline:
                print(f'We should not create airspace here')
                airspace_obj = AirspaceCheck.from_task(task)

        check_fixes(self, flight.fixes, task, tp, lead_coeff, airspace_obj, deadline=deadline, print=print)

        calculate_final_results(self, task, tp, lead_coeff, airspace_obj, deadline=deadline, print=print)

    def to_geojson_result(self, track, task, pilot_info=None, second_interval=5):
        """Dumps the flight to geojson format used for mapping.
        Contains tracklog split into pre SSS, pre Goal and post goal parts, thermals, takeoff/landing,
        result object, waypoints achieved, and bounds

        second_interval = resolution of tracklog. default one point every 5 seconds. regardless it will
                            keep points where waypoints were achieved.
        returns the Json string."""
        from mapUtils import result_to_geojson

        info = {'taskid': task.id, 'task_name': task.task_name, 'comp_name': task.comp_name}
        if pilot_info:
            info.update(
                dict(
                    pilot_name=pilot_info.name,
                    pilot_nat=pilot_info.nat,
                    pilot_sex=pilot_info.sex,
                    pilot_parid=pilot_info.par_id,
                    Glider=pilot_info.glider,
                )
            )
        else:
            info = {}
        tracklog, thermals, takeoff_landing, bbox, waypoint_achieved, infringements = result_to_geojson(
            self, task, track.flight, second_interval
        )
        data = {
            'info': info,
            'tracklog': tracklog,
            'thermals': thermals,
            'takeoff_landing': takeoff_landing,
            'bounds': bbox,
            'waypoint_achieved': waypoint_achieved,
            'infringements': infringements,
        }
        return data

    def save_tracklog_map_file(self, task, flight=None, second_interval=5):
        """ Creates the file to be used to display pilot's track on map"""
        import json
        from pathlib import Path

        from Defines import MAPOBJDIR
        from pilot.track import Track

        if self.result_type not in ('abs', 'dnf', 'mindist', 'nyp'):
            ID = self.par_id if not self.ID else self.ID  # registration needs to check that all pilots
            # have a unique ID, with option to use par_id as ID for all pilots if no ID is given
            print(f"{ID}. {self.name}: ({self.track_file})")
            if not flight:
                filename = Path(task.file_path, self.track_file)
                '''load track file'''
                flight = Track.process(filename, task)
            data = create_tracklog_map_file(self, task, flight, second_interval)
            res_path = Path(MAPOBJDIR, 'tracks', str(task.id))
            """check if directory already exists"""
            if not res_path.is_dir():
                res_path.mkdir(mode=0o755, parents=True)
            """creates a name for the file.
            par_id.track"""
            filename = f'{self.par_id}.track'
            fullname = Path(res_path, filename)
            """copy file"""
            try:
                with open(fullname, 'w') as f:
                    json.dump(data, f)
                return fullname
            except:
                print('Error saving file:', fullname)

    def save_tracklog_map_result_file(self, data, trackid, taskid):
        """save tracklog map result file in the correct folder as defined by DEFINES"""
        from pathlib import Path

        res_path = Path(MAPOBJDIR, 'tracks', str(taskid))
        """check if directory already exists"""
        if not res_path.is_dir():
            res_path.mkdir(mode=0o755, parents=True)
        """creates a name for the track
        name_surname_date_time_index.igc
        if we use flight date then we need an index for multiple tracks"""
        filename = f'{trackid}.track'
        fullname = Path(res_path, filename)
        try:
            with open(fullname, 'w') as f:
                json.dump(data, f)
            return fullname
        except:
            print('Error saving file:', fullname)

    def create_result_dict(self):
        """ creates dict() with all information"""
        from result import TaskResult as R

        result = {x: getattr(self, x) for x in R.results_list if x in dir(self)}
        result['notifications'] = [n.as_dict() for n in self.notifications]
        result['waypoints_achieved'] = [w.as_dict() for w in self.waypoints_achieved]
        return result


def verify_all_tracks(task, lib, airspace=None, print=print):
    """Gets in input:
    task:       Task object
    lib:        Formula library module"""
    from pathlib import Path
    from trackUtils import igc_parsing_config_from_yaml, check_flight
    from pilot.track import Track

    pilots = [p for p in task.pilots if p.result_type not in ('abs', 'dnf', 'mindist') and p.track_file]

    '''check if any track is missing'''
    if any(not Path(task.file_path, p.track_file).is_file() for p in pilots):
        print(f"The following tracks are missing from folder {task.file_path}:")
        for track in [p.track_file for p in pilots if not Path(task.file_path, p.track_file).is_file()]:
            print(f"{track}")
        return None

    print('getting tracks...')
    number_of_pilots = len(task.pilots)
    FlightParsingConfig = igc_parsing_config_from_yaml(task.igc_config_file)

    for track_number, pilot in enumerate(task.pilots, 1):
        print(f"{track_number}/{number_of_pilots}|track_counter")
        if pilot.result_type not in ('abs', 'dnf', 'mindist') and pilot.track_file:
            print(f"{pilot.ID}. {pilot.name}: ({pilot.track_file})")
            filename = Path(task.file_path, pilot.track_file)
            '''load track file'''
            flight = Track.process(filename, task, config=FlightParsingConfig)
            if flight:
                pilot.flight_notes = flight.notes
                if flight.valid:
                    '''check flight against task and create map'''
                    check_flight(pilot, flight, task, airspace=airspace, print=print)
                elif flight:
                    print(f'Error in parsing track: {[x for x in flight.notes]}')
    lib.process_results(task)


def adjust_flight_results(task, lib, airspace=None):
    """Called when multi-start or elapsed time task was stopped.
    We need to check again and adjust results of pilots that flew more than task duration"""
    from pilot.track import Track
    from trackUtils import check_flight

    maxtime = task.duration
    for pilot in task.pilots:
        if pilot.SSS_time:
            last_time = pilot.SSS_time + maxtime
            if (not pilot.ESS_time and pilot.best_distance_time > last_time) or (
                pilot.ESS_time and pilot.ss_time > maxtime
            ):
                '''need to adjust pilot result'''
                filename = Path(task.file_path, pilot.track_file)
                '''load track file'''
                flight = Track.process(filename, task)
                '''check flight against task and create map'''
                if flight:
                    check_flight(pilot, flight, task, airspace=airspace, print=print)

    lib.process_results(task)


def update_status(par_id: int, task_id: int, status: str) -> int:
    """Create or update pilot status ('abs', 'dnf', 'mindist')"""
    result = FlightResult.read(par_id, task_id)
    result.result_type = status
    row = TblTaskResult.from_obj(result)
    row.task_id = task_id
    row.save_or_update()
    return row.track_id


def delete_track(trackid: int, delete_file=False):
    from pathlib import Path

    from db.tables import TblTaskResult
    from trackUtils import get_task_fullpath

    row_deleted = None
    track = TblTaskResult.get_by_id(trackid)
    if track:
        if track.track_file is not None and delete_file:
            Path(get_task_fullpath(track.task_id), track.track_file).unlink(missing_ok=True)
        track.delete()
        row_deleted = True
    return row_deleted


def get_task_results(task_id: int, comp_id: int = None) -> list:
    from db.tables import TblNotification as N, TblTaskResult as R, TblTrackWaypoint as W, TblCompAttribute as CA, \
        TblTask as T
    from pilot.notification import Notification
    from .participant import get_participants_meta

    if not comp_id:
        comp_id = T.get_by_id(task_id).comp_id
    pilots = [R.populate(p, FlightResult()) for p in R.get_task_results(task_id)]
    track_list = list(filter(None, map(lambda x: x.track_id, pilots)))
    notifications = N.from_track_list(track_list)
    achieved = W.get_dict_list(track_list)
    attr_list = CA.get_all(comp_id=comp_id, attr_key='meta')
    if attr_list:
        par_list = [p.par_id for p in pilots]
        custom_list = get_participants_meta(par_list)
    for p in pilots:
        if attr_list:
            atts = [e for e in custom_list if e.par_id == p.par_id and e.attr_id in map(lambda x: x.attr_id, attr_list)]
            p.custom = {str(a.attr_id): a.meta_value for a in atts}
        if not p.result_type:
            p.result_type = 'nyp'
        else:
            pil_notif = list(filter(lambda x: x.track_id == p.track_id, notifications))
            if pil_notif:
                p.notifications = [el.populate(Notification()) for el in pil_notif]
                notifications = list(filter(lambda x: x not in pil_notif, notifications))
            if p.result_type in ('lo', 'goal'):
                wa = list(filter(lambda x: x['track_id'] == p.track_id, achieved))
                if wa:
                    p.waypoints_achieved = [WaypointAchieved.from_dict(el) for el in wa]
                    achieved = list(filter(lambda x: x not in wa, achieved))
    return pilots


def get_task_pilots(task_id: int, comp_id: int = None) -> list:
    """ Loads FlightResult obj. with only Participants info into Task obj."""
    from db.tables import TblTask as T, TblTaskResult as R
    from compUtils import get_participants

    if not comp_id:
        comp_id = T.get_by_id(task_id).comp_id
    pilots = [FlightResult.from_participant(p) for p in get_participants(comp_id)]
    tracks = R.get_all(task_id=task_id)
    if tracks:
        for p in pilots:
            res = next((x for x in tracks if x.par_id == p.par_id), None)
            if res:
                p.track_id, p.track_file, p.result_type = res.track_id, res.track_file, res.result_type
    return pilots


def save_track(result: FlightResult, task_id: int):
    """stores pilot result to database.
    we already have FlightResult.to_db()
    but if we organize track reading using Pilot obj. this should be useful.
    We will also be able to delete a lot of redundant info about track filename, pilot ID, task_id and so on"""
    from db.tables import TblTaskResult as R
    from pilot.notification import update_notifications
    from pilot.waypointachieved import update_waypoints_achieved

    '''checks conformity'''
    if not (result.par_id and task_id):
        '''we miss info about pilot and task'''
        print(f"Error: missing info about participant ID and/or task ID")
        return None

    if result.track_id:
        '''read db row'''
        row = R.get_by_id(result.track_id)
        row.update(**result.as_dict())
    else:
        '''create a new result'''
        row = R.from_obj(result)
        row.task_id = task_id
        row.save()
        result.track_id = row.track_id

    '''notifications'''
    update_notifications(result)
    '''waypoints_achieved'''
    update_waypoints_achieved(result)


def update_all_results(pilots: list, task_id: int):
    """get results to update from the list
    It is called from Task.check_all_tracks(), so only during Task full rescoring
    And from FSDB.add results.
    We are then deleting all present non admin Notification from database for results, as related to old scoring.
    """
    from dataclasses import asdict

    from db.tables import TblNotification as N
    from db.tables import TblTaskResult as R
    from db.tables import TblTrackWaypoint as W
    from sqlalchemy import and_

    insert_mappings = []
    update_mappings = []
    notif_mappings = []
    achieved_mappings = []
    for pilot in pilots:
        r = dict(task_id=task_id)
        for key in R.__table__.columns.keys():
            if hasattr(pilot, key):
                r[key] = getattr(pilot, key)
        if pilot.track_id:
            update_mappings.append(r)
        else:
            insert_mappings.append(r)

    '''update database'''
    with db_session() as db:
        if insert_mappings:
            db.bulk_insert_mappings(R, insert_mappings, return_defaults=True)
            db.flush()
            for elem in insert_mappings:
                next(pilot for pilot in pilots if pilot.par_id == elem['par_id']).track_id = elem['track_id']
        if update_mappings:
            db.bulk_update_mappings(R, update_mappings)
            db.flush()
        '''notifications and waypoints achieved'''
        '''delete old entries'''
        db.query(N).filter(
            and_(
                N.track_id.in_([r['track_id'] for r in update_mappings]),
                N.notification_type.in_(['jtg', 'auto', 'track']),
            )
        ).delete(synchronize_session=False)
        db.query(W).filter(W.track_id.in_([r['track_id'] for r in update_mappings])).delete(synchronize_session=False)
        '''collect new ones'''
        for pilot in pilots:
            notif_mappings.extend(
                [
                    dict(track_id=pilot.track_id, **asdict(n))
                    for n in pilot.notifications
                    if not n.notification_type == 'custom'
                ]
            )
            achieved_mappings.extend([dict(track_id=pilot.track_id, **asdict(w)) for w in pilot.waypoints_achieved])
        '''bulk insert'''
        if achieved_mappings:
            db.bulk_insert_mappings(W, achieved_mappings)
        if notif_mappings:
            db.bulk_insert_mappings(N, notif_mappings, return_defaults=True)
            db.flush()
            notif_list = filter(lambda i: i['notification_type'] in ['jtg', 'auto'], notif_mappings)
            trackIds = set([i['track_id'] for i in notif_list])
            for idx in trackIds:
                pilot = next(p for p in pilots if p.track_id == idx)
                for n in filter(lambda i: i['track_id'] == idx, notif_list):
                    notif = next(el for el in pilot.notifications if el.comment == n['comment'])
                    notif.not_id = n['not_id']
    return True


def create_tracklog_map_file(pilot, task, flight, second_interval=5):
    """Dumps the flight to geojson format used for mapping.
    Contains tracklog split into pre SSS, pre Goal and post goal parts, thermals, takeoff/landing,
    result object, waypoints achieved, and bounds
    second_interval = resolution of tracklog. default one point every 5 seconds. regardless it will
                        keep points where waypoints were achieved.
    returns the Json string."""
    from pathlib import Path

    from mapUtils import result_to_geojson

    '''create info'''
    info = {
        'taskid': task.id,
        'task_name': task.task_name,
        'comp_name': task.comp_name,
        'pilot_name': pilot.name,
        'pilot_nat': pilot.nat,
        'pilot_sex': pilot.sex,
        'pilot_parid': pilot.par_id,
        'Glider': pilot.glider,
        'track_file': Path(task.file_path, pilot.track_file).as_posix(),
    }
    tracklog, thermals, takeoff_landing, bbox, waypoint_achieved, infringements = result_to_geojson(
        pilot, task, flight, second_interval
    )
    data = {
        'info': info,
        'tracklog': tracklog,
        'thermals': thermals,
        'takeoff_landing': takeoff_landing,
        'bounds': bbox,
        'waypoint_achieved': waypoint_achieved,
        'infringements': infringements,
    }
    return data
