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
                    'ss_time',
                    'first_time',
                    'real_start_time',
                    'goal_time',
                    'SSS_time',
                    'ESS_time',
                    'turnpoints_made',
                    'ESS_altitude',
                    'goal_altitude',
                    'last_altitude',
                    'max_altitude',
                    'height',
                    'last_time',
                    'landing_time',
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
        return ((self.task is not None) and self.pilots and self.track_source
                and self.task.turnpoints and (self.task.start_time is not None))

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
        if not (self.task and self.task.turnpoints):
            return 'Task not defined'
        elif not self.properly_set:
            return 'Livetracking source is not set properly'
        else:
            if not self.task.start_time:
                return 'Times are not set yet'
            else:
                return 'Task is set'

    @property
    def headers(self):
        from calcUtils import sec_to_string
        main = ''
        details = ''
        if not (self.task and self.task.turnpoints):
            main = "Today's Task is not yet defined. Try Later."
        elif not self.properly_set:
            main = "Livetracking source is not set properly."
        else:
            task_type = 'Race to Goal' if self.task.task_type.lower() == 'race' else self.task.task_type
            main = f"Task Set: {round(self.task.opt_dist / 1000, 1)} Km {task_type}."
            if not self.task.start_time:
                details = 'Times are not set yet.'
            else:
                window = sec_to_string(self.task.window_open_time, self.task.time_offset, False)
                start = sec_to_string(self.task.start_time, self.task.time_offset, False)
                details = f'Window opens at {window} and start is at {start} (Local Time).'
        return dict(main=main, details=details)

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
        from result import Task_result
        file_stats = dict(timestamp=self.now, status=self.status)
        headers = self.headers
        info = {}
        data = []
        if not self.task:
            file_stats['status'] = 'Task is not set yet'
        else:
            info = {x: getattr(self.task, x) for x in Task_result.info_list if x in dir(self.task)}
            if not self.task.turnpoints:
                file_stats['status'] = 'Task is not set yet'
            elif not (self.track_source and self.pilots):
                file_stats['status'] = 'Livetracking source is not set properly.'
            else:
                if not self.task.start_time:
                    file_stats['status'] = 'Task Start time is not set yet'
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
        from result import Task_result
        self.result['file_stats']['timestamp'] = self.now
        '''check if status changed'''
        status = self.result['file_stats']['status']
        if not status == self.status:
            self.result['file_stats']['status'] = self.status
            self.result['headers'] = self.headers
            self.result['info'] = {x: getattr(self.task, x) for x in Task_result.info_list if x in dir(self.task)}
        else:
            for p in self.pilots:
                result = next(r for r in self.result['data'] if r['par_id'] == p.info.par_id)
                result.update({x: getattr(p.result, x) for x in LiveTracking.results_list if x in dir(p.result)})
                result['notifications'] = [n.__dict__ for n in p.notifications]
        self.create_json_file()

    def create_json_file(self):
        # from Defines import LIVETRACKDIR
        # from os import path
        # fullname = path.join(LIVETRACKDIR, str(self.task_id))
        try:
            with open(self.filename, 'w') as f:
                f.write(self.json_result)
            return True
        except:
            print(f'Error saving file: {self.filename}')

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
                if (p.livetrack and p.livetrack[-1].rawtime > (p.result.last_time or 0)
                        and not p.result.goal_time and not p.result.landing_time):
                    check_livetrack(pilot=p, task=self.task, airspace_obj=self.airspace)
                    # print(f' -- -- Pilot {p.info.name}:')
                    # print(f' ..... -- last fix {p.livetrack[-2].rawtime}')
                    # print(f' ..... -- rawtime: {p.result.last_time}')
                    # print(f' ..... -- Distance: {p.result.distance_flown}')
                    # print(f' ..... -- start: {p.result.real_start_time is not None}')
                    # print(f' ..... -- wpt made: {p.result.waypoints_made}')
                    # print(f' ..... -- Goal: {p.result.goal_time is not None}')
                    # if p.result.goal_time:
                    #     print(f' ..... -- Time: {p.result.time}')
                    #     print(f' ..... -- Waypoints:')
                    #     print(f'{p.result.waypoints_achieved}')
                    #     print(f' ..... -- Notifications:')
                    #     print(f'{p.result.notifications}')
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
        pilots = [p for p in task.pilots if p.info.live_id and not p.result.landing_time]
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
                print(response.json()['629878'][0])
                return response.json()
            except HTTPError as http_err:
                print(f'HTTP error trying to get tracks: {http_err}')
            except Exception as err:
                print(f'Error trying to get tracks: {err}')


