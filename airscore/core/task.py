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

from os import path, makedirs, remove
from pathlib import Path

import jsonpickle
from sqlalchemy import and_
from sqlalchemy.orm import aliased

from Defines import RESULTDIR, MAPOBJDIR, TRACKDIR
from airspace import AirspaceCheck
from calcUtils import json, get_date, get_datetime, decimal_to_seconds
from compUtils import read_rankings
from db_tables import TblTask
from flight_result import verify_all_tracks, adjust_flight_results
from formula import TaskFormula
from geo import Geo
from igc_lib import defaultdict
from mapUtils import save_all_geojson_files
from myconn import Database
from pilot import Pilot, update_all_results
from result import TaskResult, create_json_file
from route import distance, polar, Turnpoint, get_shortest_path, convert_turnpoints, get_line
from sqlalchemy.exc import SQLAlchemyError


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
        clear_waypoints: delete waypoints from TblTaskWaypoint
        update_waypoints:  write waypoints to TblTaskWaypoint
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

    def __init__(self, comp_id=None, task_id=None, task_type=None, start_time=None, task_deadline=None,
                 stopped_time=None, check_launch='off'):
        self.task_id = task_id
        self.task_type = task_type  # 'race', 'elapsed_time'
        self.start_time = start_time
        self.task_deadline = task_deadline  # seconds from midnight: task deadline
        self.stopped_time = stopped_time  # seconds from midnight: time task was stopped (TaskStopAnnouncementTime).
        self.check_launch = check_launch  # check launch flag. whether we check that pilots leave from launch.
        self.comp_id = comp_id
        self.comp_code = None
        self.comp_name = None
        self.comp_site = None
        self.comp_class = None
        self.reg_id = None
        self.region_name = None
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
        self.projected_turnpoints = []  # list of cPoint objects
        self.projected_line = []  # list of cPoint objects
        self.optimised_legs = []  # opt distance between cylinders
        self.partial_distance = []  # distance from launch to waypoint
        self.legs = []  # non optimised legs
        self.geo = None  # Geo Object
        self.stats = dict()  # STATIC scored task statistics, used when importing results from JSON / FSDB files
        self.pilots = []  # scored task results
        self.airspace_check = False  # BOOL airspace check
        self.openair_file = None  # STR
        self.QNH = 1013.25  # Pressure Reference for altitude if altitude_mode = QNH
        self.comment = None
        self.time_offset = 0  # seconds
        self.cancelled = False
        self.locked = False
        self.task_path = None
        self.comp_path = None
        self.track_source = None    # ['xcontest', 'flymaster'] external available sources for tracks in Defines.py
        self.igc_config_file = None     # config yaml for igc_lib.

        '''Formula'''
        if self.id:
            self.formula = TaskFormula.read(self.id)
        elif self.comp_id:
            self.formula = TaskFormula.from_comp(self.comp_id)
        else:
            self.formula = None

    def __setattr__(self, attr, value):
        import datetime
        property_names = [p for p in dir(Task) if isinstance(getattr(Task, p), property)]
        if attr == 'date':
            if type(value) is str:
                value = get_date(value)
            elif isinstance(value, datetime.datetime):
                value = value.date()
        if attr not in property_names:
            self.__dict__[attr] = value
            if attr == 'task_id' and hasattr(self, 'formula'):
                self.formula.__dict__[attr] = value

    def __str__(self):
        out = ''
        out += 'Task:'
        out += f'{self.comp_name} - {self.task_name} | Date: {self.date_str} \n'
        out += f'{self.comment} \n'
        for wpt in self.turnpoints:
            out += f'  {wpt.name}  {wpt.type}  {round(wpt.radius / 1000, 2)} km \n'
        out += f'Task Opt. Distance: {round(self.opt_dist / 1000, 2)} Km \n'
        return out

    def __eq__(self, other=None):
        if not other or not isinstance(other, Task):
            return NotImplemented
        keys = ['task_type', 'start_time', 'task_deadline', 'stopped_time', 'window_open_time', 'window_close_time',
                'start_close_time', 'SS_interval', 'start_iteration', 'distance', 'opt_dist', 'cancelled']
        for k in keys:
            if not getattr(self, k) == getattr(other, k):
                return False
        return True

    def __ne__(self, other=None):
        if not other or not isinstance(other, Turnpoint):
            return NotImplemented
        return not self.__eq__(other)

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
        return path.join(TRACKDIR, self.comp_path, self.task_path.lower())

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
    def distances_to_go(self):
        """calculates a list of distances from turnpoint to goal (assumes goal is the last turnpoint)"""
        t = len(self.optimised_turnpoints) - 1
        d = 0
        distances_to_go = [0]
        while t >= 1:
            d += distance(self.optimised_turnpoints[t], self.optimised_turnpoints[t - 1])
            distances_to_go.insert(0, d)
            t -= 1
        return distances_to_go

    @property
    def duration(self):
        # seconds, elapsed time from stop_time to last_SS_time
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

    @property
    def total_start_number(self):
        if self.task_type == 'RACE' and self.SS_interval:
            if self.start_iteration:
                return self.start_iteration + 1
            else:
                # indefinite start number
                if self.start_close_time:
                    return int((self.start_close_time - self.start_time) / self.SS_interval)
        elif self.start_time:
            return 1
        else:
            return 0

    ''' * Geographic Projection *'''

    @property
    def bbox_center(self):
        from statistics import mean
        if not self.turnpoints:
            return 0.0, 0.0
        lat = mean(t.lat for t in self.turnpoints)
        lon = mean(t.lon for t in self.turnpoints)
        return lat, lon

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
        return len([p for p in self.valid_results if not p.still_flying_at_deadline])

    ''' distance stats'''

    @property
    def tot_distance_flown(self):
        if self.formula:
            if self.formula.min_dist and self.pilots_launched > 0:
                return sum([p.distance_flown for p in self.valid_results if p.distance_flown])
        return 0

    @property
    def tot_dist_over_min(self):
        if self.formula:
            if self.formula.min_dist and self.pilots_launched > 0:
                return sum([max(p.distance_flown - self.formula.min_dist, 0) for p in self.valid_results])
        return 0

    @property
    def std_dev_dist(self):
        if self.formula:
            from statistics import stdev
            if self.formula.min_dist and self.pilots_launched > 0:
                return stdev([max(p.distance_flown, self.formula.min_dist) for p in self.valid_results])
        return 0

    @property
    def max_distance_flown(self):
        if self.formula:
            if self.formula.min_dist and self.pilots_launched > 0:
                return max(max(p.distance_flown for p in self.valid_results), self.formula.min_dist)
        return 0

    @property
    def max_distance(self):
        if self.formula:
            if self.formula.min_dist and self.pilots_launched > 0:
                # Flight_result.distance = max(distance_flown, total_distance)
                return max(max(p.distance for p in self.valid_results), self.formula.min_dist)
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
    def last_landing_time(self):
        """ Landing time of last pilot in flight"""
        if self.pilots_launched:
            return max((p.last_time if not p.landing_time else p.landing_time)
                       for p in self.valid_results if p.last_time)
        else:
            return None

    @property
    def last_landout_time(self):
        """ Landing time of last pilot landed out"""
        if self.pilots_launched:
            return max((p.last_time if not p.landing_time else p.landing_time)
                       for p in self.valid_results if p.last_time and not p.ESS_time)
        else:
            return None

    @property
    def max_time(self):
        if self.pilots_launched:
            last_pilot_time = (self.last_landout_time if not self.max_ess_time
                               else max(self.last_landout_time, self.max_ess_time))
            if self.stopped_time:
                return min(last_pilot_time, self.stop_time)
            else:
                return min(last_pilot_time, self.task_deadline)
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
        from db_tables import TaskObjectView as T, TblTaskWaypoint as W
        if not (type(task_id) is int and task_id > 0):
            print(f'Error: {task_id} is not a valid id')
            return f'Error: {task_id} is not a valid id'
        task = Task(task_id=task_id)
        '''get task from db'''
        with Database() as db:
            # get the task details.
            try:
                t = db.session.query(T).get(task_id)
                if not t:
                    db.session.close()
                    error = f'Error: No task found with id {task_id}'
                    print(error)
                    return error
                tps = db.session.query(W).filter(W.task_id == task_id).order_by(W.num)
                db.populate_obj(task, t)
                '''populate turnpoints'''
                for tp in tps:
                    turnpoint = Turnpoint(tp.lat, tp.lon, tp.radius, tp.type, tp.shape, tp.how, tp.altitude, tp.name,
                                          tp.num, tp.description, tp.wpt_id)
                    task.turnpoints.append(turnpoint)
                    s_point = polar(lat=tp.ssr_lat, lon=tp.ssr_lon)
                    task.optimised_turnpoints.append(s_point)
                    if tp.partial_distance is not None:  # this will be None in DB before we optimise route, but we append to this list so we should not fill it with Nones
                        task.partial_distance.append(tp.partial_distance)
            except SQLAlchemyError as e:
                error = str(e)
                print(f"Error retrieving task from database: {error}")
                db.session.rollback()
                db.session.close()
                return error
        '''check if we already have a filepath for task'''
        if task.task_path is None or '':
            task.create_path()
        '''add geo object if we have turnpoints'''
        if task.turnpoints is not None and len(task.turnpoints) > 0:
            task.create_projection()
        return task

    def read_turnpoints(self):
        """Reads Task turnpoints from database, for use in front end"""
        from db_tables import TblTaskWaypoint as W
        with Database() as db:
            try:
                # get the task turnpoint details.
                results = db.session.query(W.wpt_id, W.rwp_id, W.name, W.num, W.description, W.how, W.radius, W.shape,
                                           W.type, W.partial_distance).filter(W.task_id == self.task_id).order_by(
                    W.num).all()
                if results:
                    results = [row._asdict() for row in results]
                return results
            except SQLAlchemyError:
                print(f"Error trying to retrieve Tasks details for Comp ID {self.comp_id}")
                return None

    def create_path(self, track_path=None):
        """create filepath from # and date if not given
            and store it in database"""
        if track_path:
            self.task_path = track_path
        elif self.task_num and self.date:
            self.task_path = '_'.join([('t' + str(self.task_num)), self.date.strftime('%Y%m%d')])
        else:
            return
        if self.id:
            full_path = path.join(TRACKDIR, self.comp_path, self.task_path.lower())
            if not path.exists(full_path):
                makedirs(full_path)
            '''store to database'''
            with Database() as db:
                q = db.session.query(TblTask).get(self.id)
                q.task_path = self.task_path
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
        ''' retrieve scoring formula library'''
        lib = self.formula.get_lib()
        if mode == 'full' or self.stopped_time:
            # TODO: check if we changed task, or we had new tracks, after last results generation
            #       If this is the case we should not need to re-score unless especially requested
            '''Task Full Rescore
                - recalculate Opt. route
                - check all tracks'''
            print(f" - FULL Mode -")
            '''get projection'''
            self.create_projection()
            print(f"Calculating task optimised distance...")
            self.calculate_task_length()
            self.calculate_optimised_task_length()
            print(f"Storing calculated values to database...")
            self.update_task_distance()
            print(f"Task Opt. Route: {round(self.opt_dist / 1000, 4)} Km")
            '''get airspace info if needed'''
            airspace = None if not self.airspace_check else AirspaceCheck.from_task(self)
            print(f"Processing pilots tracks...")
            self.check_all_tracks(lib, airspace)
        else:
            ''' get pilot list and results'''
            self.get_results(lib)
        if self.pilots_launched == 0:
            print(f"Task (ID {self.id}) has no results yet")
            return None
        ''' Calculates task result'''
        print(f"Calculating task results...")
        lib.calculate_results(self)
        '''create result elements from task, formula and results objects'''
        elements = self.create_json_elements()
        ref_id, _, _ = create_json_file(comp_id=self.comp_id, task_id=self.id,
                                        code='_'.join([self.comp_code, self.task_code]), elements=elements,
                                        status=status)
        return ref_id

    def create_json_elements(self):
        """ returns Dict with elements to generate json file"""

        pil_list = sorted([p for p in self.pilots if p.result_type not in ['dnf', 'abs']],
                          key=lambda k: k.score, reverse=True)
        pil_list += [p for p in self.pilots if p.result_type == 'dnf']
        pil_list += [p for p in self.pilots if p.result_type == 'abs']

        info = {x: getattr(self, x) for x in TaskResult.info_list if x in dir(self)}
        formula = {x: getattr(self.formula, x) for x in TaskResult.formula_list if x in dir(self.formula)}
        stats = {x: getattr(self, x) for x in TaskResult.stats_list if x in dir(self)}
        route = []
        for idx, tp in enumerate(self.turnpoints):
            wpt = {x: getattr(tp, x) for x in TaskResult.route_list if x in dir(tp)}
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

    def check_all_tracks(self, lib=None, airspace=None):
        """ checks all igc files against Task and creates results """

        if not lib:
            '''retrieve scoring formula library'''
            lib = self.formula.get_lib()

        ''' get pilot and tracks list'''
        self.get_results()

        ''' calculate projected turnpoints'''
        if not self.geo:
            self.create_projection()

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
                verify_all_tracks(self, lib, airspace)

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
                verify_all_tracks(self, lib, airspace)
        else:
            '''get all results for the task'''
            verify_all_tracks(self, lib, airspace)
        '''store results to database'''
        print(f"updating database with new results...")
        update_all_results(self.task_id, self.pilots)
        '''save map files if needed'''
        save_all_geojson_files(self)
        '''process results with scoring system'''
        lib.process_results(self)

    def get_pilots(self):
        from db_tables import TblParticipant as P
        from sqlalchemy.exc import SQLAlchemyError
        from pilot import Pilot
        pilots = []
        with Database() as db:
            try:
                results = db.session.query(P).filter(P.comp_id == self.comp_id).all()
                for row in results:
                    pilot = Pilot.create(task_id=self.task_id)
                    db.populate_obj(pilot.info, row)
                    pilots.append(pilot)
            except SQLAlchemyError:
                print('DB Error retrieving task results')
                db.session.rollback()
                return
        self.pilots = pilots

    def get_results(self, lib=None):
        """ Loads all Pilot obj. into Task obj."""
        from db_tables import FlightResultView as F, TblNotification as N
        from notification import Notification
        from sqlalchemy.exc import SQLAlchemyError
        from pilot import Pilot
        pilots = []
        with Database() as db:
            try:
                results = db.session.query(F).filter(F.task_id == self.task_id).all()
                notifications = db.session.query(N).filter(N.track_id.in_([p.track_id for p in results])).all()
                for row in results:
                    pilot = Pilot.create(task_id=self.task_id)
                    db.populate_obj(pilot.result, row)
                    db.populate_obj(pilot.info, row)
                    db.populate_obj(pilot.track, row)
                    # notifications = db.session.query(N).filter(N.track_id == pilot.track.track_id).all()
                    for el in [n for n in notifications if n.track_id == pilot.track.track_id]:
                        n = Notification()
                        db.populate_obj(n, el)
                        if n.notification_type == 'track':
                            pilot.track.notifications.append(n)
                        else:
                            pilot.result.notifications.append(n)
                    if self.stopped_time and pilot.result.stopped_distance:
                        pilot.result.still_flying_at_deadline = True
                    pilots.append(pilot)
            except SQLAlchemyError:
                print('DB Error retrieving task results')
                db.session.rollback()
                return
        self.pilots = pilots
        if lib:
            '''prepare results for scoring'''
            lib.process_results(self)
        # return pilots

    def get_geo(self):
        clat, clon = self.bbox_center
        self.geo = Geo.from_coords(clat, clon)

    def update_task_distance(self):
        from db_tables import TblTask as T, TblTaskWaypoint as W
        with Database() as db:
            '''add optimised and total distance to task'''
            q = db.session.query(T)
            t = q.get(self.task_id)
            t.distance = self.distance
            t.opt_dist = self.opt_dist
            t.SS_distance = self.SS_distance
            t.opt_dist_to_ESS = self.opt_dist_to_ESS
            t.opt_dist_to_SS = self.opt_dist_to_SS
            db.session.commit()

            '''add opt legs to task wpt'''
            w = db.session.query(W)
            for idx, tp in enumerate(self.turnpoints):
                sr = self.optimised_turnpoints[idx]
                wpt = w.get(tp.id)
                wpt.ssr_lat = sr.lat
                wpt.ssr_lon = sr.lon
                wpt.partial_distance = self.partial_distance[idx]
            db.session.commit()

    def update_task_info(self):
        # t = aliased(TblTask)

        with Database() as db:
            print(f"taskid:{self.task_id}")
            q = db.session.query(TblTask).get(self.task_id)
            db.populate_row(q, self)
            # for k, v in self.as_dict().items():
            #     if hasattr(q, k):
            #         setattr(q, k, v)
            db.session.commit()

    def update_formula(self):
        self.formula.to_db()

    def create_projection(self):
        """creates geo.Geo flat projection, projected turnpoints and line/semicircle bisecting segment extremes"""
        from route import get_line, convert_turnpoints
        self.get_geo()
        tol, min_tol = self.formula.tolerance, self.formula.min_tolerance
        self.projected_turnpoints = convert_turnpoints(self.turnpoints, self.geo)
        self.projected_line = convert_turnpoints(get_line(self.turnpoints, tol, min_tol), self.geo)

    def to_db(self, session=None):
        """Inserts new task or updates existent one"""
        with Database(session) as db:
            try:
                if not self.id:
                    task = TblTask(comp_id=self.comp_id, task_num=self.task_num, task_name=self.task_name,
                                   date=self.date)
                    db.session.add(task)
                    db.session.flush()
                    self.task_id = task.task_id
                else:
                    task = db.session.query(TblTask).get(self.id)
                for k, v in self.as_dict().items():
                    if k not in ['task_id', 'comp_id'] and hasattr(task, k):
                        setattr(task, k, v)
                '''save formula parameters'''
                if self.formula:
                    for key in TaskFormula.task_overrides:
                        setattr(task, key, getattr(self.formula, key))
                db.session.commit()
                '''save waypoints'''
                if self.turnpoints:
                    self.update_waypoints(session=session)
            except SQLAlchemyError as e:
                error = str(e.__dict__)
                print(f"Error storing task to database: {error}")
                db.session.rollback()
                db.session.close()
                return error

    def update_from_xctrack_data(self, taskfile_data):
        """processes XCTrack file that is already in memory as json data and updates the task defintion"""
        from compUtils import get_wpts
        from calcUtils import string_to_seconds

        startopenzulu = taskfile_data['sss']['timeGates'][0]
        deadlinezulu = taskfile_data['goal']['deadline']

        self.start_time = string_to_seconds(startopenzulu)
        self.task_deadline = string_to_seconds(deadlinezulu)

        '''check task start and start close times are ok for new start time
        we will check to be at least 1 hour before and after'''
        if not self.window_open_time or self.start_time - self.window_open_time < 3600:
            self.window_open_time = self.start_time - 3600
        if not self.start_close_time or self.start_close_time - self.start_time < 3600:
            self.start_close_time = self.start_time + 3600

        if taskfile_data['sss']['type'] == 'ELAPSED-TIME':
            self.task_type = 'ELAPSED TIME'
        else:
            self.task_type = 'RACE'
            '''manage multi start'''
            self.SS_interval = 0
            if len(taskfile_data['sss']['timeGates']) > 1:
                second_start = string_to_seconds(taskfile_data['sss']['timeGates'][1])
                self.SS_interval = int((second_start - self.start_time) / 60)  # interval in minutes
                self.start_close_time = int(
                    self.start_time + len(taskfile_data['sss']['timeGates']) * (second_start - self.start_time)) - 1

        print('xct start:       {} '.format(self.start_time))
        print('xct deadline:    {} '.format(self.task_deadline))

        waypoint_list = get_wpts(self.id)
        print('n. waypoints: {}'.format(len(taskfile_data['turnpoints'])))

        for i, tp in enumerate(taskfile_data['turnpoints']):
            waytype = "waypoint"
            shape = "circle"
            how = "entry"  # default entry .. looks like xctrack doesn't support exit cylinders apart from SSS
            wpID = waypoint_list[tp["waypoint"]["name"]]
            wpNum = i + 1

            if i < len(taskfile_data['turnpoints']) - 1:
                if 'type' in tp:
                    if tp['type'] == 'TAKEOFF':
                        waytype = "launch"  # live
                        # waytype = "start"  # aws
                        how = "exit"
                    elif tp['type'] == 'SSS':
                        waytype = "speed"
                        if taskfile_data['sss']['direction'] == "EXIT":  # get the direction form the SSS section
                            how = "exit"
                    elif tp['type'] == 'ESS':
                        waytype = "endspeed"
            else:
                waytype = "goal"
                if taskfile_data['goal']['type'] == 'LINE':
                    shape = "line"

            turnpoint = Turnpoint(tp['waypoint']['lat'], tp['waypoint']['lon'], tp['radius'], waytype, shape, how)
            turnpoint.name = tp["waypoint"]["name"]
            # turnpoint.rwp_id = wpID
            turnpoint.num = wpNum
            self.turnpoints.append(turnpoint)

    def update_from_xctrack_file(self, filename):
        """ Updates Task from xctrack file, which is in json format.
        """

        with open(filename, encoding='utf-8') as json_data:
            # a bit more checking..
            print("file: ", filename)
            try:
                task_data = json.load(json_data)
            except:
                print("file is not a valid JSON object")
                exit()

        self.update_from_xctrack_data(task_data)

    @staticmethod
    def create_from_xctrack_file(filename):
        """ Creates Task from xctrack file, which is in json format.
        NEEDS UPDATING BUT WE CAN PROBABLY REMOVE THIS AS THE TASK SHOULD ALWAYS BE CREATED BEFORE IMPORT??
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

        if not filename or not path.isfile(filename):
            '''we get the active json file'''
            filename = get_task_json_filename(task_id)

        if not filename:
            print(f"There's no active json file for task {task_id}, or given filename does not exists")
            return None

        print(f"task {task_id} json file: {filename}")

        with open(path.join(RESULTDIR, filename), encoding='utf-8') as json_data:
            # a bit more checking..
            try:
                t = jsonpickle.decode(json_data.read())
            except:
                print("file is not a valid JSON object")
                return None

        # pp(t)

        task = Task(task_id=task_id)
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
        task.formula = TaskFormula.from_dict(t['formula'])
        ''' get route'''
        task.turnpoints = []
        task.partial_distance = []

        for idx, tp in enumerate(t['route'], 1):
            '''creating waypoints'''
            # I could take them from database, but this is the only way to be sure it is the correct one
            turnpoint = Turnpoint(tp['lat'], tp['lon'], tp['radius'], tp['type'],
                                  tp['shape'], tp['how'])

            turnpoint.name = tp['name']
            turnpoint.num = idx
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
            type = 'waypoint'
            shape = 'circle'
            how = 'entry'
            lat = coords[point.getAttribute("name")][1]
            lon = coords[point.getAttribute("name")][0]
            radius = float(point.getAttribute("radius"))

            if point == tpoints[0]:  # if it is the 1st turnpoint then it is a start
                type = 'speed'
                if point.getAttribute("Exit") == "true":
                    how = "exit"
            elif point == tpoints[-1]:  # if it is the last turnpoint i.e. the goal
                type = 'goal'
                if point.getAttribute("type") == "line":
                    shape = 'line'
            # In theory they could be "End_of_speed_section" but this is not supported by LK8000.
            # For paragliders it would be safe to assume that the 2nd to last is always "End_of_speed_section"

            turnpoint = Turnpoint(lat=lat, lon=lon, radius=radius, type=type, shape=shape, how=how)
            turnpoints.append(turnpoint)
        task = Task(turnpoints, start_time, task_deadline)
        return task

    @classmethod
    def from_fsdb(cls, t, offset=0, keep_task_path=False):
        """ Creates Task from FSDB FsTask element, which is in xml format.
            Unfortunately the fsdb format isn't published so much of this is simply an
            exercise in reverse engineering.
        """
        from formula import TaskFormula
        from compUtils import get_fsdb_task_path
        from calcUtils import get_date, get_time, time_to_seconds

        tas = dict()
        stats = dict()
        turnpoints = []
        optimised_legs = []
        # results = []

        task = cls()

        task.check_launch = 'off'
        task.task_name = t.get('name')
        task.task_num = 0 + int(t.get('id'))
        print(f"task {task.task_num} - name: {task.task_name}")
        task.time_offset = offset
        if keep_task_path:
            task.task_path = get_fsdb_task_path(t.get('tracklog_folder'))

        """formula info"""
        formula = TaskFormula.from_fsdb(t)
        # f = t.find('FsScoreFormula')
        # formula = TaskFormula()
        # formula.formula_name = f.get('id')
        # formula.arr_alt_bonus = 'off'
        # if ((f.get('use_arrival_altitude_points') is not None and float(f.get('use_arrival_altitude_points')) > 0)
        #         or f.get('use_arrival_altitude_points') == 'aatb'):
        #     formula.arr_alt_bonus = 'on'
        # """Departure and Arrival from formula"""
        # formula.formula_arrival = 'position' if float(f.get('use_arrival_position_points')) == 1 else 'time' if float(
        #     f.get(
        #         'use_arrival_position_points')) == 1 else 'off'  # not sure if and which type Airscore is supporting at the moment
        # formula.tolerance = 0.0 + float(f.get('turnpoint_radius_tolerance')
        #                                 if f.get('turnpoint_radius_tolerance') else 0.1)  # tolerance, perc / 100
        #
        # if float(f.get('use_departure_points')) > 0:
        #     formula.formula_departure = 'on'
        # elif float(f.get('use_leading_points')) > 0:
        #     formula.formula_departure = 'leadout'
        # else:
        #     formula.formula_departure = 'off'

        """Task Status"""
        node = t.find('FsTaskState')
        formula.score_back_time = int(node.get('score_back_time')) * 60
        state = node.get('task_state')
        task.comment = ': '.join([state, node.get('cancel_reason')])
        if state == 'CANCELLED':
            """I don't need if cancelled"""
            return None
        task.stopped_time = time_to_seconds(get_time(node.get('stop_time'))) - offset
        # task.stopped_time = get_datetime(node.get('stop_time')) if not (state == 'REGULAR') else None
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
        qnh = None if node is None else float(node.get('qnh_setting').replace(',', '.')
                                              if node.get('qnh_setting') else 1013.25)
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
            last = len(node.findall('FsTurnpoint'))
            if node.find('FsStartGate') is None:
                '''elapsed time
                    on start gate, have to get start opening time from ss wpt'''
                task.task_type = 'elapsed time'
            else:
                '''race'''
                startgates = len(node.findall('FsStartGate'))
                task.task_type = 'race'
                task.start_time = time_to_seconds(get_time(node.find('FsStartGate').get('open'))) - offset
                # print ("gates: {}".format(startgates))
                if startgates > 1:
                    '''race with multiple start gates'''
                    # print ("MULTIPLE STARTS")
                    task.start_iteration = startgates - 1
                    time = time_to_seconds(get_time(node.findall('FsStartGate')[1].get('open'))) - offset
                    task.SS_interval = time - task.start_time
                    '''if prefer minutes: time_difference(tas['tasStartTime'], time).total_seconds()/60'''
                    print(f"    **** interval: {task.SS_interval}")

        """Task Route"""
        for idx, w in enumerate(node.iter('FsTurnpoint'), 1):
            if idx in [1, sswpt, eswpt, last]:
                if idx == 1:
                    '''launch'''
                    turnpoint = Turnpoint(float(w.get('lat')), float(w.get('lon')), int(w.get('radius')))
                    turnpoint.name = w.get('id')
                    turnpoint.num = len(turnpoints) + 1
                    turnpoint.type = 'launch'
                    task.date = get_date(w.get('open'))
                    task.window_open_time = time_to_seconds(get_time(w.get('open'))) - offset
                    task.window_close_time = time_to_seconds(get_time(w.get('close'))) - offset
                    if task.window_close_time <= task.window_open_time:
                        # sanity
                        task.window_close_time = None
                    if 'free distance' in task.task_type:
                        '''get start and close time for free distance task types'''
                        task.start_time = time_to_seconds(get_time(w.get('open'))) - offset
                        task.start_close_time = time_to_seconds(get_time(w.get('close'))) - offset
                    turnpoints.append(turnpoint)
                if idx == sswpt:
                    '''start'''
                    turnpoint = Turnpoint(float(w.get('lat')), float(w.get('lon')), int(w.get('radius')))
                    turnpoint.name = w.get('id')
                    turnpoint.num = len(turnpoints) + 1
                    turnpoint.type = 'speed'
                    task.start_close_time = time_to_seconds(get_time(w.get('close'))) - offset
                    '''guess start direction: exit if launch is same wpt'''
                    launch = next(p for p in turnpoints if p.type == 'launch')
                    if launch.lat == turnpoint.lat and launch.lon == turnpoint.lon:
                        turnpoint.how = 'exit'
                    if 'elapsed time' in task.task_type:
                        '''get start for elapsed time task types'''
                        task.start_time = time_to_seconds(get_time(w.get('open'))) - offset
                    turnpoints.append(turnpoint)
                if idx == eswpt:
                    '''ess'''
                    turnpoint = Turnpoint(float(w.get('lat')), float(w.get('lon')), int(w.get('radius')))
                    turnpoint.name = w.get('id')
                    turnpoint.num = len(turnpoints) + 1
                    turnpoint.type = 'endspeed'
                    task.task_deadline = time_to_seconds(get_time(w.get('close'))) - offset
                    turnpoints.append(turnpoint)
                if idx == last:
                    '''goal'''
                    turnpoint = Turnpoint(float(w.get('lat')), float(w.get('lon')), int(w.get('radius')))
                    turnpoint.name = w.get('id')
                    turnpoint.num = len(turnpoints) + 1
                    turnpoint.type = 'goal'
                    if gtype == 'LINE':
                        turnpoint.shape = 'line'
                    turnpoints.append(turnpoint)
            else:
                '''waypoint'''
                turnpoint = Turnpoint(float(w.get('lat')), float(w.get('lon')), int(w.get('radius')))
                turnpoint.name = w.get('id')
                turnpoint.num = len(turnpoints) + 1
                turnpoints.append(turnpoint)

            # turnpoint = Turnpoint(float(w.get('lat')), float(w.get('lon')), int(w.get('radius')))
            # turnpoint.id = len(turnpoints) + 1
            # turnpoint.name = w.get('id')
            # turnpoint.altitude = int(w.get('altitude'))
            # print(f"    {turnpoint.id}  {turnpoint.name}  {turnpoint.radius}")
            # if turnpoint.id == 1:
            #     turnpoint.type = 'launch'
            #     task.date = get_date(w.get('open'))
            #     task.window_open_time = time_to_seconds(get_time(w.get('open')))
            #     task.window_close_time = time_to_seconds(get_time(w.get('close')))
            #     # sanity
            #     if task.window_close_time <= task.window_open_time:
            #         task.window_close_time = None
            #     if 'free distance' in task.task_type:
            #         # print('Sono in launch - free')
            #         '''get start and close time for free distance task types'''
            #         task.start_time = time_to_seconds(get_time(w.get('open')))
            #         task.start_close_time = time_to_seconds(get_time(w.get('close')))
            #         # task.task_deadline = get_datetime(w.get('close'))
            #     if turnpoint.id == sswpt:
            #         '''need to manage tasks where first wpt is ss. adding a point as launch'''
            #         turnpoints.append(turnpoint)
            # if turnpoint.id == sswpt:
            #     # print('Sono in ss')
            #     turnpoint.type = 'speed'
            #     task.start_close_time = time_to_seconds(get_time(w.get('close')))
            #     if 'elapsed time' in task.task_type:
            #         '''get start for elapsed time task types'''
            #         task.start_time = time_to_seconds(get_time(w.get('open')))
            # elif turnpoint.id == eswpt:
            #     # print('Sono in es')
            #     turnpoint.type = 'endspeed'
            #     task.task_deadline = time_to_seconds(get_time(w.get('close')))
            #     if turnpoint.id == len(node.findall('FsTurnpoint')):
            #         '''need to manage tasks where last wpt is es. adding a point as es'''
            #         turnpoints.append(turnpoint)
            # if turnpoint.id == len(node.findall('FsTurnpoint')):
            #     # print('Sono in goal')
            #     turnpoint.type = 'goal'
            #     if gtype == 'LINE':
            #         turnpoint.shape = 'line'
            # # else:
            # #     wpt['tawType'] = 'waypoint'
            #
            # turnpoints.append(turnpoint)

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

    def calculate_optimised_task_length(self, method="fast_andoyer"):
        """ new optimized route procedure that uses John Stevenson on FAI Basecamp.
            trasforms wgs84 to plan trasverse cartesian projection, calculates
            optimised fix on cylinders, and goes back to wgs84 for distance calculations.
        """

        '''check we have at least 3 points'''
        if len(self.turnpoints) < 3:
            return

        '''calculate optimised distance fixes on cylinders'''
        if self.geo is None:
            self.create_projection()

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
        from db_tables import TblTaskWaypoint as W

        self.turnpoints.clear()
        self.optimised_turnpoints.clear()
        self.optimised_legs.clear()
        self.partial_distance.clear()
        self.legs.clear()
        self.projected_turnpoints.clear()
        self.projected_line.clear()

        '''delete waypoints from database'''
        with Database() as db:
            db.session.question.query(W).filter(W.task_id == self.id).delete()
            db.session.commit()

    def update_waypoints(self, session=None):
        from db_tables import TblTaskWaypoint as W
        insert_mappings = []
        update_mappings = []
        for idx, tp in enumerate(self.turnpoints):
            opt_lat, opt_lon, cumulative_dist = None, None, None
            if len(self.optimised_turnpoints) > 0:
                opt_lat, opt_lon = self.optimised_turnpoints[idx].lat, self.optimised_turnpoints[idx].lon
            if len(self.partial_distance) > 0:
                cumulative_dist = self.partial_distance[idx]
            tp.num = idx + 1
            wpt = dict(tp.as_dict(), task_id=self.id, ssr_lat=opt_lat, ssr_lon=opt_lon,
                       partial_distance=cumulative_dist)
            if tp.wpt_id:
                update_mappings.append(wpt)
            else:
                insert_mappings.append(wpt)
        with Database(session) as db:
            try:
                if update_mappings:
                    db.session.bulk_update_mappings(W, update_mappings)
                    db.session.flush()
                if insert_mappings:
                    db.session.bulk_insert_mappings(W, insert_mappings, return_defaults=True)
                    for elem in insert_mappings:
                        next(tp for tp in self.turnpoints if tp.num == elem['num']).wpt_id = elem['wpt_id']
                db.session.commit()
            except SQLAlchemyError as e:
                error = str(e.__dict__)
                print(f"Error storing task to database: {error}")
                db.session.rollback()
                db.session.close()
                return error

    def livetracking(self):
        from livetracking import get_livetracks, associate_livetracks, check_livetrack
        pilots = [p for p in self.pilots if p.info.live_id]
        if not pilots:
            print(f'*** NO PILOT with Live ID. Aborting ...')
            return False
        airspace = AirspaceCheck.from_task(self)
        i = 0
        response = []
        print(f'*** Task Deadline: {self.task_deadline}:')

        while max(p.result.last_time or 0 for p in pilots) < self.task_deadline:
            '''get livetracks from flymaster live server'''
            print(f'*** Cicle {i}:')
            print(f' -- Getting livetracks starting from time {max(p.result.last_time for p in pilots)} ...')
            previous = response
            response = get_livetracks(self)
            if not response or response == previous:
                print(f' -- NO RESPONSE. Stopping ...')
                break
            print(f' -- Associating livetracks ...')
            associate_livetracks(self, response)
            for p in pilots:
                if p.livetrack and p.livetrack[-2].rawtime > (p.result.last_time or 0) and not p.result.goal_time:
                    check_livetrack(pilot=p, task=self, airspace_obj=airspace)
                    print(f' -- -- Pilot {p.info.name}:')
                    # print(f' ..... -- last fix {p.livetrack[-2].rawtime}')
                    print(f' ..... -- rawtime: {p.result.last_time}')
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
            i += 1
        for p in pilots:
            print(f'Name: {p.name}')
            print(f'Waypoints achieved:')
            print(f'{p.result.waypoints_achieved}')
            print(f'Distance: {p.result.distance_flown}')
            print(f'Time: {p.result.time}')
            print(f'Notifications:')
            print(f'{p.result.notifications}')


