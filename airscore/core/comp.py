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
from os import path

from sqlalchemy import and_
from Defines import TRACKDIR, RESULTDIR, SELF_REG_DEFAULT, PILOT_DB
from calcUtils import get_date, c_round
from compUtils import get_tasks_result_files, get_participants, read_rankings, create_classifications, create_comp_path
from db.tables import TblCompetition
from formula import Formula
from pilot.participant import Participant
from result import CompResult, create_json_file
from task import Task


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
                 comp_class=None, region=None, comp_type='RACE', restricted=True, locked=False, external=False,
                 check_launch='off'):

        self.comp_id = comp_id  # com_id
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
        self.cat_id = None  # cat_id
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
        self.igc_config_file = None  # config yaml for igc_lib. This setting will be passed on to new tasks
        self.airspace_check = False  # BOOL airspace check. This setting will be passed on to new tasks
        self.check_launch = check_launch  # check launch flag. whether we check that pilots leave from launch. This setting will be passed on to new tasks
        self.self_register = PILOT_DB and SELF_REG_DEFAULT  # set to true if we have pilot DB on and self reg on by default
        self.check_g_record = False

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
        return path.join(TRACKDIR, self.comp_path)

    @property
    def total_validity(self):
        if len(self.tasks) > 0:
            return c_round(sum([t.ftv_validity for t in self.tasks]), 4)
        else:
            return 0

    @property
    def avail_validity(self):
        if len(self.tasks) > 0:
            if self.formula.overall_validity == 'ftv':
                return c_round(self.total_validity * self.formula.validity_param, 4)
            else:
                return self.total_validity
        return 0

    @property
    def dropped_tasks(self):
        if len(self.tasks) > 0:
            if self.formula.overall_validity == 'round':
                return int(len(self.tasks) / self.formula.validity_param)
        return 0

    # @property
    # def airspace_check(self):
    #     if self.openair_file:
    #         return True
    #     return False

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
    def read(comp_id: int) -> object or None:
        """Reads competition from database
        takes com_id as argument"""
        from db.tables import CompObjectView as C
        if not (type(comp_id) is int and comp_id > 0):
            print(f"comp_id needs to be int > 0, {comp_id} was given")
            return None
        try:
            # get comp details.
            q = C.get_by_id(comp_id)
            comp = q.populate(Comp())
            comp.formula = q.populate(Formula())
            return comp
        except AttributeError:
            print(f'Error: no comp found with ID {comp_id}.')
            return None

    def create_path(self):
        """create filepath from # and date if not given
            and store it in database"""
        from compUtils import create_comp_code

        if self.comp_path:
            print(f"Error: Comp has already a valid path: {self.comp_path}")
            return None
        if not self.date_from:
            print(f"Error: Comp has no Date")
            return None
        if not self.comp_code:
            self.comp_code = create_comp_code(self.comp_name, self.date_from)
        self.comp_path = create_comp_path(self.date_from, self.comp_code)

        if self.comp_id:
            '''store to database'''
            q = TblCompetition.query.get(self.id)
            q.update(comp_path=self.comp_path)

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

        row = TblCompetition() if not self.comp_id else TblCompetition.get_by_id(self.comp_id)
        row.from_obj(self)
        row.save_or_update()
        self.comp_id = row.comp_id
        return self.comp_id

    def get_rankings(self):
        self.rankings = create_classifications(self.cat_id)

    @staticmethod
    def from_fsdb(fs_comp, short_name=None):
        """gets comp and formula info from FSDB file"""
        from calcUtils import get_date
        from pathlib import Path
        from glob import glob
        from compUtils import create_comp_code, is_shortcode_unique

        comp = Comp()

        comp.comp_name = fs_comp.get('name')
        comp.comp_class = (fs_comp.get('discipline')).upper()
        comp.comp_site = fs_comp.get('location')
        comp.date_from = get_date(fs_comp.get('from'))
        comp.date_to = get_date(fs_comp.get('to'))
        comp.time_offset = int(float(fs_comp.get('utc_offset')) * 3600)
        comp.sanction = ('FAI 1' if fs_comp.get('fai_sanctioning') == '1'
                         else 'FAI 2' if fs_comp.get('fai_sanctioning') == '2' else 'none')
        comp.external = True
        comp.locked = True

        '''check if we have comp_code'''
        if short_name and is_shortcode_unique(short_name, comp.date_from):
            comp.comp_code = short_name
        else:
            comp.comp_code = create_comp_code(comp.comp_name, comp.date_from)
        comp.create_path()

        '''check path does not already exist'''
        if Path(comp.file_path).exists():
            '''create a new comp_code and comp_path'''
            index = len(glob(comp.file_path + '*/')) + 1
            comp.comp_code = '_'.join([comp.comp_code, str(index)])
            print(f"Comp short name already exists: changing to {comp.comp_code}")
            comp.comp_path = create_comp_path(comp.date_from, comp.comp_code)
        return comp

    def get_tasks_details(self):
        """gets tasks details from database. They could be different from JSON data for scored tasks"""
        from db.tables import TaskObjectView as T

        results = T.query.with_entities(T.task_id, T.reg_id, T.region_name, T.task_num, T.task_name, T.date, T.opt_dist,
                                        T.comment, T.window_open_time, T.task_deadline, T.window_close_time,
                                        T.start_time, T.start_close_time, T.track_source) \
            .filter_by(comp_id=self.comp_id).all()
        if results:
            results = [row._asdict() for row in results]
        return results

    @staticmethod
    def from_json(comp_id: int, ref_id=None):
        """Reads competition from json result file
        takes com_id as argument"""
        from db.tables import TblResultFile as R
        if ref_id:
            file = R.query.get(ref_id).filename
        else:
            file = R.query.with_entities(R.filename).filter(and_(R.comp_id == comp_id,
                                                                 R.task_id.is_(None), R.active == 1)).scalar()
        if file:
            comp = Comp(comp_id=comp_id)
            with open(path.join(RESULTDIR, file), 'r') as f:
                '''read task json file'''
                data = json.load(f)
                for k, v in data['info'].items():
                    # not using update to intercept changing in formats
                    if hasattr(comp, k):
                        setattr(comp, k, v)
                # comp.as_dict().update(data['info'])
                comp.stats = dict(**data['stats'])
                comp.rankings.update(data['rankings'])
                comp.tasks.extend(data['tasks'])
                comp.formula = Formula.from_dict(data['formula'])
                comp.data = dict(**data['file_stats'])
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
    def create_results(comp_id, status=None, decimals=None, name_suffix=None):
        """creates the json result file and the database entry
            :param
        name_suffix: optional name suffix to be used in filename.
        This is so we can overwrite comp results that are only used in front end to create competition
         page not display results """
        from calcUtils import c_round
        comp = Comp.read(comp_id)
        '''PARAMETER: decimal positions'''
        if decimals is None or not isinstance(decimals, int):
            decimals = comp.formula.comp_result_decimal
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
                s = next((c_round(pil.score or 0, decimals) for pil in task.pilots if pil.par_id == p.par_id), 0)
                if r > 0:  # sanity
                    perf = c_round(s / r, decimals + 3)
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
            r = {x: getattr(p, x) for x in CompResult.result_list if x in dir(p)}
            r['score'] = res['score']
            r['results'] = {x: res[x] for x in res.keys() if isinstance(res[x], dict)}
            results.append(r)
        '''create json file'''
        result = {'info': {x: getattr(comp, x) for x in CompResult.info_list},
                  'rankings': comp.rankings,
                  'tasks': [{x: getattr(t, x) for x in CompResult.task_list} for t in comp.tasks],
                  'results': results,
                  'formula': {x: getattr(comp.formula, x) for x in CompResult.formula_list},
                  'stats': {x: getattr(comp, x) for x in CompResult.stats_list}
                  }
        ref_id, filename, timestamp = create_json_file(comp_id=comp.id, task_id=None, code=comp.comp_code,
                                                       elements=result, status=status, name_suffix=name_suffix)
        return comp, ref_id, filename, timestamp

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
        from calcUtils import c_round

        val = self.formula.overall_validity
        param = self.formula.validity_param
        avail_validity = self.avail_validity

        for pil in self.results:
            pil['score'] = 0

            ''' if we score all tasks, or tasks are not enough to have discards,
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
                                pil[idx]['score'] = c_round(pil[idx]['score'] * (pval / tval), d)
                                pval = 0

            '''calculates final pilot score'''
            pil['score'] = sum(pil[x]['score'] for x in pil.keys() if isinstance(pil[x], dict))

        ''' order list'''
        self.results = sorted(self.results, key=lambda x: x['score'], reverse=True)


def delete_comp(comp_id, files=True):
    """delete all database entries and files on disk related to comp"""
    from db.tables import TblTask as T
    from db.tables import TblForComp as FC
    from db.tables import TblResultFile as RF
    from db.tables import TblParticipant as P
    from task import delete_task
    from result import delete_result

    tasks = T.query.with_entities(T.task_id).filter_by(comp_id=comp_id).all()
    if tasks:
        '''delete tasks'''
        for task in tasks:
            delete_task(task.task_id, files=files)
        results = RF.query.with_entities(RF.ref_id).filter_by(comp_id=comp_id).all()
        if results:
            '''delete result json files'''
            for res in results:
                delete_result(res.ref_id, files)
        '''delete db entries: formula, participants, comp'''
        P.delete_all(comp_id=comp_id)
        FC.delete_all(comp_id=comp_id)
        TblCompetition.get_by_id(comp_id).delete()
