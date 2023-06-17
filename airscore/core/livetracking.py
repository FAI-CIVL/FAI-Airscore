"""
Code to get live tracking tracks chunks and calculate live results
Web interrogation:
https://lt.flymaster.net/wlb/getLiveData.php?trackers={“176399":1559779200,”177485":1557549310}

where 176399 is the tracker serial number, and 1559779200 is unixtime stamp of the fixes,  100 fixes will be sent.

result will be a json array:

"d":1564562248,"ai":"2601676","oi":"1325414","h":"961","c":"920","s":"966","b":"128","v":"10"

where d is the timestamp of the fix
ai is the latitude divide by 60000 to get a coordinate.
oi is the longitude
h is the gps altitude
c is the barometric altitude
s is the height of ground (SRTM)
b bearing
v velocity
"""
import time
from datetime import datetime
from pathlib import Path
from Defines import LIVETRACKDIR

from airspace import AirspaceCheck
from logger import Logger
from pilot.flightresult import FlightResult
from pilot.notification import Notification
from pilot.waypointachieved import WaypointAchieved
from trackUtils import create_igc_filename, igc_parsing_config_from_yaml
from pilot.track import GNSSFix
from calcUtils import igc_coords, sec_to_time, sec_to_string, epoch_to_string
from task import Task

'''parameters for livetracking'''
config = igc_parsing_config_from_yaml('smartphone')
config.max_flight_speed = 250  # Km/h
config.max_still_seconds = 30  # max consecutive seconds under min speed not to be considered landed
config.time_after_deadline = 180  # (sec) time after deadline at which livetrack can be stopped
config.min_distance = 100  # meters max distance from launch not to be considered airborne if fast enough
config.min_alt_difference = 50  # meters min altitude difference not to be considered landed

'''number of fixes to get from server'''
default_interval = 180  # seconds


class LiveFix(GNSSFix):
    """GNSSFix from igc_lib, a little easier to initialise, adding alt attribute as gps alt if not specified"""
    def __init__(self, rawtime, lat, lon, press_alt, gnss_alt, alt=None, height=None, speed=None, index=None):
        self.alt = alt or gnss_alt
        self.height = height
        self.speed = speed

        super().__init__(rawtime=rawtime, lat=lat, lon=lon, validity='A',
                         press_alt=press_alt, gnss_alt=gnss_alt, index=index, extras='')


class LiveResult(FlightResult):
    """FlightResult from pilot.flightresult, adding livetracking attributes and methods used in livetracking"""
    def __init__(self, livetrack: list = None, suspect_landing_fix: LiveFix = None, live_comment: str = None, **kwargs):
        super(LiveResult, self).__init__(**kwargs)
        self.livetrack = livetrack or []
        self.suspect_landing_fix = suspect_landing_fix
        self.live_comment = live_comment

    @staticmethod
    def from_result(d: dict):
        """ creates a LiveResult obj. from result dict in Livetracking json file"""

        p = LiveResult()
        p.as_dict().update(d)
        p.waypoints_achieved = [WaypointAchieved.from_dict(d) for d in p.waypoints_achieved]
        p.notifications = [Notification.from_dict(d) for d in p.notifications]
        if isinstance(p.suspect_landing_fix, dict):
            fix = p.suspect_landing_fix
            p.suspect_landing_fix = LiveFix(**fix)

    def update_from_result(self, d: dict):
        """ creates a LiveResult obj. from result dict in Livetracking json file"""

        self.as_dict().update(d)
        self.waypoints_achieved = [WaypointAchieved.from_dict(d) for d in self.waypoints_achieved]
        self.notifications = [Notification.from_dict(d) for d in self.notifications]
        if isinstance(self.suspect_landing_fix, dict):
            fix = self.suspect_landing_fix
            self.suspect_landing_fix = LiveFix(**fix)

    def create_result_dict(self):
        """ creates dict() with all information"""

        result = {x: getattr(self, x) for x in LiveTracking.results_list if x in dir(self)}
        result['notifications'] = [n.as_dict() for n in self.notifications]
        result['waypoints_achieved'] = [w.as_dict() for w in self.waypoints_achieved]
        result['suspect_landing_fix'] = None
        if self.suspect_landing_fix:
            f = self.suspect_landing_fix
            result['suspect_landing_fix'] = dict(rawtime=f.rawtime, lat=f.lat, lon=f.lon, press_alt=f.press_alt,
                                                 gnss_alt=f.gnss_alt, alt=f.alt, speed=f.speed, index=f.index)

        return result


class LiveTask(Task):
    """Task from task, with methods to get LiveResult Obj instead of FlightResult"""
    def __init__(self, **kwargs):

        super().__init__(**kwargs)

    def get_results(self):
        """ Loads all FlightResult obj. into Task obj."""

        pilots = get_task_results(self.id)
        if self.stopped_time:
            for p in pilots:
                p.still_flying_at_deadline = p.stopped_distance > 0
        self.pilots = pilots


