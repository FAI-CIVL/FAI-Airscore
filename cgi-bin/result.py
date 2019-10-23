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

    def __init__(self, ref_id = None, comp_id = None, task_id = None, status = None, task = None, rankings = None, info = None, formula = None, stats = None, timestamp = None, results = None, filename = None, test = 0):
        self.ref_id     = ref_id        #refPk row in database
        self.status     = status        #status of the result ('provisional', 'final', )
        self.comp_id    = comp_id       #comPk
        self.task_id    = task_id       #tasPk
        self.task       = task          #task route info
        self.rankings   = rankings      #list of sub rankings
        self.info       = info          #list of info about the task
        self.formula    = formula       #task formula parameters
        self.stats      = stats         #statistics
        self.timestamp  = timestamp     #creation timestamp
        self.results    = results       #list of pilots result
        self.filename   = filename      #json filename

    def __str__(self):
        out = ''
        out += 'Task Results:'
        out += 'Task date: {} \n'.format(self.info['task_date'])
        out += '{} \n'.format(self.status)
        for wpt in self.task:
            out += '  {}  {}  {}  {} km \n'.format(wpt['ID'], wpt['type'], wpt['radius'], round( wpt['cumulative_dist'] / 1000, 2))
        out += 'Task Distance: {} Km \n'.format(round(self.info['task_opt_dist']/1000,2))
        for line in self.results:
            out += '{}  {} km  {}  {} \n'.format(line['name'], round(line['distance']/1000, 2), line['ES_time'], (round(line['score'], 0) if line['score'] else 0))
        return out

    @classmethod
    def read_db(cls, task_id, test = 0):
        """
            reads task result
        """
        import time
        from datetime import datetime
        from pprint import pprint
        import Defines as d

        info = dict()
        task = dict()
        stats = dict()
        formula = dict()
        rank = dict()

        '''read class rankings'''
        rank = read_rankings(task_id, test)

        '''read task info, formula and stats'''
        comp_id, task_code, info, formula, stats = read_task(task_id, test)
        if comp_id is None:
            print('task is not in database or not in a valid competition')
            return

        ts = int(time.time())
        dt = datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')
        filename = d.JSONDIR + '_'.join([task_code,dt]) + '.json'

        '''read task route'''
        task = read_task_route(task_id, test)
        if task is None:
            print('Task route does not exist')
            return

        if test:
            pprint(info)
            pprint(task)
            pprint(formula)
            pprint(stats)
            print (ts)
            print(dt)
            print(filename)

        '''read pilots result'''
        results = read_task_result(task_id, test = 0)
        if results is None:
            print('Task has no results yet')
            return

        result = cls(   comp_id     = comp_id,
                        task_id     = task_id,
                        task        = task,
                        rankings    = rank,
                        formula     = formula,
                        stats       = stats,
                        results     = results,
                        info        = info,
                        timestamp   = ts,
                        filename    = filename
                    )
        return result

    def to_json(self, filename = None, status = None, test = 0):
        """
        creates the JSON file of the result
        """
        import os
        import simplejson as json
        from calcUtils import DateTimeEncoder

        if filename:
            self.filename = filename

        self.status = status

        result =    {   'data':     {'timestamp':self.timestamp, 'status':self.status},
                        'info':     self.info,
                        'rankings': self.rankings,
                        'task':     [wpt for wpt in self.task],
                        'results':  [res for res in self.results],
                        'formula':  self.formula,
                        'stats':    self.stats
                    }

        with open(self.filename, 'w') as f:
            json.dump(result, f)
        os.chown(self.filename, 1000, 1000)
        return self.filename

    def to_db(self, test = 0):
        """
        insert the result into database
        """

        '''store timestamp in local time'''
        timestamp = self.timestamp + self.info['time_offset']

        query = """
                    INSERT INTO `tblResultFile`(
                        `comPk`,
                        `tasPk`,
                        `refTimestamp`,
                        `refJSON`,
                        `refStatus`
                    )
                    VALUES('{}', '{}', '{}', '{}', '{}')
                """.format(self.comp_id, self.task_id, timestamp, self.filename, self.status)

        if test:
            print ('Insert query:')
            print(query)
        else:
            with Database() as db:
                self.ref_id = db.execute(query)
        return self.ref_id

    @staticmethod
    def create_result(task, formula, results, status=None):
        '''create task results json file from task object and results list
        '''
        import time
        from datetime import datetime
        from pprint import pprint as pp
        import Defines as d

        ts = int(time.time())
        dt = datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')
        filename = d.JSONDIR + '_'.join([task.task_code,dt]) + '.json'
        comp_id = task.comp_id
        task_id = task.task_id

        result = Task_result(comp_id=comp_id, task_id=task_id, filename=filename, timestamp=dt)

        '''create result object elements from task, formula and results objects'''

        # task_code = t['tasCode']
        result.get_task_info(task)
        result.get_formula(formula)
        result.get_task_stats(task.stats)
        result.get_task_route(task)
        result.get_task_pilots(results)
        result.rankings = read_rankings(task_id)

        print(f"task ID: {result.task_id}, timestamp: {result.timestamp}, file: {result.filename}")
        pp(result.info)
        pp(result.formula)
        pp(result.stats)
        pp(result.task)
        pp(result.results)
        pp(result.rankings)


    def get_task_route(self, task):
        '''gets route from task object and creates a list of dict'''

        route = task.turnpoints
        dist =  task.partial_distance
        task_route = []
        attr_list =[    'name',
                        'description',
                        'how',
                        'radius',
                        'shape',
                        'type',
                        'lat',
                        'lon',
                        'altitude'
                        ]
        for idx, tp in enumerate(route):
            wpt = {x:getattr(tp, x) for x in attr_list}
            wpt['cumulative_dist'] = dist[idx-1] if idx > 0 else 0
            task_route.append(wpt)

        self.task = task_route

    def get_task_info(self, task):
        '''gets info from task object and creates a dict'''

        attr_list =[    'comp_name',
                        'comp_site',
                        'comp_class',
                        'date',
                        'task_name',
                        'time_offset',
                        'comment',
                        'window_open_time',
                        'task_deadline',
                        'window_close_time',
                        'check_launch',
                        'start_time',
                        'start_close_time',
                        'SS_interval',
                        'last_start_time',
                        'task_type',
                        'distance',
                        'opt_dist',
                        'SS_distance',
                        'stopped_time',
                        'goal_altitude']

        self.info = {x:getattr(task, x) for x in attr_list}

    def get_formula(self, formula):
        '''gets info from task object and creates a dict'''

        attr_list = [   'formula_name',
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
                        'arr_alt_bonus',
                        'tolerance']

        self.formula = {x:getattr(formula, x) for x in attr_list}

    def get_task_stats(self, stats):
        '''gets info from task object and creates a dict'''

        attr_list = [   'fastest',
                        'fastest_in_goal',
                        'min_dept_time',
                        'min_ess_time',
                        'max_distance',
                        'tot_dist_flown',
                        'tot_dist_over_min',
                        'day_quality',
                        'dist_validity',
                        'time_validity',
                        'launch_validity',
                        'stop_validity',
                        'avail_dist_points',
                        'avail_dep_points',
                        'avail_time_points',
                        'avail_arr_points',
                        'pilots_launched',
                        'pilots_present',
                        'pilots_ess',
                        'pilots_landed',
                        'pilots_goal',
                        'max_score',
                        'min_lead_coeff']

        self.stats = {x:stats[x] for x in attr_list}

    def get_task_pilots(self, results):
        '''gets pilots results from results list'''

        list = []

        attr_list = [   'track_id',
                        'pil_id',
                        'name',
                        'sponsor',
                        'nat',
                        'sex',
                        'glider',
                        'class',
                        'distance',
                        'speed',
                        'start_time',
                        'goal_time',
                        'result',
                        'SS_time',
                        'ES_time',
                        'turnpoints_made',
                        'dist_points',
                        'time_points',
                        'dep_points',
                        'arr_points',
                        'score',
                        'penalty',
                        'comment',
                        'lead_coeff',
                        'last_altitude',
                        'last_time']

        for pil in results:
            res = {x:pil[x] for x in attr_list}
            res['name'] = res['name'].title()
            res['glider'] = res['glider'].title()
            list.append(res)

        self.results = list


