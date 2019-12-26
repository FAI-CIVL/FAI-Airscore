"""
Competition Library

contains
    Comp class
    function to write comp result json file
    function to write comp result fsdb file

Use: from comp import Comp

Stuart Mackintosh Antonio Golfari - 2019
"""

from myconn import Database
from formula import Task_formula
from calcUtils import json, get_datetime, decimal_to_seconds, time_difference
from igc_lib import defaultdict
from pathlib import Path
import jsonpickle
import Defines


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

    def __init__(self, comp_id=None, comp_name=None, comp_site=None, date_from=None, date_to=None,
                 comp_class=None, region=None, comp_type='RACE', restricted=True, locked=False, external=False):

        self.comp_id = comp_id  # comPk
        self.comp_name = comp_name  # str
        self.comp_site = comp_site  # str
        self.date_from = date_from  # in datetime.date (Y-m-d) format
        self.date_to = date_to  # in datetime.date (Y-m-d) format
        self.comp_class = comp_class  # 'PG', 'HG', 'mixed'
        self.region = region  # Region object
        self.participants = []  # list of Partecipant obj
        self.tasks = []  # list of Task obj.
        self.stats = dict()  # event statistics
        self.rankings = dict()  # rankings
        self.data = dict()
        self.formula = None  # Formula obj.
        self.MD_name = None  # str
        self.contact = None  # str
        self.cat_id = None  # claPk
        self.sanction = None  # 'League', 'PWC', 'FAI 1', 'FAI 2', 'none'
        self.comp_type = comp_type  # 'RACE', 'Route', 'Team-RACE'
        self.comp_code = None  # str 8 chars codename
        self.restricted = restricted  # bool
        self.time_offset = None  # int
        self.stylesheet = None  # str
        self.locked = locked  # bool
        self.external = external  # bool
        self.website = None  # str
        self.comp_path = None  # str

        # self.formula                    = Formula.read(self.comp_id) if self.comp_id else None

    def __setattr__(self, attr, value):
        from calcUtils import get_date
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
        from datetime import datetime
        return self.date_from.strftime("%Y-%m-%d")

    @property
    def end_date_str(self):
        from datetime import datetime
        return self.date_to.strftime("%Y-%m-%d")

    @property
    def file_path(self):
        if not self.comp_path:
            self.create_path()
        from os import path as p
        from Defines import FILEDIR
        return p.join(FILEDIR, str(self.date_from.year), self.comp_code.lower())

    def as_dict(self):
        return self.__dict__

    @staticmethod
    def read(comp_id):
        """Reads competition from database
        takes comPk as argument"""
        from db_tables import CompObjectView as C
        from formula import Formula
        from sqlalchemy.exc import SQLAlchemyError

        if not (type(comp_id) is int and comp_id > 0):
            print(f"comp_id needs to be int > 0, {comp_id} was given")
            return None

        with Database() as db:
            # get comp details.
            try:
                q = db.session.query(C).get(comp_id)
                comp = Comp(comp_id=comp_id)
                db.populate_obj(comp, q)
                comp.formula = Formula(comp_id=comp_id)
                db.populate_obj(comp.formula, q)
            except SQLAlchemyError:
                print("Comp Read Error")
                db.session.rollback()
        return comp

    def create_path(self, filepath=None):
        """create filepath from # and date if not given
            and store it in database"""
        from db_tables import tblCompetition as C
        from os import path as p

        if filepath:
            self.comp_path = filepath
        elif self.comp_code and self.date_from:
            self.comp_path = p.join(str(self.date_from.year), str(self.comp_code).lower())
        else:
            return

        with Database() as db:
            q = db.session.query(C).get(self.id)
            q.comPath = self.comp_path
            db.session.commit()

    def to_db(self):
        """create a DB entry from Comp object
        """

        '''check we have the minimum required infos'''
        if not (self.comp_name and self.comp_code and self.date_from and self.comp_class):
            print('cannot insert an invalid competition. Need more info.')
            return None

        from db_tables import tblCompetition as C, tblForComp as FC
        from sqlalchemy.exc import SQLAlchemyError

        with Database() as db:
            try:
                if self.comp_id is not None:
                    row = db.session.query(C).get(self.comp_id)
                else:
                    row = C()

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
                row.comType = self.comp_type
                row.comEntryRestrict = 'registered' if self.restricted else 'open'
                row.comLocked = self.locked
                row.comStyleSheet = self.stylesheet
                row.comExt = self.external
                row.comExtUrl = self.website
                row.comPath = self.comp_path
                if self.comp_id is None:
                    db.session.add(row)
                db.session.flush()
                self.comp_id = row.comPk
            except SQLAlchemyError:
                print('cannot insert competition. DB insert error.')
                db.session.rollback()
                return None

        return self.comp_id

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

    def update_comp_info(self):
        from datetime import datetime as dt
        from db_tables import tblCompetition as C

        with Database() as db:
            q = db.session.query(C).get(self.id)
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
            q.comEntryRestrict = self.restricted
            q.comClass = self.comp_class
            q.comType = self.comp_type
            q.comLocked = self.locked
            q.comStyleSheet = self.stylesheet
            db.session.commit()

    @staticmethod
    def from_json(comp_id, ref_id=None):
        """Reads competition from json result file
        takes comPk as argument"""
        from db_tables import tblResultFile as R
        from participant import Participant
        from formula import Formula
        from sqlalchemy import and_, or_
        from os import path
        import json
        import Defines

        if type(comp_id) is int and comp_id > 0:
            with Database() as db:
                if ref_id:
                    file = db.session.query(R).get(ref_id).refJSON
                else:
                    file = db.session.query(R.refJSON).filter(
                        and_(R.comPk == comp_id, R.tasPk == None, R.refVisible == 1)).scalar()
            if file:
                comp = Comp(comp_id=comp_id)
                with open(path.join(Defines.RESULTDIR, file), 'r') as f:
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
    def create_results(comp_id, status=None):
        """creates the json result file and the database entry"""
        from compUtils import get_tasks_result_files, get_participants
        from result import Comp_result as C, create_json_file
        import json
        import Defines
        from operator import itemgetter

        '''PARAMETER: decimal positions'''
        # TODO implement result decimal positions parameter
        decimals = 0  # should be a formula parameter, or a ForComp parameter?

        comp = Comp.read(comp_id)
        val = comp.formula.overall_validity  # ftv, round, all
        ftv_type = comp.formula.formula_type  # pwc, fai
        param = comp.formula.validity_param  # ftv param, dropped task param

        '''retrieve active task result files and reads info'''
        files = get_tasks_result_files(comp_id)

        '''initialize obj attributes'''
        tasks = []
        participants = get_participants(comp_id)
        stats = {'tot_dist_flown': 0.0, 'tot_flights': 0, 'valid_tasks': len(files),
                 'tot_pilots': len(participants)}
        rankings = {}

        for idx, t in enumerate(files):
            with open(Defines.RESULTDIR + t.file, 'r') as f:
                '''read task json file'''
                data = json.load(f)

                '''create task code'''
                code = ('T' + str(idx + 1))

                '''get task info'''
                task = {'code': code, 'id': t.task_id, 'status': data['file_stats']['status']}
                i = dict(data['info'], **data['stats'])
                task.update({x: i[x] for x in C.tasks_list})
                if val == 'ftv':
                    task['ftv_validity'] = (round(task['max_score'], decimals) if ftv_type == 'pwc'
                                            else round(task['day_quality'] * 1000, decimals))
                    # avail_validity       += task['ftv_validity']
                tasks.append(task)

                '''add task stats to overall'''
                stats['tot_dist_flown'] += float(i['tot_dist_flown'])
                stats['tot_flights'] += int(i['pilots_launched'])

                ''' get rankings (just once)'''
                if not rankings: rankings.update(data['rankings'])

                '''get pilots result'''
                task_results = {}
                for res in data['results']:
                    task_results.setdefault(res['par_id'], {}).update({code: res['score']})
                for p in participants:
                    s = 0 if not task_results.get(p.par_id, {}) else round(task_results.get(p.par_id, {})[code],
                                                                           decimals)
                    # s = round(task_results.get(p.par_id, {})[code], d)
                    r = task['ftv_validity'] if val == 'ftv' else 1000
                    if r > 0:  # sanity
                        perf = round(s / r, decimals + 3)
                        p.results.update({code: {'pre': s, 'perf': perf, 'score': s}})
                    else:
                        p.results.update({code: {'pre': s, 'perf': 0, 'score': 0}})

        '''calculate final score'''
        results = get_final_scores(participants, tasks, comp.formula, decimals)
        stats['winner_score'] = max([t.score for t in results])

        comp.tasks = tasks
        comp.stats = stats
        comp.rankings = rankings
        comp.participants = sorted(results, key=lambda k: k.score, reverse=True)

        '''create json file'''
        result = {'info': {x: getattr(comp, x) for x in C.info_list},
                  'rankings': comp.rankings,
                  'tasks': [t for t in comp.tasks],
                  'results': [{x: getattr(res, x) for x in C.result_list} for res in comp.participants],
                  'formula': {x: getattr(comp.formula, x) for x in C.formula_list},
                  'stats': comp.stats
                  }
        ref_id = create_json_file(comp_id=comp.id, task_id=None, code=comp.comp_code, elements=result, status=status)
        return ref_id


