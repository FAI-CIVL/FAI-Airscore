"""
Task Library

contains
    Task class
    get_map_json and write_map_json - json files for task map

Use: from task import Task

Stuart Mackintosh - 2019

TO DO:
Add support for FAI Sphere ???
"""

from route      import distance, polar, find_closest, cartesian2polar, polar2cartesian, calcBearing, opt_goal, opt_wp, \
                        opt_wp_exit, opt_wp_enter, Turnpoint
from myconn     import Database
from formula    import Task_formula
from calcUtils  import json, get_datetime, decimal_to_seconds, time_difference
from igc_lib    import defaultdict
from pathlib    import Path
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
        create_from_fsdb: read fsdb xml file, create task object

        task distance:
        calculate_task_length: calculate non optimised distances.
        calculate_optimised_task_length_old: find optimised distances and waypoints. old perl method, no longer used
        calculate_optimised_task_length: find optimised distances and waypoints.
        distances_to_go: calculates distance from each waypoint to goal
    """

    def __init__(self, task_id=None, task_type=None, start_time=None, task_deadline=None,
                    stopped_time=None, check_launch='off'):
        self.id                         = task_id
        self.task_type                  = task_type
        self.start_time                 = start_time
        self.task_deadline              = task_deadline     # seconds from midnight: task deadline
        self.stopped_time               = stopped_time      # seconds from midnight: time task was stopped (TaskStopAnnouncementTime).
        self.check_launch               = check_launch      # check launch flag. whether we check that pilots leave from launch.
        self.comp_id                    = None
        self.comp_name                  = None
        self.comp_site                  = None
        self.comp_class                 = None
        self.date                       = None              # in Y-m-d format
        self.task_name                  = None
        self.task_code                  = None
        self.window_open_time           = None              # seconds from midnight: takeoff window opening time (or any earlier pilots were permitted to take off)
        self.window_close_time          = None              # seconds from midnight: not managed yet
        self.start_close_time           = None
        self.SS_interval                = 0                 # seconds: Interval among start gates when more than one
        self.opt_dist                   = 0
        self.opt_dist_to_SS             = 0
        self.opt_dist_to_ESS            = 0
        self.SS_distance                = 0
        self.distance                   = 0                 # non optimised distance
        self.turnpoints                 = []                # list of Turnpoint objects
        self.optimised_turnpoints       = []                # fixes on cylinders for opt route
        self.optimised_legs             = []                # opt distance between cylinders
        self.partial_distance           = []                # distance from launch to waypoint
        self.legs                       = []                # non optimised legs
        self.stats                      = dict()            # scored task statistics
        # self.results = []  #scored task results
        self.comment                    = None
        self.time_offset                = 0                 # seconds
        self.launch_valid               = None
        self.stop_time                  = None              # seconds from midnight, task stopTime
        self.duration                   = None              # seconds, duration of track time in stopped task (PG, some cases)

        self.formula                    = Task_formula.read(self.id) if self.id else None

    def __str__(self):
        out = ''
        out += 'Task:'
        out += '{} - {} | Date: {} \n'.format(self.comp_name, self.task_name, self.date)
        out += '{} \n'.format(self.comment)
        for wpt in self.turnpoints:
            out += '  {}  {}  {} km \n'.format(wpt.name, wpt.type, round(wpt.radius/1000, 2))
        out += 'Task Opt. Distance: {} Km \n'.format(round(self.opt_dist/1000,2))
        return out

    @property
    def last_start_time(self):
        return self.stats['last_SS'] if self.stats else 0

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

    @staticmethod
    def read(task_id):
        """Reads Task from database
        takes tasPk as argument"""
        from db_tables import TaskObjectView as T, TaskWaypointView as W

        if not (type(task_id) is int and task_id > 0):
            print("task not present in database ", task_id)
            return None

        task = Task(task_id)

        with Database() as db:
            # get the task details.
            t   = db.session.query(T)
            w   = db.session.query(W)
            db.populate_obj(task, t.get(task_id))
            tps = w.filter(W.task_id==task_id).order_by(W.partial_distance)
        for tp in tps:
            turnpoint = Turnpoint(tp.lat, tp.lon, tp.radius, tp.type.strip(),
                                  tp.shape, tp.how, tp.altitude, tp.name,
                                  tp.description, tp.id, tp.rwpPk)
            task.turnpoints.append(turnpoint)
            s_point = polar(lat=tp.ssr_lat,lon=tp.ssr_lon)
            task.optimised_turnpoints.append(s_point)
            if tp.partial_distance is not None: #this will be None in DB before we optimise route, but we append to this list so we should not fill it with Nones
                task.partial_distance.append(tp.partial_distance)

        return task

    def create_scoring(self, status=None, mode='default'):
        '''
            Create Scoring
            - if necessary,recalcutales all tracks (stopped task, changed task settings)
            - gets info about formula, pilots results
            - calculates scores
            - creates a json file
            - adds json file to database

            Inputs:
            - status:   str - 'provisional', 'final', 'official' ...
            - mode:     str - 'default'
                              'full'    recalculates all tracks
        '''
        from result     import Task_result as R
        from pprint     import pprint as pp

        '''retrieve scoring formula library'''
        lib = self.formula.get_lib()

        if ( mode == 'full' or self.stopped_time ):
            # TODO: check if we changed task, or we had new tracks, after last results generation
            #       If this is the case we should not need to rescore unless especially requested
            '''Task Full Rescore
                - recalculate Opt. route
                - check all tracks'''
            self.calculate_task_length()
            self.calculate_optimised_task_length()
            self.update_task_distance()
            self.check_all_tracks(lib)

        self.stats.update(lib.task_totals(self.id))

        if self.stats['pilots_present'] == 0:
            print(f'''Task (ID {self.id}) has no results yet''')
            return 0

        self.stats.update(lib.day_quality(self))
        results = lib.points_allocation(self)
        ref_id  = R.create_result(self, results, status)
        return ref_id

    def is_valid(self):
        '''In stopped task, check if duration is enough to be valid'''
        if not self.stopped_time:
            print(f'Task (ID {self.id}) has not been stopped.')
            return True

        if self.comp_class == 'PG' :
            '''
            We need to calculate stopTime from announcingTime
            In paragliding the score-back time is set as part of the competition parameters
            (see section 5.7).
            taskStopTime = taskStopAnnouncementTime − competitionScoreBackTime
            In paragliding, a stopped task will be scored if the flying time was one hour or more.
            For Race to Goal tasks, this means that the Task Stop Time must be one hour or more
            after the race start time.
            minimumTime = 60 min .
            typeOfTask = RaceToGoal ∧ numberOfStartGates = 1:
                taskStopTime − startTime < minimumTime : taskValidity = 0
            TypeOfTask ≠ RaceToGoal ∨ numberOfStartGates > 1:
                taskStopTime − max(∀p :p ∈ StartedPilots :startTime p ) < minimumTime : taskValidity = 0
            '''

            min_task_duration   = 3600
            last_time           = self.stopped_time - self.formula.score_back_time
            if (self.task_type == 'elapsed time' or self.SS_interval) and self.last_start_time:
                duration        = last_time - self.last_start_time
            else:
                duration        = last_time - self.start_time

        elif task.comp_class == 'HG':
            '''
            In hang-gliding, stopped tasks are “scored back” by a time that is determined
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

            if self.stats['pilots_goal']:
                return True
            elif self.stats['pilots_goal'] is None:
                print(f'Tracks (Task ID {self.id}) have not been checked yet or stats have not been updated.')
                return False
            min_task_duration = 3600 * 1.5 # 90 min
            last_time   = ( (self.stopped_time - self.formula.score_back_time)
                            if not self.SS_interval
                            else (self.stopped_time - self.SS_interval))
            duration    = last_time - self.start_time

        if duration < min_task_duration:
            return False
        else:
            self.duration   = duration
            self.stop_time  = last_time
            return True

    def check_all_tracks(self, lib = None):
        ''' checks all igc files against Task and creates results '''

        from flight_result import verify_all_tracks, adjust_flight_results, update_all_results

        if not lib:
            '''retrieve scoring formula library'''
            lib = self.formula.get_lib()

        ''' manage Stopped Task    '''
        print(f'stopped time: {self.stopped_time}')
        if self.stopped_time:
            print(f'We are executing Stopped Task Routine')
            if self.comp_class == 'PG' :
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
                results = verify_all_tracks(self, lib)
                update_all_results(results)     #avoidable if we use results to update stats instead of db

                if self.task_type == 'elapsed time' or self.SS_interval:
                    '''need to check track and get last_start_time'''
                    self.stats.update(lib.task_totals(self.id))
                    # duration = last_time - self.last_start_time
                    if not self.is_valid():
                        return f'duration is not enough for all pilots, task with id {self.id} is not valid, scoring is not needed.'
                    results = adjust_flight_results(self, results, lib)

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

                if not self.is_valid():
                    return f'task duration is not enough, task with id {self.id} is not valid, scoring is not needed'

                results = verify_all_tracks(self, lib)

        else:
            '''get all results for the task'''
            results = verify_all_tracks(self, lib)

        '''store results to database'''
        update_all_results(results)

    def update_task_distance(self):
        from db_tables import tblTask as T, tblTaskWaypoint as W
        with Database() as db:
            '''add optimised and total distance to task'''
            q = db.session.query(T)
            t = q.get(self.id)
            t.tasDistance           = self.distance
            t.tasShortRouteDistance = self.opt_dist
            t.tasSSDistance         = self.SS_distance
            t.tasEndSSDistance      = self.opt_dist_to_ESS
            t.tasStartSSDistance    = self.opt_dist_to_SS
            db.session.commit()

            '''add opt legs to task wpt'''
            w = db.session.query(W)
            for idx, tp in enumerate(self.turnpoints):
                sr  = self.optimised_turnpoints[idx]
                wpt = w.get(tp.id)
                wpt.ssrLatDecimal       = sr.lat
                wpt.ssrLongDecimal      = sr.lon
                wpt.ssrCumulativeDist   = self.partial_distance[idx]
                db.session.commit()

    def update_task_info(self):
        with Database() as db:
            start_time          = self.start_time + self.time_offset
            task_deadline       = self.task_deadline + self.time_offset
            task_start          = self.window_open_time + self.time_offset
            start_close_time    = self.start_close_time + self.time_offset
            start_interval      = int(self.SS_interval / 60)
            task_type           = self.task_type.lower()

            sql = """  UPDATE
                            `tblTask`
                        SET
                            `tasStartTime` = DATE_ADD(
                                `tasDate`,
                                INTERVAL %s SECOND
                            ),
                            `tasFinishTime` = DATE_ADD(
                                `tasDate`,
                                INTERVAL %s SECOND
                            ),
                            `tasTaskStart` = DATE_ADD(
                                `tasDate`,
                                INTERVAL %s SECOND
                            ),
                            `tasStartCloseTime` = DATE_ADD(
                                `tasDate`,
                                INTERVAL %s SECOND
                            ),
                            `tasSSInterval` = %s,
                            `tasTaskType` = %s
                        WHERE
                            `tasPk` = %s """
            params = [start_time, task_deadline, task_start, start_close_time, start_interval, task_type, self.id]
            #update start and deadline
            db.execute(sql, params)

    def update_from_xctrack_file(self, filename):
        """ Updates Task from xctrack file, which is in json format.
        """
        from compUtils import get_wpts
        from calcUtils import string_to_seconds

        offset = 0
        task_file = filename

        #turnpoints = []
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

        self.start_time     = string_to_seconds(startopenzulu)
        self.task_deadline  = string_to_seconds(deadlinezulu)

        '''check task start and start close times are ok for new start time
        we will check to be at least 1 hour before and after'''
        if not self.window_open_time or self.start_time - self.window_open_time < 3600:
            self.window_open_time = self.start_time - 3600
        if not self.start_close_time or self.start_close_time - self.start_time < 3600:
            self.start_close_time = self.start_time + 3600

        if t['sss']['type'] == 'ELAPSED-TIME': self.task_type = 'ELAPSED TIME'
        else:
            self.task_type = 'RACE'
            '''manage multi start'''
            self.SS_interval = 0
            if len(t['sss']['timeGates']) > 1:
                second_start            = string_to_seconds(t['sss']['timeGates'][1])
                self.SS_interval         = int((second_start - self.start_time) / 60)    # interval in minutes
                self.start_close_time   = int(self.start_time + len(t['sss']['timeGates']) * (second_start - self.start_time)) - 1

        print('xct start:       {} '.format(self.start_time))
        print('xct deadline:    {} '.format(self.task_deadline))

        waypoint_list = get_wpts(self.id)
        print('n. waypoints: {}'.format(len(t['turnpoints'])))

        for i, tp in enumerate(t['turnpoints']):
            waytype = "waypoint"
            shape = "circle"
            how = "entry"  #default entry .. looks like xctrack doesn't support exit cylinders apart from SSS
            wpID = waypoint_list[tp["waypoint"]["name"]]
            #wpNum = i+1

            if i < len(t['turnpoints']) -1:
                if 'type' in tp :
                    if tp['type'] == 'TAKEOFF':
                        waytype = "launch"  #live
                        #waytype = "start"  #aws
                        how = "exit"
                    elif tp['type'] == 'SSS':
                        waytype = "speed"
                        if t['sss']['direction'] == "EXIT":  #get the direction form the SSS section
                            how = "exit"
                    elif tp['type'] == 'ESS':
                        waytype = "endspeed"
            else:
                waytype = "goal"
                if t['goal']['type'] == 'LINE':
                    shape = "line"

            turnpoint = Turnpoint(tp['waypoint']['lat'], tp['waypoint']['lon'], tp['radius'], waytype, shape, how)
            turnpoint.name  = tp["waypoint"]["name"]
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
    def create_from_json(task_id, filename = None):
        """ Creates Task from JSON task file.
            If filename is empty, it gets the active one
            Inputs:
                task_id     int: task ID
                filename    str: (opt.) json filename

        """
        from os             import path as p
        from result         import get_task_json
        from flight_result  import Flight_result

        if not filename or not p.isfile(filename):
            '''we get the active json file'''
            filename = get_task_json(task_id)

        if not filename:
            print(f"There's no active json file for task {task_id}, or given filename does not exists")
            return None

        print(f"task {task_id} json file: {filename}")


        # info        = {}
        # turnpoints  = []

        with open(filename, encoding='utf-8') as json_data:
            # a bit more checking..
            try:
                t = json.load(json_data)
            except:
                print("file is not a valid JSON object")
                return None

        # info = dict(t['info'])

        task = Task(task_id)
        task.__dict__.update(dict(t['info']))
        task.stats.update(dict(t['stats']))
        task.turnpoints = []

        for id, tp in enumerate(t['task']):
            '''creating waypoints'''
            # I could take them from database, but this is the only way to be sure it is the correct one
            turnpoint = Turnpoint(tp['lat'], tp['lon'], tp['radius'], tp['type'],
                                  tp['shape'], tp['how'])

            turnpoint.name          = tp['name']
            turnpoint.id            = id+1
            turnpoint.description   = tp['description']
            turnpoint.altitude      = tp['altitude']
            task.turnpoints.append(turnpoint)
            task.partial_distance.append(tp['cumulative_dist'])

        task.results = []

        for pil in t['results']:
            ''' create Flight_result objects from json list'''
            # should unify property names
            result = Flight_result(pil_id=pil['pil_id'], track_file = pil['track_file'])
            result.distance_flown           = pil['distance']
            result.first_time               = pil['first_time']
            result.SSS_time                 = pil['SS_time']
            result.real_start_time         = pil['start_time']
            result.ESS_time                 = pil['ES_time']
            result.goal_time                = pil['goal_time']
            result.best_waypoint_achieved   = pil['turnpoints_made']
            result.last_time                = pil['last_time']
            result.lead_coeff               = pil['lead_coeff']
            result.ESS_altitude             = pil['ESS_altitude']
            result.goal_altitude            = pil['goal_altitude']
            result.max_altitude             = pil['max_altitude']
            result.last_altitude            = pil['last_altitude']
            result.distance_score           = pil['dist_points']
            result.departure_score          = pil['dep_points']
            result.arrival_score            = pil['arr_points']
            result.time_score               = pil['time_points']
            result.penalty                  = pil['penalty']
            result.comment                  = pil['comment']
            result.score                    = pil['score']
            result.result_type              = pil['result']

            task.results.append(result)

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
    def create_from_fsdb(cls, t):
        """ Creates Task from FSDB FsTask element, which is in xml format.
            Unfortunately the fsdb format isn't published so much of this is simply an
            exercise in reverse engineering.
        """
        tas             = dict()
        stats           = dict()
        turnpoints      = []
        optimised_legs  = []
        #results = []

        #t = tree.getroot()
        tas['tasCheckLaunch']   = 0
        tas['tasName']          = t.get('name')
        tas['id']               = 0 + int(t.get('id'))
        #print ("task id: {} - name: {}".format(tas['id'], tas['tasName']))

        """formula info"""
        f = t.find('FsScoreFormula')
        tas['tasHeightBonus']   = 'off'
        if ((f.get('use_arrival_altitude_points') is not None and float(f.get('use_arrival_altitude_points')) > 0)
            or f.get('use_arrival_altitude_points') is 'aatb'):
            tas['tasHeightBonus'] = 'on'
        """Departure and Arrival from formula"""
        tas['tasArrival']       = 'on' if float(f.get('use_arrival_position_points') + f.get('use_arrival_position_points')) > 0 else 'off' #not sure if and which type Airscore is supporting at the moment
        tas['tolerance']        = 0 + float(f.get('turnpoint_radius_tolerance')) * 100  # tolerance

        if float(f.get('use_departure_points')) > 0:
            tas['tasDeparture'] = 'on'
        elif float(f.get('use_leading_points')) > 0:
            tas['tasDeparture'] = 'leadout'
        else:
            tas['tasDeparture'] = 'off'

        """Task Status"""
        node = t.find('FsTaskState')
        tas['tasComment'] = None
        tas['forScorebackTime'] = int(node.get('score_back_time'))
        tas['state'] = node.get('task_state')
        tas['tasComment'] = node.get('cancel_reason')
        if tas['state'] is not 'CANCELLED':
            """I don't need if cancelled"""
            tas['tasStoppedTime'] = get_datetime(node.get('stop_time')) if not (tas['state'] == 'REGULAR') else None
            """Task Stats"""
            p = t.find('FsTaskScoreParams')
            if p is not None:
                '''a non scored task could miss this element'''
                tas['tasShortRouteDistance'] = float(p.get('task_distance'))
                tas['tasDistance'] = float(p.get('task_distance')) #need to calculate distance through centers
                tas['tasSSDistance'] = float(p.get('ss_distance'))
                stats['pilots_present'] = int(p.get('no_of_pilots_present'))
                stats['pilots_launched'] = int(p.get('no_of_pilots_flying'))
                stats['pilots_goal'] = int(p.get('no_of_pilots_reaching_goal'))
                stats['max_distance'] = float(p.get('best_dist')) * 1000 # in meters
                stats['totdistovermin'] = float(p.get('sum_flown_distance')) * 1000 # in meters
                try:
                    '''happens this values are error strings'''
                    stats['day_quality'] = float(p.get('day_quality'))
                    stats['dist_validity'] = float(p.get('distance_validity'))
                    stats['time_validity'] = float(p.get('time_validity'))
                    stats['launch_validity'] = float(p.get('launch_validity'))
                    stats['stop_validity'] = float(p.get('stop_validity'))
                    stats['avail_dist_points'] = float(p.get('available_points_distance'))
                    stats['avail_dep_points'] = float(p.get('available_points_leading'))
                    stats['avail_time_points'] = float(p.get('available_points_time'))
                    stats['avail_arr_points'] = float(p.get('available_points_arrival'))
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
                stats['fastest'] = decimal_to_seconds(float(p.get('best_time'))) if float(p.get('best_time')) > 0 else 0
            for l in p.iter('FsTaskDistToTp'):
                optimised_legs.append(float(l.get('distance'))*1000)

        node = t.find('FsTaskDefinition')
        tas['qnh'] = float(node.get('qnh_setting').replace(',', '.'))
        #tas['tasDate'] = get_datetime(node.find('FsStartGate').get('open'))
        """guessing type from startgates"""
        tas['tasSSInterval'] = 0
        startgates = 0
        headingpoint = 0
        if node.get('ss') is None:
            '''open distance
                not yet implemented in Airscore'''
            tas['tasTaskType'] = 'free distance'
            if node.find('FsHeadingpoint') is not None:
                '''open distance with bearing'''
                headingpoint = 1
                tas['tasTaskType'] = 'distance with bearing'
                tas['tasBearingLat'] = float(node.find('FsHeadingpoint').get('lat'))
                tas['tasBearingLon'] = float(node.find('FsHeadingpoint').get('lon'))
        else:
            sswpt = int(node.get('ss'))
            eswpt = int(node.get('es'))
            gtype = node.get('goal')
            tas['gstart'] = int(node.get('groundstart'))
            if node.find('FsStartGate') is None:
                '''elapsed time
                    on start gate, have to get start opening time from ss wpt'''
                tas['tasTaskType'] = 'elapsed time'
            else:
                '''race'''
                startgates = len(node.findall('FsStartGate'))
                tas['tasTaskType'] = 'race'
                tas['tasStartTime'] = get_datetime(node.find('FsStartGate').get('open'))
                #print ("gates: {}".format(startgates))
                if startgates > 1:
                    '''race with multiple start gates'''
                    #print ("MULTIPLE STARTS")
                    time = get_datetime(node.findall('FsStartGate')[1].get('open')).time()
                    interval = time_difference(tas['tasStartTime'].time(), time)
                    '''if prefer minutes: time_difference(tas['tasStartTime'], time).total_seconds()/60'''
                    print ("    **** interval: {}".format(interval))
                    tas['tasSSInterval'] = interval
        #print ("task type: {} - Interval: {}".format(tas['tasTaskType'], tas['tasSSInterval']))

        """Task Route"""
        for w in node.iter('FsTurnpoint'):
            wpt = dict()
            wpt['tawNumber'] = len(turnpoints) + 1
            #wpt['ssrCumulativeDist'] = c_dist.pop(0)
            wpt['rwpName'] = w.get('id')
            #print ("wpt id: {} ".format(wpt['id']))
            wpt['rwpLatDecimal'] = float(w.get('lat'))
            wpt['rwpLonDecimal'] = float(w.get('lon'))
            wpt['rwpAltitude'] = int(w.get('altitude'))
            wpt['tawRadius'] = int(w.get('radius'))
            #print ("radius: {} \n".format(wpt['radius']))
            wpt['tawShape'] = 'circle'
            #print ("   len(node) = {} - wpt['tawNumber'] = {} \n".format(len(node), wpt['tawNumber']))
            if wpt['tawNumber'] == 1:
                #print('Sono in launch')
                wpt['tawType'] = 'launch'
                tas['tasDate'] = get_datetime(w.get('open')).date()
                tas['tasTaskStart'] = get_datetime(w.get('open'))
                if 'free distance' in tas['tasTaskType']:
                    #print('Sono in launch - free')
                    '''get start and close time for free distance task types'''
                    tas['tasStartTime'] = get_datetime(w.get('open'))
                    tas['tasStartCloseTime'] = get_datetime(w.get('close'))
                    tas['tasFinishTime'] = get_datetime(w.get('close'))
            elif wpt['tawNumber'] == sswpt:
                #print('Sono in ss')
                wpt['tawType'] = 'speed'
                tas['tasStartCloseTime'] = get_datetime(w.get('close'))
                if 'elapsed time' in tas['tasTaskType']:
                    '''get start for elapsed time task types'''
                    tas['tasStartTime'] = get_datetime(w.get('open'))
            elif wpt['tawNumber'] == eswpt:
                #print('Sono in es')
                wpt['tawType'] = 'endspeed'
                tas['tasFinishTime'] = get_datetime(w.get('close'))
            elif wpt['tawNumber'] == len(node) - startgates - headingpoint: #need to remove FsStartGate and FsHeadingpoint nodes from count
                #print('Sono in goal')
                wpt['tawType'] = 'goal'
                if gtype == 'LINE':
                    wpt['tawShape'] = 'line'
            else:
                wpt['tawType'] = 'waypoint'

            turnpoint = Turnpoint(wpt['rwpLatDecimal'], wpt['rwpLonDecimal'], wpt['tawRadius'], wpt['tawType'], wpt['tawShape'], 'entry')
            turnpoint.name = wpt['rwpName']
            turnpoint.id = wpt['tawNumber']
            turnpoint.altitude = wpt['rwpAltitude']
            turnpoints.append(turnpoint)

        #tas['route'] = route
        task = cls(turnpoints, tas['tasStartTime'], tas['tasFinishTime'], tas['tasTaskType'], tas['tasStoppedTime'])
        task.task_name = tas['tasName']
        task.window_open_time = tas['tasTaskStart']
        task.start_close_time = tas['tasStartCloseTime']
        task.opt_dist = tas['tasShortRouteDistance'] * 1000 # in meters
        task.SS_distance = tas['tasSSDistance'] * 1000 # in meters
        task.arrival = tas['tasArrival']
        task.departure = tas['tasDeparture']
        task.arr_alt_bonus = tas['tasHeightBonus']
        task.comment = tas['tasComment']
        task.calculate_task_length()
        #print ("Tot. Dist.: {}".format(task.distance))
        task.stats = stats
        task.optimised_legs = optimised_legs
        #task.results = results
        #print ("{} - date: {} - type: {} - dist.: {} - opt. dist.: {}".format(task.task_name, task.window_open_time.date(), task.task_type, task.distance, task.opt_dist))
        #print ("open: {} - start: {} - close: {} - end: {} \n".format(task.window_open_time, task.start_time, task.start_close_time, task.task_deadline))

        return task

    def calculate_task_length(self, method="fast_andoyer"):
        # calculate non optimised route distance.
        self.distance = 0
        for wpt in range(1, len(self.turnpoints)):
            leg_dist = distance(self.turnpoints[wpt - 1], self.turnpoints[wpt], method)
            self.legs.append(leg_dist)
            self.distance += leg_dist
            #print ("leg dist.: {} - Dist.: {}".format(leg_dist, self.distance))

    def calculate_optimised_task_length_old(self, method="fast_andoyer"):

        it1 = []
        it2 = []
        wpts = self.turnpoints
        self.opt_dist = 0  #reset in case of recalc.

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
                sss_wpt = wpt+1
            if self.turnpoints[wpt].type == 'endspeed':
                ess_wpt = wpt+1

        # work out self.opt_dist_to_SS, self.opt_dist_to_ESS, self.SS_distance
        self.opt_dist_to_SS = sum(self.optimised_legs[0:sss_wpt])
        self.opt_dist_to_ESS = sum(self.optimised_legs[0:ess_wpt])
        self.SS_distance = sum(self.optimised_legs[sss_wpt:ess_wpt])
        self.optimised_turnpoints = closearr

    def calculate_optimised_task_length_fast_andoyer(self, method="fast_andoyer"):
        from geographiclib.geodesic import Geodesic
        geod = Geodesic.WGS84
        wpts = self.turnpoints
        self.opt_dist = 0  #reset in case of recalc.

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

            #print(f'{t} of{len(self.turnpoints)}')
            t2 = self.turnpoints[t + 1]

            if t + 2 > len(self.turnpoints)-1:
                t3 = None
            else:
                t3 = self.turnpoints[t + 2]

            opt = opt_wp(t1, t2, t3, t2.radius)

            if exit_same:
                p = geod.Direct(t1.lat, t1.lon, calcBearing(t1.lat, t1.lon, opt.lat, opt.lon),
                                self.turnpoints[t].radius)
                opt_exit = Turnpoint(lat=p['lat2'], lon=p['lon2'], type='optimised', radius=0, shape='optimised', how='optimised')
                optimised.append(opt_exit)
            if exit_different:
                opt_exit = opt_wp_exit(opt, t1, self.turnpoints[t])
                optimised.append(opt_exit)
            if enter_same:
                p = geod.Direct(t2.lat, t2.lon, calcBearing(t2.lat, t2.lon, t1.lat, t1.lon), self.turnpoints[t].radius)
                opt_enter = Turnpoint(lat=p['lat2'], lon=p['lon2'], type='optimised', radius=0, shape='optimised', how='optimised')
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
                sss_wpt = wpt+1
            if self.turnpoints[wpt].type == 'endspeed':
                ess_wpt = wpt+1

        # work out self.opt_dist_to_SS, self.opt_dist_to_ESS, self.SS_distance
        self.opt_dist_to_SS = sum(self.optimised_legs[0:sss_wpt])
        self.opt_dist_to_ESS = sum(self.optimised_legs[0:ess_wpt])
        self.SS_distance = sum(self.optimised_legs[sss_wpt:ess_wpt])
        self.optimised_turnpoints = optimised

    def calculate_optimised_task_length(self, method="fast_andoyer"):
        ''' new optimized route procedure that uses John Stevenson on FAI Basecamp.
            trasforms wgs84 to plan trasverse cartesian projection, calculates
            optimised fix on cilynders, and goes back to wgs84 for distance calculations.
        '''
        from route import get_shortest_path

        '''calculate optimised distance fixes on cilynders'''
        optimised = get_shortest_path(self)

        '''updates all task attributes'''
        self.optimised_legs = []
        self.optimised_legs.append(0)
        self.partial_distance = []
        self.partial_distance.append(0)
        self.opt_dist = 0
        for i in range(1, len(optimised)):
            leg_dist = distance(optimised[i-1], optimised[i], method)
            self.optimised_legs.append(leg_dist)
            self.opt_dist += leg_dist
            self.partial_distance.append(self.opt_dist)

        # work out which turnpoints are SSS and ESS
        sss_wpt = 0
        ess_wpt = 0
        for wpt in range(len(self.turnpoints)):
            if self.turnpoints[wpt].type == 'speed':
                sss_wpt = wpt+1
            if self.turnpoints[wpt].type == 'endspeed':
                ess_wpt = wpt+1

        # work out self.opt_dist_to_SS, self.opt_dist_to_ESS, self.SS_distance
        self.opt_dist_to_SS = sum(self.optimised_legs[0:sss_wpt])
        self.opt_dist_to_ESS = sum(self.optimised_legs[0:ess_wpt])
        self.SS_distance = sum(self.optimised_legs[sss_wpt:ess_wpt])
        self.optimised_turnpoints = optimised

        # ''' update task short route'''
        # with Database() as db:
        #     query = ''
        #     for idx, item in enumerate(task.turnpoints):
        #         tp = task.optimised_turnpoints[idx]
        #         query = """ UPDATE `tblTaskWaypoint`
        #                     SET
        #                         `ssrLatDecimal` = %s,
        #                         `ssrLongDecimal` = %s
        #                     WHERE `tawPk` = %s
        #                     LIMIT 1"""
        #
        #         params = [tp.lat, tp.lon, item.id]
        #         db.execute(query, params)

    def clear_waypoints(self):
        self.turnpoints.clear()
        self.optimised_turnpoints.clear()
        self.optimised_legs.clear()
        self.partial_distance.clear()
        self.legs.clear()

        '''delete waypoints from database'''
        with Database() as db:
            query = """DELETE FROM `tblTaskWaypoint`
                        WHERE `tasPk` = %s"""
            db.execute(query, [self.id])

    def update_waypoints(self):
        for idx, wp in enumerate(self.turnpoints):
            wpNum = idx + 1
            with Database() as db:
                sql = """  INSERT INTO `tblTaskWaypoint`(
                                `tasPk`,
                                `rwpPk`,
                                `tawNumber`,
                                `tawType`,
                                `tawHow`,
                                `tawShape`,
                                `tawTime`,
                                `tawRadius`
                                )
                            VALUES(%s,%s,%s,%s,%s,%s,'0',%s)"""
                params = [self.id, wp.rwpPk, wpNum, wp.type, wp.how, wp.shape, wp.radius]
                id = db.execute(sql, params)
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

    task_file = Path(Defines.MAPOBJDIR+'tasks/'+str(task_id) + '.task')
    if not task_file.is_file():
        write_map_json(task_id)
    else:
        with open(task_file, 'r') as f:
            data = jsonpickle.decode(f.read())
            #print (data)
            task_coords = data['task_coords']
            turnpoints = data['turnpoints']
            short_route = data['short_route']
            goal_line = data['goal_line']
            tolerance = data['tolerance']

    return task_coords, turnpoints, short_route, goal_line, tolerance

def write_map_json(task_id):
    import os
    from geographiclib.geodesic import Geodesic
    from route import get_line
    from mapUtils import get_route_bbox

    geod = Geodesic.WGS84
    task_file = Path(Defines.MAPOBJDIR+'tasks/'+str(task_id) + '.task')

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
                                  'goal_line': goal_line, 'tolerance': tolerance}))
