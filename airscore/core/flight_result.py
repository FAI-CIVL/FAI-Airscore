"""
Flight Result Library

contains Flight_result class.
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
from os import path, makedirs

import jsonpickle
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

from Defines import MAPOBJDIR
from airspace import AirspaceCheck
from calcUtils import string_to_seconds
from db_tables import TblTaskResult
from formulas.libs.leadcoeff import LeadCoeff
from myconn import Database
from route import in_semicircle, start_made_civl, tp_made_civl, \
    tp_time_civl, get_shortest_path, distance_flown


class Tp(object):
    def __init__(self, task):
        self.turnpoints = task.turnpoints
        self.optimised_turnpoints = task.optimised_turnpoints
        self.pointer = 0

    @property
    def next(self):
        return self.turnpoints[self.pointer]

    @property
    def name(self):
        if self.type == 'launch':
            return 'Left Launch'
        elif self.type == 'speed':
            return 'SSS'
        elif self.type == 'endspeed':
            return 'ESS'
        if self.type == 'goal':
            return 'Goal'
        elif self.type == 'waypoint':
            wp = [tp for tp in self.turnpoints if tp.type == 'waypoint']
            return 'TP{:02}'.format(wp.index(self.next) + 1)

    @property
    def total_number(self):
        return len(self.turnpoints)

    @property
    def type(self):
        return self.turnpoints[self.pointer].type

    @property
    def last_made(self):
        return self.turnpoints[self.pointer] if self.pointer == 0 else self.turnpoints[self.pointer - 1]

    @property
    def last_made_index(self):
        return 0 if self.pointer == 0 else self.pointer - 1

    @property
    def start_index(self):
        if any(x for x in self.turnpoints if x.type == 'speed'):
            return self.turnpoints.index(next(x for x in self.turnpoints if x.type == 'speed'))
        else:
            return None

    @property
    def ess_index(self):
        if any(x for x in self.turnpoints if x.type == 'endspeed'):
            return self.turnpoints.index(next(x for x in self.turnpoints if x.type == 'endspeed'))
        else:
            return None

    @property
    def start_done(self):
        return self.start_index < self.pointer

    @property
    def ess_done(self):
        return self.ess_index < self.pointer

    @property
    def made_all(self):
        return True if self.pointer == self.total_number else False

    def move_to_next(self):
        if self.pointer < len(self.turnpoints):
            self.pointer += 1


class Flight_result(object):
    """Set of statistics about a flight with respect a task.
    Attributes:
        real_start_time: time the pilot actually crossed relevant start gate.
        SSS_time:       time the task was started . i.e relevant start gate.
        waypoints achieved: the last waypoint achieved by the pilot, SSS, ESS, Goal or a waypoint number (wp1 is first wp after SSS)
        ESS_time:       the time the pilot crossed the ESS (local time)
        fixed_LC:       fixed part of lead_coeff, indipendent from other tracks
        lead_coeff:     lead points coeff (for GAP based systems), sum of fixed_LC and variable part calculated during scoring
        """

    def __init__(self, par_id=None, first_time=None, real_start_time=None, SSS_time=0, ESS_time=None, goal_time=None,
                 last_time=None,
                 best_waypoint_achieved='No waypoints achieved', fixed_LC=0, lead_coeff=0, distance_flown=0,
                 last_altitude=0,
                 jump_the_gun=None, track_file=None):
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
        self.distance_flown = distance_flown
        self.total_distance = 0
        self.max_altitude = 0
        self.ESS_altitude = 0
        self.goal_altitude = 0
        self.last_altitude = last_altitude
        self.landing_time = 0
        self.landing_altitude = 0
        self.jump_the_gun = jump_the_gun  # not used at the moment
        self.result_type = 'lo'
        self.score = 0
        self.departure_score = 0
        self.arrival_score = 0
        self.distance_score = 0
        self.time_score = 0
        self.penalty = 0
        self.percentage_penalty = 0
        self.airspace_plot = []
        self.infringements = []  # Infringement for each space
        self.comment = []  # should this be a list?
        # self.ID = None  # Could delete?
        # self.par_id = par_id  # Could delete?
        # self.track_file = track_file  # Could delete?

    def __setattr__(self, attr, value):
        property_names = [p for p in dir(Flight_result) if isinstance(getattr(Flight_result, p), property)]
        if attr not in property_names:
            self.__dict__[attr] = value

    @property
    def ss_time(self):
        if self.ESS_time:
            return self.ESS_time - self.SSS_time
        else:
            return None

    @property
    def time(self):
        if self.ESS_time:
            return self.ESS_time - self.SSS_time
        else:
            return None

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
        if self.distance_flown:
            return max(self.distance_flown, self.total_distance)
        else:
            return 0

    # @property
    # def time_after(self):
    #     if self.ESS_time:
    #         return self.ESS_time - self.SSS_time
    #     else:
    #         return 0

    @property
    def waypoints_made(self):
        if self.waypoints_achieved:
            return len(Counter(el[0] for el in self.waypoints_achieved))
        else:
            return 0

    def as_dict(self):
        return self.__dict__

    @classmethod
    def from_fsdb(cls, res, SS_distance=None, dep=None, arr=None, offset=0):
        """ Creates Results from FSDB FsPartecipant element, which is in xml format.
            Unfortunately the fsdb format isn't published so much of this is simply an
            exercise in reverse engineering.
        """

        result = cls()
        ID = int(res.get('id'))

        if res.find('FsFlightData') is None and res.find('FsResult') is None:
            '''pilot is abs'''
            print(f"ID {ID}: ABS")
            result.result_type = 'abs'
            return result
        elif res.find('FsFlightData') is None or res.find('FsFlightData').get('tracklog_filename') in [None, '']:
            print(f"ID {ID}: No track")
            print(f" - distance: {float(res.find('FsResult').get('distance'))}")
            if float(res.find('FsResult').get('distance')) > 0:
                '''pilot is min dist'''
                print(f"ID {ID}: Min Dist")
                result.result_type = 'mindist'
            else:
                '''pilot is dnf'''
                print(f"ID {ID}: DNF")
                result.result_type = 'dnf'
            return result

        d = res.find('FsFlightData')
        result.real_start_time = None if not d.get('started_ss') else string_to_seconds(d.get('started_ss')) - offset
        result.last_altitude = int(d.get('last_tracklog_point_alt')
                                   if d.get('last_tracklog_point_alt') is not None else 0)
        result.max_altitude = int(d.get('max_alt')
                                  if d.get('max_alt') is not None else 0)
        result.track_file = d.get('tracklog_filename')
        result.lead_coeff = None if d.get('lc') is None else float(d.get('lc'))
        if not d.get('finished_ss') == "":
            result.ESS_altitude = int(d.get('altitude_at_ess')
                                      if d.get('altitude_at_ess') is not None else 0)
        if d.get('reachedGoal') == "1":
            result.goal_time = (None if not d.get('finished_task')
                                else string_to_seconds(d.get('finished_task')) - offset)
            result.result_type = 'goal'
        if res.find('FsResult') is not None:
            '''reading flight data'''
            r = res.find('FsResult')
            # result['rank'] = int(r.get('rank'))
            result.score = float(r.get('points'))
            result.total_distance = float(r.get('distance')) * 1000  # in meters
            result.distance_flown = float(r.get('real_distance')) * 1000  # in meters
            # print ("start_ss: {}".format(r.get('started_ss')))
            result.SSS_time = None if not r.get('started_ss') else string_to_seconds(r.get('started_ss')) - offset
            if result.SSS_time is not None:
                result.ESS_time = (None if not r.get('finished_ss')
                                   else string_to_seconds(r.get('finished_ss')) - offset)
                if SS_distance is not None and result.ESS_time is not None and result.ESS_time > 0:
                    result.speed = (SS_distance / 1000) / ((result.ESS_time - result.SSS_time) / 3600)
            else:
                result.ESS_time = None
            result.last_altitude = int(r.get('last_altitude_above_goal'))
            result.distance_score = float(r.get('distance_points'))
            result.time_score = float(r.get('time_points'))
            result.penalty = 0  # fsdb score is already decreased by penalties
            if not r.get('penalty_reason') == "":
                if r.get('penalty') != "0":
                    comment = f"{float(r.get('penalty')) * 100}%: "
                else:
                    comment = f"{float(r.get('penalty_points'))} points: "
                comment += r.get('penalty_reason')
                result.comment.append(comment)
            if not r.get('penalty_reason_auto') == "":
                comment = f"{float(r.get('penalty_points_auto'))} points: "
                comment += r.get('penalty_reason_auto')
                result.comment.append(comment)
            if dep == 'on':
                result.departure_score = float(r.get('departure_points'))
            elif dep == 'leadout':
                result.departure_score = float(r.get('leading_points'))
            else:
                result.departure_score = 0  # not necessary as it it initialized to 0
            result.arrival_score = float(r.get('arrival_points')) if arr != 'off' else 0

        return result

    @staticmethod
    def read(res_id):
        """reads result from database"""
        from db_tables import FlightResultView as R

        result = Flight_result()
        with Database() as db:
            # get result details.
            q = db.session.query(R)
            db.populate_obj(result, q.get(res_id))
        return result

    @staticmethod
    def from_dict(d):
        result = Flight_result()
        for key, value in d.items():
            if hasattr(result, key):
                setattr(result, key, value)
        return result

    @classmethod
    def check_flight(cls, flight, task, airspace_obj=None, deadline=None):
        """ Checks a Flight object against the task.
            Args:
                   flight:  a Flight object
                   task:    a Task
                   deadline: in multiple start or elapsed time, I need to check again track using Min_flight_time
                                as deadline
            Returns:
                    a list of GNSSFixes of when turnpoints were achieved.
        """

        ''' Altitude Source: '''
        alt_source = 'GPS' if task.formula.scoring_altitude is None else task.formula.scoring_altitude

        '''initialize'''
        result = cls()
        tolerance = task.formula.tolerance or 0
        min_tol_m = task.formula.min_tolerance or 0
        max_jump_the_gun = task.formula.max_JTG or 0  # seconds
        jtg_penalty_per_sec = 0 if max_jump_the_gun == 0 else task.formula.JTG_penalty_per_sec

        if not task.optimised_turnpoints:
            task.calculate_optimised_task_length()
        distances2go = task.distances_to_go  # Total task Opt. Distance, in legs list

        '''leadout coefficient'''
        if task.formula.formula_departure == 'leadout':
            lead_coeff = LeadCoeff(task)
        else:
            lead_coeff = None

        result.first_time = flight.fixes[
            0].rawtime if not hasattr(flight, 'takeoff_fix') else flight.takeoff_fix.rawtime  # time of flight origin
        max_altitude = 0  # max altitude
        result.last_altitude = 0

        '''Stopped task managing'''
        if task.stopped_time:
            if not deadline:
                '''Using stop_time (stopped_time - score_back_time)'''
                deadline = task.stop_time

        '''Turnpoint managing'''
        tp = Tp(task)

        '''Airspace check managing'''
        airspace_plot = []
        infringements_list = []
        airspace_penalty = 0
        if task.airspace_check:
            if task.airspace_check and not airspace_obj:
                print(f'We should not create airspace here')
                airspace_obj = AirspaceCheck.from_task(task)

        for i in range(len(flight.fixes) - 1):
            '''Get two consecutive trackpoints as needed to use FAI / CIVL rules logic
            '''
            # start_time = tt.time()
            my_fix = flight.fixes[i]
            next_fix = flight.fixes[i + 1]
            result.last_time = my_fix.rawtime
            alt = next_fix.gnss_alt if alt_source == 'GPS' else next_fix.press_alt

            if alt > max_altitude:
                max_altitude = alt

            '''handle stopped task'''
            if task.stopped_time and next_fix.rawtime > deadline:
                result.last_altitude = alt  # check the rules on this point..which alt to
                break

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

            '''launch turnpoint managing'''
            if tp.type == "launch":
                if task.check_launch == 'on':
                    # Set radius to check to 200m (in the task def it will be 0)
                    # could set this in the DB or even formula if needed..???
                    tp.next.radius = 200  # meters
                    if tp.next.in_radius(my_fix, tolerance, min_tol_m):
                        result.waypoints_achieved.append(
                            [tp.name, my_fix.rawtime, alt])  # pilot has achieved turnpoint
                        tp.move_to_next()

                else:
                    tp.move_to_next()

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
                    time = int(round(tp_time_civl(my_fix, next_fix, tp.next), 0))
                    result.waypoints_achieved.append([tp.name, time, alt])  # pilot has started
                    result.real_start_time = time
                    tp.move_to_next()

            elif pilot_can_restart(task, tp, my_fix, result):
                # print(f'time: {my_fix.rawtime}, start: {task.start_time} | Interval: {task.SS_interval} | my start: {result.real_start_time} | better_start: {pilot_get_better_start(task, my_fix.rawtime, result.SSS_time)} | can start: {pilot_can_start(task, tp, my_fix)} can restart: {pilot_can_restart(task, tp, my_fix, result)} | tp: {tp.name}')
                if start_made_civl(my_fix, next_fix, tp.last_made, tolerance, min_tol_m):
                    time = int(round(tp_time_civl(my_fix, next_fix, tp.next), 0))
                    result.waypoints_achieved.pop()
                    result.waypoints_achieved.append([tp.name, time, alt])  # pilot has started again
                    result.real_start_time = time
                    if lead_coeff:
                        lead_coeff.reset()

            if tp.start_done:
                '''Turnpoint managing'''
                if (tp.next.shape == 'circle'
                        and tp.next.type in ('endspeed', 'waypoint')):
                    if tp_made_civl(my_fix, next_fix, tp.next, tolerance, min_tol_m):
                        time = int(round(tp_time_civl(my_fix, next_fix, tp.next), 0))
                        result.waypoints_achieved.append([tp.name, time, alt])  # pilot has achieved turnpoint
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
                else:
                    '''simplified and faster distance calculation'''
                    fix_dist_flown = distance_flown(next_fix, tp.pointer, task.optimised_turnpoints,
                                                    task.turnpoints[tp.pointer], distances2go)

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
        result.max_altitude = max_altitude
        result.landing_time = flight.landing_fix.rawtime
        result.landing_altitude = flight.landing_fix.gnss_alt if alt_source == 'GPS' else flight.landing_fix.press_alt

        if tp.start_done:
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
            print(f'wayponts made: {result.waypoints_achieved}')
            if max_jump_the_gun > 0 and result.real_start_time < result.SSS_time:
                diff = result.SSS_time - result.real_start_time
                result.penalty += diff * jtg_penalty_per_sec
                # check
                print(f'jump the gun: {diff} - valid: {diff <= max_jump_the_gun} - penalty: {result.penalty}')
                result.comment.append(f"Jump the gun: {diff} seconds. Penalty: {result.penalty} points")

            '''ESS Time'''
            if any(e[0] == 'ESS' for e in result.waypoints_achieved):
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
            infringements, comments, penalty = airspace_obj.get_infringements_result(infringements_list)
            result.infringements = infringements
            result.comment.extend(comments)
            result.percentage_penalty = penalty
            # result.airspace_plot = airspace_plot

        return result

    def to_db(self, task_id, track_id=None, session=None):
        """ stores new calculated results to db
            if track_id is not given, it inserts a new result
            else it updates existing one """
        # we should use Pilot.to_db()
        from db_tables import TblTaskResult as R, TblParticipant as P, TblTask as T

        '''database connection'''
        with Database(session) as db:
            if self.par_id is None:
                '''we have a result without pilot id. Try with ID number'''
                if self.ID is None:
                    '''we don't have any info about pilot'''
                    return None
                try:
                    comp_id = db.session.query(T).get(task_id).comp_id
                    self.par_id = db.session.query(P.par_id).filter(
                        and_(P.ID == self.ID, P.comp_id == comp_id)).scalar()
                except SQLAlchemyError:
                    print('Get registered pilot error')
                    db.session.rollback()
                if self.par_id is None:
                    '''we did not find a registered pilot for the result'''
                    return None

            if track_id:
                results = db.session.query(R)
                r = results.get(track_id)
            else:
                '''create a new result'''
                r = R(par_id=self.par_id, task_id=task_id)
                db.session.add(r)
                db.session.flush()
            row_id = r.track_id
            for a in dir(r):
                if a == 'comment' and self.comment:
                    r.comment = '; '.join(self.comment)
                if not a[0] == '_' and hasattr(self, a):
                    setattr(r, a, getattr(self, a))
            db.session.flush()

        return row_id

    def to_geojson_result(self, track, task, second_interval=5):
        """Dumps the flight to geojson format used for mapping.
        Contains tracklog split into pre SSS, pre Goal and post goal parts, thermals, takeoff/landing,
        result object, waypoints achieved, and bounds

        second_interval = resolution of tracklog. default one point every 5 seconds. regardless it will
                            keep points where waypoints were achieved.
        returns the Json string."""

        from mapUtils import result_to_geojson
        from db_tables import TblParticipant as p

        info = {'taskid': task.id, 'task_name': task.task_name, 'comp_name': task.comp_name}

        with Database() as db:
            pilot_details = (db.session.query(p.name, p.nat, p.sex, p.glider)
                             .filter(p.par_id == track.par_id, p.comp_id == task.comp_id).one())
        pilot_details = pilot_details._asdict()
        info['pilot_name'] = pilot_details['name']
        info['pilot_nat'] = pilot_details['nat']
        info['pilot_sex'] = pilot_details['sex']
        info['pilot_parid'] = track.par_id
        info['Glider'] = pilot_details['glider']

        tracklog, thermals, takeoff_landing, bbox, waypoint_achieved = result_to_geojson(self, track, task)
        airspace_plot = self.airspace_plot

        data = {'info': info, 'tracklog': tracklog, 'thermals': thermals, 'takeoff_landing': takeoff_landing,
                'result': jsonpickle.dumps(self), 'bounds': bbox, 'waypoint_achieved': waypoint_achieved,
                'airspace': airspace_plot}

        return data

    def save_result_file(self, data, trackid):
        """save result file in the correct folder as defined by DEFINES"""

        res_path = MAPOBJDIR + 'tracks/'

        """check if directory already exists"""
        if not path.isdir(res_path):
            makedirs(res_path)
        """creates a name for the track
        name_surname_date_time_index.igc
        if we use flight date then we need an index for multiple tracks"""

        filename = 'result_' + str(trackid) + '.track'
        fullname = path.join(res_path, filename)
        """copy file"""
        try:
            with open(fullname, 'w') as f:
                json.dump(data, f)
            return fullname
        except:
            print('Error saving file:', fullname)


def pilot_can_start(task, tp, fix):
    """ returns True if pilot, in the track fix, is in the condition to take the start gate"""

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

    max_jump_the_gun = task.formula.max_JTG or 0

    if ((tp.type == "speed")
            and
            (fix.rawtime >= (task.start_time - max_jump_the_gun))
            and
            (not task.start_close_time or fix.rawtime <= task.start_close_time)):
        return True
    else:
        return False


def pilot_can_restart(task, tp, fix, result):
    """ returns True if pilot, in the track fix, is in the condition to take the start gate"""

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

    max_jump_the_gun = task.formula.max_JTG or 0

    if tp.last_made.type == "speed" and (not task.start_close_time or fix.rawtime < task.start_close_time):
        if task.task_type == 'ELAPSED TIME':
            return True
        elif max_jump_the_gun > 0 and result.real_start_time < task.start_time:
            return True
        elif task.SS_interval and pilot_get_better_start(task, fix.rawtime, result.real_start_time):
            return True
    return False


def start_number_at_time(task, time):
    if time < task.start_time or (task.start_close_time and time > task.start_close_time):
        return 0
    elif task.total_start_number <= 1:
        return task.total_start_number
    elif task.SS_interval > 0:
        return 1 + int((time - task.start_time) / task.SS_interval)


def pilot_get_better_start(task, time, prev_time):
    return start_number_at_time(task, time) > start_number_at_time(task, prev_time)


def verify_all_tracks(task, lib, airspace=None):
    """ Gets in input:
            task:       Task object
            lib:        Formula library module"""
    from igc_lib import Flight

    print('getting tracks...')
    for pilot in task.pilots:
        print(f"type: {pilot.result_type}")
        if pilot.result_type not in ('abs', 'dnf', 'mindist'):
            print(f"{pilot.ID}. {pilot.name}: ({pilot.track.track_file})")
            filename = path.join(task.file_path, pilot.track.track_file)
            pilot.track.flight = Flight.create_from_file(filename)
            if pilot.track.flight and pilot.track.flight.valid:
                pilot.result = Flight_result.check_flight(pilot.track.flight, task, airspace_obj=airspace)
                print(f'   Goal: {bool(pilot.result.goal_time)} | part. LC: {pilot.result.fixed_LC}')
            elif pilot.track.flight:
                print(f'Error in parsing track: {[x for x in pilot.track.flight.notes]}')
    lib.process_results(task)


def adjust_flight_results(task, lib, airspace):
    """ Called when multi-start or elapsed time task was stopped.
        We need to check again and adjust results of pilots that flew more than task duration"""
    maxtime = task.duration
    for pilot in task.pilots:
        if pilot.result.SSS_time:
            last_time = pilot.result.SSS_time + maxtime
            if ((not pilot.ESS_time and pilot.last_fix_time > last_time)
                    or (pilot.ESS_time and pilot.ss_time > maxtime)):
                '''need to adjust pilot result'''
                # keep airspace infringements info
                # if task.airspace_check:
                #     infringements = pilot.result.infringements
                #     percentace_penalty = pilot.result.percentage_penalty
                #     comments = pilot.result.comments
                flight = pilot.track.flight
                adjusted = Flight_result.check_flight(flight, task, airspace_obj=airspace, deadline=last_time)
                pilot.result.result_type = adjusted.result_type
    lib.process_results(task)


def update_status(par_id, task_id, status):
    """Create or update pilot status ('abs', 'dnf', 'mindist')"""
    with Database() as db:
        try:
            result = db.session.query(TblTaskResult).filter(and_(TblTaskResult.par_id == par_id,
                                                                 TblTaskResult.task_id == task_id)).first()
            if result:
                result.tarResultType = status
            else:
                result = TblTaskResult(par_id=par_id, task_id=task_id, result_type=status)
                db.session.add(result)
            db.session.flush()
        except SQLAlchemyError as e:
            error = str(e.__dict__)
            print(f"Status update / Insert Error")
            db.session.rollback()
            db.session.close()
            return error
        return result.track_id


def delete_result(trackid):
    from trackUtils import get_task_fullpath
    from os import remove
    from db_tables import TblTaskResult as R
    row_deleted = None
    with Database() as db:
        try:
            results = db.session.query(R.track_file, R.task_id).filter(R.track_id == trackid).one()
            row_deleted = db.session.query(R.track_file, R.task_id).filter(R.track_id == trackid).delete(
                synchronize_session=False)
        except SQLAlchemyError:
            print("there was a problem deleting the track")
            return None

    if results.track_file is not None:
        full_path = get_task_fullpath(results.task_id)
        track_file = path.join(full_path, results.track_file)
        if path.isfile(track_file):
            remove(track_file)

    return row_deleted
