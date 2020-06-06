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

from .participant import Participant
import json
from collections import Counter
from os import path, makedirs
import jsonpickle
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from Defines import MAPOBJDIR
from airspace import AirspaceCheck
from calcUtils import string_to_seconds, sec_to_time
from db.tables import TblTaskResult
from formulas.libs.leadcoeff import LeadCoeff
from db.conn import db_session
from route import in_goal_sector, start_made_civl, tp_made_civl, tp_time_civl, get_shortest_path, distance_flown
from .waypointachieved import WaypointAchieved
from .notification import Notification


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

    def __init__(self, first_time=None, real_start_time=None, SSS_time=0, ESS_time=None, goal_time=None,
                 last_time=None, best_waypoint_achieved='No waypoints achieved', fixed_LC=0, lead_coeff=0,
                 distance_flown=0, last_altitude=0, track_id=None, track_file=None, **kwargs):
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
        self.result_type = 'lo'
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
        if self.notifications and sum(
                n.flat_penalty for n in self.notifications if not n.notification_type == 'jtg') > 0:
            return next(n.flat_penalty for n in self.notifications if not n.notification_type == 'jtg')
        else:
            return 0

    @property
    def jtg_penalty(self):
        if self.notifications and sum(n.flat_penalty for n in self.notifications if n.notification_type == 'jtg') > 0:
            return next(n for n in self.notifications if n.notification_type == 'jtg').flat_penalty
        else:
            return 0

    @property
    def percentage_penalty(self):
        if self.notifications and sum(n.percentage_penalty for n in self.notifications) > 0:
            return max(n.percentage_penalty for n in self.notifications)
        else:
            return 0

    @property
    def waypoints_made(self):
        if self.waypoints_achieved:
            return len(Counter(el.name for el in self.waypoints_achieved if not el.name == 'Left Launch'))
        else:
            return 0

    @classmethod
    def from_participant(cls, participant: Participant):
        """ Creates FlightResult obj from Participant obj.
        """
        if isinstance(participant, Participant):
            result = cls()
            result.as_dict().update(participant.as_dict())
            return result

    @staticmethod
    def from_fsdb(elem, task):
        """ Creates Results from FSDB FsParticipant element, which is in xml format.
            Unfortunately the fsdb format isn't published so much of this is simply an
            exercise in reverse engineering.
        """
        from pilot.notification import Notification
        offset = task.time_offset
        dep = task.formula.formula_departure
        arr = task.formula.formula_arrival

        result = FlightResult()
        result.ID = int(elem.get('id'))

        if elem.find('FsFlightData') is None and elem.find('FsResult') is None:
            '''pilot is abs'''
            print(f"ID {result.ID}: ABS")
            result.result_type = 'abs'
            return result
        elif elem.find('FsFlightData') is None or elem.find('FsFlightData').get('tracklog_filename') in [None, '']:
            print(f"ID {result.ID}: No track")
            print(f" - distance: {float(elem.find('FsResult').get('distance'))}")
            if float(elem.find('FsResult').get('distance')) > 0:
                '''pilot is min dist'''
                print(f"ID {result.ID}: Min Dist")
                result.result_type = 'mindist'
            else:
                '''pilot is dnf'''
                print(f"ID {result.ID}: DNF")
                result.result_type = 'dnf'
            return result

        if elem.find('FsFlightData') is not None:
            result.track_file = elem.find('FsFlightData').get('tracklog_filename')
        d = elem.find('FsFlightData')
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
        if elem.find('FsResult') is not None:
            '''reading flight data'''
            r = elem.find('FsResult')
            # result['rank'] = int(r.get('rank'))
            result.score = float(r.get('points'))
            result.total_distance = float(r.get('distance')) * 1000  # in meters
            result.distance_flown = float(r.get('real_distance')) * 1000  # in meters
            # print ("start_ss: {}".format(r.get('started_ss')))
            result.SSS_time = None if not r.get('started_ss') else string_to_seconds(r.get('started_ss')) - offset
            if result.SSS_time is not None:
                result.ESS_time = (None if not r.get('finished_ss')
                                   else string_to_seconds(r.get('finished_ss')) - offset)
                if task.SS_distance is not None and result.ESS_time is not None and result.ESS_time > 0:
                    result.speed = (task.SS_distance / 1000) / ((result.ESS_time - result.SSS_time) / 3600)
            else:
                result.ESS_time = None
            result.last_altitude = int(r.get('last_altitude_above_goal'))
            result.distance_score = float(r.get('distance_points'))
            result.time_score = float(r.get('time_points'))
            result.penalty = 0  # fsdb score is already decreased by penalties
            if not r.get('penalty_reason') == "":
                notification = Notification()
                if r.get('penalty') != "0":
                    notification.percentage_penalty = float(r.get('penalty'))
                else:
                    notification.flat_penalty = float(r.get('penalty_points'))
                notification.comment = r.get('penalty_reason')
                result.notifications.append(notification)
            if not r.get('penalty_reason_auto') == "":
                notification = Notification(notification_type='jtg',
                                            flat_penalty=r.get('penalty_points_auto'),
                                            comment=r.get('penalty_reason_auto'))
                result.notifications.append(notification)
            if dep == 'on':
                result.departure_score = float(r.get('departure_points'))
            elif dep == 'leadout':
                result.departure_score = float(r.get('leading_points'))
            else:
                result.departure_score = 0  # not necessary as it it initialized to 0
            result.arrival_score = float(r.get('arrival_points')) if arr != 'off' else 0
        return result

    @staticmethod
    def read(par_id: int, task_id: int):
        """reads result from database"""
        from db.tables import FlightResultView as R
        result = FlightResult()
        with db_session() as db:
            # get result details.
            q = db.query(R).filter_by(par_id=par_id, task_id=task_id).one()
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
    def check_flight(flight, task, airspace_obj=None, deadline=None, print=print):
        """ Checks a Flight object against the task.
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
        from .flightpointer import FlightPointer

        ''' Altitude Source: '''
        alt_source = 'GPS' if task.formula.scoring_altitude is None else task.formula.scoring_altitude
        alt_compensation = 0 if alt_source == 'GPS' or task.QNH == 1013.25 else task.alt_compensation

        '''initialize'''
        result = FlightResult()
        tolerance = task.formula.tolerance or 0
        min_tol_m = task.formula.min_tolerance or 0
        max_jump_the_gun = task.formula.max_JTG or 0  # seconds
        jtg_penalty_per_sec = 0 if max_jump_the_gun == 0 else task.formula.JTG_penalty_per_sec
        max_altitude = 0
        percentage_complete = 0

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
        result.landing_time = flight.landing_fix.rawtime
        result.landing_altitude = (flight.landing_fix.gnss_alt if alt_source == 'GPS'
                                   else flight.landing_fix.press_alt + alt_compensation)

        '''Stopped task managing'''
        if task.stopped_time:
            if not deadline:
                '''Using stop_time (stopped_time - score_back_time)'''
                deadline = task.stop_time
            goal_altitude = task.goal_altitude or 0
            glide_ratio = task.formula.glide_bonus or 0
            stopped_distance = 0
            stopped_altitude = 0
            total_distance = 0

        '''Turnpoint managing'''
        tp = FlightPointer(task)

        '''Airspace check managing'''
        airspace_plot = []
        infringements_list = []
        airspace_penalty = 0
        if task.airspace_check:
            if not airspace_obj and not deadline:
                print(f'We should not create airspace here')
                airspace_obj = AirspaceCheck.from_task(task)
        total_fixes = len(flight.fixes)
        for i in range(total_fixes - 1):
            # report percentage progress
            if int(i / len(flight.fixes) * 100) > percentage_complete:
                percentage_complete = int(i / len(flight.fixes) * 100)
                print(f"{percentage_complete}|% complete")

            '''Get two consecutive trackpoints as needed to use FAI / CIVL rules logic
            '''
            # start_time = tt.time()
            my_fix = flight.fixes[i]
            next_fix = flight.fixes[i + 1]
            alt = next_fix.gnss_alt if alt_source == 'GPS' else next_fix.press_alt + alt_compensation

            if alt > max_altitude:
                max_altitude = alt

            '''pilot flying'''
            if next_fix.rawtime < result.first_time:
                continue
            if result.landing_time and next_fix.rawtime > result.landing_time:
                '''pilot landed out'''
                # print(f'fix {i}: landed out - {next_fix.rawtime} - {alt}')
                break

            '''handle stopped task
            Pilots who were at a position between ESS and goal at the task stop time will be scored for their 
            complete flight, including the portion flown after the task stop time. 
            This is to remove any discontinuity between pilots just before goal and pilots who had just reached goal 
            at task stop time.
            '''
            if task.stopped_time and next_fix.rawtime > deadline and not tp.ess_done:
                result.still_flying_at_deadline = True
                break

            '''check if task deadline has passed'''
            if task.task_deadline < next_fix.rawtime:
                # Task has ended
                result.still_flying_at_deadline = True
                break

            '''check if pilot has arrived in goal (last turnpoint) so we can stop.'''
            if tp.made_all:
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

            '''launch turnpoint managing'''
            if tp.type == "launch":
                if task.check_launch == 'on':
                    # Set radius to check to 200m (in the task def it will be 0)
                    # could set this in the DB or even formula if needed..???
                    tp.next.radius = 200  # meters
                    if tp.next.in_radius(my_fix, tolerance, min_tol_m):
                        result.waypoints_achieved.append(create_waypoint_achieved(my_fix, tp, my_fix.rawtime, alt))
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
                    result.waypoints_achieved.append(
                        create_waypoint_achieved(my_fix, tp, time, alt))  # pilot has started
                    result.real_start_time = time
                    print(f"Pilot started SS at {sec_to_time(result.real_start_time)}")
                    result.best_distance_time = time
                    tp.move_to_next()

            elif pilot_can_restart(task, tp, my_fix, result):
                # print(f'time: {my_fix.rawtime}, start: {task.start_time} | Interval: {task.SS_interval} | my start: {result.real_start_time} | better_start: {pilot_get_better_start(task, my_fix.rawtime, result.SSS_time)} | can start: {pilot_can_start(task, tp, my_fix)} can restart: {pilot_can_restart(task, tp, my_fix, result)} | tp: {tp.name}')
                if start_made_civl(my_fix, next_fix, tp.last_made, tolerance, min_tol_m):
                    tp.pointer -= 1
                    time = int(round(tp_time_civl(my_fix, next_fix, tp.next), 0))
                    result.waypoints_achieved.pop()
                    result.waypoints_achieved.append(
                        create_waypoint_achieved(my_fix, tp, time, alt))  # pilot has started again
                    result.real_start_time = time
                    result.best_distance_time = time
                    print(f"Pilot restarted SS at {sec_to_time(result.real_start_time)}")
                    if lead_coeff:
                        lead_coeff.reset()
                    tp.move_to_next()

            if tp.start_done:
                '''Turnpoint managing'''
                if (tp.next.shape == 'circle'
                        and tp.next.type in ('endspeed', 'waypoint')):
                    if tp_made_civl(my_fix, next_fix, tp.next, tolerance, min_tol_m):
                        time = int(round(tp_time_civl(my_fix, next_fix, tp.next), 0))
                        result.waypoints_achieved.append(
                            create_waypoint_achieved(my_fix, tp, time, alt))  # pilot has achieved turnpoint
                        print(f"Pilot took {tp.name} at {sec_to_time(time)} at {alt}m")
                        tp.move_to_next()

                if tp.ess_done and tp.type == 'goal':
                    if ((tp.next.shape == 'circle' and tp_made_civl(my_fix, next_fix, tp.next, tolerance, min_tol_m))
                            or
                            (tp.next.shape == 'line' and (in_goal_sector(task, next_fix)))):
                        result.waypoints_achieved.append(
                            create_waypoint_achieved(next_fix, tp, next_fix.rawtime, alt))  # pilot has achieved goal
                        result.best_distance_time = next_fix.rawtime
                        print(f"Goal at {sec_to_time(next_fix.rawtime)}")
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

                if fix_dist_flown > result.distance_flown:
                    '''time of trackpoint with shortest distance to ESS'''
                    result.best_distance_time = next_fix.rawtime
                    '''updating best distance flown'''
                    # result.distance_flown = max(fix_dist_flown,
                    #                             task.partial_distance[tp.last_made_index])  # old approach
                    result.distance_flown = fix_dist_flown

                '''stopped task
                ∀p : p ∈ PilotsLandedBeforeGoal :
                    bestDistance p = max(minimumDistance, 
                                         taskDistance − min(∀trackp.pointi : shortestDistanceToGoal(trackp.pointi )−(trackp .pointi .altitude−GoalAltitude)*GlideRatio)) 
                ∀p :p ∈ PilotsReachedGoal : bestDistance p = taskDistance
                '''
                if task.stopped_time and glide_ratio and total_distance < task.opt_dist:
                    alt_over_goal = max(0, alt - goal_altitude)
                    if fix_dist_flown + glide_ratio * alt_over_goal > total_distance:
                        '''calculate total distance with glide bonus'''
                        stopped_distance = fix_dist_flown
                        stopped_altitude = alt
                        total_distance = min(fix_dist_flown + glide_ratio * alt_over_goal, task.opt_dist)

            '''Leading coefficient
            LC = taskTime(i)*(bestDistToESS(i-1)^2 - bestDistToESS(i)^2 )
            i : i ? TrackPoints In SS'''
            if lead_coeff and tp.start_done and not tp.ess_done:
                lead_coeff.update(result, my_fix, next_fix)

            '''Airspace Check'''
            if task.airspace_check and airspace_obj:
                # map_fix = [next_fix.rawtime, next_fix.lat, next_fix.lon, alt]
                plot, penalty = airspace_obj.check_fix(next_fix, alt)
                if plot:
                    # map_fix.extend(plot)
                    '''Airspace Infringement: check if we already have a worse one'''
                    airspace_name = plot[2]
                    infringement_type = plot[3]
                    dist = plot[4]
                    separation = plot[5]
                    infringements_list.append([next_fix, airspace_name, infringement_type, dist, penalty, separation])
                else:
                    ''''''
                    # map_fix.extend([None, None, None, None, None])
                # airspace_plot.append(map_fix)

        '''final results'''
        print("100|% complete")
        result.max_altitude = max_altitude
        result.last_altitude = 0 if 'alt' not in locals() else alt
        result.last_time = 0 if 'next_fix' not in locals() else next_fix.rawtime

        '''manage stopped tasks'''
        if task.stopped_time and result.still_flying_at_deadline:
            result.stopped_distance = stopped_distance
            result.stopped_altitude = stopped_altitude
            result.total_distance = total_distance

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
            # print(f'wayponts made: {result.waypoints_achieved}')
            if max_jump_the_gun > 0 and result.real_start_time < result.SSS_time:
                diff = result.SSS_time - result.real_start_time
                penalty = diff * jtg_penalty_per_sec
                # check
                print(f'jump the gun: {diff} - valid: {diff <= max_jump_the_gun} - penalty: {penalty}')
                comment = f"Jump the gun: {diff} seconds. Penalty: {penalty} points"
                result.notifications.append(Notification(notification_type='jtg',
                                                         flat_penalty=penalty, comment=comment))

            '''ESS Time'''
            if any(e.name == 'ESS' for e in result.waypoints_achieved):
                # result.ESS_time, ess_altitude = min([e[1] for e in result.waypoints_achieved if e[0] == 'ESS'])
                result.ESS_time, result.ESS_altitude = min([(x.rawtime, x.altitude) for x in result.waypoints_achieved
                                                            if x.name == 'ESS'], key=lambda t: t[0])
                result.speed = (task.SS_distance / 1000) / (result.ss_time / 3600)

                '''Distance flown'''
                ''' ?p:p?PilotsLandingBeforeGoal:bestDistancep = max(minimumDistance, taskDistance-min(?trackp.pointi shortestDistanceToGoal(trackp.pointi)))
                    ?p:p?PilotsReachingGoal:bestDistancep = taskDistance
                '''
                if any(e.name == 'Goal' for e in result.waypoints_achieved):
                    # result.distance_flown = distances2go[0]
                    result.distance_flown = task.opt_dist
                    result.goal_time, result.goal_altitude = min([(x.rawtime, x.altitude)
                                                                  for x in result.waypoints_achieved
                                                                  if x.name == 'Goal'], key=lambda t: t[0])
                    result.result_type = 'goal'
        if result.result_type != 'goal':
            print(f"Pilot landed after {result.distance_flown / 1000:.2f}km")

        result.best_waypoint_achieved = str(result.waypoints_achieved[-1].name) if result.waypoints_achieved else None

        if lead_coeff:
            result.fixed_LC = lead_coeff.summing

        if task.airspace_check:
            infringements, notifications, penalty = airspace_obj.get_infringements_result_new(infringements_list)
            result.infringements = infringements
            result.notifications.extend(notifications)
            # result.percentage_penalty = penalty
            # result.airspace_plot = airspace_plot
        return result

    def to_geojson_result(self, track, task, second_interval=5):
        """Dumps the flight to geojson format used for mapping.
        Contains tracklog split into pre SSS, pre Goal and post goal parts, thermals, takeoff/landing,
        result object, waypoints achieved, and bounds

        second_interval = resolution of tracklog. default one point every 5 seconds. regardless it will
                            keep points where waypoints were achieved.
        returns the Json string."""

        from mapUtils import result_to_geojson
        from db.tables import TblParticipant as p

        info = {'taskid': task.id, 'task_name': task.task_name, 'comp_name': task.comp_name}

        with db_session() as db:
            pilot_details = (db.query(p.name, p.nat, p.sex, p.glider)
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

    def save_tracklog_map_result_file(self, data, trackid, taskid):
        """save tracklog map result file in the correct folder as defined by DEFINES"""

        res_path = f"{MAPOBJDIR}tracks/{taskid}/"

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

    def create_result_dict(self):
        """ creates dict() with all information"""
        from result import TaskResult as R
        result = {x: getattr(self, x) for x in R.results_list if x in dir(self)}
        result['notifications'] = [n.__dict__ for n in self.notifications]
        result['waypoints_achieved'] = [dict(name=w.name, lat=w.lat, lon=w.lon, rawtime=w.rawtime,
                                             altitude=w.altitude) for w in self.waypoints_achieved]
        return result


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


def verify_all_tracks(task, lib, airspace=None, print=print):
    """ Gets in input:
            task:       Task object
            lib:        Formula library module"""
    from igc_lib import Flight

    print('getting tracks...')
    number_of_pilots = len(task.pilots)
    for track_number, pilot in enumerate(task.pilots, 1):
        print(f"{track_number}/{number_of_pilots}|track_counter")
        print(f"type: {pilot.result_type}")
        if pilot.result_type not in ('abs', 'dnf', 'mindist'):
            print(f"{pilot.ID}. {pilot.name}: ({pilot.track_file})")
            filename = path.join(task.file_path, pilot.track_file)
            '''load track file'''
            flight = Flight.create_from_file(filename)
            if flight:
                pilot.flight_notes = flight.notes
                if flight.valid:
                    '''check flight against task'''
                    pilot.check_flight(flight, task, airspace_obj=airspace, print=print)
                elif flight:
                    print(f'Error in parsing track: {[x for x in flight.notes]}')
    lib.process_results(task)


def adjust_flight_results(task, lib, airspace=None):
    """ Called when multi-start or elapsed time task was stopped.
        We need to check again and adjust results of pilots that flew more than task duration"""
    from igc_lib import Flight
    maxtime = task.duration
    for pilot in task.pilots:
        if pilot.SSS_time:
            last_time = pilot.SSS_time + maxtime
            if ((not pilot.ESS_time and pilot.best_distance_time > last_time)
                    or (pilot.ESS_time and pilot.ss_time > maxtime)):
                '''need to adjust pilot result'''
                filename = path.join(task.file_path, pilot.track_file)
                '''load track file'''
                flight = Flight.create_from_file(filename)
                adjusted = FlightResult.check_flight(flight, task, airspace_obj=None, deadline=last_time)
                pilot.result_type = adjusted.result_type
    lib.process_results(task)


def update_status(par_id: int, task_id: int, status=''):
    """Create or update pilot status ('abs', 'dnf', 'mindist')"""
    with db_session() as db:
        result = db.query(TblTaskResult).filter_by(par_id=par_id, task_id=task_id).first()
        if result:
            result.result_type = status
        else:
            result = TblTaskResult(par_id=par_id, task_id=task_id, result_type=status)
            db.add(result)
        db.flush()
        return result.track_id


def delete_track(trackid: int, delete_file=False):
    from trackUtils import get_task_fullpath
    from pathlib import Path
    from db.tables import TblTaskResult
    row_deleted = None
    with db_session() as db:
        track = db.query(TblTaskResult).filter_by(track_id=trackid).one_or_none()
        if track:
            if track.track_file is not None and delete_file:
                Path(get_task_fullpath(track.task_id), track.track_file).unlink(missing_ok=True)
            db.delete(track)
            row_deleted = True
    return row_deleted


def create_waypoint_achieved(fix, tp, time: int, alt: int):
    """creates a dictionary to be added to result.waypoints_achived"""
    return WaypointAchieved(trw_id=None, wpt_id=tp.next.wpt_id, name=tp.name, lat=fix.lat, lon=fix.lon,
                            rawtime=time, altitude=alt)


def get_task_results(task_id: int):
    from db.tables import FlightResultView as F, TblNotification as N, TblTrackWaypoint as W
    from pilot.notification import Notification
    from sqlalchemy.exc import SQLAlchemyError
    pilots = []
    with db_session() as db:
        results = db.query(F).filter_by(task_id=task_id).all()
        notifications = db.query(N).filter(N.track_id.in_([p.track_id for p in results])).all()
        achieved = db.query(W).filter(W.track_id.in_([p.track_id for p in results])).all()
        for row in results:
            pilot = FlightResult()
            row.populate(pilot)
            for el in [n for n in notifications if n.track_id == pilot.track_id]:
                n = Notification()
                el.populate(n)
                pilot.notifications.append(n)
            for el in [{k: getattr(w, k) for k in ['trw_id', 'wpt_id', 'name', 'rawtime', 'lat', 'lon', 'altitude']}
                       for w in achieved if w.track_id == pilot.track_id]:
                pilot.waypoints_achieved.append(WaypointAchieved(**el))
            pilots.append(pilot)
    return pilots


def update_all_results(task_id, pilots, session=None):
    """ get results to update from the list
        It is called from Task.check_all_tracks(), so only during Task full rescoring
        And from FSDB.add results.
        We are then deleting all present non admin Notification from database for results, as related to old scoring.
        """
    import itertools
    from db.tables import TblTaskResult as R, TblNotification as N, TblTrackWaypoint as W
    from dataclasses import asdict
    from sqlalchemy import and_
    from sqlalchemy.exc import SQLAlchemyError
    insert_mappings = []
    update_mappings = []
    notif_mappings = []
    achieved_mappings = []
    for pilot in pilots:
        res = pilot.result
        r = dict(track_id=pilot.track_id, task_id=task_id, par_id=pilot.par_id,
                 track_file=pilot.track_file, comment=pilot.comment)
        for key in [col for col in R.__table__.columns.keys() if col not in r.keys()]:
            if hasattr(res, key):
                r[key] = getattr(res, key)
        if r['track_id']:
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
        db.query(N).filter(and_(N.track_id.in_([r['track_id'] for r in update_mappings]),
                                        N.notification_type.in_(['jtg', 'airspace', 'track']))).delete(
            synchronize_session=False)
        db.query(W).filter(W.track_id.in_([r['track_id'] for r in update_mappings])).delete(
            synchronize_session=False)
        '''collect new ones'''
        for pilot in pilots:
            notif_mappings.extend([dict(track_id=pilot.track_id, **asdict(n))
                                   for n in pilot.notifications if not n.notification_type == 'admin'])
            achieved_mappings.extend([dict(track_id=pilot.track_id, **asdict(w))
                                      for w in pilot.waypoints_achieved])
        '''bulk insert'''
        if achieved_mappings:
            db.bulk_insert_mappings(W, achieved_mappings)
        if notif_mappings:
            db.bulk_insert_mappings(N, notif_mappings, return_defaults=True)
            db.flush()
            notif_list = filter(lambda i: i['notification_type'] in ['jtg', 'airspace'], notif_mappings)
            trackIds = set([i['track_id'] for i in notif_list])
            for idx in trackIds:
                pilot = next(p for p in pilots if p.track_id == idx)
                for n in filter(lambda i: i['track_id'] == idx, notif_list):
                    notif = next(el for el in pilot.notifications if el.comment == n['comment'])
                    notif.not_id = n['not_id']
    return True