class LiveTracking(object):
    results_list = [
        'par_id',
        'ID',
        'civl_id',
        'name',
        'sponsor',
        'nat',
        'sex',
        'glider',
        'glider_cert',
        'team',
        'nat_team',
        'live_id',
        'distance_flown',
        'distance',
        'first_time',
        'SSS_time',
        'real_start_time',
        'ESS_time',
        'goal_time',
        'ss_time',
        'last_time',
        'landing_time',
        'last_altitude',
        'waypoints_made',
        'height',
        'live_comment',
        'pil_id',
        'fixed_LC',
        'track_file'
    ]

    def __init__(
            self,
            task: LiveTask = None,
            airspace: AirspaceCheck = None,
            test: bool = False,
            init_timestamp: int = int(time.time())
    ):

        self.task = task  # LiveTask object
        self.airspace = airspace  # AirspaceCheck object
        self.test = test  # bool, test mode, using stored information about events in the past
        self.init_timestamp = init_timestamp  # real unix time livetracking has started
        self.result = {}  # result string
        self.offset = 0  # offset to use for recovering LT time if started late

    @property
    def timestamp(self):
        return int(time.time())

    @property
    def json_result(self):
        import jsonpickle

        return jsonpickle.encode(self.result, unpicklable=False)

    @property
    def task_id(self):
        return None if not self.task else self.task.task_id

    @property
    def pilots(self):
        return (
            [] if not self.task else [p for p in self.task.pilots if p.live_id and p.result_type not in ('dnf', 'abs')]
        )

    @property
    def flying_pilots(self):
        # return [p for p in self.pilots if not (p.landing_time or p.goal_time or p.result_type == 'min_dist')]
        return [p for p in self.pilots if not (p.landing_time or p.goal_time)]

    @property
    def flying_pilots_with_new_fixes(self):
        return [p for p in self.flying_pilots if len(p.livetrack) > config.min_fixes
                and p.livetrack[-1].rawtime > (p.last_time or 0)]

    @property
    def track_source(self):
        return None if not self.task else self.task.track_source

    @property
    def properly_set(self):
        # print(f"task: {bool(self.task is not None)}, pilots: {bool(self.pilots)}, track_source: {bool(self.track_source)}, wpt: {bool(self.task.turnpoints)}, start: {bool(self.task.start_time is not None)}")
        return (
            (self.task is not None)
            and self.pilots
            and self.track_source
            and self.task.turnpoints
            and (self.task.start_time is not None)
        )

    @property
    def unix_date(self):
        return 0 if not self.task else int(time.mktime(self.task.date.timetuple()))

    @property
    def opening_timestamp(self):
        return 0 if not self.task else self.task.window_open_time + self.unix_date

    @property
    def closing_timestamp(self):
        """ Time after which pilots cannot start racing anylonger"""
        if not self.task:
            return 0
        elif self.task.window_close_time:
            return self.task.window_close_time + self.unix_date
        elif self.task.start_close_time:
            return self.task.start_close_time + self.unix_date
        else:
            return self.ending_timestamp

    @property
    def start_timestamp(self):
        return 0 if not self.task else self.task.start_time + self.unix_date

    @property
    def ending_timestamp(self):
        if not self.task:
            return None
        elif self.task.stopped_time:
            return self.task.stopped_time + self.unix_date
        elif self.task.task_deadline:
            return self.task.task_deadline + self.unix_date
        else:
            '''end of day'''
            return self.unix_date + 3600 * 23 + 3599

    @property
    def test_offset(self):
        return self.init_timestamp - self.opening_timestamp if self.test else 0

    @property
    def now(self):
        return self.timestamp - self.test_offset if self.test else self.timestamp - self.offset

    @property
    def status(self):
        if not self.task:
            return 'Task is not set yet'
        elif self.task.cancelled:
            return 'Task is Cancelled'
        elif not (self.task and self.task.turnpoints):
            return 'Task not defined yet'
        elif not self.properly_set:
            return 'Livetracking source is not set properly'
        elif not self.task.start_time:
            return 'Times are not set yet'
        elif self.task.stopped_time:
            return 'Task is Stopped'
        else:
            if self.now < self.opening_timestamp:
                return 'Waiting Window Opening'
            elif self.finished:
                return 'Livetracking terminated'
            else:
                return 'Livetrack service running'

    @property
    def finished(self):
        return (
            self.task.cancelled
            # or self.task.stopped_time and self.now > self.task.start_time + config.time_after_deadline
            or self.now > self.ending_timestamp + config.time_after_deadline  # should cover Stopped Task as well
            or (self.properly_set and self.now > self.start_timestamp and len(self.flying_pilots) == 0)
            # or (self.now > self.closing_timestamp and all(el.first_time in (0, None) for el in self.flying_pilots))
        )

    @property
    def headers(self):

        main = ''
        details = ''
        warning = ''
        if self.task.cancelled:
            '''task has been cancelled'''
            main = f"Task has been CANCELLED."
        elif not (self.task and self.task.turnpoints):
            main = "Today's Task is not yet defined. Try Later."
        elif not self.properly_set:
            main = "Livetracking source is not set properly."
        else:
            task_type = 'Race to Goal' if self.task.task_type == 'race' else self.task.task_type.title()
            main = f"Task Set: {round(self.task.opt_dist / 1000, 1)} Km {task_type}."
            if not self.task.start_time:
                details = 'Times are not set yet.'
            else:
                window = sec_to_string(self.task.window_open_time, self.task.time_offset, seconds=False)
                start = sec_to_string(self.task.start_time, self.task.time_offset, seconds=False)
                details = f'Window opens at {window} and start is at {start} (Local Time).'
            if self.task.stopped_time:
                stopped = sec_to_string(self.task.stopped_time, self.task.time_offset, seconds=False)
                warning = f'Task has been stopped at {stopped} (Local Time).'
            elif self.finished:
                print(f'--- LT finished ---')
                print(f'cancelled: {self.task.cancelled}, stopped: {self.task.stopped_time}, already ended: {self.now > self.ending_timestamp + config.time_after_deadline}')
                print(f'finished: {self.finished}, now: {self.now} ({epoch_to_string(self.now, self.task.time_offset)}, start: {self.start_timestamp} ({epoch_to_string(self.start_timestamp, self.task.time_offset)}), end: {self.ending_timestamp} ({epoch_to_string(self.ending_timestamp, self.task.time_offset)})')
                print(f'properly_set: {self.properly_set}, flying: {len(self.flying_pilots)}')
                print(f'condition nobody is flying: {self.properly_set and self.now > self.start_timestamp and len(self.flying_pilots) == 0}')
                print(f'condition nobody will fly: {self.now > self.closing_timestamp and all(el.first_time in (0, None) for el in self.flying_pilots)}')
                warning = f'Livetracking is terminated. Provisional Results will be available shortly.'
        return dict(main=main, warning=warning, details=details)

    @property
    def filename(self):

        return None if not self.task else Path(LIVETRACKDIR, str(self.task_id))

    @staticmethod
    def read(task_id):

        try:
            task = LiveTask.read(task_id)
            if any((wp.type == 'goal' for wp in task.turnpoints)) and not task.distance:
                task.calculate_task_length()
                task.calculate_optimised_task_length()
            test = task.date < datetime.today().date()
            task.get_results()

            airspace = AirspaceCheck.from_task(task)
            livetrack = LiveTracking(task, airspace, test)
        except:
            livetrack = None

        return livetrack

    def create_result(self):
        from result import TaskResult

        file_stats = {
            'timestamp': self.now,
            'init_timestamp': self.init_timestamp,
            'result_type': 'task',
            'status': self.status
        }

        headers = self.headers
        info = {x: getattr(self.task, x) for x in TaskResult.info_list if x in dir(self.task)}
        data = []
        route = []

        if self.properly_set:
            for idx, tp in enumerate(self.task.turnpoints):
                wpt = {x: getattr(tp, x) for x in TaskResult.route_list if x in dir(tp)}
                wpt['cumulative_dist'] = self.task.partial_distance[idx]
                route.append(wpt)
            for p in self.pilots:
                result = {x: getattr(p, x) for x in self.results_list if x in dir(p)}
                result['notifications'] = [n.as_dict() for n in p.notifications]
                result['waypoints_achieved'] = [w.as_dict() for w in p.waypoints_achieved]
                result['suspect_landing_fix'] = None

                if p.suspect_landing_fix:
                    f = p.suspect_landing_fix
                    result['suspect_landing_fix'] = dict(rawtime=f.rawtime, lat=f.lat, lon=f.lon,
                                                         press_alt=f.press_alt, gnss_alt=f.gnss_alt,
                                                         index=f.index)
                data.append(result)
        self.result.update(dict(file_stats=file_stats, headers=headers, info=info, route=route, data=data))
        self.create_json_file()

    def update_result_status(self, finalise: bool = False):
        from result import TaskResult

        self.result['file_stats']['timestamp'] = self.now
        '''check if status changed'''
        status = self.result['file_stats']['status']
        if finalise or not status == self.status:
            if finalise:
                self.result['file_stats']['status'] = f'Livetracking is terminated. ' \
                                                      f'Provisional Results will be available shortly.'
            else:
                self.result['file_stats']['status'] = self.status
            self.result['headers'] = self.headers
            self.result['info'] = {x: getattr(self.task, x) for x in TaskResult.info_list if x in dir(self.task)}

    def update_pilots_list(self):
        """Removes any pilot from result json file that has meanwhile become ABS or DNF"""
        self.result['data'][:] = [d for d in self.result['data'] if any(p.par_id == d['par_id'] for p in self.pilots)]

    def update_pilot_result(self, p: LiveResult):

        result = next(r for r in self.result['data'] if r['par_id'] == p.par_id)
        if not result['landing_time']:  # should never happen
            print(f"{p.name} updating json result")
            result.update({x: getattr(p, x) for x in LiveTracking.results_list if x in dir(p)})
            result['notifications'] = [n.as_dict() for n in p.notifications]
            result['waypoints_achieved'] = [w.as_dict() for w in p.waypoints_achieved]
            result['suspect_landing_fix'] = None
            if p.suspect_landing_fix and not p.landing_time:
                f = p.suspect_landing_fix
                result['suspect_landing_fix'] = dict(rawtime=f.rawtime, lat=f.lat, lon=f.lon,
                                                     press_alt=f.press_alt, gnss_alt=f.gnss_alt,
                                                     index=f.index)
        print(f"{result}")

    def create_json_file(self):
        try:
            with open(self.filename, 'w') as f:
                f.write(self.json_result)
            return True
        except:
            print(f'Error saving file: {self.filename}')

    def create_json_test(self, json: dict):
        import jsonpickle

        try:
            with open(Path(LIVETRACKDIR, f'{self.task_id}_test.txt'), 'w') as f:
                f.write(jsonpickle.encode(json, unpicklable=False))
            return True
        except:
            print(f'Error saving test file')

    def update_json_test(self):
        import json

        try:
            with open(Path(LIVETRACKDIR, f'{self.task_id}_test.txt'), 'r+') as f:
                d = json.load(f)
                d['timestamp'] = self.now
                d['run'] += 1
                f.seek(0)
                f.write(json.dumps(d))
                f.truncate()
            return True
        except:
            print(f'Error updating test file')

    def task_has_changed(self):
        db_task = LiveTask.read(self.task_id)
        if not self.task.__eq__(db_task):
            '''changed'''
            db_task.pilots = self.task.pilots
            self.task = db_task
            self.task.calculate_task_length()
            self.task.calculate_optimised_task_length()
            return True
        return False

    def create(self):
        """
        LiveTracking Initialization:
        - creates IGC files
        - creates results json file"""

        Logger('ON', 'livetracking.txt')
        '''for testing'''
        print(f' -- LT CREATE --')
        print(f'Window open: {datetime.fromtimestamp(self.opening_timestamp).isoformat()}')
        print(f'Deadline: {datetime.fromtimestamp(self.ending_timestamp).isoformat()}')
        print(f'Livetrack Starting: {datetime.fromtimestamp(self.timestamp).isoformat()}')
        if self.test:
            print(f'Test Starting Timestamp: {datetime.fromtimestamp(self.now).isoformat()}')

        '''create IGC files'''
        for p in self.pilots:
            create_igc_file(p, self.task)
            p.result_type = 'lo'
            # p.saved_to_db = False
            p.suspect_landing_fix = None
        print(f'IGC File created')

        '''create Results JSON file'''
        self.create_result()

        '''recover the gap if LT started after task opening'''
        if self.opening_timestamp < self.now - default_interval < self.ending_timestamp:
            print(f"LT started after task opening by {self.now - self.opening_timestamp} seconds: recovering the gap")
            self.offset = self.now - self.opening_timestamp
            print(f"Time starting recovering: {epoch_to_string(self.now, self.task.time_offset)}")  # Local Time
            while True:
                self.run(interval=default_interval)
                max_time = max(el.last_time or 0 for el in self.flying_pilots)
                max_time_epoch = max_time + self.unix_date
                # if max_time_epoch > self.now + self.offset or self.offset <= 0:
                if self.offset + default_interval <= 0:  # strange I need to add this to get to real time
                    self.offset = 0
                    print(f"Recovered the gap. Starting normal LT mode")
                    break
                print(f"reducing offset")
                self.offset -= default_interval

        print(f'Livetracking JSON File created')
        print(f' -- LT CREATE END --')
        Logger('OFF')

    @staticmethod
    def create_test(task_id: int):
        task = LiveTask.read(task_id)
        test = task.date < datetime.today().date()
        task.get_pilots()
        airspace = AirspaceCheck.from_task(task)
        livetrack = LiveTracking(task, airspace, test)
        livetrack.create_json_test(dict(task_id=task_id,
                                        timestamp=livetrack.now,
                                        init_timestamp=livetrack.init_timestamp,
                                        test=test,
                                        run=0))
        return livetrack

    @staticmethod
    def run_test(task_id: int):
        import requests
        from result import open_json_file

        file = Path(LIVETRACKDIR, f'{task_id}_test.txt')
        if not file.is_file():
            return None

        data = open_json_file(Path(LIVETRACKDIR, f'{task_id}_test.txt'))
        task = LiveTask.read(task_id)
        task.get_pilots()
        test = task.date < datetime.today().date()
        airspace = AirspaceCheck.from_task(task)
        init_timestamp = data.get('init_timestamp')
        run = data.get('run')

        livetrack = LiveTracking(task, airspace, test, init_timestamp)

        ISS_URL = 'http://api.open-notify.org/iss-pass.json'
        lat, lon = 41.6, 9.7
        location = {'lat': lat, 'lon': lon}
        response = requests.get(ISS_URL, params=location).json()

        if 'response' in response:
            next_pass = response['response'][0]['risetime']
            next_pass_datetime = epoch_to_string(next_pass)
            livetrack.update_json_test()
            return next_pass_datetime, run
        else:
            return None

    def run(self, interval: int = default_interval):
        """Incremental background job.
            - reads livetracking json file
            - creates LieTracking Object
            - creates pilots FlightResult Objects according to json results
            - retrieves track fixes from Livetracking server for pilots still flying
            - checks tracks
            - updates results in json file"""

        from frontendUtils import track_result_output
        from result import open_json_file

        '''read results from json file'''
        self.result = open_json_file(self.filename)
        self.init_timestamp = self.result['file_stats'].get('init_timestamp')
        valid_results = []

        self.update_pilots_list()

        if self.properly_set:
            Logger('ON', 'livetracking.txt')
            self.update_result_status()
            print(f"RUN, from read")
            print(f"Flying pilots: {len(self.flying_pilots)}")
            for p in self.flying_pilots:
                d = next(el for el in self.result['data'] if el['par_id'] == p.par_id)
                p.update_from_result(d)
                print(f"RUN, from json")
                print(f"{p.name} (live {p.live_id}: first {p.first_time}, last (next live request time) {p.last_time}, landing {p.landing_time}")

            cycle_starting_time = self.now
            print(f"cycle starting time: {epoch_to_string(self.now, self.task.time_offset)}")  # Local Time
            response = get_livetracks(self.task, self.flying_pilots, cycle_starting_time, interval)
            if not response:
                print(f'{self.now}: -- NO RESPONSE or NO NEW FIXES ...')
            else:
                print(f'{self.now}: -- Associating livetracks ...')
                associate_livetracks(self.task, self.flying_pilots, response, cycle_starting_time)
                print(f'{self.now}: -- Checking tracks ...')

                for p in self.flying_pilots_with_new_fixes:
                    print(f"* {p.name}: getting to live check")
                    check_livetrack(result=p, task=self.task, airspace=self.airspace)
                    print(f"after check_livetrack in run")
                    print(f"{p.name} first_time: {p.first_time}, last_time: {p.last_time}, live comment: {p.live_comment}")
                    if (p.landing_time or p.goal_time) and not p.track_id:
                        '''pilot landed or made goal, save track result'''
                        print(f"{p.name} before track saving: {p.result_type}, live comment: {p.live_comment}")
                        save_livetrack_result(p, self.task, self.airspace)
                        valid_results.append(track_result_output(p, self.task.task_id))
                        print(f"{p.name}: Track saved: track_id: {p.track_id}")
                        print(f"result_type: {p.result_type}, live comment: {p.live_comment}")
                        p.live_comment = 'landed'
                    self.update_pilot_result(p)

                self.create_json_file()
            Logger('OFF')
        return valid_results

    def finalise(self):
        """closes Livetracking service:
        - changes status in json file
        - saves all remaining tracks """
        '''change status'''
        self.update_result_status(finalise=True)

        '''save all tracks for pilots still flying'''
        for p in [el for el in self.pilots if not el.track_id]:
            save_livetrack_result(p, self.task, self.airspace)


