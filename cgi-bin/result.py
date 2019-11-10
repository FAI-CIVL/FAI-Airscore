"""
Results Library

contains
    Task_result class
    Comp_result class

Methods:
    create_result - write result to JSON file and creates DB entry (tblResultFile)

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019

"""

from myconn import Database

class Task_result:
    """
        creates Task Result sheets
        - in JSON format
        - in HTML format for AirTribune
    """

    def __init__(self, ref_id = None, comp_id = None, task_id = None, status = None, task = None, rankings = None, info = None, formula = None, stats = None, results = None, filename = None):
        self.ref_id     = ref_id        # refPk row in database
        self.status     = status        # status of the result ('provisional', 'final', )
        self.comp_id    = comp_id       # comPk
        self.task_id    = task_id       # tasPk
        self.task       = task          # task route info
        self.rankings   = rankings      # list of sub rankings
        self.info       = info          # list of info about the task
        self.formula    = formula       # task formula parameters
        self.stats      = stats         # statistics
        self.results    = results       # list of pilots result
        self.filename   = filename      # json filename

        from time import time
        self.timestamp  = int(time())   #timestamp of generation

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

    def to_json(self, filename = None, status = None):
        """
        creates the JSON file of the result
        """
        import os
        import simplejson as json
        from calcUtils import DateTimeEncoder

        if filename:    self.filename = filename
        if status:      self.status   = status

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

    def to_db(self):
        """
        insert the result into database
        """

        '''store timestamp in local time'''
        timestamp = int(self.timestamp + self.info['time_offset'])

        query = """
                    INSERT INTO `tblResultFile`(
                        `comPk`,
                        `tasPk`,
                        `refTimestamp`,
                        `refJSON`,
                        `refStatus`
                    )
                    VALUES(%s, %s, %s, %s, %s)
                """
        params = [self.comp_id, self.task_id, timestamp, self.filename, self.status]

        with Database() as db:
            self.ref_id = db.execute(query, params)
        return self.ref_id

    @staticmethod
    def create_result(task, results, status=None):
        ''' create task results json file from task object and results list
            inputs:
                - task:         OBJ     - Task Object
                - results:      LIST    - Flight_result Objects
                - status:       STR     - 'provisional', 'official' ...
        '''
        from    datetime import datetime
        from    pprint   import pprint as pp
        import  Defines  as d

        comp_id         = task.comp_id
        task_id         = task.id

        result          = Task_result(comp_id=comp_id, task_id=task_id, status=status)

        dt              = datetime.fromtimestamp(result.timestamp).strftime('%Y%m%d_%H%M%S')
        result.filename = d.JSONDIR + '_'.join([task.task_code,dt]) + '.json'

        '''create result object elements from task, formula and results objects'''
        result.get_task_info(task)
        result.get_formula(task.formula)
        result.get_task_stats(task.stats)
        result.get_task_route(task)
        result.get_task_pilots(results)
        result.rankings = read_rankings(task_id)

        '''create json file'''
        result.to_json()

        ref_id = result.to_db() if not None else 0
        return ref_id

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


