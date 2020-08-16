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
from task import Task
from airspace import AirspaceCheck
import time
from datetime import datetime
from logger import Logger
from pathlib import Path
from pilot.flightresult import FlightResult
from pilot.track import igc_parsing_config_from_yaml, create_igc_filename

'''parameters for livetracking'''
config = igc_parsing_config_from_yaml('smartphone')
config.max_flight_speed = 250  # Km/k
config.max_still_seconds = 60  # max consecutive seconds under min speed not to be considered landed
config.min_alt_difference = 50  # meters min altitude difference not to be considered landed
config.min_fixes = 5  # min number of fixes to be considered a valid livetrack chunk


class LiveTracking(object):
    results_list = ['par_id',
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
                    'turnpoints_made',
                    'height',
                    'live_comment',
                    'pil_id']

    def __init__(self, task=None, airspace=None, test=False):
        self.task = task  # Task object
        self.airspace = airspace  # AirspaceCheck object
        self.test = test  # bool, test mode, using stored informations about events in the past
        self.start_timestamp = int(time.time())
        self.result = {}  # result string

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
    def flying_pilots(self):
        return [p for p in self.pilots if not (p.landing_time or p.goal_time)]

    @property
    def track_source(self):
        return None if not self.task else self.task.track_source

    @property
    def properly_set(self):
        # print(f"task: {bool(self.task is not None)}, pilots: {bool(self.pilots)}, track_source: {bool(self.track_source)}, wpt: {bool(self.task.turnpoints)}, start: {bool(self.task.start_time is not None)}")
        return ((self.task is not None) and self.pilots and self.track_source and self.task.turnpoints
                and (self.task.start_time is not None))

    @property
    def unix_date(self):
        return 0 if not self.task else int(time.mktime(self.task.date.timetuple()))

    @property
    def opening_timestamp(self):
        return 0 if not self.task else self.task.window_open_time + self.unix_date

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
        return self.start_timestamp - self.opening_timestamp if self.test else 0

    @property
    def now(self):
        return self.timestamp - self.test_offset

    @property
    def status(self):
        if self.task.cancelled:
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
            return 'Task is set'

    @property
    def headers(self):
        from calcUtils import sec_to_string
        main = ''
        details = ''
        warning = ''
        if self.task.cancelled:
            '''task has been cancelled'''
            main = f"Task has been cancelled."
        elif not (self.task and self.task.turnpoints):
            main = "Today's Task is not yet defined. Try Later."
        elif not self.properly_set:
            main = "Livetracking source is not set properly."
        else:
            task_type = 'Race to Goal' if self.task.task_type.lower() == 'race' else self.task.task_type
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
        return dict(main=main, warning=warning, details=details)

    @property
    def pilots(self):
        return [] if not self.task else [p for p in self.task.pilots
                                         if p.live_id and p.result_type not in ('dnf', 'abs')]

    @property
    def filename(self):
        from Defines import LIVETRACKDIR
        from os import path
        return None if not self.task else path.join(LIVETRACKDIR, str(self.task_id))

    @staticmethod
    def read(task_id):
        task = Task.read(task_id)
        if task.turnpoints:
            if not task.distance:
                task.calculate_task_length()
            if not task.optimised_turnpoints:
                task.calculate_optimised_task_length()
        test = task.date < datetime.today().date()
        task.get_pilots()
        airspace = AirspaceCheck.from_task(task)
        livetrack = LiveTracking(task, airspace, test)
        for p in livetrack.pilots:
            create_igc_file(p, task)
            p.result_type = 'lo'
            # p.saved_to_db = False
            p.suspect_landing_fix = None
        livetrack.create_result()
        return livetrack

    def create_result(self):
        from result import TaskResult
        file_stats = dict(timestamp=self.now, status=self.status)
        headers = self.headers
        info = {x: getattr(self.task, x) for x in TaskResult.info_list if x in dir(self.task)}
        data = []
        route = []
        if not self.task:
            file_stats['status'] = 'Task is not set yet'
        elif self.task.cancelled:
            file_stats['status'] = 'Cancelled'
        else:
            # info = {x: getattr(self.task, x) for x in TaskResult.info_list if x in dir(self.task)}
            if not self.task.turnpoints:
                file_stats['status'] = 'Task is not set yet'
            elif not (self.track_source and self.pilots):
                file_stats['status'] = 'Livetracking source is not set properly.'
            else:
                if not self.task.start_time:
                    file_stats['status'] = 'Task Start time is not set yet'
                elif self.task.stopped_time:
                    file_stats['status'] = 'Stopped'
                else:
                    file_stats['status'] = 'Task Set'
                for idx, tp in enumerate(self.task.turnpoints):
                    wpt = {x: getattr(tp, x) for x in TaskResult.route_list if x in dir(tp)}
                    wpt['cumulative_dist'] = self.task.partial_distance[idx]
                    route.append(wpt)
                for p in self.pilots:
                    result = {x: getattr(p, x) for x in LiveTracking.results_list if x in dir(p)}
                    result['notifications'] = [n.__dict__ for n in p.notifications]
                    data.append(result)
        self.result.update(dict(file_stats=file_stats, headers=headers, info=info, route=route, data=data))
        self.create_json_file()

    def update_result(self):
        from result import TaskResult
        self.result['file_stats']['timestamp'] = self.now
        '''check if status changed'''
        status = self.result['file_stats']['status']
        if not status == self.status:
            self.result['file_stats']['status'] = self.status
            self.result['headers'] = self.headers
            self.result['info'] = {x: getattr(self.task, x) for x in TaskResult.info_list if x in dir(self.task)}
        else:
            for p in self.pilots:
                result = next(r for r in self.result['data'] if r['par_id'] == p.par_id)
                result.update({x: getattr(p, x) for x in LiveTracking.results_list if x in dir(p)})
                result['notifications'] = [n.__dict__ for n in p.notifications]
        self.create_json_file()

    def create_json_file(self):
        try:
            with open(self.filename, 'w') as f:
                f.write(self.json_result)
            return True
        except:
            print(f'Error saving file: {self.filename}')

    def task_has_changed(self):
        db_task = Task.read(self.task_id)
        if not self.task.__eq__(db_task):
            '''changed'''
            db_task.pilots = self.task.pilots
            self.task = db_task
            self.task.calculate_task_length()
            self.task.calculate_optimised_task_length()
            return True
        return False

    def run(self, interval=99):
        if not self.properly_set:
            print(f'Livetracking source is not set properly.')
            return
        Logger('ON', 'livetracking.txt')
        i = 0
        response = {}
        print(f'Window open: {datetime.fromtimestamp(self.opening_timestamp).isoformat()}')
        print(f'Deadline: {datetime.fromtimestamp(self.ending_timestamp).isoformat()}')
        print(f'Livetrack Starting: {datetime.fromtimestamp(self.timestamp).isoformat()}')
        if self.test:
            print(f'Test Starting Timestamp: {datetime.fromtimestamp(self.now).isoformat()}')
        if self.opening_timestamp - interval > self.now:
            '''wait window opening'''
            print(f'Waiting for window opening: {self.opening_timestamp - interval - self.now} seconds ...')
            time.sleep(self.opening_timestamp - interval - self.now)
        while self.opening_timestamp - interval <= self.now <= self.ending_timestamp + interval:
            '''check task did not change'''
            if self.task_has_changed():
                print(f'*** *** Cycle {i} ({self.timestamp}): TASK HAS CHANGED ***')
                self.update_result()
                if not self.properly_set:
                    print(f'* Task not properly set.')
                    print(f'* Livetrack Stopping: {datetime.fromtimestamp(self.timestamp).isoformat()}')
                    break
                elif self.task.cancelled:
                    print(f'* Task Cancelled.')
                    print(f'* Livetrack Stopping: {datetime.fromtimestamp(self.timestamp).isoformat()}')
                    break
                elif self.opening_timestamp > self.now - interval:
                    time.sleep(self.opening_timestamp - (self.now - interval))
            '''get livetracks from flymaster live server'''
            print(f'*** Cycle {i} ({self.timestamp}):')
            print(f' -- Getting livetracks ...')
            cycle_starting_time = self.now
            previous = response
            response = get_livetracks(self.task, self.flying_pilots, cycle_starting_time, interval)
            if not response or response == previous:
                print(f' -- NO RESPONSE or NO NEW FIXES ...')
            else:
                print(f' -- Associating livetracks ...')
                associate_livetracks(self.task, self.flying_pilots, response, cycle_starting_time)
            for p in self.flying_pilots:
                if (hasattr(p, 'livetrack')
                        and len(p.livetrack) > config.min_fixes
                        and p.livetrack[-1].rawtime > (p.last_time or 0)):
                    check_livetrack(result=p, task=self.task, airspace=self.airspace)
                    if (p.landing_time or p.goal_time) and not p.track_id:
                        '''pilot landed or made goal, save track result'''
                        save_livetrack_result(p, self.task, self.airspace)
                        print(f"result saved: track_id: {p.track_id}")
            self.update_result()
            i += 1
            time.sleep(max(interval / 2 - (self.now - cycle_starting_time), 0))
            # t = self.timestamp
        print(f'Livetrack Ending: {datetime.fromtimestamp(self.timestamp).isoformat()}')
        print(f'Saving results...')
        for p in [el for el in self.pilots if not el.track_id]:
            save_livetrack_result(p, self.task, self.airspace)

        Logger('OFF')
        print(f'Livetrack Ending: {datetime.fromtimestamp(self.timestamp).isoformat()}')