def get_livetracks(task: Task, pilots: list, timestamp, interval: int = default_interval):
    """Requests live tracks fixes to Livetracking Server
    Flymaster gives back chunks of 100 fixes for each live_id"""
    import jsonpickle
    import requests
    from Defines import FM_LIVE
    from requests.exceptions import HTTPError

    request = {}
    if task.track_source.lower() == 'flymaster':
        print(f'pilots to get: {len(pilots)}')
        for p in pilots:
            live = int(p.live_id)
            '''get epoch time'''
            if not p.first_time:
                '''pilot not launched yet'''
                last_time = timestamp - interval
            else:
                last_time = int(time.mktime(task.date.timetuple()) + (p.last_time or task.window_open_time))
            request[live] = last_time
        url = FM_LIVE + str(jsonpickle.encode(request))
        if request:
            try:
                response = requests.get(url)
                response.raise_for_status()
                return response.json()
            except HTTPError as http_err:
                print(f'HTTP error trying to get tracks: {http_err}')
            except Exception as err:
                print(f'Error trying to get tracks: {err}')


def associate_livetracks(task: LiveTask, pilots: list, response, timestamp):
    """ Flymaster Livetracking fix info:
        dict
        d  - timestamp, epoc
        v  - speed, km/h
        c  - baro alt, m
        h  - gnss alt, m
        s  - ground alt, m
        ai - lat, deg * 60000
        oi - lon, deg * 60000 """
    import time

    '''initialise'''
    midnight = int(time.mktime(task.date.timetuple()))
    alt_source = 'GPS' if task.formula.scoring_altitude is None else task.formula.scoring_altitude
    alt_compensation = 0 if alt_source == 'GPS' or task.QNH == 1013.25 else task.alt_compensation
    for live_id, fixes in response.items():
        pil = next((p for p in pilots if p.live_id == live_id), None)
        if not pil:
            continue
        if len(fixes) < config.min_fixes:
            '''livetrack segment too short'''
            pil.livetrack = []
            continue
        if pil.landing_time:
            '''already landed'''
            # shouldn't happen as landed pilots are filtered in tracks request
            continue
        if not pil.first_time and not pilot_is_airborne(fixes):
            '''did not take off yet'''
            # print(f"{pil.name}: first_time {pil.first_time} - did not took off yet")
            pil.last_time = int(fixes[-1]['d']) - midnight
            pil.live_comment = 'not flying'
            pil.livetrack = []
            continue
        flight = []
        # print(f"{pil.name}: first_time {pil.first_time} - adding fixes to pilot object")
        # print(f"Fixes to add: {len(fixes)}")
        for idx, el in enumerate(fixes):
            t = int(el['d']) - midnight
            s = int(el['v'])
            baro_alt = int(el['c'])
            gnss_alt = int(el['h'])
            alt = gnss_alt if alt_source == 'GPS' else baro_alt + alt_compensation
            ground = int(el['s'])
            height = abs(alt - ground)
            if pil.last_time and t < pil.last_time:
                '''fix behind last scored fix'''
                continue
            if t > timestamp - midnight:
                '''fix ahead of cycle time'''
                break
            lat = int(el['ai']) / 60000
            lon = int(el['oi']) / 60000
            flight.append(LiveFix(t, lat, lon, baro_alt, gnss_alt, alt, height, s, idx))
        pil.livetrack = flight
        print(f"{pil.name}: livetrack fixes: {len(pil.livetrack)}")
        if pil.livetrack:
            print(f"{pil.name}: updating livetrack file")
            update_livetrack_file(pil, flight, task.file_path)


