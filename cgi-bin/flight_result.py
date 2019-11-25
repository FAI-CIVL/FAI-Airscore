"""
Flight Result Library

contains Flight_result class.
contains statistics about a flight with regards to a task.

Methods:
    from_fsdb
    check_flight - check flight against task and record results (times, distances and leadout coeff)
    store_result - write result to DB (tblTaskResult)
    store_result_test - write result to DB in test mode(tblTaskResult_test)
	store_result_json - not needed, think we can delete
	to_geojson_result - create json file containing tracklog (split into preSSS, preGoal and postGoal), Thermals, bounds and result obj
	save_result_file - save the json file.

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019

"""

from calcUtils import get_datetime
from route import rawtime_float_to_hms, in_semicircle, distance_flown
from myconn import Database
import jsonpickle, json
from mapUtils import checkbbox
from route import distance
from collections import namedtuple

class Flight_result(object):
    """Set of statistics about a flight with respect a task.
    Attributes:
        Start_time:     time the task was started . i.e relevant start gate. (local time)
        SSS_time:       array of time(s) the pilot started, i.e. crossed the start line (local time)
        Waypoints achieved: the last waypoint achieved by the pilot, SSS, ESS, Goal or a waypoint number (wp1 is first wp after SSS)
        ESS_time:       the time the pilot crossed the ESS (local time)
        total_time:     the length of time the pilot took to complete the course. ESS- Start_time (for Race) or ESS - SSS_time (for elapsed)
        fixed_LC:       fixed part of lead_coeff, indipendent from other tracks
        lead_coeff:     lead points coeff (for GAP based systems), sum of fixed_LC and variable part calcullated during scoring
        """

    def __init__(self, pil_id=None, first_time=None, real_start_time=None, SSS_time=0, ESS_time=None, goal_time=None, last_time=None,
                 best_waypoint_achieved='No waypoints achieved', fixed_LC=0, lead_coeff=0, distance_flown=0, last_altitude=0,
                 jump_the_gun=None, track_file=None):
        """

        :type lead_coeff: int
        """
        self.first_time                 = first_time
        self.real_start_time            = real_start_time
        self.SSS_time                   = SSS_time
        self.ESS_time                   = ESS_time
        self.goal_time                  = goal_time
        self.last_time                  = last_time
        self.best_waypoint_achieved     = best_waypoint_achieved
        self.waypoints_achieved         = []
        self.fixed_LC                   = fixed_LC
        self.lead_coeff                 = lead_coeff
        self.distance_flown             = distance_flown
        self.max_altitude               = 0
        self.ESS_altitude               = 0
        self.goal_altitude              = 0
        self.last_altitude              = last_altitude
        self.landing_time               = 0
        self.landing_altitude           = 0
        self.jump_the_gun               = jump_the_gun
        self.score                      = 0
        self.total_distance             = 0
        self.departure_score            = 0
        self.arrival_score              = 0
        self.distance_score             = 0
        self.time_score                 = 0
        self.penalty                    = 0
        self.comment                    = None
        self.ext_id                     = None
        self.pil_id                     = pil_id
        self.result_type                = 'lo'
        self.SS_distance                = None
        self.track_file                 = track_file

    @property
    def speed(self):
        if self.ESS_time and self.SS_distance:
            return (self.SS_distance / 1000) / (self.total_time / 3600)
        else:
            return 0
    @property
    def total_time(self):
        if self.ESS_time:
            return self.ESS_time - self.SSS_time
        else:
            return 0

    @property
    def stopped_altitude(self):
        if self.stopped_time:
            return self.last_altitude
        else:
            return 0

    @property
    def waypoints_made(self):
        from collections import Counter
        if self.waypoints_achieved:
            return len(Counter(el[0] for el in self.waypoints_achieved))
        else:
            return 0

    @classmethod
    def from_fsdb(cls, res, dep=None, arr=None):
        """ Creates Results from FSDB FsPartecipant element, which is in xml format.
            Unfortunately the fsdb format isn't published so much of this is simply an
            exercise in reverse engineering.
        """
        from datetime import timedelta

        result = cls()
        result.ext_id = int(res.get('id'))
        if res.find('FsResult') is not None:
            '''reading flight data'''
            r = res.find('FsResult')
            # result['rank'] = int(r.get('rank'))
            result.score = int(r.get('points'))
            result.total_distance = float(r.get('distance')) * 1000  # in meters
            result.distance_flown = float(r.get('real_distance')) * 1000  # in meters
            # print ("start_ss: {}".format(r.get('started_ss')))
            result.real_start_time = get_datetime(r.get('started_ss')).time() if r.get(
                'started_ss') is not None else None
            result.SSS_time = float(r.get('ss_time_dec_hours'))
            if result.SSS_time > 0:
                result.ESS_time = get_datetime(r.get('finished_ss')).time()
                print(" ESS Time: {}".format(result.ESS_time))
                print(" * time but not goal: {}".format(r.get('got_time_but_not_goal_penalty')))
                if r.get('got_time_but_not_goal_penalty') == 'False':
                    print(" * pilot made Goal! *")
                    '''pilot did make goal, we need to put a time in tarGoal
                        I just put a time 10 minutes after ESS time'''
                    result.goal_time = (get_datetime(r.get('finished_ss')) + timedelta(minutes=10)).time()
                    print("    fake goal time: {}".format(result.goal_time))
            else:
                result.ESS_time = None
            result.last_altitude = int(r.get('last_altitude_above_goal'))
            result.distance_score = float(r.get('distance_points'))
            result.time_score = float(r.get('time_points'))
            result.penalty = int(r.get('penalty_points'))
            result.comment = r.get('penalty_reason')
            if dep is 'on':
                result.departure_score = float(r.get('departure_points'))
            elif dep is 'leadout':
                result.departure_score = float(r.get('leading_points'))
            else:
                result.departure_score = 0  # not necessary as it it initialized to 0
            result.arrival_score = float(r.get('arrival_points')) if arr is 'on' else 0
        else:
            '''pilot has no recorded flight'''
            result.result_type = 'abs'
        # print ("Result in obj: id {} was: {} start: {} end: {} points: {} ".format(result.ext_id, result.result_type, result.Start_time, result.ESS_time, result.score))

        return result

    @classmethod
    def read_from_db(cls, res_id):
        """reads result from database"""
        from db_tables import FlightResultView as R

        result = cls()
        with Database() as db:
            # get result details.
            q = db.session.query(R)
            db.populate_obj(result, q.get(res_id))
        return result

    @classmethod
    def check_flight(cls, Flight, task, formula_parameters, min_tol_m=0, deadline=None):
        """ Checks a Flight object against the task.
            Args:
                   Flight:  a Flight object
                   task:    a Task object
                   min_tol: minimum tolerance in meters, default is 0
            Returns:
                    a list of GNSSFixes of when turnpoints were achieved.
        """
        from route import start_made_civl, tp_made_civl, tp_time_civl

        ''' Altitude Source: to implement
            defaulting to GPS'''
        alt_source = 'gps'

        '''initialize'''
        result      = cls()
        tolerance   = task.tolerance
        time_offset = task.time_offset      # local time offset for result times (SSS and ESS)

        if not task.optimised_turnpoints:
            task.calculate_optimised_task_length()
        distances2go        = task.distances_to_go  # Total task Opt. Distance, in legs list
        best_dist_to_ess    = [task.SS_distance]  # Best distance to ESS, for LC calculation
        waypoint            = 1  # for report purpouses
        t                   = 0  # turnpoint pointer
        started             = False  # check if pilot has a valid start fix

        result.first_time   = Flight.fixes[0].rawtime if not Flight.takeoff_fix else Flight.takeoff_fix.rawtime  # time of flight origin
        max_altitude        = 0     # max altitude

        for i in range(len(Flight.fixes) - 1):
            '''Get two consecutive trackpoints as needed to use FAI / CIVL rules logic
            '''
            fix                     = Flight.fixes[i]
            next                    = Flight.fixes[i + 1]
            result.last_time        = fix.rawtime
            alt                     = next.gnss_alt if alt_source == 'gps' else next.press_alt

            if alt > max_altitude: max_altitude = alt

            '''handle stopped task'''
            if task.stopped_time:
                if not deadline:
                    deadline = task.stop_time
                if next.rawtime > deadline:
                    # result.last_altitude = alt  # check the rules on this point..which alt to
                    break

            '''check if pilot has arrived in goal (last turnpoint) so we can stop.'''
            if t >= len(task.turnpoints):
                break

            '''check if task deadline has passed'''
            if task.task_deadline < next.rawtime:
                # Task has ended
                break

            '''check if start closing time passed and pilot did not start'''
            if (task.start_close_time and (task.start_close_time < fix.rawtime) and not started):
                # start closed
                break

            '''check tp type is known'''
            if task.turnpoints[t].type not in ('launch', 'speed', 'waypoint', 'endspeed', 'goal'):
                assert False, "Unknown turnpoint type: %s" % task.turnpoints[t].type

            '''launch turnpoint managing'''
            if task.turnpoints[t].type == "launch":
                # not checking launch yet
                if task.check_launch == 'on':
                    # Set radius to check to 200m (in the task def it will be 0)
                    # could set this in the DB or even formula if needed..???
                    task.turnpoints[t].radius = 200  # meters
                    if task.turnpoints[t].in_radius(fix, tolerance, min_tol_m):
                        result.waypoints_achieved.append(["Left Launch", fix.rawtime, alt])  # pilot has achieved turnpoint
                        t += 1

                else:
                    t += 1

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

            if (((task.turnpoints[t].type == "speed" and not started)
                 or
                 (task.turnpoints[t - 1].type == "speed" and (task.SS_interval or task.task_type == 'ELAPSED TIME')))
                    and
                    (fix.rawtime >= (task.start_time - formula_parameters.max_jump_the_gun))
                    and
                    (not (task.start_close_time) or (fix.rawtime <= task.start_close_time))):

                # we need to check if it is a restart, so to use correct tp
                if task.turnpoints[t - 1].type == "speed":
                    SS_tp = task.turnpoints[t - 1]
                    restarting = True
                else:
                    SS_tp = task.turnpoints[t]
                    restarting = False

                if start_made_civl(fix, next, SS_tp, tolerance, min_tol_m):
                    time = round(tp_time_civl(fix, next, SS_tp), 0)
                    result.waypoints_achieved.append(["SSS", time, alt])  # pilot has started
                    started = True
                    result.fixed_LC = 0  # resetting LC to last start time
                    if not restarting:
                        t += 1

            if started:
                '''Turnpoint managing'''
                if (task.turnpoints[t].shape == 'circle'
                        and task.turnpoints[t].type in ('endspeed', 'waypoint')):
                    tp = task.turnpoints[t]
                    if tp_made_civl(fix, next, tp, tolerance, min_tol_m):
                        time = round(tp_time_civl(fix, next, tp), 0)
                        name = 'ESS' if tp.type == 'endspeed' else 'TP{:02}'.format(waypoint)
                        # if tp.type == 'endspeed' and ess_altitude == 0:
                        #     ess_altitude = alt
                        # result.best_waypoint_achieved = 'waypoint ' + str(waypoint) + ' made'
                        result.waypoints_achieved.append([name, time, alt])  # pilot has achieved turnpoint
                        waypoint += 1
                        t += 1

                if task.turnpoints[t].type == 'goal':
                    goal_tp = task.turnpoints[t]
                    if ((goal_tp.shape == 'circle' and tp_made_civl(fix, next, goal_tp, tolerance, min_tol_m))
                            or (goal_tp.shape == 'line' and (in_semicircle(task, task.turnpoints, t, fix)
                                                             or in_semicircle(task, task.turnpoints, t, next)))):
                        result.waypoints_achieved.append(['Goal', next.rawtime, alt])  # pilot has achieved turnpoint
                        # if goal_altitude == 0:  goal_altitude = alt
                        break

            '''update result data
            Once launched, distance flown should be max result among:
            - previous value;
            - optimized dist. to last turnpoint made;
            - total optimized distance minus opt. distance from next wpt to goal minus dist. to next wpt;
            '''
            if t > 0:
                result.distance_flown = max(result.distance_flown, (distances2go[0] - distances2go[t-1]),
                                        distance_flown(next, t, task.optimised_turnpoints, task.turnpoints[t], distances2go))
            # print('fix {} | Dist. flown {} | tp {}'.format(i, round(result.distance_flown, 2), t))

            '''Leading coefficient
                LC = taskTime(i)*(bestDistToESS(i-1)^2 - bestDistToESS(i)^2 )
                i : i ? TrackPoints In SS'''
            if started and not any(e[0] == 'ESS' for e in result.waypoints_achieved):
                real_start_time = max([e[1] for e in result.waypoints_achieved if e[0] == 'SSS'])
                taskTime = next.rawtime - real_start_time
                best_dist_to_ess.append(task.opt_dist_to_ESS - result.distance_flown)
                result.fixed_LC += formula_parameters.coef_func(taskTime, best_dist_to_ess[0], best_dist_to_ess[1])
                best_dist_to_ess.pop(0)

        '''final results'''
        result.max_altitude     = max_altitude
        result.last_altitude    = alt

        result.landing_time     = Flight.landing_fix.rawtime
        result.landing_altitude = Flight.landing_fix.gnss_alt if alt_source == 'gps' else Flight.landing_fix.press_alt

        if started:
            '''
            start time
            if race, the first times
            if multistart, the first time of the last gate pilot made
            il elapsed time, the time of last fix on start
            SS Time: the gate time'''
            result.SSS_time = task.start_time
            result.real_start_time = min([e[1] for e in result.waypoints_achieved if e[0] == 'SSS'])

            if task.task_type == 'RACE' and task.SS_interval:
                start_num = int((task.start_close_time - task.start_time) / (task.SS_interval * 60))
                gate = task.start_time + ((task.SS_interval * 60) * start_num)  # last gate
                while gate > task.start_time:
                    if any([e for e in result.waypoints_achieved if e[0] == 'SSS' and e[1] >= gate]):
                        result.SSS_time = gate
                        result.real_start_time = min(
                            [e[1] for e in result.waypoints_achieved if e[0] == 'SSS' and e[1] >= gate])
                        break
                    gate -= task.SS_interval * 60

            elif task.task_type == 'ELAPSED TIME':
                result.real_start_time = max([e[1] for e in result.waypoints_achieved if e[0] == 'SSS'])
                result.SSS_time = result.real_start_time

            # result.Start_time_str = (("%02d:%02d:%02d") % rawtime_float_to_hms(result.SSS_time + time_offset))

            '''ESS Time'''
            if any(e[0] == 'ESS' for e in result.waypoints_achieved):
                # result.ESS_time, ess_altitude = min([e[1] for e in result.waypoints_achieved if e[0] == 'ESS'])
                result.ESS_time, result.ESS_altitude = min([(x[1],x[2]) for x in result.waypoints_achieved if x[0] == 'ESS'], key = lambda t: t[0])
                result.SS_distance = task.SS_distance
                # result.ESS_time_str = (("%02d:%02d:%02d") % rawtime_float_to_hms(result.ESS_time + time_offset))
                # result.total_time = result.ESS_time - result.SSS_time
                # result.total_time_str = (("%02d:%02d:%02d") % rawtime_float_to_hms(result.ESS_time - result.SSS_time))

                '''Distance flown'''
                ''' ?p:p?PilotsLandingBeforeGoal:bestDistancep = max(minimumDistance, taskDistance-min(?trackp.pointi shortestDistanceToGoal(trackp.pointi)))
                    ?p:p?PilotsReachingGoal:bestDistancep = taskDistance
                '''
                if any(e[0] == 'Goal' for e in result.waypoints_achieved):
                    result.distance_flown = distances2go[0]
                    # result.goal_time = min([e[1] for e in result.waypoints_achieved if e[0] == 'Goal'])
                    result.goal_time, result.goal_altitude = min([(x[1],x[2]) for x in result.waypoints_achieved if x[0] == 'Goal'], key = lambda t: t[0])
                    result.result_type = 'goal'

        result.best_waypoint_achieved = str(result.waypoints_achieved[-1][0]) if result.waypoints_achieved else None

        # if result.ESS_time is None: # we need to do this after other operations
        #     result.fixed_LC += formula_parameters.coef_landout((task.task_deadline - task.start_time),((task.opt_dist_to_ESS - result.distance_flown) / 1000))
        # print('    * Did not reach ESS LC: {}'.format(result.fixed_LC))

        result.fixed_LC = formula_parameters.coef_func_scaled(result.fixed_LC, task.opt_dist_to_ESS)
        # print('    * Final LC: {} \n'.format(result.fixed_LC))
        return result

    def store_result(self, task_id, track_id = None):
        ''' stores new calculated results to db
            if track_id is not given, it inserts a new result
            else it updates existing one '''
        from collections import Counter
        from db_tables import tblTaskResult as R

        '''checks conformity'''
        if not self.goal_time: self.goal_time = 0
        endss = 0 if not self.ESS_time else self.ESS_time
        num_wpts = len(Counter(el[0] for el in self.waypoints_achieved))

        '''database connection'''
        with Database() as db:
            if track_id:
                results = db.session.query(R)
                r = results.get(track_id)
            else:
                '''create a new result'''
                r = R(pilPk=self.pil_id, tasPk=task_id)

            r.tarDistance   = self.distance_flown
            r.tarSpeed      = self.speed
            r.tarLaunch     = self.first_time
            r.tarStart      = self.real_start_time
            r.tarGoal       = self.goal_time
            r.tarSS         = self.SSS_time
            r.tarES         = endss
            r.tarTurnpoints = num_wpts
            r.tarFixedLC    = self.fixed_LC
            r.tarESAltitude = self.ESS_altitude
            r.tarGoalAltitude   = self.goal_altitude
            r.tarMaxAltitude    = self.max_altitude
            r.tarLastAltitude   = self.last_altitude
            r.tarLastTime       = self.last_time
            r.tarLandingAltitude    = self.landing_altitude
            r.tarLandingTime        = self.landing_time
            r.tarResultType         = self.result_type

            if not track_id: db.session.add(r)

            db.session.commit()

    def store_result_json(self):
        json.dump(self)

    def to_geojson_result(self, track, task, second_interval=5):
        """Dumps the flight to geojson format used for mapping.
        Contains tracklog split into pre SSS, pre Goal and post goal parts, thermals, takeoff/landing,
        result object, waypoints achieved, and bounds

        second_interval = resolution of tracklog. default one point every 5 seconds. regardless it will
                            keep points where waypoints were achieved.
        returns the Json string."""

        from geojson import Point, Feature, FeatureCollection, MultiLineString
        from route import distance
        from collections import namedtuple

        features = []
        toff_land = []
        thermals = []
        point = namedtuple('fix', 'lat lon')

        min_lat = track.flight.fixes[0].lat
        min_lon = track.flight.fixes[0].lon
        max_lat = track.flight.fixes[0].lat
        max_lon = track.flight.fixes[0].lon
        bbox = [[min_lat, min_lon], [max_lat, max_lon]]

        takeoff = Point((track.flight.takeoff_fix.lon, track.flight.takeoff_fix.lat))
        toff_land.append(Feature(geometry=takeoff, properties={"TakeOff": "TakeOff"}))
        landing = Point((track.flight.landing_fix.lon, track.flight.landing_fix.lat))
        toff_land.append(Feature(geometry=landing, properties={"Landing": "Landing"}))

        for thermal in track.flight.thermals:
            thermals.append((thermal.enter_fix.lon, thermal.enter_fix.lat,
                             f'{thermal.vertical_velocity():.1f}m/s gain:{thermal.alt_change():.0f}m'))

        pre_sss = []
        pre_goal = []
        post_goal = []
        waypoint_achieved = []

        #if the pilot did not make goal, goal time will be None. set to after end of track to avoid issues.
        if not self.goal_time:
            goal_time= track.flight.fixes[-1].rawtime + 1
        else:
            goal_time = self.goal_time

        # if the pilot did not make SSS then it will be 0, set to task start time.
        if self.SSS_time==0:
            SSS_time = task.start_time
        else:
            SSS_time = self.SSS_time

        waypoint = 0
        lastfix = track.flight.fixes[0]
        for fix in track.flight.fixes:
            bbox = checkbbox(fix.lat, fix.lon, bbox)
            keep = False
            if fix.rawtime >= lastfix.rawtime + second_interval:
                keep = True
                lastfix = fix

            if fix.rawtime == self.waypoints_achieved[waypoint][1]:
                time = (("%02d:%02d:%02d") % rawtime_float_to_hms(fix.rawtime + task.time_offset * 3600))
                waypoint_achieved.append(
                    [fix.lon, fix.lat, fix.gnss_alt, fix.press_alt, self.waypoints_achieved[waypoint][0], time,
                     fix.rawtime,
                     f'{self.waypoints_achieved[waypoint][0]} '
                     f'gps alt: {fix.gnss_alt:.0f}m '
                     f'baro alt: {fix.press_alt:.0f}m '
                     f'time: {time}'])
                keep = True
                if waypoint < len(self.waypoints_achieved) - 1:
                    waypoint += 1

            if keep:
                if fix.rawtime <= SSS_time:
                    pre_sss.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))
                if fix.rawtime >= SSS_time and fix.rawtime <= goal_time:
                    pre_goal.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))
                if fix.rawtime >= goal_time:
                    post_goal.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))

        for w in range(1, len(waypoint_achieved[1:]) + 1):
            current = point(lon=waypoint_achieved[w][0], lat=waypoint_achieved[w][1])
            previous = point(lon=waypoint_achieved[w - 1][0], lat=waypoint_achieved[w - 1][1])
            straight_line_dist = distance(previous, current) / 1000
            time_taken = (waypoint_achieved[w][6] - waypoint_achieved[w - 1][6]) / 3600
            time_takenHMS = rawtime_float_to_hms(time_taken * 3600)
            speed = straight_line_dist / time_taken
            waypoint_achieved[w].append(round(straight_line_dist, 2))
            waypoint_achieved[w].append(("%02d:%02d:%02d") % time_takenHMS)
            waypoint_achieved[w].append(round(speed, 2))

        waypoint_achieved[0].append(0)
        waypoint_achieved[0].append(("0:00:00"))
        waypoint_achieved[0].append('-')

        route_multilinestring = MultiLineString([pre_sss])
        features.append(Feature(geometry=route_multilinestring, properties={"Track": "Pre_SSS"}))
        route_multilinestring = MultiLineString([pre_goal])
        features.append(Feature(geometry=route_multilinestring, properties={"Track": "Pre_Goal"}))
        route_multilinestring = MultiLineString([post_goal])
        features.append(Feature(geometry=route_multilinestring, properties={"Track": "Post_Goal"}))

        feature_collection = FeatureCollection(features)

        data = {'tracklog': feature_collection, 'thermals': thermals, 'takeoff_landing': toff_land,
                'result': jsonpickle.dumps(self), 'bounds': bbox, 'waypoint_achieved': waypoint_achieved}

        return data


    def save_result_file(self, data, trackid):
        """save result file in the correct folder as defined by DEFINES"""

        from os import path, makedirs
        import Defines
        res_path = Defines.MAPOBJDIR + 'tracks/'

        """check if directory already exists"""
        if not path.isdir(res_path):
            makedirs(res_path)
        """creates a name for the track
        name_surname_date_time_index.igc
        if we use flight date then we need an index for multiple tracks"""

        filename = 'result_'+str(trackid)+ '.json'
        fullname = path.join(res_path, filename)
        """copy file"""
        try:
            with open(fullname, 'w') as f:
                json.dump(data, f)
            return fullname
        except:
            print('Error saving file:', fullname)