def get_livetracks(task: Task, pilots: list, timestamp, interval):
    """ Requests live tracks fixes to Livetracking Server
        Flymaster gives back chunks of 100 fixes for each live_id """
    import requests
    import jsonpickle
    from requests.exceptions import HTTPError
    from Defines import FM_LIVE
    request = {}
    if task.track_source.lower() == 'flymaster':
        # pilots = [p for p in task.pilots
        #           if p.live_id and not (p.landing_time or p.goal_time or p.result_type in ('dnf', 'abs'))]
        print(f'pilots to get: {len(pilots)}')
        # url = 'https://lt.flymaster.net/wlb/getLiveData.php?trackers='
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
                # print(response.json()['629878'][0])
                return response.json()
            except HTTPError as http_err:
                print(f'HTTP error trying to get tracks: {http_err}')
            except Exception as err:
                print(f'Error trying to get tracks: {err}')


def associate_livetracks(task: Task, pilots: list, response, timestamp):
    from igc_lib import GNSSFix
    import time
    '''initialise'''
    midnight = int(time.mktime(task.date.timetuple()))
    alt_source = 'GPS' if task.formula.scoring_altitude is None else task.formula.scoring_altitude
    alt_compensation = 0 if alt_source == 'GPS' or task.QNH == 1013.25 else task.alt_compensation
    for live_id, fixes in response.items():
        pil = next((p for p in pilots if p.live_id == live_id), None)
        if not pil:
            continue
        # res = pil.result
        if len(fixes) < config.min_fixes:
            '''livetrack segment too short'''
            pil.livetrack = []
            continue
        if pil.landing_time:
            '''already landed'''
            # shouldn't happen as landed pilots are filtered in tracks request
            continue
        if not any(el for el in fixes if int(el['v']) > config.min_gsp_flight):
            '''not flying'''
            pil.last_time = int(fixes[-1]['d']) - midnight
            pil.live_comment = 'not flying'
            pil.livetrack = []
            continue
        flight = []
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
            fix = GNSSFix(t, lat, lon, 'A', baro_alt, gnss_alt, idx, '')
            fix.alt = alt
            fix.height = height
            fix.speed = s
            flight.append(fix)
        pil.livetrack = flight
        update_livetrack_file(pil, flight, task.file_path)