def check_livetrack(result: LiveResult, task: LiveTask, airspace: AirspaceCheck = None):
    """Checks a list of LiveFix objects against the task, having previous result.
    Args:
           result:   a LiveResult object
           task:     a LiveTask object
           airspace: a AirspaceCheck object
    """
    from flightcheck import flightcheck
    from flightcheck.flightpointer import FlightPointer
    from formulas.libs.leadcoeff import LeadCoeff

    '''initialize'''
    fixes = result.livetrack

    '''Turnpoint managing'''
    tp = FlightPointer(task)
    tp.pointer = result.waypoints_made + 1

    '''leadout coefficient'''
    if task.formula.formula_departure == 'leadout':
        lead_coeff = LeadCoeff(task)
        # print(f"{result.name} - cycle init Lead Coeff: {lead_coeff.summing}, fixed LC: {result.fixed_LC}")
        if tp.start_done:
            lead_coeff.best_dist_to_ess = [lead_coeff.opt_dist_to_ess - result.distance_flown / 1000]
    else:
        lead_coeff = None

    '''Airspace check managing'''
    if task.airspace_check:
        if task.airspace_check and not airspace:
            print(f'We should not create airspace here')
            airspace = AirspaceCheck.from_task(task)
    real_start_time, already_ess, previous_achieved = result.real_start_time, result.ESS_time, result.waypoints_achieved
    flightcheck.check_fixes(result, fixes, task, tp, lead_coeff, airspace, livetracking=True, igc_parsing_config=config)
    # print(f"check_livetrack")
    # print(f"{result.name}: first {result.first_time}, last {result.last_time}, last fix = {fixes[-1].rawtime}")

    calculate_incremental_results(
        result, task, tp, lead_coeff, airspace, real_start_time, already_ess, previous_achieved
    )
    # print(f"after incremental: first {result.first_time}, last {result.last_time}, last fix = {fixes[-1].rawtime}")