class Comp_result:
    """
        creates Task Result sheets
        - in JSON format
        - in HTML format for AirTribune
    """

    def __init__(self, comPk = None, date = None, test = 0):
        self.comp_id = None
        self.date  = None

    @classmethod
    def read_db(cls, comPk, date = None, test = 0):
        """
            reads comp results
        """


def read_rankings(task_id, test = 0):
    '''reads sub rankings list for the task and creates a dictionary'''

    rank = dict()
    query = """ SELECT
                    R.`ranName` AS rank,
                    CCT.`cerName` AS cert
                FROM
                    `tblClasCertRank` CC
                JOIN `TaskView` T USING(`claPk`)
                JOIN `tblRanking` R USING(`ranPk`)
                JOIN `tblCertification` CCT ON CCT.`cerPk` <= CC.`cerPk` AND CCT.`comClass` = R.`comClass`
                WHERE
                    T.`tasPk` = %s AND CC.`cerPk` > 0
            """
    if test:
        print('Rankings:')
        print('Query:')
        print(query)

    with Database() as db:
        t = db.fetchall(query, [task_id])
    if not t:
        print('Task does not have rankings')
        #rank = {'Open Class':[]}
    else:
        for l in t:
            if l['rank'] in rank:
                rank[l['rank']].append(l['cert'])
            else:
                rank[l['rank']] = [l['cert']]

        '''add female and team choices'''
        query = """ SELECT
                        claFem      AS female,
                        claTeam     AS team
                    FROM
                        tblClassification
                        JOIN TaskView USING (claPk)
                    WHERE
                        tasPk = %s
                    LIMIT 1
                """

        with Database() as db:
            t = db.fetchone(query, [task_id])
        if t:
            rank['Female'] = t['female']
            rank['Team'] = t['team']

    if test:
        print('rankings list:')
        pprint(rank)
    return rank