def simulate_livetracking(task_id):
    print(f'*** Getting Task {task_id}:')
    LT = LiveTracking.read(task_id)
    LT.run()


def check_livetrack(result: FlightResult, task: Task, airspace: AirspaceCheck = None):
    """ Checks a Flight object against the task.
        Args:
               result:   a FlightResult object
               task:     a Task object
               airspace: a AirspaceCheck object
        Returns:
                a list of GNSSFixes of when turnpoints were achieved.
    """
    from flightcheck.flightpointer import FlightPointer
    from flightcheck import flightcheck
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

    calculate_incremental_results(result, task, tp, lead_coeff, airspace,
                                  real_start_time, already_ess, previous_achieved)


def get_live_json(task_id):
    from Defines import LIVETRACKDIR
    from os import path
    import jsonpickle
    fullname = path.join(LIVETRACKDIR, str(task_id))
    try:
        with open(fullname, 'r') as f:
            result = jsonpickle.decode(f.read())
    except:
        print(f"Error reading file")
        file_stats = dict(timestamp=int(time.time()), status='Live Not Set Yet')
        headers = {}
        data = []
        info = {}
        result = dict(file_stats=file_stats, headers=headers, data=data, info=info)
    return result


def clear_notifications(task, result):
    """ check Notifications, and keeps only the relevant ones"""
    jtg = not (task.formula.max_JTG in [None, 0])
    notifications = []
    if jtg and any(n for n in result.notifications if n.notification_type == 'jtg'):
        if result.real_start_time < task.start_time:
            notifications.append(min([n for n in result.notifications if n.notification_type == 'jtg'],
                                     key=lambda x: x.flat_penalty))
    if any(n for n in result.notifications if n.notification_type == 'airspace' and n.percentage_penalty > 0):
        notifications.append(max([n for n in result.notifications if n.notification_type == 'airspace'
                                  and n.percentage_penalty > 0], key=lambda x: x.percentage_penalty))
    return notifications


