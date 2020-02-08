"""
Competition Library

contains
    Comp class
    function to write comp result json file
    function to write comp result fsdb file

Use: from comp import Comp

Stuart Mackintosh Antonio Golfari - 2019
"""

import json

from compUtils import get_tasks_result_files, get_participants, read_rankings, calculate_comp_path
from calcUtils import get_date
from Defines import FILEDIR, RESULTDIR
from participant import Participant
from formula import Formula
from os import path
from result import Comp_result, create_json_file
from task import Task
from myconn import Database
from db_tables import tblCompetition
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError


class Comp(object):
    """Comp definition, DB operations
        Some Attributes:
        date_from: datetime.date
        date_to:   datetime.date
        comp_class: str - PG, HG etc.
        comp_site:   str

    methods:
        database
        read(comp_id): read comp info from DB

    """

    def __init__(self, comp_id=None, comp_name=None, comp_site=None, date_from=None, comp_code=None, date_to=None,
                 comp_class=None, region=None, comp_type='RACE', restricted=True, locked=False, external=False):

        self.comp_id = comp_id  # comPk
        self.comp_name = comp_name  # str
        self.comp_site = comp_site  # str
        self.date_from = date_from  # in datetime.date (Y-m-d) format
        self.date_to = date_to  # in datetime.date (Y-m-d) format
        self.comp_class = comp_class  # 'PG', 'HG', 'mixed'
        self.region = region  # Region object
        self.participants = []  # list of Participant obj
        self.tasks = []  # list of Task obj.
        # self.stats = dict()  # event statistics
        self.rankings = dict()  # rankings
        # self.data = dict()
        self.formula = None  # Formula obj.
        self.MD_name = None  # str
        self.contact = None  # str
        self.cat_id = None  # claPk
        self.sanction = None  # 'League', 'PWC', 'FAI 1', 'FAI 2', 'none'
        self.comp_type = comp_type  # 'RACE', 'Route', 'Team-RACE'
        self.comp_code = comp_code  # str 8 chars codename
        self.restricted = restricted  # bool
        self.openair_file = None  # STR
        self.time_offset = None  # int
        self.stylesheet = None  # str
        self.locked = locked  # bool
        self.external = external  # bool
        self.website = None  # str
        self.comp_path = None  # str
        self.results = []

        # self.formula                    = Formula.read(self.comp_id) if self.comp_id else None

    def __setattr__(self, attr, value):
        import datetime
        if attr in ('date_from', 'date_to'):
            if type(value) is str:
                value = get_date(value)
            elif isinstance(value, datetime.datetime):
                value = value.date()
        self.__dict__[attr] = value

    def __str__(self):
        out = ''
        out += 'Comp:'
        out += f'{self.comp_name} - from {self.start_date_str} to {self.end_date_str} \n'
        out += f'{self.comp_site} \n'
        return out

    @property
    def id(self):
        return self.comp_id

    @property
    def start_date_str(self):
        return self.date_from.strftime("%Y-%m-%d")

    @property
    def end_date_str(self):
        return self.date_to.strftime("%Y-%m-%d")

    @property
    def file_path(self):
        if not self.comp_path:
            self.create_path()
        return path.join(FILEDIR, str(self.date_from.year), self.comp_code.lower())

    @property
    def tot_validity(self):
        if len(self.tasks) > 0:
            return round(sum([t.ftv_validity for t in self.tasks]), 4)
        else:
            return 0

    @property
    def avail_validity(self):
        if len(self.tasks) > 0:
            if self.formula.overall_validity == 'ftv':
                return round(self.tot_validity * self.formula.validity_param, 4)
            else:
                return self.tot_validity
        return 0

    @property
    def dropped_tasks(self):
        if len(self.tasks) > 0:
            if self.formula.overall_validity == 'round':
                return int(len(self.tasks) / self.formula.validity_param)
        return 0

    @property
    def airspace_check(self):
        if self.openair_file:
            return True
        return False

    def as_dict(self):
        return self.__dict__

    ''' * Statistic Properties *'''

    @property
    def tot_pilots(self):
        if len(self.tasks) > 0:
            return len(self.participants)
        else:
            return 0

    @property
    def valid_tasks(self):
        if len(self.tasks) > 0:
            return len([t for t in self.tasks if t.is_valid()])
        else:
            return 0

    @property
    def tot_flights(self):
        if len(self.tasks) > 0:
            return sum([t.pilots_launched for t in self.tasks])
        else:
            return 0

    @property
    def tot_distance_flown(self):
        if len(self.tasks) > 0:
            return sum([t.tot_distance_flown for t in self.tasks])
        else:
            return 0

    @property
    def winner_score(self):
        if len([x for x in self.results if 'score' in x.keys()]) > 0:
            return max(r['score'] for r in self.results)
        else:
            return 0

    @property
    def tot_flight_time(self):
        if len(self.tasks) > 0:
            return sum([t.tot_flight_time for t in self.tasks])
        else:
            return 0

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
            try:
                q = db.session.query(C).get(comp_id)
                # comp = Comp(comp_id=comp_id)
                db.populate_obj(comp, q)
                comp.formula = Formula(comp_id=comp_id)
                db.populate_obj(comp.formula, q)
            except SQLAlchemyError:
                print("Comp Read Error")
                db.session.rollback()
                return None
        return comp

    def create_path(self, filepath=None):
        """create filepath from # and date if not given
            and store it in database"""

        if filepath:
            self.comp_path = filepath
        elif self.comp_code and self.date_from:
            self.comp_path = calculate_comp_path(self.date_from, self.comp_code)
        else:
            return

        with Database() as db:
            q = db.session.query(tblCompetition).get(self.id)
            q.comPath = self.comp_path
            db.session.commit()

    def to_db(self):
        """create or update a DB entry from Comp object. If comp_id is provided it will update otherwise add a new row
            mandatory info for a comp:
                comp_name
                comp_code (short name)
                date_from
                date_to
                comp_class (PG or HG)
                comp_site - location of the comp. String can be site name or general description
        """

        '''check we have the minimum required info'''
        if not (self.comp_name and self.comp_code and self.date_from and self.comp_class and self.comp_site):
            print('cannot insert an invalid competition. Need more info.')
            return None

        with Database() as db:
            try:
                if self.comp_id is not None:
                    row = db.session.query(tblCompetition).get(self.comp_id)
                else:
                    row = tblCompetition()

                row.comName = self.comp_name
                row.comCode = self.comp_code
                row.comDateFrom = self.date_from
                row.comDateTo = self.date_to
                row.comLocation = self.comp_site
                row.comClass = self.comp_class
                row.claPk = self.cat_id
                row.comMeetDirName = self.MD_name
                row.comContact = self.contact
                row.comTimeOffset = self.time_offset
                row.comSanction = self.sanction
                row.comOpenAirFile = self.openair_file
                row.comType = self.comp_type
                row.comEntryRestrict = 'registered' if self.restricted else 'open'
                row.comLocked = self.locked
                row.comStyleSheet = self.stylesheet
                row.comExt = self.external
                row.comExtUrl = self.website
                row.comPath = self.comp_path if not None else calculate_comp_path(self.date_from, self.comp_code)
                if self.comp_id is None:
                    db.session.add(row)
                db.session.flush()
                self.comp_id = row.comPk
                db.session.commit()
            except SQLAlchemyError:
                print('cannot insert competition. DB insert error.')
                db.session.rollback()
                return None

        return self.comp_id

    def get_rankings(self):
        self.rankings = read_rankings(self.comp_id)

    @staticmethod
    def from_fsdb(fs_comp):
        """gets comp and formula info from FSDB file"""
        from calcUtils import get_date

        comp = Comp()

        comp.comp_name = fs_comp.get('name')
        comp.comp_class = (fs_comp.get('discipline')).upper()
        comp.comp_site = fs_comp.get('location')
        comp.date_from = get_date(fs_comp.get('from'))
        comp.date_to = get_date(fs_comp.get('to'))
        comp.time_offset = float(fs_comp.get('utc_offset'))
        comp.sanction = ('FAI 1' if fs_comp.get('fai_sanctioning') == '1'
                         else 'FAI 2' if fs_comp.get('fai_sanctioning') == '2' else 'none')
        comp.external = True
        comp.locked = True

        return comp

    def get_tasks_details(self):
        """gets tasks details from database. They could be different from JSON data for scored tasks"""
        from db_tables import TaskObjectView as T

        with Database() as db:
            try:
                results = db.session.query(T.task_id, T.task_num, T.task_name, T.date, T.opt_dist,
                                           T.comment).filter(T.comp_id == self.comp_id).all()
                if results:
                    results = [row._asdict() for row in results]
                return results
            except SQLAlchemyError:
                print(f"Error trying to retrieve Tasks details for Comp ID {self.comp_id}")
                return None

    def update_comp_info(self):

        with Database() as db:
            try:
                q = db.session.query(tblCompetition).get(self.id)
                q.comDateFrom = self.date_from
                q.comDateTo = self.date_to
                q.comName = self.comp_name
                q.comCode = self.comp_code
                q.comSanction = self.sanction
                q.comLocation = self.comp_site
                q.regPk = self.region
                q.comContact = self.contact
                q.comMeetDirName = self.MD_name
                q.comTimeOffset = self.time_offset
                q.claPk = self.cat_id
                q.comExtUrl = self.website
                q.comExt = self.external
                q.comEntryRestrict = 'registered' if self.restricted else 'open'
                q.comClass = self.comp_class
                q.comType = self.comp_type
                q.comLocked = self.locked
                q.comStyleSheet = self.stylesheet
                db.session.commit()
            except SQLAlchemyError:
                print('cannot update competition. DB error.')
                db.session.rollback()
                return None

    @staticmethod
    def from_json(comp_id, ref_id=None):
        """Reads competition from json result file
        takes comPk as argument"""
        from db_tables import tblResultFile as R

        if type(comp_id) is int and comp_id > 0:
            with Database() as db:
                if ref_id:
                    file = db.session.query(R).get(ref_id).refJSON
                else:
                    file = db.session.query(R.refJSON).filter(
                        and_(R.comPk == comp_id, R.tasPk == None, R.refVisible == 1)).scalar()
            if file:
                comp = Comp(comp_id=comp_id)
                with open(path.join(RESULTDIR, file), 'r') as f:
                    '''read task json file'''
                    data = json.load(f)
                    for k in comp.__dict__.keys():
                        # not using update to intercept changing in formats
                        if k in data['info'].keys():
                            setattr(comp, k, data['info'][k])
                    # comp.as_dict().update(data['info'])
                    comp.stats.update(data['stats'])
                    comp.rankings.update(data['rankings'])
                    comp.tasks.extend(data['tasks'])
                    comp.formula = Formula.from_dict(data['formula'])
                    comp.data.update(data['file_stats'])
                    results = []
                    for p in data['results']:
                        '''get participants'''
                        participant = Participant(comp_id=comp_id)
                        participant.as_dict().update(p)
                        results.append(participant)
                    # should already be ordered, so probably not necessary
                    comp.participants = sorted(results, key=lambda k: k.score, reverse=True)
                return comp

    @staticmethod
    def create_results(comp_id, status=None, decimals=None):
        """creates the json result file and the database entry"""

        '''PARAMETER: decimal positions'''
        # TODO implement result decimal positions parameter
        if decimals is None or not isinstance(decimals, int):
            decimals = 0  # should be a formula parameter, or a ForComp parameter?

        comp = Comp.read(comp_id)

        '''retrieve active task result files and reads info'''
        files = get_tasks_result_files(comp_id)

        '''initialize obj attributes'''
        comp.participants = get_participants(comp_id)
        ''' get rankings '''
        comp.get_rankings()

        for idx, t in enumerate(files):
            task = Task.create_from_json(task_id=t.task_id, filename=t.file)
            comp.tasks.append(task)

            ''' task validity (if not using ftv, ftv_validity = day_quality)'''
            r = task.ftv_validity * 1000

            '''get pilots result'''
            for p in comp.participants:
                res = next((d for d in comp.results if d.get('par_id', None) == p.par_id), False)
                if res is False:
                    ''' create pilot result Dict (once)'''
                    # comp.results.append({'par_id': p.par_id, 'results': []})
                    comp.results.append({'par_id': p.par_id})
                    res = comp.results[-1]

                s = next((round(pil.score, decimals) for pil in task.pilots if pil.par_id == p.par_id), 0)

                if r > 0:  # sanity
                    perf = round(s / r, decimals + 3)
                    # res['results'].append({task.task_code: {'pre': s, 'perf': perf, 'score': s}})
                    res.update({task.task_code: {'pre': s, 'perf': perf, 'score': s}})
                else:
                    # res['results'].append({task.task_code: {'pre': s, 'perf': 0, 'score': 0}})
                    res.update({task.task_code: {'pre': s, 'perf': 0, 'score': 0}})

        '''calculate final score'''
        comp.get_final_scores(decimals)

        ''' create result elements'''
        results = []
        for res in comp.results:
            '''create results dict'''
            p = next(x for x in comp.participants if x.par_id == res['par_id'])
            r = {x: getattr(p, x) for x in Comp_result.result_list if x in dir(p)}
            r['score'] = res['score']
            r['results'] = {x: res[x] for x in res.keys() if isinstance(res[x], dict)}
            results.append(r)

        # comp.participants = sorted(results, key=lambda k: k.score, reverse=True)
        #
        '''create json file'''
        result = {'info': {x: getattr(comp, x) for x in Comp_result.info_list},
                  'rankings': comp.rankings,
                  'tasks': [{x: getattr(t, x) for x in Comp_result.task_list} for t in comp.tasks],
                  'results': results,
                  'formula': {x: getattr(comp.formula, x) for x in Comp_result.formula_list},
                  'stats': {x: getattr(comp, x) for x in Comp_result.stats_list}
                  }
        ref_id = create_json_file(comp_id=comp.id, task_id=None, code=comp.comp_code, elements=result, status=status)
        return comp, ref_id
        # return result

    def get_final_scores(self, d=0):
        """calculate final scores depending on overall validity:
            - all:      sum of all tasks results
            - round:    task discard every [param] tasks
            - ftv:      calculate task scores and total score based on FTV [param]

            input:
                results:    participant list
                tasks:      tasks list
                formula:    comp formula dict
                d:          decimals on single tasks score, default 0
        """

        val = self.formula.overall_validity
        param = self.formula.validity_param
        avail_validity = self.avail_validity

        # if val == 'ftv':
        #     avail_validity = sum(t['ftv_validity'] for t in tasks) * param
        # elif val == 'round':
        #     dropped = int(len(tasks) / param)

        for pil in self.results:
            pil['score'] = 0

            ''' if we score all tasks, or tasks are not enough to ha discards,
                or event has just one valid task regardless method,
                we can simply sum all score values
            '''
            if not ((val == 'all')
                    or (val == 'round' and self.dropped_tasks == 0)
                    or (len(self.tasks) < 2)):
                '''create a ordered list of results, perf desc'''
                # sorted_results = sorted(pil['results'], key=lambda x: (x[1]['perf'], x[1]['pre']), reverse=True)
                sorted_results = sorted([x for x in pil.items() if isinstance(x[1], dict)],
                                        key=lambda x: (x[1]['perf'], x[1]['pre']), reverse=True)

                if val == 'round' and len(self.tasks) >= param:
                    '''we need to order by score desc and sum only the ones we need'''
                    for i in range(self.dropped_tasks):
                        idx = sorted_results.pop()[0]  # getting id of worst result task
                        pil[idx]['score'] = 0

                elif val == 'ftv' and len(self.tasks) > 1:
                    '''ftv calculation'''
                    pval = avail_validity
                    for idx, s in sorted_results:
                        if not (pval > 0):
                            pil[idx]['score'] = 0
                        else:
                            '''get ftv_validity of corresponding task'''
                            tval = next(t.ftv_validity for t in self.tasks if t.task_code == idx)
                            if pval > tval:
                                '''we can use the whole score'''
                                pval -= tval
                            else:
                                '''we need to calculate proportion'''
                                pil[idx]['score'] = round(pil[idx]['score'] * (pval / tval), d)
                                pval = 0

            '''calculates final pilot score'''
            pil['score'] = sum(pil[x]['score'] for x in pil.keys() if isinstance(pil[x], dict))

        ''' order list'''
        self.results = sorted(self.results, key=lambda x: x['score'], reverse=True)