def get_live_json(task_id):
    import jsonpickle
    from Defines import LIVETRACKDIR

    fullname = Path(LIVETRACKDIR, str(task_id))
    try:
        with open(fullname, 'r') as f:
            result = jsonpickle.decode(f.read())
    except (FileNotFoundError, Exception):
        print(f"Error reading file")
        file_stats = dict(timestamp=int(time.time()), status='Live Not Set Yet')
        headers = {}
        data = []
        info = {}
        result = dict(file_stats=file_stats, headers=headers, data=data, info=info)
    return result


def clear_notifications(task, result):
    """ check Notifications, and keeps only the relevant ones"""
    jtg = task.formula.max_JTG not in [None, 0]
    notifications = []
    if jtg and any(n for n in result.notifications if n.notification_type == 'jtg'):
        if result.real_start_time < task.start_time:
            notifications.append(
                min([n for n in result.notifications if n.notification_type == 'jtg'], key=lambda x: x.flat_penalty)
            )
    if any(n for n in result.notifications if n.notification_type == 'auto' and n.percentage_penalty > 0):
        notifications.append(
            max(
                [n for n in result.notifications if n.notification_type == 'auto' and n.percentage_penalty > 0],
                key=lambda x: x.percentage_penalty,
            )
        )
    return notifications


