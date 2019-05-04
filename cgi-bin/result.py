"""
Results Library

contains
    Task_result class
    Comp_result class

Use: from result import Task_result

Antonio Golfari & Stuart Mackintosh - 2019
"""

from myconn import Database

class Task_result:
    """
        creates Task Result sheets
        - in JSON format
        - in HTML format for AirTribune
    """

    def __init__(self, info = None, formula = None, stats = None, timestamp = None, results = None, filename = None, test = 0):
        self.info       = info
        self.formula    = formula
        self.stats      = stats
        self.timestamp  = timestamp
        self.results    = results
        self.filename   = filename

    def __str__(self):
        out = ''
        out += 'Task Results:'
        out += 'Task date: {} \n'.format(self.info['task_date'])
        # for idx, item in enumerate(self.task.turnpoints):
        #     out += '  {}  {}  {}  {} km \n'.format(item.name, item.type, item.radius, round(self.task.partial_distance[idx]/1000, 2))
        out += 'Task Distance: {} Km \n'.format(round(self.info['task_opt_dist']/1000,2))
        for line in self.results:
            out += '{}  {} km  {}  {} \n'.format(line['pilName'], round(line['tarDistance']/1000, 2), line['tarES'], (round(line['tarScore'], 0) if line['tarScore'] else 0))
        return out

    # @classmethod
    # def read_db(cls, task_id, date = None, test = 0):
    #     """
    #         reads task result
    #     """
    #     from task import Task
    #     from flight_result import Flight_result
    #
    #     task = Task.read_task(task_id)
    #
    #     query = (""" SELECT
    #                     tarPk
    #                 FROM
    #                     tblResult
    #                 WHERE
    #                     tasPk = {}
    #                 ORDER BY
    #                     tarScore DESC,
    #                     pilName
    #             """.format(task_id))
    #
    #     if test:
    #         print('task read correctly')
    #         print('Query:')
    #         print(query)
    #
    #     with Database() as db:
    #         # get the task details.
    #         t = db.fetchall(query)
    #     if t is None:
    #         print('Not a valid task')
    #         return
    #     else:
    #         result = cls()
    #         for res in t:
    #             id = res['tarPk']
    #             result.results.append(Flight_result.read_from_db(id, test))
    #             if test:
    #                 print('result id: {}'.format(id))
    #
    #         result.task = task
    #         result.date = task.date
    #         result.tasPk = task.tasPk
    #         result.comPk = task.comPk
    #         return result

    @classmethod
    def read_db(cls, task_id, test = 0):
        """
            reads task result
        """
        #from task import Task
        #from formula import Task_formula
        #from flight_result import Flight_result
        import time
        from datetime import datetime
        from pprint import pprint

        info = dict()
        stats = dict()
        formula = dict()

        # '''create task object'''
        # task = Task.read_task(task_id)
        # if test:
        #     print('task read correctly')

        # '''create task parameters object'''
        # formula = Task_formula.read(task_id, test)
        # if test:
        #     print('task formula read correctly')
        #     print(formula)

        '''read task info, formula and stats'''
        query = (""" SELECT
                        `comName`                   AS comp_name,
                        `comClass`                  AS comp_class,
                        `tasDate`                   AS task_date,
                        `tasName`                   AS task_name,
                        `comTimeOffset`             AS time_offset,
                        `tasComment`                AS task_comment,
                        `tasTaskStart`              AS window_open_time,
                        `tasFinishTime`             AS task_deadline,
                        `tasLaunchClose`            AS window_close_time,
                        `tasCheckLaunch`            AS check_launch,
                        `tasStartTime`              AS SS_time,
                        `tasStartCloseTime`         AS SS_close_time,
                        `tasSSInterval`             AS SS_interval,
                        `tasTaskType`               AS task_type,
                        `tasDistance`               AS task_distance,
                        `tasShortRouteDistance`     AS task_opt_dist,
                        `tasSSDistance`             AS SS_distance,
                        `forName`                   AS formula_name,
                        `forDiffDist`               AS diff_distance,
                        `forGoalSSpenalty`          AS no_goal_penalty,
                        `forStoppedGlideBonus`      AS glide_bonus,
                        `forStoppedElapsedCalc`     AS stopped_time_calc,
                        `forNomGoal`                AS nominal_goal,
                        `forMinDistance`            AS min_dist,
                        `forNomDistance`            AS nominal_dist,
                        `forNomTime`                AS nominal_time,
                        `forNomLaunch`              AS nominal_launch,
                        `forScorebackTime`          AS score_back_time,
                        `tasDeparture`              AS departure,
                        `tasArrival`                AS arrival,
                        `tasHeightBonus`            AS height_bonus,
                        `tasMargin`                 AS tolerance,
                        `tasStoppedTime`            AS task_stopped_time,
                        `tasLastStartTime`          AS last_start_time,
                        `tasFastestTime`            AS fastest_time,
                        `tasFirstDepTime`           AS first_dep_time,
                        `tasFirstArrTime`           AS first_arr_time,
                        `tasMaxDistance`            AS max_distance,
                        `tasResultsType`            AS result_type,
                        `tasTotalDistanceFlown`     AS tot_dist_flown,
                        `tasTotDistOverMin`         AS tot_dist_over_min,
                        `tasQuality`                AS day_quality,
                        `tasDistQuality`            AS dist_validity,
                        `tasTimeQuality`            AS time_validity,
                        `tasLaunchQuality`          AS launch_validity,
                        `tasStopQuality`            AS stop_validity,
                        `tasAvailDistPoints`        AS avail_dist_points,
                        `tasAvailLeadPoints`        AS avail_lead_points,
                        `tasAvailTimePoints`        AS avail_time_points,
                        `tasAvailArrPoints`         AS avail_arr_points,
                        `tasLaunchValid`,
                        `tasPilotsLaunched`         AS pilots_flying,
                        `tasPilotsTotal`            AS pilots_present,
                        `tasPilotsES`               AS pilots_es,
                        `tasPilotsLO`               AS pilots_lo,
                        `tasPilotsGoal`             AS pilots_goal,
                        `maxScore`                  AS max_score,
                        `tasGoalAlt`                AS goal_altitude,
                        `tasCode`
                    FROM
                        `tblTaskView`
                    WHERE
                        `tasPk` = {}
                    LIMIT 1
                """.format(task_id))

        if test:
            print('read task stats:')
            print('Query:')
            print(query)

        with Database() as db:
            # get the task details.
            t = db.fetchone(query)
        if t is None:
            print('Task does not exist')
            return
        else:
            '''create info, formula and stats dict from query result'''
            info_data = [       'comp_name',
                                'comp_class',
                                'task_date',
                                'task_name',
                                'time_offset',
                                'task_comment',
                                'window_open_time',
                                'task_deadline',
                                'window_close_time',
                                'check_launch',
                                'SS_time',
                                'SS_close_time',
                                'SS_interval',
                                'task_type',
                                'task_distance',
                                'task_opt_dist',
                                'SS_distance']
            formula_data = [    'formula_name',
                                'diff_distance',
                                'no_goal_penalty',
                                'glide_bonus',
                                'stopped_time_calc',
                                'nominal_goal',
                                'min_dist',
                                'nominal_dist',
                                'nominal_time',
                                'nominal_launch',
                                'score_back_time',
                                'departure',
                                'arrival',
                                'height_bonus',
                                'tolerance']
            stats_data = [      'task_stopped_time',
                                'last_start_time',
                                'fastest_time',
                                'first_dep_time',
                                'first_arr_time',
                                'max_distance',
                                'result_type',
                                'tot_dist_flown',
                                'tot_dist_over_min',
                                'day_quality',
                                'dist_validity',
                                'time_validity',
                                'launch_validity',
                                'stop_validity',
                                'avail_dist_points',
                                'avail_lead_points',
                                'avail_time_points',
                                'avail_arr_points',
                                'pilots_flying',
                                'pilots_present',
                                'pilots_es',
                                'pilots_lo',
                                'pilots_goal',
                                'max_score',
                                'goal_altitude']
            info = {x:t[x] for x in info_data}
            formula = {x:t[x] for x in formula_data}
            stats = {x:t[x] for x in stats_data}
            ts = int(time.time())
            d = datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')
            filename = '_'.join([t['tasCode'],d]) + '.json'
            if test:
                pprint(info)
                pprint(formula)
                pprint(stats)
                print (ts)
                print(d)
                print(filename)

        '''read pilots result'''
        query = (""" SELECT
                        pilName,
                        pilNationCode,
                        traGlider,
                        pilSponsor,
                        tarDistance,
                        tarSpeed,
                        tarStart,
                        tarSS,
                        tarES,
                        tarGoal,
                        tarResultType,
                        tarTurnpoints,
                        tarPenalty,
                        tarComment,
                        tarPlace,
                        tarSpeedScore,
                        tarDistanceScore,
                        tarArrivalScore,
                        tarDepartureScore,
                        tarScore,
                        tarLastAltitude,
                        tarLastTime
                    FROM
                        tblResult
                    WHERE
                        tasPk = {}
                    ORDER BY
                        tarScore DESC,
                        pilName
                """.format(task_id))

        if test:
            print('read results:')
            print('Query:')
            print(query)

        with Database() as db:
            # get the task details.
            t = db.fetchall(query)
        if t is None:
            print('Not a valid task')
            return
        else:
            result = cls()
            result.formula = formula
            result.stats = stats
            result.results = t
            result.info = info
            result.timestamp = ts
            result.filename = filename
            return result

    def to_json(self, filename = None):
        """
        creates the JSON file of the result
        """
        import json, os
        import Defines as d
        from calcUtils import DateTimeEncoder

        # '''create a dict for task info'''
        # info = {    'name':self.task.name}

        #data = {self.date, self.formula, self.stats, self.results}
        if not filename:
            jsondir = d.JSONDIR
            filename = jsondir + self.filename

        result =  {     'info':     [self.info],
                        'formula':  [self.formula],
                        'results':  [res for res in self.results],
                        'stats':    [self.stats] }
        json_file = json.dumps(result, cls=DateTimeEncoder, indent = 4)
        with open(filename, 'w') as f:
            f.write(json_file)
        os.chown(filename, 1000, 1000)
        return json_file

class Comp_result:
    """
        creates Task Result sheets
        - in JSON format
        - in HTML format for AirTribune
    """

    def __init__(self, comPk = None, date = None, test = 0):
        self.comPk = None
        self.date  = None

    @classmethod
    def read_db(cls, comPk, date = None, test = 0):
        """
            reads comp results
        """
