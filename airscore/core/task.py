"""
Task Library

contains
    Task class
        Class to represent Comp Task
    Task Methods:
        read:       reads task information from database and creates Task Obj
        to_db:      stores task info to database
        create results:     scores task and writes json results file
                            (mode='full' scores after task opt. route recalculation and checking of all tracks)
        from_fsdb:  reads task from FSDB file
        get_map_json and write_map_json - json files for task map

Use: from task import Task

Stuart Mackintosh - 2019

TO DO:
Add support for FAI Sphere ???
"""

from route import distance, polar, find_closest, cartesian2polar, polar2cartesian, calcBearing, opt_goal, opt_wp, \
    opt_wp_exit, opt_wp_enter, Turnpoint
from myconn import Database
from formula import Task_formula
from calcUtils import json, get_datetime, decimal_to_seconds, time_difference
from igc_lib import defaultdict
from pathlib import Path
import jsonpickle
import Defines


class Task(object):
    """Task definition, DB operations and length calculations
        Some Attributes:
        turnpoints: A list of Turnpoint objects.
        start_time: Raw time (seconds past midnight). The time the race starts.
                    The pilots must start at or after this time.
        task_deadline: Raw time (seconds past midnight). The time the race ends.
                  The pilots must finish the race at or before this time.
                  No credit is given for distance covered after this time.
        task_type: Race to goal, Elapsed time etc.
        opt_dist: optimised distance, calculated with method calculate_optimised_task_length
        opt_dist_to_SS: optimised distance to SSS, calculated with method calculate_optimised_task_length
        opt_dist_to_ESS: optimised distance to ESS from takeoff, calculated with method calculate_optimised_task_length
        SS_distance: optimised distance from SSS to ESS, calculated with method calculate_optimised_task_length

    methods:
        database
        read(task_id): read task from DB
        clear_waypoints: delete waypoints from tblTaskWaypoint
        update_waypoints:  write waypoints to tblTaskWaypoint
        update_task_distance: write distances to DB
        update_task_info: write task timmings and type to DB

        scoring/database
        update_totals: update total statistics in DB (total distance flown, fastest time etc.)
        update_quality: update quality values in DB
        update_points_allocation: update available point values in DB

        creation:
        create_from_xctrack_file: read task from xctrack file.
        create_from_lkt_file: read task from LK8000 file, old code probably needs fixing, but unlikely to be used now we have xctrack
        from_fsdb: read fsdb xml file, create task object

        task distance:
        calculate_task_length: calculate non optimised distances.
        calculate_optimised_task_length_old: find optimised distances and waypoints. old perl method, no longer used
        calculate_optimised_task_length: find optimised distances and waypoints.
        distances_to_go: calculates distance from each waypoint to goal
    """

    def __init__(self, task_id=None, task_type=None, start_time=None, task_deadline=None,
                 stopped_time=None, check_launch='off'):
        self.task_id = task_id
        self.task_type = task_type  # 'race', 'elapsed_time'
        self.start_time = start_time
        self.task_deadline = task_deadline  # seconds from midnight: task deadline
        self.stopped_time = stopped_time  # seconds from midnight: time task was stopped (TaskStopAnnouncementTime).
        self.check_launch = check_launch  # check launch flag. whether we check that pilots leave from launch.
        self.comp_id = None
        self.comp_code = None
        self.comp_name = None
        self.comp_site = None
        self.comp_class = None
        self.date = None  # in datetime.date (Y-m-d) format
        self.task_name = None
        self.task_num = None  # task n#
        self.window_open_time = None  # seconds from midnight: takeoff window opening time
        self.window_close_time = None  # seconds from midnight: not managed yet
        self.start_close_time = None
        self.SS_interval = 0  # seconds: Interval among start gates when more than one
        self.start_iteration = None  # number of start iterations: 0 is indefinite up to start close time
        self.opt_dist = 0
        self.opt_dist_to_SS = 0
        self.opt_dist_to_ESS = 0
        self.SS_distance = 0
        self.dist_validity = 0.000
        self.time_validity = 0.000
        self.launch_validity = 0.000
        self.stop_validity = 1.000
        self.day_quality = 0.000
        self.distance = 0  # non optimised distance
        self.turnpoints = []  # list of Turnpoint objects
        self.optimised_turnpoints = []  # fixes on cylinders for opt route
        self.optimised_legs = []  # opt distance between cylinders
        self.partial_distance = []  # distance from launch to waypoint
        self.legs = []  # non optimised legs
        self.stats = dict()  # STATIC scored task statistics, used when importing results from JSON / FSDB files
        self.pilots = []  # scored task results
        self.comment = None
        self.time_offset = 0  # seconds
        self.launch_valid = None
        self.locked = False
        self.task_path = None
        self.comp_path = None
        self.track_source = None
        self.formula = Task_formula.read(self.id) if self.id else None

    def __setattr__(self, attr, value):
        from calcUtils import get_date
        import datetime
        property_names = [p for p in dir(Task) if isinstance(getattr(Task, p), property)]
        if attr == 'date':
            if type(value) is str:
                value = get_date(value)
            elif isinstance(value, datetime.datetime):
                value = value.date()
        if attr not in property_names:
            self.__dict__[attr] = value

    def __str__(self):
        out = ''
        out += 'Task:'
        out += f'{self.comp_name} - {self.task_name} | Date: {self.date_str} \n'
        out += f'{self.comment} \n'
        for wpt in self.turnpoints:
            out += f'  {wpt.name}  {wpt.type}  {round(wpt.radius / 1000, 2)} km \n'
        out += f'Task Opt. Distance: {round(self.opt_dist / 1000, 2)} Km \n'
        return out

    def as_dict(self):
        return self.__dict__

    @property
    def results(self):
        return [pilot.result for pilot in self.pilots]

    @property
    def id(self):
        return self.task_id

    @property
    def date_str(self):
        return self.date.strftime("%Y-%m-%d")

    @property
    def task_code(self):
        return 'T' + str(self.task_num)

    @property
    def file_path(self):
        if not self.comp_path:
            return
        if not self.task_path:
            self.create_path()
        from os import path as p
        from Defines import FILEDIR
        return p.join(FILEDIR, self.comp_path, self.task_path.lower())

    # @property
    # def last_start_time(self):
    #     return self.stats['last_SS'] if self.stats else 0

    @property
    def tolerance(self):
        return self.formula.tolerance if self.formula else None

    @property
    def goal_altitude(self):
        if self.turnpoints:
            return self.turnpoints[-1].altitude
        else:
            return None

    @property
    def departure(self):
        return self.formula.departure if self.formula else None

    @property
    def arrival(self):
        return self.formula.arrival if self.formula else None

    @property
    def arr_alt_bonus(self):
        return self.formula.arr_alt_bonus if self.formula else None

    @property
    def stop_time(self):
        # seconds from midnight, task stopTime
        if not (self.stopped_time and self.formula.score_back_time):
            return 0
        if self.comp_class == 'PG':
            '''
            We need to calculate stopTime from announcingTime
            In paragliding the score-back time is set as part of the competition parameters
            (see section 5.7).
            taskStopTime = taskStopAnnouncementTime − competitionScoreBackTime
            '''
            return max(0, self.stopped_time - self.formula.score_back_time)
        elif self.comp_class == 'HG':
            '''
            In hang-gliding, stopped tasks are “scored back” by a time that is determined
            by the number of start gates and the start gate interval:
            The task stop time is one start gate interval, or 15 minutes in case of a
            single start gate, before the task stop announcement time.
            numberOfStartGates = 1 : taskStopTime = taskStopAnnouncementTime − 15min.
            numberOfStartGates > 1 : taskStopTime = taskStopAnnouncementTime − startGateInterval.
            '''
            return ((self.stopped_time - self.formula.score_back_time)
                    if not self.SS_interval
                    else (self.stopped_time - self.SS_interval))

    @property
    def duration(self):
        # seconds from midnight, elapsed time from stop_time to last_SS_time
        if not self.stopped_time:
            return 0
        if self.comp_class == 'PG':
            '''Need to distinguish wether we have multiple start or elapsed time'''
            if (self.task_type == 'elapsed time' or self.SS_interval) and self.max_ss_time:
                return self.stop_time - self.max_ss_time
            else:
                return self.stop_time - self.start_time
        elif self.comp_class == 'HG':
            # TODO is it so simple in HG? Need to check
            return self.stop_time - self.start_time

    @property
    def ftv_validity(self):
        if not self.formula or not self.day_quality or not self.max_score:
            return 0
        if self.formula.overall_validity == 'ftv':
            return (round(self.max_score / 1000, 4) if self.formula.formula_type == 'pwc'
                    else round(self.day_quality, 4))
        else:
            return self.day_quality

    ''' * Statistic Properties *'''

    ''' list of present pilots' results'''

    @property
    def valid_results(self):
        return [pilot.result for pilot in self.pilots if pilot.result_type not in ('abs', 'dnf')]

    ''' pilots stats'''

    @property
    def pilots_present(self):
        return len([p for p in self.pilots if p.result_type != 'abs'])

    @property
    def pilots_launched(self):
        return len(self.valid_results)

    @property
    def pilots_ss(self):
        return len([p for p in self.valid_results if p.SSS_time])

    @property
    def pilots_ess(self):
        return len([p for p in self.valid_results if p.ESS_time])

    @property
    def pilots_goal(self):
        return len([p for p in self.valid_results if p.goal_time])

    # pilots already landed at task deadline / stop time
    @property
    def pilots_landed(self):
        return len([p for p in self.valid_results if p.last_altitude == 0 or p.result_type == 'goal'])

    ''' distance stats'''

    @property
    def tot_distance_flown(self):
        if self.formula.min_dist and self.pilots_launched:
            return sum([p.distance_flown for p in self.valid_results if p.distance_flown])
        else:
            return 0

    @property
    def tot_dist_over_min(self):
        if self.formula.min_dist and self.pilots_launched:
            return sum([max(p.distance_flown - self.formula.min_dist, 0) for p in self.valid_results])
        else:
            return 0

    @property
    def std_dev_dist(self):
        from statistics import stdev
        if self.formula.min_dist and self.pilots_launched:
            return stdev([max(p.distance_flown, self.formula.min_dist) for p in self.valid_results])
        else:
            return 0

    @property
    def max_distance_flown(self):
        if self.formula.min_dist and self.pilots_launched:
            return max(max(p.distance_flown for p in self.valid_results), self.formula.min_dist)
        else:
            return 0

    @property
    def max_distance(self):
        if self.formula.min_dist and self.pilots_launched:
            # Flight_result.distance = max(distance_flown, total_distance)
            return max(max(p.distance for p in self.valid_results), self.formula.min_dist)
        else:
            return 0

    '''time stats'''

    @property
    def min_dept_time(self):
        if self.pilots_ss:
            return min(p.real_start_time for p in self.valid_results if p.real_start_time and p.real_start_time > 0)
        else:
            return None

    @property
    def max_dept_time(self):
        if self.pilots_ss:
            return max(p.real_start_time for p in self.valid_results if p.real_start_time and p.real_start_time > 0)
        else:
            return None

    @property
    def min_ss_time(self):
        if self.pilots_ss:
            return min(p.SSS_time for p in self.valid_results if p.SSS_time and p.SSS_time > 0)
        else:
            return None

    @property
    def max_ss_time(self):
        if self.pilots_ss:
            return max(p.SSS_time for p in self.valid_results if p.SSS_time and p.SSS_time > 0)
        else:
            return None

    @property
    def min_ess_time(self):
        if self.pilots_ess:
            return min(p.ESS_time for p in self.valid_results if p.ESS_time and p.ESS_time > 0)
        else:
            return None

    @property
    def max_ess_time(self):
        if self.pilots_ess:
            return max(p.ESS_time for p in self.valid_results if p.ESS_time and p.ESS_time > 0)
        else:
            return None

    @property
    def fastest(self):
        if self.pilots_ess:
            return min(p.ss_time for p in self.valid_results if p.ESS_time and p.ESS_time > 0)
        else:
            return None

    @property
    def fastest_in_goal(self):
        if self.pilots_goal:
            return min(p.ss_time for p in self.valid_results if p.goal_time and p.goal_time > 0)
        else:
            return None

    @property
    def max_time(self):
        if self.pilots_launched:
            return max(p.last_time for p in self.valid_results if p.last_time)
        else:
            return None

    @property
    def tot_flight_time(self):
        if self.pilots_launched:
            return sum([p.flight_time for p in self.valid_results if p.flight_time])
        else:
            return None

    ''' scoring stats'''

    @property
    def min_lead_coeff(self):
        if len([p for p in self.valid_results if p.lead_coeff]) > 0:
            return min(p.lead_coeff for p in self.valid_results if p.lead_coeff is not None and p.lead_coeff > 0)
        else:
            return None

    @property
    def max_score(self):
        if len([p for p in self.valid_results if p.score]) > 0:
            return max(p.score for p in self.valid_results if p.score)
        else:
            return None

    @staticmethod
    def read(task_id):
        """Reads Task from database
        takes tasPk as argument"""
        from db_tables import TaskObjectView as T, TaskWaypointView as W

        if not (type(task_id) is int and task_id > 0):
            print("task not present in database ", task_id)
            return None

        task = Task(task_id)
        '''get task from db'''
        with Database() as db:
            # get the task details.
            t = db.session.query(T)
            w = db.session.query(W)
            db.populate_obj(task, t.get(task_id))
            tps = w.filter(W.task_id == task_id).order_by(W.partial_distance)
        '''populate turnpoints'''
        for tp in tps:
            turnpoint = Turnpoint(tp.lat, tp.lon, tp.radius, tp.type.strip(),
                                  tp.shape, tp.how, tp.altitude, tp.name,
                                  tp.description, tp.id)
            task.turnpoints.append(turnpoint)
            s_point = polar(lat=tp.ssr_lat, lon=tp.ssr_lon)
            task.optimised_turnpoints.append(s_point)
            if tp.partial_distance is not None:  # this will be None in DB before we optimise route, but we append to this list so we should not fill it with Nones
                task.partial_distance.append(tp.partial_distance)

        '''check if we already have a filepath for task'''
        if task.task_path is None or '':
            task.create_path()

        return task

    def create_path(self, path=None):
        """create filepath from # and date if not given
            and store it in database"""
        from db_tables import tblTask as T

        if path:
            self.task_path = path
        elif self.task_num and self.date:
            self.task_path = '_'.join([('t' + str(self.task_num)), self.date.strftime('%Y%m%d')])
        else:
            return

        with Database() as db:
            q = db.session.query(T).get(self.id)
            q.tasPath = self.task_path
            db.session.commit()

    def create_results(self, status=None, mode='default'):
        """
            Create Scoring
            - if necessary, recalculates all tracks (stopped task, changed task settings)
            - gets info about formula, pilots results
            - calculates scores
            - creates a json file
            - adds json file to database

            Inputs:
            - status:   str - 'provisional', 'final', 'official' ...
            - mode:     str - 'default'
                              'full'    recalculates all tracks
        """
        from result import create_json_file

        ''' retrieve scoring formula library'''
        lib = self.formula.get_lib()

        if mode == 'full' or self.stopped_time:
            # TODO: check if we changed task, or we had new tracks, after last results generation
            #       If this is the case we should not need to re-score unless especially requested
            '''Task Full Rescore
                - recalculate Opt. route
                - check all tracks'''
            print(f" - FULL Mode -")
            print(f"Calculating task optimised distance...")
            self.calculate_task_length()
            self.calculate_optimised_task_length()
            print(f"Storing calculated values to database...")
            self.update_task_distance()
            print(f"Task Opt. Route: {round(self.opt_dist / 1000, 4)} Km")
            print(f"Processing pilots tracks...")
            self.check_all_tracks(lib)

        else:
            ''' get pilot list and results'''
            self.get_results(lib)

        if self.pilots_launched == 0:
            print(f"Task (ID {self.id}) has no results yet")
            return 0

        ''' Calculates task result'''
        print(f"Calculating point allocation...")
        lib.points_allocation(self)

        '''create result elements from task, formula and results objects'''
        elements = self.create_json_elements()
        ref_id = create_json_file(comp_id=self.comp_id, task_id=self.id,
                                  code='_'.join([self.comp_code, self.task_code]), elements=elements, status=status)
        return ref_id

    def create_json_elements(self):
        """ returns Dict with elements to generate json file"""
        from result import Task_result as R
        from compUtils import read_rankings

        pil_list = sorted([p for p in self.pilots if p.result_type not in ['dnf', 'abs']],
                          key=lambda k: k.score, reverse=True)
        pil_list += [p for p in self.pilots if p.result_type == 'dnf']
        pil_list += [p for p in self.pilots if p.result_type == 'abs']

        info = {x: getattr(self, x) for x in R.info_list if x in dir(self)}
        formula = {x: getattr(self.formula, x) for x in R.formula_list if x in dir(self.formula)}
        stats = {x: getattr(self, x) for x in R.stats_list if x in dir(self)}
        route = []
        for idx, tp in enumerate(self.turnpoints):
            wpt = {x: getattr(tp, x) for x in R.route_list if x in dir(tp)}
            wpt['cumulative_dist'] = self.partial_distance[idx]
            route.append(wpt)
        results = []
        for pil in pil_list:
            res = pil.create_result_dict()
            results.append(res)
        rankings = read_rankings(self.comp_id)
        # rankings = {}
        if not rankings or len(rankings) == 0:
            ''' create an overall ranking'''
            rankings.update({'overall': [cert for cert in set([p.info.glider_cert for p in self.pilots])]})

        '''create json file'''
        result = {'info': info,
                  'route': route,
                  'results': results,
                  'formula': formula,
                  'stats': stats,
                  'rankings': rankings
                  }
        return result

    def is_valid(self):
        """In stopped task, check if duration is enough to be valid"""
        if self.pilots_launched == 0:
            print(f'Tracks (Task ID {self.id}) have not been checked yet or stats have not been updated.')
            return False
        if not self.stopped_time:
            print(f'Task (ID {self.id}) has not been stopped.')
            return True

        min_task_duration = self.formula.validity_min_time
        if self.comp_class == 'PG':
            '''
            In paragliding, a stopped task will be scored if the flying time was one hour or more.
            For Race to Goal tasks, this means that the Task Stop Time must be one hour or more
            after the race start time.
            minimumTime = 60 min .
            typeOfTask = RaceToGoal ∧ numberOfStartGates = 1:
                taskStopTime − startTime < minimumTime : taskValidity = 0
            TypeOfTask ≠ RaceToGoal ∨ numberOfStartGates > 1:
                taskStopTime − max(∀p :p ∈ StartedPilots :startTime p ) < minimumTime : taskValidity = 0
            '''
            if min_task_duration is None:
                min_task_duration = 3600  # 60 min default for paragliding

        elif self.comp_class == 'HG':
            '''
            In hang gliding, a stopped task can only be scored if either a pilot reached goal
            or the race had been going on for a certain minimum time.
            The minimum time depends on whether the competition is the Women’s World Championship or not.
            The race start time is defined as the time when the first valid start was taken by a competition pilot.
            typeOfCompetition = Women's : minimumTime = 60min.
            typeOfCompetition ≠ Women's : minimumTime = 90min.
            taskStopTime − timeOfFirstStart < minimumTime ∧ numberOfPilotsInGoal(taskStopTime) = 0 : taskValidity = 0
            '''
            if self.pilots_goal:
                return True
            if min_task_duration is None:
                min_task_duration = 3600 * 1.5  # 90 min default for hg

        '''is task valid?'''
        if self.duration < min_task_duration:
            return False
        return True

    def check_all_tracks(self, lib=None):
        """ checks all igc files against Task and creates results """
        from flight_result import verify_all_tracks, adjust_flight_results
        from pilot import update_all_results

        if not lib:
            '''retrieve scoring formula library'''
            lib = self.formula.get_lib()

        ''' get pilot and tracks list'''
        self.get_results()

        ''' manage Stopped Task    '''
        print(f'stopped time: {self.stopped_time}')
        if self.stopped_time:
            print(f'We are executing Stopped Task Routine')
            if self.comp_class == 'PG':
                '''
                If (class == 'PG' and (SS_Interval or type == 'ELAPSED TIME')
                    We cannot check tracks just once.
                    We need to find last_SS_time and then check again tracks until duration == stopTime - last_SS_time

                We need to calculate stopTime from announcingTime'''
                '''     In paragliding the score-back time is set as part of the competition parameters
                        (see section 5.7).
                        taskStopTime = taskStopAnnouncementTime − competitionScoreBackTime
                        In paragliding, a stopped task will be scored if the flying time was one hour or more.
                        For Race to Goal tasks, this means that the Task Stop Time must be one hour or more
                        after the race start time. For all other tasks, in order for them to be scored,
                        the task stop time must be one hour or more after the last pilot started.
                        minimumTime = 60 min .
                        typeOfTask = RaceToGoal ∧ numberOfStartGates = 1:
                            taskStopTime − startTime < minimumTime : taskValidity = 0
                        TypeOfTask ≠ RaceToGoal ∨ numberOfStartGates > 1:
                            taskStopTime − max(∀p :p ∈ StartedPilots :startTime p ) < minimumTime : taskValidity = 0
                '''
                if not self.is_valid():
                    return f'task duration is not enough, task with id {self.id} is not valid, scoring is not needed'

                # min_task_duration = 3600
                # last_time = self.stopped_time - self.formula.score_back_time
                verify_all_tracks(self, lib)

                if self.task_type == 'elapsed time' or self.SS_interval:
                    '''need to check track and get last_start_time'''
                    # self.stats.update(lib.task_totals(self.id))
                    # duration = last_time - self.last_start_time
                    if not self.is_valid():
                        return f'duration is not enough for all pilots, task with id {self.id} is not valid, ' \
                               f'scoring is not needed.'
                    adjust_flight_results(self, lib)

            elif self.comp_class == 'HG':
                ''' In hang-gliding, stopped tasks are “scored back” by a time that is determined
                    by the number of start gates and the start gate interval:
                    The task stop time is one start gate interval, or 15 minutes in case of a
                    single start gate, before the task stop announcement time.
                    numberOfStartGates = 1 : taskStopTime = taskStopAnnouncementTime − 15min.
                    numberOfStartGates > 1 : taskStopTime = taskStopAnnouncementTime − startGateInterval.
                    In hang gliding, a stopped task can only be scored if either a pilot reached goal
                    or the race had been going on for a certain minimum time.
                    The minimum time depends on whether the competition is the Women’s World Championship or not.
                    The race start time is defined as the time when the first valid start was taken by a competition pilot.
                    typeOfCompetition = Women's : minimumTime = 60min.
                    typeOfCompetition ≠ Women's : minimumTime = 90min.
                    taskStopTime − timeOfFirstStart < minimumTime ∧ numberOfPilotsInGoal(taskStopTime) = 0 : taskValidity = 0
                '''
                # TODO It's not really clear if in elapsed time or multiple start, minimum duration like PG is applied

                if not self.is_valid():
                    return f'task duration is not enough, task with id {self.id} is not valid, scoring is not needed'

                verify_all_tracks(self, lib)

        else:
            '''get all results for the task'''
            verify_all_tracks(self, lib)

        '''store results to database'''
        print(f"updating database with new results...")
        update_all_results(self.task_id, self.pilots)

        lib.process_results(self)

    def get_results(self, lib=None):
        """ Loads all Pilot obj. into Task obj."""
        from db_tables import FlightResultView as F
        from sqlalchemy.exc import SQLAlchemyError
        from pilot import Pilot

        pilots = []

        with Database() as db:
            try:
                results = db.session.query(F).filter(F.task_id == self.task_id).all()
                for row in results:
                    pilot = Pilot.create(task_id=self.task_id)
                    db.populate_obj(pilot.result, row)
                    db.populate_obj(pilot.info, row)
                    db.populate_obj(pilot.track, row)
                    pilots.append(pilot)
            except SQLAlchemyError:
                print('DB Error retrieving task results')
                db.session.rollback()
                return
        self.pilots = pilots
        if lib:
            '''prepare results for scoring'''
            lib.process_results(self)
        return pilots

    def update_task_distance(self):
        from db_tables import tblTask as T, tblTaskWaypoint as W
        with Database() as db:
            '''add optimised and total distance to task'''
            q = db.session.query(T)
            t = q.get(self.id)
            t.tasDistance = self.distance
            t.tasShortRouteDistance = self.opt_dist
            t.tasSSDistance = self.SS_distance
            t.tasEndSSDistance = self.opt_dist_to_ESS
            t.tasStartSSDistance = self.opt_dist_to_SS
            db.session.commit()

            '''add opt legs to task wpt'''
            w = db.session.query(W)
            for idx, tp in enumerate(self.turnpoints):
                sr = self.optimised_turnpoints[idx]
                wpt = w.get(tp.id)
                wpt.ssrLatDecimal = sr.lat
                wpt.ssrLongDecimal = sr.lon
                wpt.ssrCumulativeDist = self.partial_distance[idx]
            db.session.commit()

    def update_task_info(self):
        from datetime import datetime as dt
        from db_tables import tblTask as T
        from calcUtils import sec_to_time

        start_time = sec_to_time(self.start_time + self.time_offset)
        task_deadline = sec_to_time(self.task_deadline + self.time_offset)
        task_start = sec_to_time(self.window_open_time + self.time_offset)
        start_close_time = sec_to_time(self.start_close_time + self.time_offset)
        start_interval = int(self.SS_interval / 60)
        task_type = self.task_type.lower()

        with Database() as db:
            q = db.session.query(T).get(self.id)
            date = q.date
            q.tasStartTime = dt.combine(date, start_time)
            q.tasFinishTime = dt.combine(date, task_deadline)
            q.tasTaskStart = dt.combine(date, task_start)
            q.tasStartCloseTime = dt.combine(date, start_close_time)
            q.tasSSInterval = start_interval
            q.tasTaskType = task_type
            db.session.commit()

    def to_db(self, session=None):
        """Inserts new task or updates existent one"""
        # TODO update part, now it just inserts new Task and new Waypoints
        from db_tables import tblTask as T, tblTaskWaypoint as W
        from sqlalchemy.exc import SQLAlchemyError
        from datetime import datetime
        from calcUtils import sec_to_time

        task_start = datetime.combine(self.date, sec_to_time(self.window_open_time))
        launch_close = None if self.window_close_time is None else datetime.combine(self.date,
                                                                                    sec_to_time(self.window_close_time))
        deadline = datetime.combine(self.date, sec_to_time(self.task_deadline))
        start_time = None if self.start_time is None else datetime.combine(self.date, sec_to_time(self.start_time))
        start_close = None if self.start_close_time is None else datetime.combine(self.date,
                                                                                  sec_to_time(self.start_close_time))
        stopped_time = None if self.stopped_time is None else datetime.combine(self.date,
                                                                               sec_to_time(self.stopped_time))

        with Database(session) as db:
            try:
                task = T(tasName=self.task_name, comPk=self.comp_id, tasDate=self.date, tasNum=self.task_num,
                         tasTaskStart=task_start, tasFinishTime=deadline, tasLaunchClose=launch_close,
                         tasStartTime=start_time,
                         tasStartCloseTime=start_close, tasStoppedTime=stopped_time, tasDistance=self.distance,
                         tasShortRouteDistance=self.opt_dist, tasStartSSDistance=self.opt_dist_to_SS,
                         tasEndSSDistance=self.opt_dist_to_ESS, tasSSDistance=self.SS_distance,
                         tasSSInterval=self.SS_interval,
                         tasLaunchValid=self.launch_valid, tasComment=self.comment)
                db.session.add(task)
                db.session.flush()
                self.task_id = task.tasPk
                wpts = []
                for idx, tp in enumerate(self.turnpoints):
                    opt_lat, opt_lon, cumulative_dist = None, None, None
                    if len(self.optimised_turnpoints) > 0:
                        opt_lat, opt_lon = self.optimised_turnpoints[idx].lat, self.optimised_turnpoints[idx].lon
                    if len(self.partial_distance) > 0:
                        cumulative_dist = self.partial_distance[idx]
                    wpt = W(tasPk=self.id, tawNumber=tp.id, tawName=tp.name, tawLat=tp.lat, tawLon=tp.lon,
                            tawAlt=tp.altitude,
                            tawDesc=tp.description, tawType=tp.type, tawHow=tp.how, tawShape=tp.shape,
                            tawRadius=tp.radius,
                            ssrLatDecimal=opt_lat, ssrLongDecimal=opt_lon, ssrCumulativeDist=cumulative_dist)
                    wpts.append(wpt)
                db.session.bulk_save_objects(wpts)

            except SQLAlchemyError:
                print(f'Task storing error')
                db.session.rollback()
                return None

    def update_from_xctrack_file(self, filename):
        """ Updates Task from xctrack file, which is in json format.
        """
        from compUtils import get_wpts
        from calcUtils import string_to_seconds

        offset = 0
        task_file = filename

        # turnpoints = []
        with open(task_file, encoding='utf-8') as json_data:
            # a bit more checking..
            print("file: ", task_file)
            try:
                t = json.load(json_data)
            except:
                print("file is not a valid JSON object")
                exit()

        startopenzulu = t['sss']['timeGates'][0]
        deadlinezulu = t['goal']['deadline']

        self.start_time = string_to_seconds(startopenzulu)
        self.task_deadline = string_to_seconds(deadlinezulu)

        '''check task start and start close times are ok for new start time
        we will check to be at least 1 hour before and after'''
        if not self.window_open_time or self.start_time - self.window_open_time < 3600:
            self.window_open_time = self.start_time - 3600
        if not self.start_close_time or self.start_close_time - self.start_time < 3600:
            self.start_close_time = self.start_time + 3600

        if t['sss']['type'] == 'ELAPSED-TIME':
            self.task_type = 'ELAPSED TIME'
        else:
            self.task_type = 'RACE'
            '''manage multi start'''
            self.SS_interval = 0
            if len(t['sss']['timeGates']) > 1:
                second_start = string_to_seconds(t['sss']['timeGates'][1])
                self.SS_interval = int((second_start - self.start_time) / 60)  # interval in minutes
                self.start_close_time = int(
                    self.start_time + len(t['sss']['timeGates']) * (second_start - self.start_time)) - 1

        print('xct start:       {} '.format(self.start_time))
        print('xct deadline:    {} '.format(self.task_deadline))

        waypoint_list = get_wpts(self.id)
        print('n. waypoints: {}'.format(len(t['turnpoints'])))

        for i, tp in enumerate(t['turnpoints']):
            waytype = "waypoint"
            shape = "circle"
            how = "entry"  # default entry .. looks like xctrack doesn't support exit cylinders apart from SSS
            wpID = waypoint_list[tp["waypoint"]["name"]]
            # wpNum = i+1

            if i < len(t['turnpoints']) - 1:
                if 'type' in tp:
                    if tp['type'] == 'TAKEOFF':
                        waytype = "launch"  # live
                        # waytype = "start"  # aws
                        how = "exit"
                    elif tp['type'] == 'SSS':
                        waytype = "speed"
                        if t['sss']['direction'] == "EXIT":  # get the direction form the SSS section
                            how = "exit"
                    elif tp['type'] == 'ESS':
                        waytype = "endspeed"
            else:
                waytype = "goal"
                if t['goal']['type'] == 'LINE':
                    shape = "line"

            turnpoint = Turnpoint(tp['waypoint']['lat'], tp['waypoint']['lon'], tp['radius'], waytype, shape, how)
            turnpoint.name = tp["waypoint"]["name"]
            turnpoint.rwpPk = wpID
            self.turnpoints.append(turnpoint)

    @staticmethod
    def create_from_xctrack_file(filename):
        """ Creates Task from xctrack file, which is in json format.
        """

        offset = 0

        task_file = filename

        turnpoints = []
        with open(task_file, encoding='utf-8') as json_data:
            # a bit more checking..
            print("file: ", task_file)
            try:
                t = json.load(json_data)
            except:
                print("file is not a valid JSON object")
                exit()

        startopenzulu = t['sss']['timeGates'][0]
        deadlinezulu = t['goal']['deadline']
        task_type = 'RACE' if t['sss']['type'] == 'RACE' else 'ELAPSED TIME'

        startzulu_split = startopenzulu.split(":")  # separate hours, minutes and seconds.
        deadlinezulu_split = deadlinezulu.split(":")  # separate hours, minutes and seconds.

        start_time = (int(startzulu_split[0]) + offset) * 3600 + int(startzulu_split[1]) * 60
        task_deadline = (int(deadlinezulu_split[0]) + offset) * 3600 + int(deadlinezulu_split[1]) * 60

        for tp in t['turnpoints'][:-1]:  # loop through all waypoints except last one which is always goal
            waytype = "waypoint"
            shape = "circle"
            how = "entry"  # default entry .. looks like xctrack doesn't support exit cylinders apart from SSS

            if 'type' in tp:
                if tp['type'] == 'TAKEOFF':
                    waytype = "launch"  # live
                    # waytype = "start"  #aws
                    how = "exit"
                if tp['type'] == 'SSS':
                    waytype = "speed"
                    if t['sss']['direction'] == "EXIT":  # get the direction form the SSS section
                        how = "exit"
                if tp['type'] == 'ESS':
                    waytype = "endspeed"
            turnpoint = Turnpoint(tp['waypoint']['lat'], tp['waypoint']['lon'], tp['radius'], waytype, shape, how)
            turnpoints.append(turnpoint)

        # goal - last turnpoint
        tp = t['turnpoints'][-1]
        waytype = "goal"
        if t['goal']['type'] == 'LINE':
            shape = "line"

        turnpoint = Turnpoint(tp['waypoint']['lat'], tp['waypoint']['lon'], tp['radius'], waytype, shape, how)
        turnpoints.append(turnpoint)

        task = Task(turnpoints, start_time, task_deadline, task_type)
        task.calculate_optimised_task_length()

        return task

    @staticmethod
    def create_from_json(task_id, filename=None):
        """ Creates Task from JSON task file.
            If filename is empty, it gets the active one
            Inputs:
                task_id     int: task ID
                filename    str: (opt.) json filename

        """
        from os import path as p
        # from result         import get_task_json  # !!! this function does not exist in result.py
        from flight_result import Flight_result
        from pilot import Pilot
        from Defines import RESULTDIR
        from pprint import pprint as pp

        if not filename or not p.isfile(filename):
            '''we get the active json file'''
            filename = get_task_json_filename(task_id)

        if not filename:
            print(f"There's no active json file for task {task_id}, or given filename does not exists")
            return None

        print(f"task {task_id} json file: {filename}")

        with open(p.join(RESULTDIR, filename), encoding='utf-8') as json_data:
            # a bit more checking..
            try:
                t = jsonpickle.decode(json_data.read())
            except:
                print("file is not a valid JSON object")
                return None

        # pp(t)

        task = Task(task_id)
        # task.__dict__.update(t['info'])
        ''' get task info'''
        for key, value in t['info'].items():
            if hasattr(task, key):
                setattr(task, key, value)
        ''' get task stats'''
        # I need to get only the ones we do not calculate from results
        for key, value in t['stats'].items():
            if hasattr(task, key):
                setattr(task, key, value)
        # task.stats.update(t['stats'])
        ''' get task formula'''
        task.formula = Task_formula.from_dict(t['formula'])
        ''' get route'''
        task.turnpoints = []
        task.partial_distance = []

        for idx, tp in enumerate(t['route'], 1):
            '''creating waypoints'''
            # I could take them from database, but this is the only way to be sure it is the correct one
            turnpoint = Turnpoint(tp['lat'], tp['lon'], tp['radius'], tp['type'],
                                  tp['shape'], tp['how'])

            turnpoint.name = tp['name']
            turnpoint.id = idx
            turnpoint.description = tp['description']
            turnpoint.altitude = tp['altitude']
            task.turnpoints.append(turnpoint)
            task.partial_distance.append(tp['cumulative_dist'])

        ''' get results'''
        task.pilots = []
        for pil in t['results']:
            ''' create Pilot objects from json list'''
            task.pilots.append(Pilot.from_result(task_id, pil))

        return task

    @staticmethod
    def create_from_lkt_file(filename):
        """ Creates Task from LK8000 task file, which is in xml format.
            LK8000 does not have End of Speed Section or task finish time.
            For the goal, at the moment, Turnpoints can't handle goal cones or lines,
            for this reason we default to goal_cylinder.
        """
        import xml.dom.minidom as D

        # Open XML document using minidom parser
        DOMTree = D.parse(filename)
        task = DOMTree.documentElement

        # Get the taskpoints, waypoints and time gate
        taskpoints = task.getElementsByTagName("taskpoints")[0]  # TODO: add code to handle if these tags are missing.
        waypoints = task.getElementsByTagName("waypoints")[0]
        gate = task.getElementsByTagName("time-gate")[0]
        tpoints = taskpoints.getElementsByTagName("point")
        wpoints = waypoints.getElementsByTagName("point")
        start_time = gate.getAttribute("open-time")

        start_hours, start_minutes = start_time.split(':')
        start_time = int(start_hours) * 3600 + int(start_minutes) * 60
        task_deadline = 23 * 3600 + 59 * 60 + 59  # default task_deadline of 23:59

        # create a dictionary of names and a list of longitudes and latitudes
        # as the waypoints co-ordinates are stored separate to turnpoint details
        coords = defaultdict(list)

        for point in wpoints:
            name = point.getAttribute("name")
            longitude = float(point.getAttribute("longitude"))
            latitude = float(point.getAttribute("latitude"))
            coords[name].append(longitude)
            coords[name].append(latitude)

        # create list of turnpoints
        turnpoints = []
        for point in tpoints:
            lat = coords[point.getAttribute("name")][1]
            lon = coords[point.getAttribute("name")][0]
            radius = float(point.getAttribute("radius")) / 1000

            if point == tpoints[0]:  # if it is the 1st turnpoint then it is a start
                if point.getAttribute("Exit") == "true":
                    kind = "start_exit"
                else:
                    kind = "start_enter"
            else:
                if point == tpoints[-1]:  # if it is the last turnpoint i.e. the goal
                    if point.getAttribute("type") == "line":
                        kind = "goal_cylinder"  # TODO(kuaka): change to 'line' once we can process it
                    else:
                        kind = "goal_cylinder"
                else:
                    kind = "cylinder"  # All turnpoints other than the 1st and the last are "cylinders".
                    # In theory they could be "End_of_speed_section" but this is not supported by LK8000.
                    # For paragliders it would be safe to assume that the 2nd to last is always "End_of_speed_section"

            turnpoint = Turnpoint(lat, lon, radius, kind)
            turnpoints.append(turnpoint)
        task = Task(turnpoints, start_time, task_deadline)
        return task

    @classmethod
    def from_fsdb(cls, t):
        """ Creates Task from FSDB FsTask element, which is in xml format.
            Unfortunately the fsdb format isn't published so much of this is simply an
            exercise in reverse engineering.
        """
        from formula import Task_formula
        from calcUtils import get_date, get_time, time_to_seconds

        tas = dict()
        stats = dict()
        turnpoints = []
        optimised_legs = []
        # results = []

        task = cls()

        task.check_launch = 0
        task.task_name = t.get('name')
        task.task_num = 0 + int(t.get('id'))
        print(f"task {task.task_num} - name: {task.task_name}")

        """formula info"""
        f = t.find('FsScoreFormula')
        formula = Task_formula()
        formula.formula_name = f.get('id')
        formula.arr_alt_bonus = 'off'
        if ((f.get('use_arrival_altitude_points') is not None and float(f.get('use_arrival_altitude_points')) > 0)
                or f.get('use_arrival_altitude_points') == 'aatb'):
            formula.arr_alt_bonus = 'on'
        """Departure and Arrival from formula"""
        formula.formula_arrival = 'position' if float(f.get('use_arrival_position_points')) == 1 else 'time' if float(
            f.get(
                'use_arrival_position_points')) == 1 else 'off'  # not sure if and which type Airscore is supporting at the moment
        formula.tolerance = 0 + float(f.get('turnpoint_radius_tolerance'))  # tolerance perc /100

        if float(f.get('use_departure_points')) > 0:
            formula.formula_departure = 'on'
        elif float(f.get('use_leading_points')) > 0:
            formula.formula_departure = 'leadout'
        else:
            formula.formula_departure = 'off'

        """Task Status"""
        node = t.find('FsTaskState')
        formula.score_back_time = int(node.get('score_back_time'))
        state = node.get('task_state')
        task.comment = ': '.join([state, node.get('cancel_reason')])
        if state == 'CANCELLED':
            """I don't need if cancelled"""
            return None

        task.stopped_time = get_datetime(node.get('stop_time')) if not (state == 'REGULAR') else None
        """Task Stats"""
        p = t.find('FsTaskScoreParams')
        '''a non scored task could miss this element'''
        task.opt_dist = None if p is None else float(p.get('task_distance')) * 1000
        task.distance = None  # need to calculate distance through centers
        task.opt_dist_to_ESS = None if p is None else float(p.get('launch_to_ess_distance')) * 1000
        task.SS_distance = None if p is None else float(p.get('ss_distance')) * 1000
        stats['pilots_present'] = None if p is None else int(p.get('no_of_pilots_present'))
        stats['pilots_launched'] = None if p is None else int(p.get('no_of_pilots_flying'))
        stats['pilots_goal'] = None if p is None else int(p.get('no_of_pilots_reaching_goal'))
        stats['max_distance'] = None if p is None else float(p.get('best_dist')) * 1000  # in meters
        stats['totdistovermin'] = None if p is None else float(p.get('sum_flown_distance')) * 1000  # in meters
        try:
            '''happens this values are error strings'''
            stats['day_quality'] = 0 if p is None else float(p.get('day_quality'))
            stats['dist_validity'] = 0 if p is None else float(p.get('distance_validity'))
            stats['time_validity'] = 0 if p is None else float(p.get('time_validity'))
            stats['launch_validity'] = 0 if p is None else float(p.get('launch_validity'))
            stats['stop_validity'] = 0 if p is None else float(p.get('stop_validity'))
            stats['avail_dist_points'] = 0 if p is None else float(p.get('available_points_distance'))
            stats['avail_dep_points'] = 0 if p is None else float(p.get('available_points_leading'))
            stats['avail_time_points'] = 0 if p is None else float(p.get('available_points_time'))
            stats['avail_arr_points'] = 0 if p is None else float(p.get('available_points_arrival'))
        except:
            stats['day_quality'] = 0
            stats['dist_validity'] = 0
            stats['time_validity'] = 0
            stats['launch_validity'] = 0
            stats['stop_validity'] = 0
            stats['avail_dist_points'] = 0
            stats['avail_dep_points'] = 0
            stats['avail_time_points'] = 0
            stats['avail_arr_points'] = 0
        stats['fastest'] = 0 if p is None else decimal_to_seconds(float(p.get('best_time'))) if float(
            p.get('best_time')) > 0 else 0
        if p is not None:
            for l in p.iter('FsTaskDistToTp'):
                optimised_legs.append(float(l.get('distance')) * 1000)

        node = t.find('FsTaskDefinition')
        qnh = None if node is None else float(node.get('qnh_setting').replace(',', '.'))
        # task.date = None if not node else get_date(node.find('FsStartGate').get('open'))
        """guessing type from startgates"""
        task.SS_interval = 0
        startgates = 0
        headingpoint = 0
        if node.get('ss') is None:
            '''open distance
                not yet implemented in Airscore'''
            # TODO: free distance and free distance with bearing
            task.task_type = 'free distance'
            if node.find('FsHeadingpoint') is not None:
                '''open distance with bearing'''
                headingpoint = 1
                task.task_type = 'distance with bearing'
                task.bearing_lat = float(node.find('FsHeadingpoint').get('lat'))
                task_bearing_lon = float(node.find('FsHeadingpoint').get('lon'))
        else:
            sswpt = int(node.get('ss'))
            eswpt = int(node.get('es'))
            gtype = node.get('goal')
            gstart = int(node.get('groundstart'))
            if node.find('FsStartGate') is None:
                '''elapsed time
                    on start gate, have to get start opening time from ss wpt'''
                task.task_type = 'elapsed time'
            else:
                '''race'''
                startgates = len(node.findall('FsStartGate'))
                task.task_type = 'race'
                task.start_time = time_to_seconds(get_time(node.find('FsStartGate').get('open')))
                # print ("gates: {}".format(startgates))
                if startgates > 1:
                    '''race with multiple start gates'''
                    # print ("MULTIPLE STARTS")
                    time = time_to_seconds(get_time(node.findall('FsStartGate')[1].get('open')))
                    task.SS_interval = time - task.start_time
                    '''if prefer minutes: time_difference(tas['tasStartTime'], time).total_seconds()/60'''
                    print(f"    **** interval: {task.SS_interval}")

        """Task Route"""
        for w in node.iter('FsTurnpoint'):
            turnpoint = Turnpoint(float(w.get('lat')), float(w.get('lon')), int(w.get('radius')))
            turnpoint.id = len(turnpoints) + 1
            turnpoint.name = w.get('id')
            turnpoint.altitude = int(w.get('altitude'))
            print(f"    {turnpoint.id}  {turnpoint.name}  {turnpoint.radius}")
            if turnpoint.id == 1:
                turnpoint.type = 'launch'
                task.date = get_date(w.get('open'))
                task.window_open_time = time_to_seconds(get_time(w.get('open')))
                task.window_close_time = time_to_seconds(get_time(w.get('close')))
                # sanity
                if task.window_close_time <= task.window_open_time:
                    task.window_close_time = None
                if 'free distance' in task.task_type:
                    # print('Sono in launch - free')
                    '''get start and close time for free distance task types'''
                    task.start_time = time_to_seconds(get_time(w.get('open')))
                    task.start_close_time = time_to_seconds(get_time(w.get('close')))
                    # task.task_deadline = get_datetime(w.get('close'))
            elif turnpoint.id == sswpt:
                # print('Sono in ss')
                turnpoint.type = 'speed'
                task.start_close_time = time_to_seconds(get_time(w.get('close')))
                if 'elapsed time' in task.task_type:
                    '''get start for elapsed time task types'''
                    task.start_time = time_to_seconds(get_time(w.get('open')))
            elif turnpoint.id == eswpt:
                # print('Sono in es')
                turnpoint.type = 'endspeed'
                task.task_deadline = time_to_seconds(get_time(w.get('close')))
            elif turnpoint.id == len(
                    node) - startgates - headingpoint:  # need to remove FsStartGate and FsHeadingpoint nodes from count
                # print('Sono in goal')
                turnpoint.type = 'goal'
                if gtype == 'LINE':
                    turnpoint.shape = 'line'
            # else:
            #     wpt['tawType'] = 'waypoint'

            turnpoints.append(turnpoint)

        # tas['route'] = route
        task.formula = formula
        task.turnpoints = turnpoints
        task.calculate_task_length()
        # print ("Tot. Dist.: {}".format(task.distance))
        task.stats = stats
        task.partial_distance = optimised_legs
        # task.results = results
        # print ("{} - date: {} - type: {} - dist.: {} - opt. dist.: {}".format(task.task_name, task.window_open_time.date(), task.task_type, task.distance, task.opt_dist))
        # print ("open: {} - start: {} - close: {} - end: {} \n".format(task.window_open_time, task.start_time, task.start_close_time, task.task_deadline))

        return task

    def calculate_task_length(self, method="fast_andoyer"):
        # calculate non optimised route distance.
        self.distance = 0
        for wpt in range(1, len(self.turnpoints)):
            leg_dist = distance(self.turnpoints[wpt - 1], self.turnpoints[wpt], method)
            self.legs.append(leg_dist)
            self.distance += leg_dist
            # print ("leg dist.: {} - Dist.: {}".format(leg_dist, self.distance))

    def calculate_optimised_task_length_old(self, method="fast_andoyer"):

        it1 = []
        it2 = []
        wpts = self.turnpoints
        self.opt_dist = 0  # reset in case of recalc.

        closearr = []
        num = len(wpts)

        if num < 1:
            self.partial_distance.append(self.opt_dist)
            return 0

        if num == 1:
            first = cartesian2polar(polar2cartesian(wpts[0]))
            closearr.append(first)
            return closearr

        # Work out shortest route!
        # End points don't vary?
        it1.append(wpts[0])
        newcl = wpts[0]
        for i in range(num - 2):
            # print "From it1: $i: ", $wpts->[$i]->{'name'}, "\n";
            if wpts[i + 1].lat == wpts[i + 2].lat and wpts[i + 1].lon == wpts[i + 2].lon:
                newcl = find_closest(newcl, wpts[i + 1], None, method)
            else:
                newcl = find_closest(newcl, wpts[i + 1], wpts[i + 2], method)
            it1.append(newcl)
        # FIX: special case for end point ..
        newcl = find_closest(newcl, wpts[num - 1], None, method)
        it1.append(newcl)

        num = len(it1)
        it2.append(it1[0])
        newcl = it1[0]
        for i in range(num - 2):
            # print "From it2: $i: ", $wpts->[$i]->{'name'}, "\n";
            newcl = find_closest(newcl, it1[i + 1], it1[i + 2], method)
            it2.append(newcl)

        it2.append(it1[num - 1])

        num = len(it2)
        closearr.append(it2[0])
        newcl = it2[0]
        for i in range(num - 2):
            # print "From it3: $i: ", $wpts->[$i]->{'name'}, "\n";
            newcl = find_closest(newcl, it2[i + 1], it2[i + 2], method)
            closearr.append(newcl)
        closearr.append(it2[num - 1])

        # calculate optimised route distance
        self.optimised_legs = []
        self.optimised_legs.append(0)
        self.partial_distance = []
        self.partial_distance.append(0)
        self.opt_dist = 0
        for opt_wpt in range(1, len(closearr)):
            leg_dist = distance(closearr[opt_wpt - 1], closearr[opt_wpt], method)
            self.optimised_legs.append(leg_dist)
            self.opt_dist += leg_dist
            self.partial_distance.append(self.opt_dist)

        # work out which turnpoints are SSS and ESS
        sss_wpt = 0
        ess_wpt = 0
        for wpt in range(len(self.turnpoints)):
            if self.turnpoints[wpt].type == 'speed':
                sss_wpt = wpt + 1
            if self.turnpoints[wpt].type == 'endspeed':
                ess_wpt = wpt + 1

        # work out self.opt_dist_to_SS, self.opt_dist_to_ESS, self.SS_distance
        self.opt_dist_to_SS = sum(self.optimised_legs[0:sss_wpt])
        self.opt_dist_to_ESS = sum(self.optimised_legs[0:ess_wpt])
        self.SS_distance = sum(self.optimised_legs[sss_wpt:ess_wpt])
        self.optimised_turnpoints = closearr

    def calculate_optimised_task_length_fast_andoyer(self, method="fast_andoyer"):
        from geographiclib.geodesic import Geodesic
        geod = Geodesic.WGS84
        wpts = self.turnpoints
        self.opt_dist = 0  # reset in case of recalc.

        closearr = []
        num = len(wpts)

        if num < 1:
            return 0

        if num == 1:
            first = cartesian2polar(polar2cartesian(wpts[0]))
            closearr.append(first)
            return closearr

        # Work out shortest route!
        # End points don't vary?
        optimised = []
        t = 0

        while t < len(self.turnpoints) - 1:

            exit_same = False
            exit_different = False
            enter_same = False
            enter_different = False

            if t == 0:
                t1 = self.turnpoints[t]
                optimised.append(t1)
            else:
                t1 = opt

            if t + 2 > len(self.turnpoints) - 1:
                optimised.append(opt_goal(t1, self.turnpoints[-1]))
                break
            # next wpt has the same centre but a bigger exit radius  (and therefore we are in it)
            if t1.lat == self.turnpoints[t + 1].lat and t1.lon == self.turnpoints[t + 1].lon:
                t += 1
                exit_same = True
            #  we are in the next one but it does not have the same centre
            elif self.turnpoints[t + 1].in_radius(t1, 0, 0):
                t += 1
                exit_different = True
                # case of having to exit and then next wpt also in the exit cylinder, reset t back 1
                if self.turnpoints[t].in_radius(self.turnpoints[t + 1], 0, 0):
                    t -= 1
            # or it is the same as the following one (i.e entry large radius followed by smaller like ess and goal often are)
            elif self.turnpoints[t + 2].lat == self.turnpoints[t + 1].lat and self.turnpoints[t + 2].lon == \
                    self.turnpoints[t + 1].lon:
                t += 1
                enter_same = True
            #  we are in the next one but it does not have the same centre
            elif self.turnpoints[t + 2].in_radius(self.turnpoints[t + 1], 0, 0):
                t += 1
                enter_different = True

            # print(f'{t} of{len(self.turnpoints)}')
            t2 = self.turnpoints[t + 1]

            if t + 2 > len(self.turnpoints) - 1:
                t3 = None
            else:
                t3 = self.turnpoints[t + 2]

            opt = opt_wp(t1, t2, t3, t2.radius)

            if exit_same:
                p = geod.Direct(t1.lat, t1.lon, calcBearing(t1.lat, t1.lon, opt.lat, opt.lon),
                                self.turnpoints[t].radius)
                opt_exit = Turnpoint(lat=p['lat2'], lon=p['lon2'], type='optimised', radius=0, shape='optimised',
                                     how='optimised')
                optimised.append(opt_exit)
            if exit_different:
                opt_exit = opt_wp_exit(opt, t1, self.turnpoints[t])
                optimised.append(opt_exit)
            if enter_same:
                p = geod.Direct(t2.lat, t2.lon, calcBearing(t2.lat, t2.lon, t1.lat, t1.lon), self.turnpoints[t].radius)
                opt_enter = Turnpoint(lat=p['lat2'], lon=p['lon2'], type='optimised', radius=0, shape='optimised',
                                      how='optimised')
                optimised.append(opt_enter)
            if enter_different:
                opt_enter = opt_wp_enter(opt, t2, self.turnpoints[t + 1])
                optimised.append(opt_enter)

            optimised.append(opt)

            t += 1
        total = 0
        for o in range(len(optimised) - 1):
            d = geod.Inverse(optimised[o].lat, optimised[o].lon, optimised[o + 1].lat, optimised[o + 1].lon)['s12']
            total += d

        # calculate optimised route distance
        self.optimised_legs = []
        self.optimised_legs.append(0)
        self.partial_distance = []
        self.partial_distance.append(0)
        self.opt_dist = 0
        for opt_wpt in range(1, len(optimised)):
            leg_dist = distance(optimised[opt_wpt - 1], optimised[opt_wpt], method)
            self.optimised_legs.append(leg_dist)
            self.opt_dist += leg_dist
            self.partial_distance.append(self.opt_dist)

        # work out which turnpoints are SSS and ESS
        sss_wpt = 0
        ess_wpt = 0
        for wpt in range(len(self.turnpoints)):
            if self.turnpoints[wpt].type == 'speed':
                sss_wpt = wpt + 1
            if self.turnpoints[wpt].type == 'endspeed':
                ess_wpt = wpt + 1

        # work out self.opt_dist_to_SS, self.opt_dist_to_ESS, self.SS_distance
        self.opt_dist_to_SS = sum(self.optimised_legs[0:sss_wpt])
        self.opt_dist_to_ESS = sum(self.optimised_legs[0:ess_wpt])
        self.SS_distance = sum(self.optimised_legs[sss_wpt:ess_wpt])
        self.optimised_turnpoints = optimised

    def calculate_optimised_task_length(self, method="fast_andoyer"):
        """ new optimized route procedure that uses John Stevenson on FAI Basecamp.
            trasforms wgs84 to plan trasverse cartesian projection, calculates
            optimised fix on cylinders, and goes back to wgs84 for distance calculations.
        """
        from route import get_shortest_path

        '''check we have at least 3 points'''
        if len(self.turnpoints) < 3: return

        '''calculate optimised distance fixes on cilynders'''
        optimised = get_shortest_path(self)

        '''updates all task attributes'''
        self.optimised_legs = []
        self.optimised_legs.append(0)
        self.partial_distance = []
        self.partial_distance.append(0)
        self.opt_dist = 0
        for i in range(1, len(optimised)):
            leg_dist = distance(optimised[i - 1], optimised[i], method)
            self.optimised_legs.append(leg_dist)
            self.opt_dist += leg_dist
            self.partial_distance.append(self.opt_dist)

        # work out which turnpoints are SSS and ESS
        sss_wpt = 0
        ess_wpt = 0
        for wpt in range(len(self.turnpoints)):
            if self.turnpoints[wpt].type == 'speed':
                sss_wpt = wpt + 1
            if self.turnpoints[wpt].type == 'endspeed':
                ess_wpt = wpt + 1

        # work out self.opt_dist_to_SS, self.opt_dist_to_ESS, self.SS_distance
        self.opt_dist_to_SS = sum(self.optimised_legs[0:sss_wpt])
        self.opt_dist_to_ESS = sum(self.optimised_legs[0:ess_wpt])
        self.SS_distance = sum(self.optimised_legs[sss_wpt:ess_wpt])
        self.optimised_turnpoints = optimised

    def clear_waypoints(self):
        from db_tables import tblTaskWaypoint as W

        self.turnpoints.clear()
        self.optimised_turnpoints.clear()
        self.optimised_legs.clear()
        self.partial_distance.clear()
        self.legs.clear()

        '''delete waypoints from database'''
        with Database() as db:
            db.session.question.query(W).filter(W.tasPk == self.id).delete()
            db.session.commit()

    def update_waypoints(self):
        from db_tables import tblTaskWaypoint as W
        with Database() as db:
            for idx, wp in enumerate(self.turnpoints):
                wpNum = idx + 1
                wpt = W(tasPk=self.id, rwpPk=wp.rwpPk, tawNumber=wpNum, tawType=wp.type,
                        tawHow=wp.how, tawShape=wp.shape, tawTime=0, tawRadius=wp.radius)
                db.session.add(wpt)
                id = db.session.commit()
                self.turnpoints[idx].id = id

    @property
    def distances_to_go(self):
        """calculates a list of distances from turnpoint to goal (assumes goal is the last turnpoint)"""
        t = len(self.optimised_turnpoints) - 1
        d = 0
        distance_to_go = [0]
        while t >= 1:
            d += distance(self.optimised_turnpoints[t], self.optimised_turnpoints[t - 1])
            distance_to_go.insert(0, d)
            t -= 1
        return distance_to_go