# def read_task(task_id, test = 0):
#     ''' read task from database, and returns:
#             comp_id
#             info        array of task info
#             formula
#             stats
#     '''
#
#     query = """ SELECT
#                     T.`comPk`                       AS comp_id,
#                     T.`comName`                     AS comp_name,
#                     T.`comLocation`                 AS comp_site,
#                     T.`comClass`                    AS comp_class,
#                     DATE_FORMAT(T.`tasDate`, '%%Y-%%m-%%d') AS date,
#                     T.`tasName`                     AS task_name,
#                     T.`comTimeOffset`               AS time_offset,
#                     T.`tasComment`                  AS comment,
#                     DATE_FORMAT(T.`tasTaskStart`, '%%T')   AS window_open_time,
#                     DATE_FORMAT(T.`tasFinishTime`, '%%T')  AS task_deadline,
#                     DATE_FORMAT(T.`tasLaunchClose`, '%%T') AS window_close_time,
#                     T.`tasCheckLaunch`              AS check_launch,
#                     DATE_FORMAT(T.`tasStartTime`, '%%T')   AS SS_time,
#                     DATE_FORMAT(T.`tasStartCloseTime`, '%%T') AS SS_close_time,
#                     T.`tasSSInterval`               AS SS_interval,
#                     DATE_FORMAT(T.`tasLastStartTime`, '%%T') AS last_start_time,
#                     T.`tasTaskType`                 AS task_type,
#                     T.`tasDistance`                 AS distance,
#                     T.`tasShortRouteDistance`       AS opt_dist,
#                     T.`tasSSDistance`               AS SS_distance,
#                     T.`forName`                     AS formula_name,
#                     T.`forDiffDist`                 AS diff_distance,
#                     T.`forGoalSSpenalty`            AS no_goal_penalty,
#                     T.`forStoppedGlideBonus`        AS glide_bonus,
#                     T.`forStoppedElapsedCalc`       AS stopped_time_calc,
#                     T.`forNomGoal`                  AS nominal_goal,
#                     T.`forMinDistance`              AS min_dist,
#                     T.`forNomDistance`              AS nominal_dist,
#                     T.`forNomTime`                  AS nominal_time,
#                     T.`forNomLaunch`                AS nominal_launch,
#                     T.`forScorebackTime`            AS score_back_time,
#                     T.`tasDeparture`                AS departure,
#                     T.`tasArrival`                  AS arrival,
#                     T.`tasHeightBonus`              AS arr_alt_bonus,
#                     T.`tasMargin`                   AS tolerance,
#                     DATE_FORMAT(T.`tasStoppedTime`, '%%T') AS stopped_time,
#                     TT.`minTime`                    AS fastest_time,
#                     TT.`firstStart`                 AS first_dep_time,
#                     TT.`firstESS`                   AS first_arr_time,
#                     TT.`maxDist`                    AS max_distance,
#                     T.`tasResultsType`              AS result_type,
#                     TT.`TotalDistance`              AS tot_dist_flown,
#                     TT.`TotDistOverMin`             AS tot_dist_over_min,
#                     T.`tasQuality`                  AS day_quality,
#                     T.`tasDistQuality`              AS dist_validity,
#                     T.`tasTimeQuality`              AS time_validity,
#                     T.`tasLaunchQuality`            AS launch_validity,
#                     T.`tasStopQuality`              AS stop_validity,
#                     T.`tasAvailDistPoints`          AS avail_dist_points,
#                     T.`tasAvailLeadPoints`          AS avail_lead_points,
#                     T.`tasAvailTimePoints`          AS avail_time_points,
#                     T.`tasAvailArrPoints`           AS avail_arr_points,
#                     T.`tasLaunchValid`,
#                     T.`tasPilotsLaunched`           AS pilots_flying,
#                     TT.`TotalPilots`                AS pilots_present,
#                     TT.`TotalESS`                   AS pilots_es,
#                     T.`tasPilotsLO`                 AS pilots_lo,
#                     TT.`TotalGoal`                  AS pilots_goal,
#                     T.`maxScore`                    AS max_score,
#                     T.`tasGoalAlt`                  AS goal_altitude,
#                     T.`tasCode`,
#                     TT.`LCmin`                      AS min_lead_coeff
#                 FROM
#                     `TaskView` T
#                     LEFT OUTER JOIN `TaskTotalsView` TT using(`tasPk`)
#                 WHERE
#                     T.`tasPk` = %s
#                 LIMIT 1
#             """
#
#     if test:
#         print('read task:')
#         print('Query:')
#         print(query)
#
#     with Database() as db:
#         t = db.fetchone(query, [task_id])
#     if t is None:
#         print('Task does not exist')
#         return
#
#     '''create info, formula and stats dict from query result'''
#     info_data = [       'comp_name',
#                         'comp_site',
#                         'comp_class',
#                         'date',
#                         'task_name',
#                         'time_offset',
#                         'comment',
#                         'window_open_time',
#                         'window_close_time',
#                         'task_deadline',
#                         'check_launch',
#                         'start_time',
#                         'start_close_time',
#                         'SS_interval',
#                         'last_start_time',
#                         'task_type',
#                         'distance',
#                         'opt_dist',
#                         'SS_distance',
#                         'goal_altitude',
#                         'stopped_time']
#     formula_data = [    'formula_name',
#                         'diff_distance',
#                         'no_goal_penalty',
#                         'glide_bonus',
#                         'stopped_time_calc',
#                         'nominal_goal',
#                         'min_dist',
#                         'nominal_dist',
#                         'nominal_time',
#                         'nominal_launch',
#                         'score_back_time',
#                         'departure',
#                         'arrival',
#                         'height_bonus',
#                         'tolerance']
#     stats_data = [      'fastest_time',
#                         'first_dep_time',
#                         'first_arr_time',
#                         'max_distance',
#                         'result_type',
#                         'tot_dist_flown',
#                         'tot_dist_over_min',
#                         'day_quality',
#                         'dist_validity',
#                         'time_validity',
#                         'launch_validity',
#                         'stop_validity',
#                         'avail_dist_points',
#                         'avail_lead_points',
#                         'avail_time_points',
#                         'avail_arr_points',
#                         'pilots_flying',
#                         'pilots_present',
#                         'pilots_es',
#                         'pilots_lo',
#                         'pilots_goal',
#                         'max_score',
#                         'min_lead_coeff']
#     comp_id = t['comp_id']
#     task_code = t['tasCode']
#     info = {x:t[x] for x in info_data}
#     formula = {x:t[x] for x in formula_data}
#     stats = {x:t[x] for x in stats_data}
#
#     return comp_id, task_code, info, formula, stats