def get_final_scores(results, tasks, formula, d=0):
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
    from operator import itemgetter

    val = formula.overall_validity
    param = formula.validity_param
    avail_validity = 0

    if val == 'ftv':
        avail_validity = sum(t['ftv_validity'] for t in tasks) * param
    elif val == 'round':
        dropped = int(len(tasks) / param)

    for pil in results:
        pil.score = 0

        ''' if we score all tasks, or tasks are not enough to ha discards,
            or event has just one valid task regardless method,
            we can simply sum all score values
        '''
        if not ((val == 'all')
                or (val == 'round' and dropped == 0)
                or (len(tasks) < 2)):
            '''create a ordered list of results, perf desc'''
            sorted_results = sorted(pil.results.items(), key=lambda x: (x[1]['perf'], x[1]['pre']), reverse=True)

            if val == 'round' and len(tasks) >= param:
                '''we need to order by score desc and sum only the ones we need'''
                for i in range(dropped):
                    id = sorted_results.pop()[0]  # getting id of worst result task
                    pil.results[id]['score'] = 0

            elif val == 'ftv' and len(tasks) > 1:
                '''ftv calculation'''
                pval = avail_validity
                for id, s in sorted_results:
                    if not (pval > 0):
                        pil.results[id]['score'] = 0
                    else:
                        '''get ftv_validity of corresponding task'''
                        tval = [t['ftv_validity'] for t in tasks if t['code'] == id].pop()
                        if pval > tval:
                            '''we can use the whole score'''
                            pval -= tval
                        else:
                            '''we need to calculate proportion'''
                            pil.results[id]['score'] = round(pil.results[id]['score'] * (pval / tval), d)
                            pval = 0

        '''calculates final pilot score'''
        pil.score = sum(pil.results[x]['score'] for x in pil.results)

    return results