def evaluate_infringements(result: LiveResult, notifications: list):
    """ check Notifications, and keeps only the relevant ones"""
    if len(notifications) > 0:
        notifications.extend([n for n in result.notifications if n.notification_type == 'auto'])
        result.notifications = [n for n in result.notifications if not n.notification_type == 'auto']
        result.notifications.append(max(notifications, key=lambda x: x.percentage_penalty))


def update_livetrack_file(result: LiveResult, flight: list, path: str):
    """IGC Fix Format:
    B1132494613837N01248410EA0006900991
    """

    file = Path(path, result.track_file)
    if file.is_file():
        '''create fixes lines'''
        lines = ''
        for fix in flight:
            fixtime = sec_to_time(fix.rawtime).strftime("%H%M%S")
            lat, lon = igc_coords(fix.lat, fix.lon)
            baro_alt = str(int(fix.press_alt)).zfill(5)
            gnss_alt = str(int(fix.gnss_alt)).zfill(5)
            lines += f"B{fixtime}{lat}{lon}A{baro_alt}{gnss_alt}\n"
        '''append lines'''
        f = open(file, "a+")
        f.write(lines)
        f.close()


def create_igc_file(result: FlightResult, task: Task):
    """Flymaster IGC initialize format:

    AXFMSFP Flymaster Live, V1.0, S/N 618839
    HFFXA010
    HFPLTPILOT:Alessandro Ploner
    HFGTYGLIDERTYPE:
    HFGIDGLIDERID:
    HFDTM100GPSDATUM:WGS-1984
    HFCIDCOMPETITIONID:72
    HFCCLCOMPETITIONCLASS:
    HOSITSITE:Meduno - Monte Valinis-IT
    HFGPS:UBLOXNEO6
    HFPRSPRESSALTSENSOR:NA
    HFRFWFIRMWAREVERSION:202g
    HFRHWHARDWAREVERSION:1.0R2
    HFFTYFRTYPE:FLYMASTER,LIVE
    HFDTE150719
    B1132494613837N01248410EA0006900991
    B1132504613834N01248408EA0006900990
    """
    if result.track_file and Path(task.file_path, result.track_file).is_file():
        print(f"File already exists")
        return

    """check if directory already exists"""
    if not Path(task.file_path).is_dir():
        Path(task.file_path).mkdir(mode=0o755)
    '''create filename'''
    file = create_igc_filename(task.file_path, task.date, result.name, result.ID)
    result.track_file = file.name

    '''create IGC header'''
    name = result.name
    glider = result.glider
    ID = result.ID
    site = task.turnpoints[0].description
    date = task.date.strftime("%d%m%y")
    header = f"AXFMSFP Flymaster Live, V1.0\n"
    header += f"HFFXA010\n"
    header += f"HFPLTPILOT:{name}\n"
    header += f"HFGTYGLIDERTYPE:{glider}\n"
    header += f"HFGIDGLIDERID:\n"
    header += f"HFDTM100GPSDATUM:WGS-1984\n"
    header += f"HFCIDCOMPETITIONID:{ID}\n"
    header += f"HFCCLCOMPETITIONCLASS:\n"
    header += f"HOSITSITE:{site}\n"
    header += f"HFGPS:UBLOXNEO6\n"
    header += f"HFPRSPRESSALTSENSOR:NA\n"
    header += f"HFRFWFIRMWAREVERSION:202g\n"
    header += f"HFRHWHARDWAREVERSION:1.0R2\n"
    header += f"HFFTYFRTYPE:FLYMASTER,LIVE\n"
    header += f"HFDTE{date}\n"

    '''create file'''
    f = open(file, "w+")
    f.write(header)
    f.close()