# def read_task_route(task_id, test = 0):
#     '''gets task route from database and creates a dict'''
#
#     query = """
#             SELECT
#                 `TW`.`tawNumber` 		AS `number`,
#                 `W`.`rwpName`			AS `ID`,
#                 `W`.`rwpDescription`	AS `description`,
#                 `TW`.`tawTime`			AS `time`,
#                 `TW`.`tawType`			AS `type`,
#                 `TW`.`tawHow`			AS `how`,
#                 `TW`.`tawShape`			AS `shape`,
#                 `TW`.`tawAngle`			AS `angle`,
#                 `TW`.`tawRadius`		AS `radius`,
#                 `TW`.`ssrCumulativeDist` AS `partial_distance`
#             FROM
#                 `tblTaskWaypoint` `TW`
#                 JOIN `tblRegionWaypoint` `W` USING(`rwpPk`)
#             WHERE
#                 `tasPk` = {}
#             """.format(task_id)
#     if test:
#         print('read task route:')
#         print('Query:')
#         print(query)
#
#     with Database() as db:
#         # get the task details.
#         task = db.fetchall(query)
#
#     return task

def read_task_result(task_id, test = 0):
    '''gets pilots result from database'''
    query = """ SELECT
                    `traPk`             AS `track_id`,
                    `pilName`			AS `name`,
                    `pilSex`            AS `sex`,
                    `pilNationCode`		AS `nat`,
                    `traGlider`			AS `glider`,
                    `traDHV`            AS `class`,
                    `pilSponsor`		AS `sponsor`,
                    `tarDistance`		AS `distance`,
                    `tarSpeed`			AS `speed`,
                    `tarStart`			AS `real_SS_time`,
                    `tarSS`				AS `SS_time`,
                    `tarES`				AS `ES_time`,
                    `tarGoal`			AS `goal_time`,
                    `tarResultType`		AS `type`,
                    `tarTurnpoints`		AS `n_turnpoints`,
                    `tarPenalty`		AS `penalty`,
                    `tarComment`		AS `comment`,
                    `tarPlace`			AS `rank`,
                    `tarSpeedScore`		AS `speed_points`,
                    `tarDistanceScore`	AS `dist_points`,
                    `tarArrivalScore`	AS `arr_points`,
                    `tarDepartureScore`	AS `dep_points`,
                    `tarScore`			AS `score`,
                    `tarLastAltitude`	AS `altitude`,
                    `tarLastTime`		AS `last_time`,
                    `tarLeadingCoeff`   AS `lead_coeff`
                FROM
                    `ResultView`
                WHERE
                    `tasPk` = %s
                ORDER BY
                    `tarScore` DESC,
                    `pilName`
            """

    if test:
        print('read results:')
        print('Query:')
        print(query)

    with Database() as db:
        # get the task details.
        results = db.fetchall(query, [task_id])

    return results