def update_livetrack_file(result: FlightResult, flight: list, path: str):
    """ IGC Fix Format:
        B1132494613837N01248410EA0006900991
    """
    from calcUtils import sec_to_time, igc_coords
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
    """ Flymaster IGC initialize format:

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
    file = create_igc_filename(task.file_path, task.date, result.name)
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


def create_map_files(pilots: list, task: Task):
    from igc_lib import Flight
    for pilot in pilots:
        if pilot.result_type not in ('abs', 'dnf', 'mindist'):
            print(f"{pilot.ID}. {pilot.name}: ({pilot.track_file})")
            filename = Path(task.file_path, pilot.track_file)
            '''load track file'''
            flight = Flight.create_from_file(filename)
            if flight:
                '''create map file'''
                pilot.save_tracklog_map_file(task, flight)


def calculate_incremental_results(result: FlightResult, task: Task, tp, lead_coeff, airspace,
                                  real_start_time, already_ess, previous_achieved):
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

    if len(result.waypoints_achieved) > len(previous_achieved):
        result.best_waypoint_achieved = str(result.waypoints_achieved[-1].name) if result.waypoints_achieved else None

    if lead_coeff:
        result.fixed_LC += lead_coeff.summing
        # print(f"{result.name} - cycle end Lead Coeff: {lead_coeff.summing}, fixed LC: {result.fixed_LC}")

    if task.airspace_check:
        _, notifications, penalty = airspace.get_infringements_result(result.infringements)
        # result.infringements.extend([el for el in infringements if el not in result.infringements])
        result.notifications = [el for el in result.notifications if not el.notification_type == 'airspace']
        result.notifications.extend(notifications)


def save_livetrack_result(p: FlightResult, task: Task, airspace: AirspaceCheck = None):
    from igc_lib import Flight
    from pilot.flightresult import save_track
    try:
        flight = Flight.create_from_file(Path(task.file_path, p.track_file))
        if flight.valid:
            print(f"flight valid. Livetracking LC: {p.fixed_LC} distance: {p.distance_flown} time: {p.ss_time}")
            # test = FlightResult()
            # test.check_flight(flight, task, airspace)
            # print(f"Calculated LC: {test.fixed_LC} distance: {test.distance_flown} time: {test.ss_time}")
            # print(f"Difference %: {(test.fixed_LC - p.fixed_LC) / p.fixed_LC * 100}")
            save_track(p, task.id)
            p.save_tracklog_map_file(task, flight)
        else:
            print(f"{p.track_file} is not a valid igc. Result not saved.")
    except:
        print(f"{p.track_file} Error trying to save result.")