def delete_task(task_id, files=False, session=None):
    from db_tables import TblTaskWaypoint as W
    from db_tables import TblTask as T
    from db_tables import TblTaskResult as R
    from db_tables import TblNotification as N
    from db_tables import TblResultFile as RF
    from db_tables import TblCompetition as C
    from result import delete_result
    from Defines import TRACKDIR
    import shutil
    from os import path
    '''delete waypoints and task from database'''
    print(f"{task_id}")
    with Database(session) as db:
        try:
            if files:
                '''delete track files'''
                info = db.session.query(T.task_path,
                                        C.comp_path).select_from(T).join(C, C.comp_id ==
                                                                         T.comp_id).filter(T.task_id == task_id).one()
                igc_folder = path.join(TRACKDIR, info.comp_path, info.task_path)
                tracklog_map_folder = path.join(MAPOBJDIR, 'tracks', str(task_id))
                task_map = path.join(MAPOBJDIR, 'tasks', str(task_id) + '.task')

                # remove igc files
                if path.exists(igc_folder):
                    shutil.rmtree(igc_folder)
                # remove tracklog map files
                if path.exists(tracklog_map_folder):
                    shutil.rmtree(tracklog_map_folder)
                # remove task map file
                if path.exists(task_map):
                    remove(task_map)
            results = db.session.query(RF.ref_id, RF.filename).filter(RF.task_id == task_id).all()
            if results:
                '''delete result json files'''
                for res in results:
                    delete_result(res.ref_id, res.filename, db.session)
            tracks = db.session.query(R.track_id).filter(R.task_id == task_id)
            if tracks:
                track_list = [t.track_id for t in tracks]
                db.session.query(N).filter(N.track_id.in_(track_list)).delete(synchronize_session=False)
                db.session.query(R).filter(R.task_id == task_id).delete(synchronize_session=False)
            '''delete db entries: results, waypoints, task'''
            # db.session.query(R).filter(T.task_id == task_id).delete(synchronize_session=False)
            db.session.query(W).filter(W.task_id == task_id).delete(synchronize_session=False)
            db.session.query(T).filter(T.task_id == task_id).delete(synchronize_session=False)
            db.session.commit()
        except SQLAlchemyError as e:
            error = str(e)
            print(f"Error deleting task from database: {error}")
            db.session.rollback()
            db.session.close()
            return error


# function to parse task object to compilations
def get_map_json(task_id):
    """gets task map json file if it exists, otherwise creates it. returns 5 separate objects for mapping"""

    task_file = Path(MAPOBJDIR + 'tasks/' + str(task_id) + '.task')
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
    from mapUtils import get_route_bbox

    geod = Geodesic.WGS84
    task_file = Path(MAPOBJDIR + 'tasks/' + str(task_id) + '.task')

    if not os.path.isdir(MAPOBJDIR + 'tasks/'):
        os.makedirs(MAPOBJDIR + 'tasks/')
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
    from db_tables import TblResultFile as R
    with Database() as db:
        filename = db.session.query(R.filename).filter(and_(
            R.task_id == task_id, R.active == 1
        )).scalar()
    return filename


def get_task_json(task_id):
    filename = get_task_json_filename(task_id)
    return get_task_json_by_filename(filename)


def get_task_json_by_filename(filename):
    try:
        with open(RESULTDIR + filename, 'r') as myfile:
            data = myfile.read()
    except:
            return None
    return json.loads(data)