class Comp_result(object):
    """
        creates Task Result sheets
        - in JSON format
        - in HTML format for AirTribune
    """

    def __init__(self, comp_id, status = None, tasks = None, stats = None, results = None, rankings = None):
        self.comp_id    = comp_id
        self.status     = status            # str:  status of the result ('provisional', 'final', )
        self.tasks      = tasks             # list: comp tasks info
        self.rankings   = rankings          # dict: sub rankings
        self.stats      = stats             # dict: comp statistics
        self.results    = results           # list: pilots results

        from    time     import time
        from    datetime import datetime
        import  Defines  as d

        self.info, self.formula = self.get_info()   # dict: info about the comp
        self.timestamp          = int(time())       # timestamp of generation
        dt                      = datetime.fromtimestamp(self.timestamp).strftime('%Y%m%d_%H%M%S')
        self.filename           = d.JSONDIR + '_'.join([self.info['comp_code'],dt]) + '.json'

    def get_info(self):
        '''gets comp info from database'''
        with Database() as db:
            query = """ SELECT
                            `comp_name`,
                            `comp_site`,
                            `date_from`,
                            `date_to`,
                            `MD_name`,
                            `contact`,
                            `sanction`,
                            `type`,
                            `comp_code`,
                            `restricted`,
                            `time_offset`,
                            `comp_class`,
                            `website`,
                            `formula`,
                            `formula_class`,
                            `task_validity`,
                            `validity_param`,
                            `team_size`,
                            `team_scoring`,
                            `team_over`
                        FROM
                            `CompResultView`
                        WHERE
                            `comp_id` = %s
                        LIMIT 1
                    """
            list = db.fetchone(query, [self.comp_id])
            info = {x:list[x] for x in ['comp_name',
                                        'comp_site',
                                        'date_from',
                                        'date_to',
                                        'MD_name',
                                        'contact',
                                        'sanction',
                                        'type',
                                        'comp_code',
                                        'restricted',
                                        'time_offset',
                                        'comp_class',
                                        'website']}

            formula = {x:list[x] for x in [ 'formula',
                                            'formula_class',
                                            'task_validity',
                                            'validity_param',
                                            'team_size',
                                            'team_scoring',
                                            'team_over']}

        return info, formula

    @classmethod
    def create_from_json(cls, comp_id, status=None):
        """
            reads task result json files and create comp result object
            inputs:
                - comp_id:      INT - comPk comp database ID
                - status        STR - 'provisional', 'official' ...
        """
        from pprint import pprint as pp
        import json

        '''PARAMETER: decimal positions'''
        d = 0       # should be a formula parameter, or a ForComp parameter?

        with Database() as db:
            '''getting active json files list'''
            query = """ SELECT
                            `tasPk` AS `task_id`,
                            `refJSON` AS `file`
                        FROM
                            `tblResultFile`
                        WHERE
                            `comPk` = %s
                        AND `refVisible` = 1
                        ORDER BY
                            `tasPk`
                        """
            files = db.fetchall(query, [comp_id])

        if not files:
            return None

        '''create result object'''
        comp_result = cls(comp_id=comp_id, status=status)

        val     = comp_result.formula['task_validity']              # ftv, round, all
        param   = comp_result.formula['validity_param']             # ftv param, dropped task param
        if val == 'ftv':
            ftv_type        = comp_result.formula['formula_class']  # pwc, fai
            # avail_validity  = 0                                     # total ftv validity

        '''inzialize obj attributes'''
        tasks       = []
        results     = get_pilots(comp_id)
        stats       = {'tot_dist_flown':0.0, 'tot_flights':0, 'valid_tasks':len(files),
                            'tot_pilots':len(results)}
        rankings    = {}

        tasks_list  = ['task_name', 'date',
                        'opt_dist', 'day_quality', 'max_score', 'pilots_goal']

        for idx, t in enumerate(files):
            with open(t['file'], 'r') as f:
                '''read task json file'''
                data = json.load(f)

                '''create task code'''
                code = ('T'+str(idx+1))

                '''get task info'''
                task = {'code':code, 'id':t['task_id']}
                i = dict(data['info'], **data['stats'])
                task.update({x:i[x] for x in tasks_list})
                if val == 'ftv':
                    task['ftv_validity'] = (  round(task['max_score'], d) if ftv_type == 'pwc'
                                         else round(task['day_quality']*1000, d) )
                    # avail_validity       += task['ftv_validity']
                tasks.append(task)

                '''add task stats to overall'''
                stats['tot_dist_flown'] += float(i['tot_dist_flown'])
                stats['tot_flights']    += int(i['pilots_launched'])

                ''' get rankings (just once)'''
                if not rankings: rankings.update(data['rankings'])

                '''get pilots result'''
                task_results = {}
                for t in data['results']:
                    task_results.setdefault(t['pil_id'], {}).update({code:t['score']})
                for p in results:
                    s = round(task_results.get(p['pil_id'], {})[code], d)
                    r = task['ftv_validity'] if val == 'ftv' else 1000
                    if r > 0:   #sanity
                        perf = round(s / r, d+3)
                        p['results'].update({code:{'pre':s, 'perf':perf, 'score':s}})
                    else:
                        p['results'].update({code:{'pre':s, 'perf':0, 'score':0}})

        '''calculate final score'''
        results = get_final_scores(results, tasks, comp_result.formula, d)
        stats['winner_score'] = max([t['score'] for t in results])

        comp_result.tasks       = tasks
        comp_result.stats       = stats
        comp_result.rankings    = rankings
        comp_result.results     = results

        '''create json file'''
        comp_result.to_json()

        ref_id = comp_result.to_db() if not None else 0
        return ref_id

    def to_json(self, filename = None, status = None):
        """
        creates the JSON file of comp result
        """
        import os
        import simplejson as json
        from calcUtils import DateTimeEncoder

        if filename:    self.filename = filename
        if status:      self.status   = status

        result =    {   'data':     {'timestamp':self.timestamp, 'status':self.status},
                        'info':     self.info,
                        'rankings': self.rankings,
                        'tasks':    [t for t in self.tasks],
                        'results':  [res for res in self.results],
                        'formula':  self.formula,
                        'stats':    self.stats
                    }

        with open(self.filename, 'w') as f:
            json.dump(result, f)
        os.chown(self.filename, 1000, 1000)
        return self.filename

    def to_db(self):
        """
        insert the result into database
        """

        '''store timestamp in local time'''
        timestamp = int(self.timestamp + self.info['time_offset'])

        query = """
                    INSERT INTO `tblResultFile`(
                        `comPk`,
                        `refTimestamp`,
                        `refJSON`,
                        `refStatus`
                    )
                    VALUES(%s, %s, %s, %s)
                """
        params = [self.comp_id, timestamp, self.filename, self.status]

        with Database() as db:
            self.ref_id = db.execute(query, params)
        return self.ref_id