# function to parse task object to compilations


def get_map_json(task_id):
    """gets task map json file if it exists, otherwise creates it. returns 5 separate objects for mapping"""

    task_file = Path(Defines.MAPOBJDIR + 'tasks/' + str(task_id) + '.task')
    if not task_file.is_file():
        write_map_json(task_id)

    with open(task_file, 'r') as f:
        data = jsonpickle.decode(f.read())
        task_coords = data['task_coords']
        turnpoints = data['turnpoints']
        short_route = data['short_route']
        goal_line = data['goal_line']
        tolerance = data['tolerance']
        bbox = data['bbox']
    return task_coords, turnpoints, short_route, goal_line, tolerance, bbox


def write_map_json(task_id):
    import os
    from geographiclib.geodesic import Geodesic
    from route import get_line
    from mapUtils import get_route_bbox

    geod = Geodesic.WGS84
    task_file = Path(Defines.MAPOBJDIR + 'tasks/' + str(task_id) + '.task')

    if not os.path.isdir(Defines.MAPOBJDIR + 'tasks/'):
        os.makedirs(Defines.MAPOBJDIR + 'tasks/')
    task_coords = []
    turnpoints = []
    short_route = []
    goal_line = None
    task = Task.read(task_id)
    tolerance = task.tolerance

    for obj in task.turnpoints:
        task_coords.append({
            'longitude': obj.lon,
            'latitude': obj.lat,
            'name': obj.name
        })

        if obj.shape == 'line':
            '''manage goal line'''
            goal_line = []
            ends = get_line(task.turnpoints)
            goal_line.append(tuple([ends[0].lat, ends[0].lon]))
            goal_line.append(tuple([ends[1].lat, ends[1].lon]))

        else:
            '''create tp cylinder'''
            turnpoints.append({
                'radius': obj.radius,
                'longitude': obj.lon,
                'latitude': obj.lat,
                #         'altitude': obj.altitude,
                'name': obj.name,
                'type': obj.type,
                'shape': obj.shape
            })

    for obj in task.optimised_turnpoints:
        short_route.append(tuple([obj.lat, obj.lon]))

    with open(task_file, 'w') as f:
        f.write(jsonpickle.dumps({'task_coords': task_coords, 'turnpoints': turnpoints, 'short_route': short_route,
                                  'goal_line': goal_line, 'tolerance': tolerance, 'bbox': get_route_bbox(task)}))


def get_task_json_filename(task_id):
    """returns active json result file"""
    from db_tables import tblResultFile as R
    from sqlalchemy import and_, or_

    with Database() as db:
        filename = db.session.query(R.refJSON.label('file')).filter(and_(
            R.tasPk == task_id, R.refVisible == 1
        )).scalar()
    return filename


def get_task_json(task_id):
    filename = get_task_json_filename(task_id)
    with open(Defines.RESULTDIR + filename, 'r') as myfile:
        data = myfile.read()
    if not data:
        return "error"
    return json.loads(data)