def reset_igc_file(result: FlightResult, task: Task):
    """deletes all fixes from a track file, keeping only headers"""
    file = Path(task.file_path, result.track_file)
    if file.exists():
        with open(file, "r+") as f:
            lines = []
            idx = 0
            for line in f:
                if idx < 15:
                    lines.append(line)
                    idx += 1
        with open(file, "w") as f:
            for line in lines:
                f.write(line)


def calculate_incremental_results(
    result: LiveResult, task: LiveTask, tp, lead_coeff, airspace, real_start_time, already_ess, previous_achieved
):
    """Incremental result update function"""
    from flightcheck import flightcheck

    if tp.start_done and not real_start_time == result.real_start_time:
        '''pilot has started or restarted'''
        result.notifications = [n for n in result.notifications if not n.notification_type == 'jtg']
        flightcheck.evaluate_start(result, task, tp)
    if tp.ess_done and not already_ess:
        '''pilot made ESS'''
        flightcheck.evaluate_ess(result, task)
    if tp.made_all:
        '''pilot made goal'''
        flightcheck.evaluate_goal(result, task)
        result.live_comment = 'goal'

    if len(result.waypoints_achieved) > len(previous_achieved):
        result.best_waypoint_achieved = str(result.waypoints_achieved[-1].name) if result.waypoints_achieved else None

    if lead_coeff:
        try:
            result.fixed_LC += lead_coeff.summing
        except (TypeError, Exception):
            result.fixed_LC = lead_coeff.summing

        # print(f"{result.name} - cycle end Lead Coeff: {lead_coeff.summing}, fixed LC: {result.fixed_LC}")

    if task.airspace_check:
        _, notifications, penalty = airspace.get_infringements_result(result.infringements)
        evaluate_infringements(result, notifications)