def adjust_flight_results(task, results, lib):

    maxtime = task.duration
    for pilot in results:
        if pilot['result'].last_fix_time - pilot['result'].SSS_time > maxtime:
            flight = pilot['track'].flight
            last_time = pilot['result'].SSS_time + maxtime
            pilot['result'] = Flight_result.check_flight(flight, task, lib.parameters, 5, deadline=last_time)
    return results

def verify_all_tracks(task, lib):
    from igc_lib import Flight
    from track import Track
    from db_tables import TrackFileView as T

    with Database() as db:
        tracks = db.session.query(T).filter(T.task_id == task.id).all()

    results = []
    if tracks:
        print('getting tracks...')
        for t in tracks:
            print(f"{t.track_id} {t.pil_id} ({t.filename}) Result:")
            track       = Track.read_file(filename=t.filename, track_id=t.track_id, pil_id=t.pil_id)
            if track and track.flight:
                result  = Flight_result.check_flight(track.flight, task, lib.parameters, 5)
                result.pil_id = t.pil_id
                print(f'   Goal: {bool(result.goal_time)} | part. LC: {result.fixed_LC}')
                results.append({'track': track, 'result': result})
    return results

def update_all_results(results):
    from collections import Counter
    from db_tables import tblTaskResult as R

    '''get results to update from the list'''
    mappings = []
    for line in results:
        res = line['result']
        track_id = line['track'].track_id

        '''checks conformity'''
        if not res.goal_time: res.goal_time = 0
        if not res.ESS_time: res.ESS_time = 0

        mapping = { 'tarPk':                track_id,
                    'tarDistance':          res.distance_flown,
                    'tarSpeed':             res.speed,
                    'tarLaunch':            res.first_time,
                    'tarStart':             res.real_start_time,
                    'tarGoal':              res.goal_time,
                    'tarSS':                res.SSS_time,
                    'tarES':                res.ESS_time,
                    'tarTurnpoints':        res.waypoints_made,
                    'tarFixedLC':           res.fixed_LC,
                    'tarESAltitude':        res.ESS_altitude,
                    'tarGoalAltitude':      res.goal_altitude,
                    'tarMaxAltitude':       res.max_altitude,
                    'tarLastAltitude':      res.last_altitude,
                    'tarLastTime':          res.last_time,
                    'tarLandingAltitude':   res.landing_altitude,
                    'tarLandingTime':       res.landing_time,
                    'tarResultType':        res.result_type }
        mappings.append(mapping)

    '''update database'''
    try:
        with Database() as db:
                db.session.bulk_update_mappings(T, mappings)
                db.session.commit()
    except:
        print(f'update all results on database gave an error')
        return False

    return True
