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
        timestamp = self.timestamp + self.info['time_offset']*3600

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

def read_task(task_id, test = 0):
    ''' read task from database, and returns:
            comp_id
            info        array of task info
            formula
            stats
    '''

    # query = (""" SELECT
    #                 `comPk`                     AS comp_id,
    #                 `comName`                   AS comp_name,
    #                 `comClass`                  AS comp_class,
    #                 DATE_FORMAT(`tasDate`, '%%Y-%%m-%%d') AS task_date,
    #                 `tasName`                   AS task_name,
    #                 `comTimeOffset`             AS time_offset,
    #                 `tasComment`                AS task_comment,
    #                 DATE_FORMAT(`tasTaskStart`, '%%T')   AS window_open_time,
    #                 DATE_FORMAT(`tasFinishTime`, '%%T')  AS task_deadline,
    #                 DATE_FORMAT(`tasLaunchClose`, '%%T') AS window_close_time,
    #                 `tasCheckLaunch`            AS check_launch,
    #                 DATE_FORMAT(`tasStartTime`, '%%T')   AS SS_time,
    #                 DATE_FORMAT(`tasStartCloseTime`, '%%T') AS SS_close_time,
    #                 `tasSSInterval`             AS SS_interval,
    #                 DATE_FORMAT(`tasLastStartTime`, '%%T') AS last_start_time,
    #                 `tasTaskType`               AS task_type,
    #                 `tasDistance`               AS task_distance,
    #                 `tasShortRouteDistance`     AS task_opt_dist,
    #                 `tasSSDistance`             AS SS_distance,
    #                 `forName`                   AS formula_name,
    #                 `forDiffDist`               AS diff_distance,
    #                 `forGoalSSpenalty`          AS no_goal_penalty,
    #                 `forStoppedGlideBonus`      AS glide_bonus,
    #                 `forStoppedElapsedCalc`     AS stopped_time_calc,
    #                 `forNomGoal`                AS nominal_goal,
    #                 `forMinDistance`            AS min_dist,
    #                 `forNomDistance`            AS nominal_dist,
    #                 `forNomTime`                AS nominal_time,
    #                 `forNomLaunch`              AS nominal_launch,
    #                 `forScorebackTime`          AS score_back_time,
    #                 `tasDeparture`              AS departure,
    #                 `tasArrival`                AS arrival,
    #                 `tasHeightBonus`            AS height_bonus,
    #                 `tasMargin`                 AS tolerance,
    #                 DATE_FORMAT(`tasStoppedTime`, '%%T') AS task_stopped_time,
    #                 `tasFastestTime`            AS fastest_time,
    #                 `tasFirstDepTime`           AS first_dep_time,
    #                 `tasFirstArrTime`           AS first_arr_time,
    #                 `tasMaxDistance`            AS max_distance,
    #                 `tasResultsType`            AS result_type,
    #                 `tasTotalDistanceFlown`     AS tot_dist_flown,
    #                 `tasTotDistOverMin`         AS tot_dist_over_min,
    #                 `tasQuality`                AS day_quality,
    #                 `tasDistQuality`            AS dist_validity,
    #                 `tasTimeQuality`            AS time_validity,
    #                 `tasLaunchQuality`          AS launch_validity,
    #                 `tasStopQuality`            AS stop_validity,
    #                 `tasAvailDistPoints`        AS avail_dist_points,
    #                 `tasAvailLeadPoints`        AS avail_lead_points,
    #                 `tasAvailTimePoints`        AS avail_time_points,
    #                 `tasAvailArrPoints`         AS avail_arr_points,
    #                 `tasLaunchValid`,
    #                 `tasPilotsLaunched`         AS pilots_flying,
    #                 `tasPilotsTotal`            AS pilots_present,
    #                 `tasPilotsES`               AS pilots_es,
    #                 `tasPilotsLO`               AS pilots_lo,
    #                 `tasPilotsGoal`             AS pilots_goal,
    #                 `maxScore`                  AS max_score,
    #                 `tasGoalAlt`                AS goal_altitude,
    #                 `tasCode`
    #             FROM
    #                 `TaskView`
    #             WHERE
    #                 `tasPk` = {}
    #             LIMIT 1
    #         """.format(task_id))

    query = """ SELECT
                    T.`comPk`                       AS comp_id,
                    T.`comName`                     AS comp_name,
                    T.`comClass`                    AS comp_class,
                    DATE_FORMAT(T.`tasDate`, '%%Y-%%m-%%d') AS task_date,
                    T.`tasName`                     AS task_name,
                    T.`comTimeOffset`               AS time_offset,
                    T.`tasComment`                  AS task_comment,
                    DATE_FORMAT(T.`tasTaskStart`, '%%T')   AS window_open_time,
                    DATE_FORMAT(T.`tasFinishTime`, '%%T')  AS task_deadline,
                    DATE_FORMAT(T.`tasLaunchClose`, '%%T') AS window_close_time,
                    T.`tasCheckLaunch`              AS check_launch,
                    DATE_FORMAT(T.`tasStartTime`, '%%T')   AS SS_time,
                    DATE_FORMAT(T.`tasStartCloseTime`, '%%T') AS SS_close_time,
                    T.`tasSSInterval`               AS SS_interval,
                    DATE_FORMAT(T.`tasLastStartTime`, '%%T') AS last_start_time,
                    T.`tasTaskType`                 AS task_type,
                    T.`tasDistance`                 AS task_distance,
                    T.`tasShortRouteDistance`       AS task_opt_dist,
                    T.`tasSSDistance`               AS SS_distance,
                    T.`forName`                     AS formula_name,
                    T.`forDiffDist`                 AS diff_distance,
                    T.`forGoalSSpenalty`            AS no_goal_penalty,
                    T.`forStoppedGlideBonus`        AS glide_bonus,
                    T.`forStoppedElapsedCalc`       AS stopped_time_calc,
                    T.`forNomGoal`                  AS nominal_goal,
                    T.`forMinDistance`              AS min_dist,
                    T.`forNomDistance`              AS nominal_dist,
                    T.`forNomTime`                  AS nominal_time,
                    T.`forNomLaunch`                AS nominal_launch,
                    T.`forScorebackTime`            AS score_back_time,
                    T.`tasDeparture`                AS departure,
                    T.`tasArrival`                  AS arrival,
                    T.`tasHeightBonus`              AS height_bonus,
                    T.`tasMargin`                   AS tolerance,
                    DATE_FORMAT(T.`tasStoppedTime`, '%%T') AS task_stopped_time,
                    TT.`minTime`                    AS fastest_time,
                    TT.`firstStart`                 AS first_dep_time,
                    TT.`firstESS`                   AS first_arr_time,
                    TT.`maxDist`                    AS max_distance,
                    T.`tasResultsType`              AS result_type,
                    TT.`TotalDistance`              AS tot_dist_flown,
                    TT.`TotDistOverMin`             AS tot_dist_over_min,
                    T.`tasQuality`                  AS day_quality,
                    T.`tasDistQuality`              AS dist_validity,
                    T.`tasTimeQuality`              AS time_validity,
                    T.`tasLaunchQuality`            AS launch_validity,
                    T.`tasStopQuality`              AS stop_validity,
                    T.`tasAvailDistPoints`          AS avail_dist_points,
                    T.`tasAvailLeadPoints`          AS avail_lead_points,
                    T.`tasAvailTimePoints`          AS avail_time_points,
                    T.`tasAvailArrPoints`           AS avail_arr_points,
                    T.`tasLaunchValid`,
                    T.`tasPilotsLaunched`           AS pilots_flying,
                    TT.`TotalPilots`                AS pilots_present,
                    TT.`TotalESS`                   AS pilots_es,
                    T.`tasPilotsLO`                 AS pilots_lo,
                    TT.`TotalGoal`                  AS pilots_goal,
                    T.`maxScore`                    AS max_score,
                    T.`tasGoalAlt`                  AS goal_altitude,
                    T.`tasCode`,
                    TT.`LCmin`                      AS min_lead_coeff
                FROM
                    `TaskView` T
                    LEFT OUTER JOIN `TaskTotalsView` TT using(`tasPk`)
                WHERE
                    T.`tasPk` = %s
                LIMIT 1
            """

    if test:
        print('read task:')
        print('Query:')
        print(query)

    with Database() as db:
        t = db.fetchone(query, [task_id])
    if t is None:
        print('Task does not exist')
        return

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
                        'last_start_time',
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
                        'goal_altitude',
                        'min_lead_coeff']
    comp_id = t['comp_id']
    task_code = t['tasCode']
    info = {x:t[x] for x in info_data}
    formula = {x:t[x] for x in formula_data}
    stats = {x:t[x] for x in stats_data}

    return comp_id, task_code, info, formula, stats

def read_task_route(task_id, test = 0):
    '''gets task route from database and creates a dict'''

    query = """
            SELECT
                `TW`.`tawNumber` 		AS `number`,
                `W`.`rwpName`			AS `ID`,
                `W`.`rwpDescription`	AS `description`,
                `TW`.`tawTime`			AS `time`,
                `TW`.`tawType`			AS `type`,
                `TW`.`tawHow`			AS `how`,
                `TW`.`tawShape`			AS `shape`,
                `TW`.`tawAngle`			AS `angle`,
                `TW`.`tawRadius`		AS `radius`,
                `TW`.`ssrCumulativeDist` AS `cumulative_dist`
            FROM
                `tblTaskWaypoint` `TW`
                JOIN `tblRegionWaypoint` `W` USING(`rwpPk`)
            WHERE
                `tasPk` = {}
            """.format(task_id)
    if test:
        print('read task route:')
        print('Query:')
        print(query)

    with Database() as db:
        # get the task details.
        task = db.fetchall(query)

    return task

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