def save_livetrack_result(p: LiveResult, task: LiveTask, airspace: AirspaceCheck = None):
    from pilot.track import Track
    from pilot.flightresult import save_track

    flight = Track.process(Path(task.file_path, p.track_file), task, config=config)
    if flight and flight.valid:
        print(f"flight valid. Livetracking LC: {p.fixed_LC} distance: {p.distance_flown} time: {p.ss_time}")
        p.check_flight(flight, task, airspace)
        # print(f"Calculated LC: {test.fixed_LC} distance: {test.distance_flown} time: {test.ss_time}")
        # print(f"Difference %: {(test.fixed_LC - p.fixed_LC) / p.fixed_LC * 100}")
        save_track(p, task.id)
        p.save_tracklog_map_file(task, flight)
    else:
        print(f"{p.track_file} is not a valid igc. Result not saved.")


def get_task_results(task_id: int) -> list:
    from db.tables import TblTaskResult as R

    pilots = [R.populate(p, LiveResult()) for p in R.get_task_results(task_id) if p.result_type not in ('abs', 'dnf')]
    for pilot in pilots:
        if not pilot.result_type:
            '''initialise'''
            pilot.result_type = 'nyp'
            pilot.fixed_LC = 0
            pilot.distance_flown = 0
            pilot.total_distance = 0
            pilot.max_altitude = 0

    return pilots
    # return [next(el for el in pilots if el.ID == 188)]


def pilot_is_airborne(fixes: list) -> bool:
    """ 3 fixes with speed higher than min flying speed"""
    # print(f"fixes with flying speed over {config.min_gsp_flight} (pilot_is_airborne {sum(int(fix['v']) > config.min_gsp_flight for fix in fixes) > 3}): {sum(int(fix['v']) > config.min_gsp_flight for fix in fixes)}")
    return sum(int(fix['v']) > config.min_gsp_flight for fix in fixes) > 3


def possibly_landed(fixes: list) -> bool:
    start = 0
    alt = 0
    valid = 0
    for idx, fix in enumerate(fixes):
        t = fix['d'] if isinstance(fix, dict) else fix.rawtime
        s = int(fix['v']) if isinstance(fix, dict) else fix.speed
        h = int(fix['h']) if isinstance(fix, dict) else fix.height
        if (s < config.min_gsp_flight and abs(h - alt) < config.min_alt_difference) or s > config.max_flight_speed:
            if start:
                if t - start > config.max_still_seconds:
                    return True
            else:
                start = t
                alt = h
        else:
            if start:
                valid += 1
                if valid >= 2:
                    valid = 0
                    start = 0
    return False
