"""
Competition Library

contains
    Comp class
    function to write comp result json file
    function to write comp result fsdb file

Use: from comp import Comp

Stuart Mackintosh Antonio Golfari - 2019
"""

from myconn     import Database
from formula    import Task_formula
from calcUtils  import json, get_datetime, decimal_to_seconds, time_difference
from igc_lib    import defaultdict
from pathlib    import Path
import jsonpickle
import Defines

class Comp(object):
    """Comp definition, DB operations
        Some Attributes:
        turnpoints: list - A list of Turnpoint objects.
        start_date: datetime.date
        end_date:   datetime.date
        comp_class: str - PG, HG etc.
        location:   str
        opt_dist_to_SS: optimised distance to SSS, calculated with method calculate_optimised_task_length
        opt_dist_to_ESS: optimised distance to ESS from takeoff, calculated with method calculate_optimised_task_length
        SS_distance: optimised distance from SSS to ESS, calculated with method calculate_optimised_task_length

    methods:
        database
        read(comp_id): read comp info from DB
        clear_waypoints: delete waypoints from tblTaskWaypoint
        update_waypoints:  write waypoints to tblTaskWaypoint

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

    def __init__(self, comp_id=None, comp_name=None, comp_site=None, date_from=None, date_to=None,
                    comp_class=None, region=None):
        self.id                         = comp_id           # comPk
        self.comp_name                  = comp_name         # str
        self.comp_site                  = comp_site         # str
        self.date_from                  = date_from         # in datetime.date (Y-m-d) format
        self.date_to                    = date_to           # in datetime.date (Y-m-d) format
        self.comp_class                 = comp_class        # 'PG', 'HG', 'mixed'
        self.region                     = region            # Region object
        self.participants               = []                # list of Partecipant obj
        self.tasks                      = []                # list of Task obj.
        self.stats                      = dict()            # event statistics
        self.rankings                   = dict()            # rankings
        self.formula                    = dict()
        self.data                       = dict()
        self.MD_name                    = None              # str
        self.contact                    = None              # str
        self.cat_id                     = None              # claPk
        self.sanction                   = None              # 'League', 'PWC', 'FAI 1', 'FAI 2', 'none'
        self.type                       = None              # 'RACE', 'Route', 'Team-RACE'
        self.comp_code                  = None              # str 8 chars codename
        self.restricted                 = None              # bool
        self.time_offset                = None              # int
        self.stylesheet                 = None              # str
        self.locked                     = None              # bool
        self.external                   = None              # bool
        self.website                    = None              # str

        # self.formula                    = Task_formula.read(self.id) if self.id else None

    def __setattr__(self, attr, value):
        from calcUtils import get_date
        import datetime
        if attr in ('date_from', 'date_to'):
            if type(value) is str:
                value = get_date(value)
            elif isinstance(value, datetime.datetime):
                value = value.date()
        if attr =='comp_id':
            attr = 'id'
        self.__dict__[attr] = value

    def __str__(self):
        out = ''
        out += 'Comp:'
        out += f'{self.comp_name} - from {self.start_date_str} to {self.end_date_str} \n'
        out += f'{self.comp_site} \n'
        return out

    @property
    def start_date_str(self):
        from datetime import datetime
        return self.date_from.strftime("%Y-%m-%d")

    @property
    def end_date_str(self):
        from datetime import datetime
        return self.date_to.strftime("%Y-%m-%d")

    @property
    def file_path(self):
        from datetime import datetime
        from os import path as p
        from Defines import FILEDIR
        return p.join(FILEDIR, self.date_to.strftime("%Y"), self.comp_code.lower())

    def as_dict(self):
        return self.__dict__

    @staticmethod
    def read(comp_id):
        """Reads competition from database
        takes comPk as argument"""
        from db_tables import CompObjectView as C

        if not (type(comp_id) is int and comp_id > 0):
            print(f"comp_id needs to be int > 0, {comp_id} was given")
            return None

        comp = Comp(comp_id=comp_id)

        with Database() as db:
            # get comp details.
            q   = db.session.query(C).get(comp_id)
            db.populate_obj(comp, q)
            comp.formula =   {x:getattr(q, x) for x in ['formula_name',
                                                    'formula_class',
                                                    'overall_validity',
                                                    'validity_param',
                                                    'team_size',
                                                    'team_scoring',
                                                    'team_over']}
        return comp

    def update_comp_info(self):
        from datetime import datetime as dt
        from db_tables import tblCompetition as C

        with Database() as db:
            q = db.session.query(C).get(self.id)
            q.comDateFrom       = self.date_from
            q.comDateTo         = self.date_to
            q.comName           = self.comp_name
            q.comCode           = self.comp_code
            q.comSanction       = self.sanction
            q.comLocation       = self.comp_site
            q.regPk             = self.region
            q.comContact        = self.contact
            q.comMeetDirName    = self.MD_name
            q.comTimeOffset     = self.time_offset/3600
            q.claPk             = self.cat_id
            q.comExtUrl         = self.website
            q.comExt            = self.external
            q.comEntryRestrict  = self.restricted
            q.comClass          = self.comp_class
            q.comType           = self.type
            q.comLocked         = self.locked
            q.comStyleSheet     = self.stylesheet
            db.session.commit()

    @staticmethod
    def from_json(comp_id, ref_id=None):
        """Reads competition from json result file
        takes comPk as argument"""
        from    db_tables      import tblResultFile as R
        from    participant    import Partecipant
        from    sqlalchemy     import and_, or_
        import  json

        if type(comp_id) is int and comp_id > 0:
            with Database() as db:
                if ref_id:
                    file = db.session.query(R).get(ref_id).refJSON
                else:
                    file = db.session.query(R.refJSON).filter(and_(R.comPk==comp_id, R.tasPk==None, R.refVisible==1)).limit(1).scalar()
            if file:
                comp = Comp(comp_id=comp_id)
                with open(file, 'r') as f:
                    '''read task json file'''
                    data = json.load(f)
                    for k in comp.__dict__.keys():
                        # not using update to intercept changings in formats
                        if k in data['info'].keys(): setattr(comp, k, data['info'][k])
                    # comp.as_dict().update(data['info'])
                    comp.stats.update(data['stats'])
                    comp.rankings.update(data['rankings'])
                    comp.tasks.extend(data['tasks'])
                    comp.formula.update(data['formula'])
                    comp.data.update(data['data'])
                    results = []
                    for p in data['results']:
                        '''get participants'''
                        participant = Partecipant(comp_id=comp_id)
                        participant.as_dict().update(p)
                        results.append(participant)
                    # should already be ordered, so probably not necessary
                    comp.participants = sorted(results, key=lambda k: k.score, reverse=True)
                return comp

    @staticmethod
    def create_results(comp_id, status=None):
        '''creates the json result file and the database entry'''
        from    compUtils  import get_tasks_result_files, get_participants
        from    result     import Comp_result as C, create_json_file
        from    pprint     import pprint as pp
        from    os         import path
        from Defines       import JSONDIR
        import  json

        '''PARAMETER: decimal positions'''
        d = 0       # should be a formula parameter, or a ForComp parameter?

        comp = Comp.read(comp_id)

        '''retrieve active task result files and reads info'''
        files = get_tasks_result_files(comp_id)

        if files:
            val     = comp.formula['overall_validity']           # ftv, round, all
            param   = comp.formula['validity_param']             # ftv param, dropped task param
            if val == 'ftv':
                ftv_type        = comp.formula['formula_class']  # pwc, fai
                # avail_validity  = 0                                     # total ftv validity

        '''inzialize obj attributes'''
        tasks           = []
        participants    = get_participants(comp_id)
        stats           = {'tot_dist_flown':0.0, 'tot_flights':0, 'valid_tasks':len(files),
                            'tot_pilots':len(participants)}
        rankings        = {}


        for idx, t in enumerate(files):
            file = path.join(JSONDIR, t.file)
            with open(file, 'r') as f:
                '''read task json file'''
                data = json.load(f)

                '''create task code'''
                code = ('T'+str(idx+1))

                '''get task info'''
                task = {'code':code, 'id':t.task_id}
                i = dict(data['info'], **data['stats'])
                task.update({x:i[x] for x in C.tasks_list})
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
                for res in data['results']:
                    task_results.setdefault(res['par_id'], {}).update({code:res['score']})
                for p in participants:
                    s = round(task_results.get(p.par_id, {})[code], d)
                    r = task['ftv_validity'] if val == 'ftv' else 1000
                    if r > 0:   #sanity
                        perf = round(s / r, d+3)
                        p.results.update({code:{'pre':s, 'perf':perf, 'score':s}})
                    else:
                        p.results.update({code:{'pre':s, 'perf':0, 'score':0}})

        '''calculate final score'''
        results = get_final_scores(participants, tasks, comp.formula, d)
        stats['winner_score'] = max([t.score for t in results])

        comp.tasks          = tasks
        comp.stats          = stats
        comp.rankings       = rankings
        comp.participants   = sorted(results, key=lambda k: k.score, reverse=True)

        '''create json file'''
        result =    {   'info':     {x:getattr(comp, x) for x in C.info_list},
                        'rankings': comp.rankings,
                        'tasks':    [t for t in comp.tasks],
                        'results':  [{x:getattr(res, x) for x in C.result_list} for res in results],
                        'formula':  comp.formula,
                        'stats':    comp.stats
                    }
        ref_id = create_json_file(comp_id=comp.id, task_id=None, code=comp.comp_code, elements=result, status=status)
        return ref_id

def get_final_scores(results, tasks, formula, d = 0):
    '''calculate final scores depending on overall validity:
        - all:      sum of all tasks results
        - round:    task discard every [param] tasks
        - ftv:      calculate task scores and total score based on FTV [param]

        input:
            results:    participant list
            tasks:      tasks list
            formula:    comp formula dict
            d:          decimals on single tasks score, default 0
    '''
    from operator import itemgetter

    val     = formula['overall_validity']
    param   = formula['validity_param']

    if      val == 'ftv':   avail_validity  = sum(t['ftv_validity'] for t in tasks) * param
    elif    val == 'round': dropped         = int(len(tasks) / param)

    for pil in results:
        pil.score = 0

        ''' if we score all tasks, or tasks are not enough to ha discards,
            or event has just one valid task regardless method,
            we can simply sum all score values
        '''
        if not( (val == 'all')
                or (val == 'round' and dropped == 0)
                or (len(tasks) < 2) ):
            '''create a ordered list of results, perf desc'''
            sorted_results = sorted(pil.results.items(), key=lambda x: (x[1]['perf'], x[1]['pre']), reverse=True)

            if (val == 'round' and len(tasks) >= param):
                '''we need to order by score desc and sum only the ones we need'''
                for i in range(dropped):
                    id = sorted_results.pop()[0]                # getting id of worst result task
                    pil.results[id]['score'] = 0

            elif val == 'ftv' and len(tasks) > 1:
                '''ftv calculation'''
                pval = avail_validity
                for id, s in sorted_results:
                    if not(pval > 0):
                        pil.results[id]['score'] = 0
                    else:
                        '''get ftv_validity of corresponding task'''
                        tval = [t['ftv_validity'] for t in tasks if t['code'] == id].pop()
                        if pval > tval:
                            '''we can use the whole score'''
                            pval -= tval
                        else:
                            '''we need to calculate proportion'''
                            pil.results[id]['score'] = round(pil.results[id]['score']*(pval/tval), d)
                            pval = 0

        '''calculates final pilot score'''
        pil.score = sum(pil.results[x]['score'] for x in pil.results)

    return results
