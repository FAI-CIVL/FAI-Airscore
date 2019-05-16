from calcUtils import get_datetime
from route import rawtime_float_to_hms, in_semicircle, distance_flown
from myconn import Database

"""
contains Flight_result class.
contains statistics about a flight with regards to a task.

Methods:
    from_fsdb
    check_flight - check flight against task and record results (times, distances and leadout coeff)
    store_result - write result to DB (tblTaskResult)
    store_result_test - write result to DB in test mode(tblTaskResult_test)
"""


class Flight_result:
    """Set of statistics about a flight with respect a task.
    Attributes:
        Start_time: time the task was started . i.e relevant start gate. (local time)
        SSS_time: array of time(s) the pilot started, i.e. crossed the start line (local time)
        Waypoints achieved: the last waypoint achieved by the pilot, SSS, ESS, Goal or a waypoint number (wp1 is first wp after SSS)
        ESS_time: the time the pilot crossed the ESS (local time)
        total_time: the length of time the pilot took to complete the course. ESS- Start_time (for Race) or ESS - SSS_time (for elapsed)
        Lead_coeff: lead points coeff (for GAP based systems)
        """

    def __init__(self, Pilot_Start_time=None, SSS_time=0, Start_time_str='', SSS_time_str='',
                 Best_waypoint_achieved='No waypoints achieved', ESS_time_str='', total_time_str=None, ESS_time=None,
                 total_time=None, Lead_coeff=0, Distance_flown=0, Stopped_time = None, Stopped_altitude = 0, Jumped_the_gun=None):
        """

        :type Lead_coeff: int
        """
        self.Start_time_str = Start_time_str
        self.SSS_time_str = SSS_time_str
        self.Pilot_Start_time = Pilot_Start_time
        self.SSS_time = SSS_time
        self.Best_waypoint_achieved = Best_waypoint_achieved
        self.Waypoints_achieved = []
        self.ESS_time = ESS_time
        self.total_time = total_time
        self.ESS_time_str = ESS_time_str
        self.total_time_str = total_time
        self.Lead_coeff = Lead_coeff
        self.Distance_flown = Distance_flown
        self.Stopped_time = Stopped_time
        self.Stopped_altitude = Stopped_altitude
        self.Jumped_the_gun = Jumped_the_gun
        self.Score = 0
        self.Total_distance = 0
        self.Departure_score = 0
        self.Arrival_score = 0
        self.Distance_score = 0
        self.Time_score = 0
        self.Penalty = 0
        self.Comment = None
        self.ext_id = None
        self.pilPk = None
        self.result_type = 'lo'
        self.goal_time = None
        self.SSDistance = None


    @property
    def speed(self):
        if self.ESS_time and self.SSDistance:
            return (self.SSDistance /1000) / (self.total_time/ 3600)
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
            #result['rank'] = int(r.get('rank'))
            result.Score = int(r.get('points'))
            result.Total_distance = float(r.get('distance')) * 1000 # in meters
            result.Distance_flown = float(r.get('real_distance')) * 1000 # in meters
            #print ("start_ss: {}".format(r.get('started_ss')))
            result.Pilot_Start_time = get_datetime(r.get('started_ss')).time() if r.get('started_ss') is not None else None
            result.SSS_time = float(r.get('ss_time_dec_hours'))
            if result.SSS_time > 0:
                result.ESS_time = get_datetime(r.get('finished_ss')).time()
                print (" ESS Time: {}".format(result.ESS_time))
                print (" * time but not goal: {}".format(r.get('got_time_but_not_goal_penalty')))
                if r.get('got_time_but_not_goal_penalty') == 'False':
                    print (" * pilot made Goal! *")
                    '''pilot did make goal, we need to put a time in tarGoal
                        I just put a time 10 minutes after ESS time'''
                    result.goal_time = (get_datetime(r.get('finished_ss')) + timedelta(minutes=10)).time()
                    print ("    fake goal time: {}".format(result.goal_time))
            else:
                result.ESS_time = None
            result.Stopped_altitude = int(r.get('last_altitude_above_goal'))
            result.Distance_score = float(r.get('distance_points'))
            result.Time_score = float(r.get('time_points'))
            result.Penalty = int(r.get('penalty_points'))
            result.Comment = r.get('penalty_reason')
            if dep is 'on':
                result.Departure_score = float(r.get('departure_points'))
            elif dep is 'leadout':
                result.Departure_score = float(r.get('leading_points'))
            else:
                result.Departure_score = 0 #not necessary as it it initialized to 0
            result.Arrival_score = float(r.get('arrival_points')) if arr is 'on' else 0
        else:
            '''pilot has no recorded flight'''
            result.result_type = 'abs'
        #print ("Result in obj: id {} was: {} start: {} end: {} points: {} ".format(result.ext_id, result.result_type, result.Start_time, result.ESS_time, result.Score))

        return result

    @classmethod
    def read_from_db(cls, res_id, test = 0):
        """reads result from database"""
        query = (""" SELECT
                        *
                    FROM
                        tblResultView
                    WHERE
                        tarPk = {}
                    LIMIT 1
                """.format(res_id))
        if test:
            print('Result query:')
            print(query)

        with Database() as db:
            # get the task details.
            t = db.fetchone(query)
        if t is None:
            print('Not a valid flight')
            return
        else:
            result = cls()
            result.pilPk = t['pilPk']
            result.Pilot_Start_time = t['tarStart']
            result.SSS_time = t['tarSS']
            result.ESS_time = t['tarES']
            result.goal_time = t['tarGoal']
            result.total_time = t['tarLastTime'] - t['tarStart']
            result.Lead_coeff = t['tarLeadingCoeff2']
            result.Distance_flown = t['tarDistance']
            result.Stopped_altitude = t['tarLastAltitude']
            result.Jumped_the_gun = None
            result.Score = t['tarScore']
            result.Total_distance = t['tarDistance']
            result.Departure_score = t['tarDepartureScore']
            result.Arrival_score = t['tarArrivalScore']
            result.Distance_score = t['tarDistanceScore']
            result.Time_score = t['tarSpeedScore']
            result.Penalty = t['tarPenalty']
            result.Comment = t['tarComment']
            result.ext_id = None
            result.result_type = 'lo'
            return result

    @classmethod
    def check_flight(cls, Flight, Task, formula_parameters, min_tol_m=0):
        """ Checks a Flight object against the task.
            Args:
                   Flight: a Flight object
                   Task: a Taskm object
                   min_tol: minimum tolerance in meters, default is 0
            Returns:
                    a list of GNSSFixes of when turnpoints were achieved.
        """
        result = cls()
        tolerance = Task.tolerance

        result.SSS_time = Task.start_time

        waypoint = 1
        proceed_to_start = False
        t = 0
        if not Task.optimised_turnpoints:
            Task.calculate_optimised_task_length()

        distances2go = Task.distances_to_go
        for fix in Flight.fixes:
            fix.rawtime_local = fix.rawtime + Task.time_offset*3600  #local time for result times (SSS and ESS)
            result.Stopped_time = fix.rawtime
            # handle stopped task
            maxtime = None
            if Task.stopped_time is not None and result.ESS_time is None:
                if formula_parameters.stopped_elapsed_calc == 'shortest_time':
                    maxtime = Task.stopped_time - Task.last_start_time

                if fix.rawtime > Task.stopped_time or \
                        (maxtime is not None and result.SSS_time is not None
                         and (fix.rawtime > result.SSS_time + maxtime)):
                    result.Stopped_altitude = max(fix.gnss_alt, fix.press_alt)  # check the rules on this point..which alt to
                    break

            # check if pilot has arrived in goal (last turnpoint) so we can stop.
            if t >= len(Task.turnpoints):
                break

            # check if task deadline has passed
            if Task.end_time < fix.rawtime:
                # Task has ended
                break

            '''launch turnpoint managing'''
            if Task.turnpoints[t].type == "launch":
                # not checking launch yet
                if Task.check_launch == 'on':
                    # Set radius to check to 200m (in the task def it will be 0)
                    # could set this in the DB or even formula if needed..???
                    Task.turnpoints[t].radius = 200 #meters
                    if Task.turnpoints[t].in_radius(fix, tolerance, min_tol_m):
                        result.Waypoints_achieved.append(["Left Launch",fix.rawtime_local])  # pilot has achieved turnpoint
                        t += 1

                else:
                    t += 1

            # to do check for restarts for elapsed time tasks and those that allow jump the gun
            # if started and Task.task_type != 'race' or result.Jumped_the_gun is not None:

            '''start turnpoint managing'''
            if (    Task.turnpoints[t].type == "speed" or
                    (Task.task_type == 'ELAPSED TIME' and Task.turnpoints[t-1].type == "speed") ):

                #we need to check if it is a restart, so to use correct tp
                if Task.task_type == 'ELAPSED TIME' and Task.turnpoints[t-1].type == "speed":
                    s_tp = Task.turnpoints[t-1]
                    restarting = True
                else:
                    s_tp = Task.turnpoints[t]
                    restarting = False

                #check if we are on the right side of start radius
                if fix.rawtime > Task.start_time - formula_parameters.max_jump_the_gun and not proceed_to_start:
                    if check_start('ready', fix, tp, tolerance, min_tol_m):
                        # pilot is on the right side of start after the start time.
                        proceed_to_start = True  # pilot is alowed to start.
                        if fix.rawtime < Task.start_time:
                            result.Jumped_the_gun = Task.start_time - fix.rawtime

                if proceed_to_start and check_start('started', fix, s_tp, tolerance, min_tol_m):
                    result.Waypoints_achieved.append(["SSS",fix.rawtime_local])  # pilot has started
                    result.Best_waypoint_achieved = 'SSS made'
                    result.Pilot_Start_time = fix.rawtime
                    result.Start_time_str = (("%02d:%02d:%02d") % rawtime_float_to_hms(fix.rawtime_local))
                    if Task.task_type == 'ELAPSED TIME': result.SSS_time = fix.rawtime
                    proceed_to_start = False
                    if not restarting:
                        #if it is a restart, t is already next waypoint
                        t += 1

            '''Turnpoint managing'''
            if Task.turnpoints[t].shape == "circle" and Task.turnpoints[t].type != "goal":
                tp = Task.turnpoints[t]

                if tp_made(fix, tp, tolerance, min_tol_m) and started:
                    result.Best_waypoint_achieved = 'waypoint ' + str(waypoint) + ' made'

                    if tp.type == "endspeed":
                        result.Waypoints_achieved.append(["ESS",fix.rawtime_local])  # pilot has achieved turnpoint
                        result.ESS_time = fix.rawtime
                        result.ESS_time_str = (("%02d:%02d:%02d") % rawtime_float_to_hms(fix.rawtime_local))
                        result.SSDistance = Task.SSDistance
                        if Task.task_type == 'RACE':
                            result.total_time = fix.rawtime - result.SSS_time

                        if Task.task_type == 'SPEEDRUN' or Task.task_type == 'ELAPSED TIME':
                            result.total_time = fix.rawtime - result.Pilot_Start_time
                        result.total_time_str = (("%02d:%02d:%02d") % rawtime_float_to_hms(result.total_time))
                    else:
                        result.Waypoints_achieved.append([waypoint,fix.rawtime_local])  # pilot has achieved turnpoint
                    waypoint += 1
                    t += 1

            elif Task.turnpoints[t].type == "goal":
                goal_tp = Task.turnpoints[t]
                if (started and
                            ((goal_tp.shape == "circle" and tp_made(fix, tp, tolerance, min_tol_m))
                            or (goal_tp.shape == "line" and in_semicircle(Task, Task.turnpoints, t,fix)))):

                    result.Waypoints_achieved.append(["Goal",fix.rawtime_local])  # pilot has achieved turnpoint
                    if started:
                        result.Best_waypoint_achieved = 'Goal made'
                        result.Distance_flown = distances2go[0]
                        result.goal_time = fix.rawtime_local
                        break

            else:
                assert False, "Unknown turnpoint type: %s" % Task.turnpoints[t].type
            taskTime = fix.rawtime - Task.start_time
            best_dist_to_ess = (Task.EndSSDistance - result.Distance_flown) / 1000
            if result.Best_waypoint_achieved != 'Goal made':
                result.Distance_flown = max(result.Distance_flown,
                                                   distance_flown(fix, t, Task.optimised_turnpoints, distances2go))

                if best_dist_to_ess > 0 and started:
                    result.Lead_coeff += formula_parameters.coef_func(taskTime, best_dist_to_ess, (
                                Task.EndSSDistance - result.Distance_flown) / 1000)
        if result.ESS_time is None: # we need to do this after other operations
            result.Lead_coeff += formula_parameters.coef_landout((Task.end_time - Task.start_time),((Task.EndSSDistance - result.Distance_flown) / 1000))

        result.Lead_coeff = formula_parameters.coef_func_scaled(result.Lead_coeff, Task.EndSSDistance)
        return result

    def store_result_test(self, traPk, tasPk):

        if not self.goal_time:
            self.goal_time = 0

        endss = self.ESS_time
        if not endss:
            endss = 0
        #print("turnponts", len(self.Waypoints_achieved))
        query = "delete from tblTaskResult_test where traPk=%s and tasPk=%s"
        params = [traPk, tasPk]
        with Database() as db:
            db.execute(query, params)

        query = "INSERT INTO tblTaskResult_test (" \
                "tasPk, traPk, tarDistance, tarSpeed, tarStart, tarGoal, tarSS, tarES, tarTurnpoints, " \
                "tarLeadingCoeff, tarPenalty, tarComment, tarLastAltitude, tarLastTime ) " \
                "VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(tasPk, traPk, self.Distance_flown, self.speed, self.Pilot_Start_time, self.goal_time, self.SSS_time, endss, len(self.Waypoints_achieved), self.Lead_coeff, self.Penalty, self.Comment, self.Stopped_altitude, self.Stopped_time)
        #print(query)

        query = "INSERT INTO tblTaskResult_test ( " \
                "tasPk, traPk, tarDistance, tarSpeed, tarStart, tarGoal, tarSS, tarES, tarTurnpoints, " \
                "tarLeadingCoeff2, tarPenalty, tarLastTime ) " \
                "VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )"
        #, #%s, %s, %s)"
        num_wpts = len(self.Waypoints_achieved)
        params = [tasPk, traPk, self.Distance_flown, self.speed, self.Pilot_Start_time, self.goal_time, self.SSS_time , endss, num_wpts, self.Lead_coeff, self.Penalty, self.Stopped_time] #, self.Comment, self.Stopped_altitude, self.Stopped_time]

        with Database() as db:
           r = db.execute(query, params)
        print(r)

    def store_result(self, traPk, tasPk):

        if not self.goal_time:
            self.goal_time = 0

        endss = self.ESS_time
        if not endss:
            endss = 0
        #print("turnponts", len(self.Waypoints_achieved))
        query = "delete from tblTaskResult where traPk=%s and tasPk=%s"
        params = [traPk, tasPk]
        with Database() as db:
            db.execute(query, params)

        query = "INSERT INTO tblTaskResult (" \
                "tasPk, traPk, tarDistance, tarSpeed, tarStart, tarGoal, tarSS, tarES, tarTurnpoints, " \
                "tarLeadingCoeff2, tarPenalty, tarComment, tarLastAltitude, tarLastTime ) " \
                "VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(tasPk, traPk, self.Distance_flown, self.speed, self.Pilot_Start_time, self.goal_time, self.SSS_time, endss, len(self.Waypoints_achieved), self.Lead_coeff, self.Penalty, self.Comment, self.Stopped_altitude, self.Stopped_time)
        #print(query)

        query = "INSERT INTO tblTaskResult ( " \
                "tasPk, traPk, tarDistance, tarSpeed, tarStart, tarGoal, tarSS, tarES, tarTurnpoints, " \
                "tarLeadingCoeff2, tarPenalty, tarLastTime ) " \
                "VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )"
        # , #%s, %s, %s)"
        num_wpts = len(self.Waypoints_achieved)
        params = [tasPk, traPk, self.Distance_flown, self.speed, self.Pilot_Start_time, self.goal_time, self.SSS_time, endss,
                  num_wpts, self.Lead_coeff, self.Penalty,
                  self.Stopped_time]  # , self.Comment, self.Stopped_altitude, self.Stopped_time]

        with Database() as db:
           r = db.execute(query, params)