def get_pilots(comp_id):
    '''gets registered pilots list from database'''
    query = """ SELECT
                    `regPk` AS `reg_id`,
                    `pilPk` AS `pil_id`,
                    `regName` AS `name`,
                    `regSex` AS `sex`,
                    `regNat` AS `nat`,
                    `regGlider` AS `glider`,
                    `regCert` AS `class`,
                    `regSponsor` AS `sponsor`,
                    `regCIVL` AS `civl`,
                    `regFAI` AS `fai`,
                    `regTeam` AS `team`
                FROM
                    `tblRegistration`
                WHERE
                    `comPk` = %s
            """

    with Database() as db:
        list = db.fetchall(query, [comp_id])
    for pil in list:
        pil['name']     = pil['name'].title()
        pil['glider']   = pil['glider'].title()
        pil['results']  = {}    # empty dict for scores

    return list


def read_rankings(task_id):
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

    return rank

def get_final_scores(results, tasks, formula, d = 0):
    '''calculate final scores depending on overall validity:
        - all:      sum of all tasks results
        - round:    task discard every [param] tasks
        - ftv:      calculate task scores and total score based on FTV [param]

        input:
            results:    pilots list
            tasks:      tasks list
            formula:    comp formula dict
            d:          decimals on single tasks score, default 0
    '''
    from operator import itemgetter

    val     = formula['task_validity']
    param   = formula['validity_param']

    if      val == 'ftv':   avail_validity  = sum(t['ftv_validity'] for t in tasks) * param
    elif    val == 'round': dropped         = int(len(tasks) / param)

    for pil in results:
        pil['score'] = 0

        ''' if we score all tasks, or tasks are not enough to ha discards,
            or event has just one valid task regardless method,
            we can simply sum all score values
        '''
        if not( (val == 'all')
                or (val == 'round' and dropped == 0)
                or (len(tasks) < 2) ):
            '''create a ordered list of results, perf desc'''
            sorted_results = sorted(pil['results'].items(), key=lambda x: (x[1]['perf'], x[1]['pre']), reverse=True)

            if (val == 'round' and len(tasks) >= param):
                '''we need to order by score desc and sum only the ones we need'''
                for i in range(dropped):
                    id = sorted_results.pop()[0]                # getting id of worst result task
                    pil['results'][id]['score'] = 0

            elif val == 'ftv' and len(tasks) > 1:
                '''ftv calculation'''
                pval = avail_validity
                for id, s in sorted_results:
                    if not(pval > 0):
                        pil['results'][id]['score'] = 0
                    else:
                        '''get ftv_validity of corresponding task'''
                        tval = [t['ftv_validity'] for t in tasks if t['code'] == id].pop()
                        if pval > tval:
                            '''we can use the whole score'''
                            pval -= tval
                        else:
                            '''we need to calculate proportion'''
                            pil['results'][id]['score'] = round(pil['results'][id]['score']*(pval/tval), d)
                            pval = 0

        '''calculates final pilot score'''
        pil['score'] = sum(pil['results'][x]['score'] for x in pil['results'])

    return results

def read_task_result(task_id):
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

    with Database() as db:
        # get the task details.
        results = db.fetchall(query, [task_id])

    return results
