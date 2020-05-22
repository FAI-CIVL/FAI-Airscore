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
from igc_lib import FlightParsingConfig


'''parameters for livetracking'''
min_flight_speed = FlightParsingConfig.min_gsp_flight   # km/h
max_flight_speed = 250  # Km/k
max_still_seconds = 30  # max consecutive seconds under min speed not to be considered landed
min_alt_difference = 15   # meters min altitude difference not to be considered landed
min_fixes = 5  # min number of fixes to be considered a valid livetrack chunk
max_alt_rate = FlightParsingConfig.max_alt_change_rate  # max altitude change rate not to be considered wrong fix
max_alt = FlightParsingConfig.max_alt
min_alt = FlightParsingConfig.min_alt


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
    def track_source(self):
        return None if not self.task else self.task.track_source

    @property
    def properly_set(self):
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
        return [] if not self.task.pilots else [p for p in self.task.pilots if p.info.live_id]

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
        livetrack.create_result()
        return livetrack

    def create_result(self):
        from result import TaskResult
        file_stats = dict(timestamp=self.now, status=self.status)
        headers = self.headers
        info = {x: getattr(self.task, x) for x in TaskResult.info_list if x in dir(self.task)}
        data = []
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
                for p in self.pilots:
                    result = dict()
                    result.update({x: getattr(p.info, x) for x in LiveTracking.results_list if x in dir(p.info)})
                    result.update({x: getattr(p.result, x) for x in LiveTracking.results_list if x in dir(p.result)})
                    result['notifications'] = [n.__dict__ for n in p.notifications]
                    data.append(result)
        self.result.update(dict(file_stats=file_stats, headers=headers, info=info, data=data))
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
                result = next(r for r in self.result['data'] if r['par_id'] == p.info.par_id)
                result.update({x: getattr(p.result, x) for x in LiveTracking.results_list if x in dir(p.result)})
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
            response = get_livetracks(self.task, cycle_starting_time, interval)
            if not response or response == previous:
                print(f' -- NO RESPONSE or NO NEW FIXES ...')
            else:
                print(f' -- Associating livetracks ...')
            associate_livetracks(self.task, response, cycle_starting_time)
            for p in self.pilots:
                if (p.livetrack and len(p.livetrack) > min_fixes and p.livetrack[-1].rawtime > (p.result.last_time or 0)
                        and not p.result.goal_time and not p.result.landing_time):
                    check_livetrack(pilot=p, task=self.task, airspace_obj=self.airspace)
            self.update_result()
            i += 1
            time.sleep(max(interval / 2 - (self.now - cycle_starting_time), 0))
            # t = self.timestamp
        print(f'Livetrack Ending: {datetime.fromtimestamp(self.timestamp).isoformat()}')
        Logger('OFF')
        print(f'Livetrack Ending: {datetime.fromtimestamp(self.timestamp).isoformat()}')


def get_livetracks(task, timestamp, interval):
    """ Requests live tracks fixes to Livetracking Server
        Flymaster gives back chunks of 100 fixes for each live_id """
    import requests
    import jsonpickle
    from requests.exceptions import HTTPError
    from Defines import FM_LIVE
    request = {}
    if task.track_source.lower() == 'flymaster':
        pilots = [p for p in task.pilots if p.info.live_id and not (p.result.landing_time or p.result.goal_time)]
        print(f'pilots to get: {len(pilots)}')
        # url = 'https://lt.flymaster.net/wlb/getLiveData.php?trackers='
        for p in pilots:
            live = int(p.info.live_id)
            '''get epoch time'''
            if not p.result.first_time:
                '''pilot not launched yet'''
                last_time = timestamp - interval
            else:
                last_time = int(time.mktime(task.date.timetuple()) + (p.result.last_time or task.window_open_time))
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


def associate_livetracks(task, response, timestamp):
    from igc_lib import GNSSFix
    import time
    from calcUtils import altitude_compensation
    '''initialise'''
    midnight = int(time.mktime(task.date.timetuple()))
    alt_source = 'GPS' if task.formula.scoring_altitude is None else task.formula.scoring_altitude
    alt_compensation = 0 if alt_source == 'GPS' or task.QNH == 1013.25 else altitude_compensation(task.QNH)
    for live_id, fixes in response.items():
        pil = next(p for p in task.pilots if p.info.live_id == live_id)
        if not pil:
            continue
        # res = pil.result
        if len(fixes) < min_fixes:
            '''livetrack segment too short'''
            pil.livetrack = []
            continue
        if pil.result.landing_time:
            '''already landed'''
            # shouldn't happen as landed pilots are filtered in tracks request
            continue
        if not any(el for el in fixes if int(el['v']) > min_flight_speed):
            '''not flying'''
            pil.result.last_time = int(fixes[-1]['d']) - midnight
            pil.result.live_comment = 'not flying'
            pil.livetrack = []
            continue
        flight = []
        # slow = 0
        # slow_alt = 0
        # slow_rawtime = 0
        for idx, el in enumerate(fixes):
            t = int(el['d']) - midnight
            s = int(el['v'])
            baro_alt = int(el['c'])
            gnss_alt = int(el['h'])
            alt = gnss_alt if alt_source == 'GPS' else baro_alt + alt_compensation
            ground = int(el['s'])
            height = abs(alt - ground)
            if pil.result.last_time and t < pil.result.last_time:
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