def associate_livetracks(task, response, timestamp):
    from igc_lib import GNSSFix
    import time
    '''initialise'''
    launch_speed = 20  # km/h
    midnight = int(time.mktime(task.date.timetuple()))
    alt_source = 'GPS' if task.formula.scoring_altitude is None else task.formula.scoring_altitude
    for key, value in response.items():
        pil = next(p for p in task.pilots if p.info.live_id == key)
        if not pil:
            continue
        # res = pil.result
        if str(key) == '629878':
            print(f' - first time: {pil.result.first_time}')
            print(f' - last time: {pil.result.last_time}')
            print(f' - landing time: {pil.result.landing_time}')
        if pil.result.landing_time:
            '''already landed'''
            # shouldn't happen as landed pilots are filtered in tracks request
            continue
        flight = []
        counter = 0
        for idx, el in enumerate(value):
            t = int(el['d']) - midnight
            s = int(el['v'])
            if pil.result.last_time and t < pil.result.last_time:
                '''fix behind last scored fix'''
                if str(key) == '629878':
                    print(f' - fix behind last scored fix')
                continue
            if t > timestamp - midnight:
                '''fix ahead of cycle time'''
                if str(key) == '629878':
                    print(
                        f' - fix ahead of cycle time | timestamp: {timestamp} / midnight {midnight} / fix time: {t} / difference {t - (timestamp - midnight + 100)}')
                break
            if not pil.result.first_time:
                if s < launch_speed:
                    ''' not launched yet'''
                    pil.result.last_time = t
                    if str(key) == '629878':
                        print(f' - not launched yet | last time = {t}')
                    continue
                else:
                    '''launched'''
                    pil.result.first_time = t
                    if str(key) == '629878':
                        print(f' - launched | first time = {t}')
            lat = int(el['ai']) / 60000
            lon = int(el['oi']) / 60000
            baro_alt = int(el['c'])
            gnss_alt = int(el['h'])
            alt = gnss_alt if alt_source == 'GPS' else baro_alt
            fix = GNSSFix(t, lat, lon, 'A', baro_alt, gnss_alt, idx, '')
            fix.alt = alt
            ground = int(el['s'])
            if pil.result.first_time and s < 10 and abs(alt - ground) < 10:
                '''pilot seems landed'''
                counter += 1
                if counter > 10:
                    ''' we assume he is landed'''
                    pil.result.landing_time = t - 1
                    pil.result.height = 0
                    break
            elif counter > 0:
                counter = 0
            pil.result.height = abs(alt - ground)
            if str(key) == '629878':
                print(f' - height = {pil.result.height}')
            if str(key) == '629878':
                print(f' - fix added | time = {t}')
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
    from flight_result import Tp, pilot_can_start, pilot_can_restart, start_number_at_time
    from route import in_semicircle, start_made_civl, tp_made_civl, \
        tp_time_civl, get_shortest_path, distance_flown
    from airspace import AirspaceCheck
    from formulas.libs.leadcoeff import LeadCoeff
    from notification import Notification

    ''' Altitude Source: '''
    alt_source = 'GPS' if task.formula.scoring_altitude is None else task.formula.scoring_altitude

    '''initialize'''
    tolerance = task.formula.tolerance or 0
    min_tol_m = task.formula.min_tolerance or 0
    max_jump_the_gun = task.formula.max_JTG or 0  # seconds
    jtg_penalty_per_sec = 0 if max_jump_the_gun == 0 else task.formula.JTG_penalty_per_sec

    if not task.optimised_turnpoints:
        task.calculate_optimised_task_length()
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
    already_started = tp.start_done
    restarted = False
    already_ESS = any(e[0] == 'ESS' for e in result.waypoints_achieved)

    '''Airspace check managing'''
    airspace_plot = []
    infringements_list = []
    airspace_penalty = 0
    if task.airspace_check:
        if task.airspace_check and not airspace_obj:
            print(f'We should not create airspace here')
            airspace_obj = AirspaceCheck.from_task(task)

    for i in range(len(fixes) - 1):
        '''Get two consecutive trackpoints as needed to use FAI / CIVL rules logic
        '''
        # start_time = tt.time()
        my_fix = fixes[i]
        next_fix = fixes[i + 1]
        result.last_time = my_fix.rawtime
        alt = next_fix.alt

        if alt > result.max_altitude:
            result.max_altitude = alt

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
            result.last_altitude = alt
            break

        '''check if start closing time passed and pilot did not start'''
        if task.start_close_time and task.start_close_time < my_fix.rawtime and not tp.start_done:
            # start closed
            break

        '''check tp type is known'''
        if tp.next.type not in ('launch', 'speed', 'waypoint', 'endspeed', 'goal'):
            assert False, f"Unknown turnpoint type: {tp.type}"

        '''check window is open'''
        if task.window_open_time > next_fix.rawtime:
            continue

        # '''launch turnpoint managing'''
        # if tp.type == "launch":
        #     if task.check_launch == 'on':
        #         # Set radius to check to 200m (in the task def it will be 0)
        #         # could set this in the DB or even formula if needed..???
        #         tp.next.radius = 200  # meters
        #         if tp.next.in_radius(my_fix, tolerance, min_tol_m):
        #             result.waypoints_achieved.append(
        #                 [tp.name, my_fix.rawtime, alt])  # pilot has achieved turnpoint
        #             tp.move_to_next()
        #
        #     else:
        #         tp.move_to_next()

        # to do check for restarts for elapsed time tasks and those that allow jump the gun
        # if started and task.task_type != 'race' or result.jump_the_gun is not None:

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
        # TODO: To compensate for altitude differences at the time when a task is stopped, a bonus distance is
        #  calculated for each point in the pilots’ track logs, based on that point’s altitude above goal. This
        #  bonus distance is added to the distance achieved at that point. All altitude values used for this
        #  calculation are GPS altitude values, as received from the pilots’ GPS devices (no compensation for
        #  different earth models applied by those devices). For all distance point calculations, including the
        #  difficulty calculations in hang-gliding (see 11.1.1), these new stopped distance values are being used
        #  to determine the pilots’ best distance values. Time and leading point calculations remain the same:
        #  they are not affected by the altitude bonus or stopped distance values.
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
            plot, penalty = airspace_obj.check_fix(next_fix, alt_source)
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
    # result.max_altitude = max(max_altitude, result.max_altitude)
    # result.landing_time = flight.landing_fix.rawtime
    # result.landing_altitude = flight.landing_fix.gnss_alt if alt_source == 'GPS' else flight.landing_fix.press_alt

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
                    # '''delete previous jtg notification'''
                    # result.notifications = [n for n in result.notifications if not n.notification_type == 'jtg']
                    result.notifications.append(Notification(notification_type='jtg',
                                                             flat_penalty=penalty, comment=comment))
                # elif restarted and any(n for n in result.notifications if n.notification_type == 'jtg'):
                #     '''delete jtg notification'''
                #     result.notifications = [n for n in result.notifications if not n.notification_type == 'jtg']
                # result.penalty += penalty
                # result.comment.append(comment)

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
            # result.distance_flown = distances2go[0]
            result.distance_flown = task.opt_dist
            result.goal_time, result.goal_altitude = min(
                [(x[1], x[2]) for x in result.waypoints_achieved if x[0] == 'Goal'], key=lambda t: t[0])
            result.result_type = 'goal'

    result.best_waypoint_achieved = str(result.waypoints_achieved[-1][0]) if result.waypoints_achieved else None

    if lead_coeff:
        result.fixed_LC = lead_coeff.summing

    if task.airspace_check:
        infringements, notifications, penalty = airspace_obj.get_infringements_result_new(infringements_list)
        result.notifications.extend(notifications)
        result.notifications = clear_notifications(task, result)
        # result.percentage_penalty = penalty
        # result.airspace_plot = airspace_plot
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