def simulate_livetracking(task_id):
    print(f'*** Getting Task {task_id}:')
    LT = LiveTracking.read(task_id)
    LT.run()


def check_livetrack(pilot, task, airspace_obj=None):
    """ Checks a Flight object against the task.
        Args:
               pilot:  a Pilot object
               task:    a Task object
               airspace_obj: a AirspaceCheck object
        Returns:
                a list of GNSSFixes of when turnpoints were achieved.
    """
    from flightresult import Tp, pilot_can_start, pilot_can_restart, start_number_at_time
    from route import in_semicircle, start_made_civl, tp_made_civl, distance, \
        tp_time_civl, get_shortest_path, distance_flown
    from airspace import AirspaceCheck
    from formulas.libs.leadcoeff import LeadCoeff
    from notification import Notification

    '''initialize'''
    tolerance = task.formula.tolerance or 0
    min_tol_m = task.formula.min_tolerance or 0
    max_jump_the_gun = task.formula.max_JTG or 0  # seconds
    jtg_penalty_per_sec = 0 if max_jump_the_gun == 0 else task.formula.JTG_penalty_per_sec

    # if not task.optimised_turnpoints:
    #     task.calculate_optimised_task_length()
    distances2go = task.distances_to_go  # Total task Opt. Distance, in legs list

    result = pilot.result
    fixes = pilot.livetrack

    '''leadout coefficient'''
    if task.formula.formula_departure == 'leadout':
        lead_coeff = LeadCoeff(task)
        lead_coeff.summing = result.fixed_LC or 0.0
    else:
        lead_coeff = None

    '''Turnpoint managing'''
    tp = Tp(task)
    tp.pointer = result.waypoints_made + 1
    '''get if pilot already started in previous track slices'''
    already_started = tp.start_done
    restarted = False
    '''get if pilot already made ESS in previous track slices'''
    already_ESS = any(e[0] == 'ESS' for e in result.waypoints_achieved)

    '''Airspace check managing'''
    infringements_list = []
    if task.airspace_check:
        if task.airspace_check and not airspace_obj:
            print(f'We should not create airspace here')
            airspace_obj = AirspaceCheck.from_task(task)

    alt = 0
    suspect_landing_fix = None
    next_fix = None

    for i in range(len(fixes) - 1):
        '''Get two consecutive trackpoints as needed to use FAI / CIVL rules logic
        '''
        # start_time = tt.time()
        my_fix = fixes[i]
        next_fix = fixes[i + 1]
        result.last_time = next_fix.rawtime
        alt = next_fix.alt

        '''check coherence'''
        if next_fix.rawtime - my_fix.rawtime < 1:
            continue
        alt_rate = abs(next_fix.alt - my_fix.alt)/(next_fix.rawtime - my_fix.rawtime)
        if alt_rate > max_alt_rate or not (min_alt < alt < max_alt):
            continue

        '''check flying'''
        speed = next_fix.speed  # km/h
        if not result.first_time:
            '''not launched yet'''
            launch = next(x for x in tp.turnpoints if x.type == 'launch')
            if distance(next_fix, launch) < 400:
                '''still on launch'''
                continue
            if abs(launch.altitude - alt) > min_alt_difference and speed > min_flight_speed:
                '''pilot launched'''
                result.first_time = next_fix.rawtime
                result.live_comment = 'flying'
        else:
            '''check if pilot landed'''
            if speed < min_flight_speed:
                if not suspect_landing_fix:
                    suspect_landing_fix = next_fix
                    # suspect_landing_alt = alt
                else:
                    time_diff = next_fix.rawtime - suspect_landing_fix.rawtime
                    alt_diff = abs(alt - suspect_landing_fix.alt)
                    if time_diff > max_still_seconds and alt_diff < min_alt_difference:
                        '''assuming pilot landed'''
                        result.landing_time = next_fix.rawtime
                        result.landing_altitude = alt
                        result.live_comment = 'landed'
                        break
            elif suspect_landing_fix is not None:
                suspect_landing_fix = None

        # if alt > result.max_altitude:
        #     result.max_altitude = alt

        # '''handle stopped task'''
        # if task.stopped_time and next_fix.rawtime > deadline:
        #     result.last_altitude = alt  # check the rules on this point..which alt to
        #     break

        '''check if pilot has arrived in goal (last turnpoint) so we can stop.'''
        if tp.made_all:
            break

        '''check if task deadline has passed'''
        if task.task_deadline < next_fix.rawtime:
            # Task has ended
            result.live_comment = 'flying past deadline'
            break

        '''check if start closing time passed and pilot did not start'''
        if task.start_close_time and task.start_close_time < my_fix.rawtime and not tp.start_done:
            # start closed
            result.live_comment = 'did not start before start closing time'
            break

        if result.landing_time and next_fix.rawtime > result.landing_time:
            '''pilot already landed'''
            # this should not happen as landed pilot are filtered
            break

        '''check tp type is known'''
        if tp.next.type not in ('launch', 'speed', 'waypoint', 'endspeed', 'goal'):
            assert False, f"Unknown turnpoint type: {tp.type}"

        '''check window is open'''
        if task.window_open_time > next_fix.rawtime:
            continue

        '''start turnpoint managing'''
        '''given all n crossings for a turnpoint cylinder, sorted in ascending order by their crossing time,
        the time when the cylinder was reached is determined.
        turnpoint[i] = SSS : reachingTime[i] = crossing[n].time
        turnpoint[i] =? SSS : reachingTime[i] = crossing[0].time

        We need to check start in 3 cases:
        - pilot has not started yet
        - race has multiple starts
        - task is elapsed time
        '''
        if pilot_can_start(task, tp, my_fix):
            # print(f'time: {my_fix.rawtime}, start: {task.start_time} | Interval: {task.SS_interval} | my start: {result.real_start_time} | better_start: {pilot_get_better_start(task, my_fix.rawtime, result.SSS_time)} | can start: {pilot_can_start(task, tp, my_fix)} can restart: {pilot_can_restart(task, tp, my_fix, result)} | tp: {tp.name}')
            if start_made_civl(my_fix, next_fix, tp.next, tolerance, min_tol_m):
                t = int(round(tp_time_civl(my_fix, next_fix, tp.next), 0))
                result.waypoints_achieved.append([tp.name, t, alt])  # pilot has started
                result.real_start_time = t
                tp.move_to_next()

        elif pilot_can_restart(task, tp, my_fix, result):
            # print(f'time: {my_fix.rawtime}, start: {task.start_time} | Interval: {task.SS_interval} | my start: {result.real_start_time} | better_start: {pilot_get_better_start(task, my_fix.rawtime, result.SSS_time)} | can start: {pilot_can_start(task, tp, my_fix)} can restart: {pilot_can_restart(task, tp, my_fix, result)} | tp: {tp.name}')
            if start_made_civl(my_fix, next_fix, tp.last_made, tolerance, min_tol_m):
                tp.pointer -= 1
                t = int(round(tp_time_civl(my_fix, next_fix, tp.next), 0))
                result.waypoints_achieved.pop()
                result.waypoints_achieved.append([tp.name, t, alt])  # pilot has started again
                result.real_start_time = t
                if lead_coeff:
                    lead_coeff.reset()
                tp.move_to_next()
                restarted = True

        if tp.start_done:
            '''Turnpoint managing'''
            if (tp.next.shape == 'circle'
                    and tp.next.type in ('endspeed', 'waypoint')):
                if tp_made_civl(my_fix, next_fix, tp.next, tolerance, min_tol_m):
                    t = int(round(tp_time_civl(my_fix, next_fix, tp.next), 0))
                    result.waypoints_achieved.append([tp.name, t, alt])  # pilot has achieved turnpoint
                    tp.move_to_next()

            if tp.next.type == 'goal':
                if ((tp.next.shape == 'circle' and tp_made_civl(my_fix, next_fix, tp.next, tolerance, min_tol_m))
                        or (tp.next.shape == 'line' and (in_semicircle(task, task.turnpoints, tp.pointer, my_fix)
                                                         or in_semicircle(task, task.turnpoints, tp.pointer,
                                                                          next_fix)))):
                    result.waypoints_achieved.append(
                        [tp.name, next_fix.rawtime, alt])  # pilot has achieved turnpoint
                    break

        '''update result data
        Once launched, distance flown should be max result among:
        - previous value;
        - optimized dist. to last turnpoint made;
        - total optimized distance minus opt. distance from next wpt to goal minus dist. to next wpt;
        '''
        if tp.pointer > 0:
            if tp.start_done and not tp.ess_done:
                '''optimized distance calculation each fix'''
                fix_dist_flown = task.opt_dist - get_shortest_path(task, next_fix, tp.pointer)
                # print(f'time: {next_fix.rawtime} | fix: {tp.name} | Optimized Distance used')
            else:
                '''simplified and faster distance calculation'''
                fix_dist_flown = distance_flown(next_fix, tp.pointer, task.optimised_turnpoints,
                                                task.turnpoints[tp.pointer], distances2go)
                # print(f'time: {next_fix.rawtime} | fix: {tp.name} | Simplified Distance used')

            result.distance_flown = max(result.distance_flown, fix_dist_flown,
                                        task.partial_distance[tp.last_made_index])

        '''Leading coefficient
        LC = taskTime(i)*(bestDistToESS(i-1)^2 - bestDistToESS(i)^2 )
        i : i ? TrackPoints In SS'''
        if lead_coeff and tp.start_done and not tp.ess_done:
            lead_coeff.update(result, my_fix, next_fix)

        '''Airspace Check'''
        if task.airspace_check and airspace_obj:
            map_fix = [next_fix.rawtime, next_fix.lat, next_fix.lon, alt]
            plot, penalty = airspace_obj.check_fix(next_fix, alt)
            if plot:
                map_fix.extend(plot)
                '''Airspace Infringement: check if we already have a worse one'''
                airspace_name = plot[2]
                infringement_type = plot[3]
                dist = plot[4]
                infringements_list.append([next_fix, airspace_name, infringement_type, dist, penalty])
            else:
                map_fix.extend([None, None, None, None, None])
            # airspace_plot.append(map_fix)

    '''final results'''
    result.last_altitude = alt
    result.height = 0 if not result.first_time or result.landing_time or not next_fix else next_fix.height

    # print(f'start indev: {tp.start_index}')
    # print(f'start done: {tp.start_done}')
    # print(f'pointer: {tp.pointer}')
    if tp.start_done:
        if not already_started or restarted:
            '''
            start time
            if race, the first times
            if multistart, the first time of the last gate pilot made
            if elapsed time, the time of last fix on start
            SS Time: the gate time'''
            result.SSS_time = task.start_time

            if task.task_type == 'RACE' and task.SS_interval:
                result.SSS_time += max(0, (start_number_at_time(task, result.real_start_time) - 1) * task.SS_interval)

            elif task.task_type == 'ELAPSED TIME':
                result.SSS_time = result.real_start_time

            '''manage jump the gun'''
            # print(f'wayponts made: {result.waypoints_achieved}')
            if max_jump_the_gun > 0:
                if result.real_start_time < result.SSS_time:
                    diff = result.SSS_time - result.real_start_time
                    penalty = diff * jtg_penalty_per_sec
                    # check
                    print(f'jump the gun: {diff} - valid: {diff <= max_jump_the_gun} - penalty: {penalty}')
                    comment = f"Jump the gun: {diff} seconds. Penalty: {penalty} points"
                    result.notifications.append(Notification(notification_type='jtg',
                                                             flat_penalty=penalty, comment=comment))

        '''ESS Time'''
        if any(e[0] == 'ESS' for e in result.waypoints_achieved) and not already_ESS:
            # result.ESS_time, ess_altitude = min([e[1] for e in result.waypoints_achieved if e[0] == 'ESS'])
            result.ESS_time, result.ESS_altitude = min(
                [(x[1], x[2]) for x in result.waypoints_achieved if x[0] == 'ESS'], key=lambda t: t[0])
            result.speed = (task.SS_distance / 1000) / (result.ss_time / 3600)

        '''Distance flown'''
        ''' ?p:p?PilotsLandingBeforeGoal:bestDistancep = max(minimumDistance, taskDistance-min(?trackp.pointi shortestDistanceToGoal(trackp.pointi)))
            ?p:p?PilotsReachingGoal:bestDistancep = taskDistance
        '''
        if any(e[0] == 'Goal' for e in result.waypoints_achieved):
            result.distance_flown = task.opt_dist
            result.goal_time, result.goal_altitude = min(
                [(x[1], x[2]) for x in result.waypoints_achieved if x[0] == 'Goal'], key=lambda t: t[0])
            result.result_type = 'goal'
            result.live_comment = 'Goal!'

    result.best_waypoint_achieved = str(result.waypoints_achieved[-1][0]) if result.waypoints_achieved else None

    if lead_coeff:
        result.fixed_LC = lead_coeff.summing

    if task.airspace_check:
        infringements, notifications, penalty = airspace_obj.get_infringements_result_new(infringements_list)
        result.notifications.extend(notifications)
        result.notifications = clear_notifications(task, result)
    return result


def get_live_json(task_id):
    from Defines import LIVETRACKDIR
    from os import path
    import jsonpickle
    fullname = path.join(LIVETRACKDIR, str(task_id))
    try:
        with open(fullname, 'r') as f:
            result = jsonpickle.decode(f.read())
            # return jsonpickle.decode(result)
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
