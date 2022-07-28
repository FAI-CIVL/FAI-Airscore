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
import compUtils
from pathlib import Path

from calcUtils import c_round, get_date
from compUtils import (
    create_comp_path,
    get_participants,
    get_tasks_result_files
)
from db.conn import db_session
from db.tables import TblCompetition
from Defines import PILOT_DB, RESULTDIR, SELF_REG_DEFAULT, TRACKDIR
from formula import Formula
from pilot.participant import Participant
from result import CompResult, create_json_file
from sqlalchemy import and_
from task import Task
from ranking import create_rankings


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

    def __init__(
        self,
        comp_id=None,
        comp_name=None,
        comp_site=None,
        date_from=None,
        comp_code=None,
        date_to=None,
        comp_class=None,
        region=None,
        comp_type='RACE',
        restricted=True,
        locked=False,
        external=False,
        igc_config_file='standard',
        airspace_check=False,
        check_launch='off',
        check_g_record=False,
        track_source=None,
    ):

        self.comp_id = comp_id  # com_id
        self.comp_name = comp_name  # str
        self.comp_site = comp_site  # str
        self.date_from = date_from  # in datetime.date (Y-m-d) format
        self.date_to = date_to  # in datetime.date (Y-m-d) format
        self.comp_class = comp_class  # 'PG', 'HG', 'mixed'
        self.region = region  # Region object
        self.participants = []  # list of Participant obj
        self.tasks = []  # list of Task obj.
        self.rankings = []  # rankings
        self.formula = None  # Formula obj.
        self.MD_name = None  # str
        self.contact = None  # str
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
        self.igc_config_file = igc_config_file  # config yaml for igc_lib. This setting will be passed on to new tasks
        self.airspace_check = airspace_check  # BOOL airspace check. This setting will be passed on to new tasks
        self.check_launch = check_launch  # check launch flag. whether we check that pilots leave from launch. This setting will be passed on to new tasks
        self.self_register = (
            PILOT_DB and SELF_REG_DEFAULT
        )  # set to true if we have pilot DB on and self reg on by default
        self.check_g_record = check_g_record
        self.track_source = track_source  # external tracks source (flymaster, xcontest, ...)

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
        return Path(TRACKDIR, self.comp_path)

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
    def tot_dist_flown(self):
        if len(self.tasks) > 0:
            return sum([t.tot_dist_flown for t in self.tasks])
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
            comp = Comp()
            # get comp details.
            q = C.get_by_id(comp_id)
            q.populate(comp)
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
            with db_session() as db:
                q = db.query(TblCompetition).get(self.id)
                q.comp_path = self.comp_path
                db.commit()

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

        with db_session() as db:
            if self.comp_id is not None:
                row = db.query(TblCompetition).get(self.comp_id)
            else:
                row = TblCompetition()
            for k, v in self.as_dict().items():
                if hasattr(row, k):
                    setattr(row, k, v)
            if not self.comp_id:
                db.add(row)
                db.flush()
                self.comp_id = row.comp_id
            db.commit()
        return self.comp_id

    def get_rankings(self):
        self.rankings = create_rankings(self.comp_id, self.comp_class)

    @staticmethod
    def from_fsdb(fs_comp, short_name: str = None):
        """gets comp and formula info from FSDB file"""
        from calcUtils import get_date
        from compUtils import create_comp_code, is_shortcode_unique

        comp = Comp()

        comp.comp_name = fs_comp.get('name')
        comp.comp_class = (fs_comp.get('discipline')).upper()
        comp.comp_site = fs_comp.get('location')
        comp.date_from = get_date(fs_comp.get('from'))
        comp.date_to = get_date(fs_comp.get('to'))
        comp.time_offset = int(float(fs_comp.get('utc_offset')) * 3600)
        comp.sanction = (
            'FAI 1'
            if fs_comp.get('fai_sanctioning') == '1'
            else 'FAI 2'
            if fs_comp.get('fai_sanctioning') == '2'
            else 'none'
        )
        comp.external = True
        comp.locked = True

        '''check if we have comp_code'''
        if short_name and is_shortcode_unique(short_name, comp.date_from):
            comp.comp_code = short_name
        else:
            comp.comp_code = create_comp_code(comp.comp_name, comp.date_from)
        comp.create_path()

        return comp

    def get_tasks_details(self):
        """gets tasks details from database. They could be different from JSON data for scored tasks"""
        return compUtils.get_tasks_details(self.comp_id)

    @staticmethod
    def from_json(comp_id: int, ref_id=None):
        """Reads competition from json result file
        takes com_id as argument"""
        from db.tables import TblResultFile as R

        with db_session() as db:
            if ref_id:
                file = db.query(R).get(ref_id).filename
            else:
                file = (
                    db.query(R.filename).filter(and_(R.comp_id == comp_id, R.task_id.is_(None), R.active == 1)).scalar()
                )
        if file:
            comp = Comp(comp_id=comp_id)
            with open(Path(RESULTDIR, file), 'r') as f:
                '''read task json file'''
                data = json.load(f)
                for k, v in data['info'].items():
                    # not using update to intercept changing in formats
                    if hasattr(comp, k):
                        setattr(comp, k, v)
                # comp.as_dict().update(data['info'])
                comp.stats = dict(**data['stats'])
                comp.rankings = data['rankings']
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
                if any(el for el in comp.participants if el.live_id):
                    comp.track_source = 'flymaster'
            return comp

    @staticmethod
    def create_results(comp_id, status=None, decimals=None, name_suffix=None):
        """creates the json result file and the database entry
            :param
        name_suffix: optional name suffix to be used in filename.
        This is so we can overwrite comp results that are only used in front end to create competition
         page not display results"""
        from calcUtils import c_round

        comp = Comp.read(comp_id)
        '''PARAMETER: decimal positions'''
        if decimals is None or not isinstance(decimals, int):
            decimals = comp.formula.comp_result_decimal
        td = comp.formula.task_result_decimal
        '''retrieve active task result files and reads info'''
        files = get_tasks_result_files(comp_id)
        '''initialize obj attributes'''
        comp.participants = get_participants(comp_id)
        comp.results.extend(
            [
                dict(results={}, **{x: getattr(p, x) for x in CompResult.result_list if x in dir(p)})
                for p in comp.participants
            ]
        )
        ''' get rankings '''
        comp.get_rankings()
        for idx, t in enumerate(files):
            task = Task.create_from_json(task_id=t.task_id, filename=t.file)
            comp.tasks.append(task)
            if task.training:
                continue
            ''' task validity (if not using ftv, ftv_validity = day_quality)'''
            r = task.ftv_validity * 1000
            '''get pilots result'''
            for p in comp.results:
                s = next((res.score or 0 for res in task.pilots if res.par_id == p['par_id']), 0)
                perf = c_round(s / r, td + 3)
                p['results'][task.task_code] = {'pre': c_round(s, td), 'perf': perf, 'score': c_round(s, td)}

        '''calculate final score'''
        comp.get_final_scores(decimals)
        '''create json file'''
        result = {
            'info': {x: getattr(comp, x) for x in CompResult.info_list},
            'rankings': comp.rankings,
            'tasks': [{x: getattr(t, x) for x in CompResult.task_list} for t in comp.tasks],
            'results': comp.results,
            'formula': {x: getattr(comp.formula, x) for x in CompResult.formula_list},
            'stats': {x: getattr(comp, x) for x in CompResult.stats_list},
        }
        ref_id, filename, timestamp = create_json_file(
            comp_id=comp.id, task_id=None, code=comp.comp_code, elements=result, status=status, name_suffix=name_suffix
        )
        return comp, ref_id, filename, timestamp

    def get_final_scores(self, cd=0):
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
        td = self.formula.task_result_decimal

        for pil in self.results:
            pil['score'] = 0

            ''' if we score all tasks, or tasks are not enough to have discards,
                or event has just one valid task regardless method,
                we can simply sum all score values
            '''
            if not ((val == 'all') or (val == 'round' and self.dropped_tasks == 0) or (len(self.tasks) < 2)):
                '''create a ordered list of results, perf desc'''
                sorted_results = sorted(pil['results'].items(), key=lambda x: (x[1]['perf'], x[1]['pre']), reverse=True)

                if val == 'round' and len(self.tasks) >= param:
                    '''we need to order by score desc and sum only the ones we need'''
                    for i in range(self.dropped_tasks):
                        idx = sorted_results.pop()[0]  # getting id of worst result task
                        pil['results'][idx]['score'] = 0

                elif val == 'ftv' and len(self.tasks) > 1:
                    '''ftv calculation'''
                    pval = avail_validity
                    for idx, s in sorted_results:
                        if not (pval > 0):
                            pil['results'][idx]['score'] = 0
                        else:
                            '''get ftv_validity of corresponding task'''
                            tval = next(t.ftv_validity for t in self.tasks if t.task_code == idx)
                            if pval > tval:
                                '''we can use the whole score'''
                                pval -= tval
                            else:
                                '''we need to calculate proportion'''
                                pil['results'][idx]['score'] = c_round(pil['results'][idx]['score'] * (pval / tval), td)
                                pval = 0

            '''calculates final pilot score'''
            pil['score'] = c_round(sum(pil['results'][x]['score'] for x in pil['results'].keys()), cd)

        ''' order list'''
        self.results = sorted(self.results, key=lambda x: x['score'], reverse=True)

    def create_participants_html(self) -> (str, dict):
        """ create a HTML file from participants list"""
        from time import time

        from calcUtils import epoch_to_string

        title = f"{self.comp_name}"
        filename = f"{self.comp_name.replace(' - ', '_').replace(' ', '_')}_participants.html"
        self.participants = get_participants(self.comp_id)
        participants = sorted(
            self.participants, key=lambda x: x.ID if all(el.ID for el in self.participants) else x.name
        )
        num = len(participants)

        '''HTML headings'''
        headings = [
            f"{self.comp_name} - {self.sanction} Event",
            f"{self.date_from} to {self.date_to}",
            f"{self.comp_site}",
        ]

        '''Participants table'''
        thead = ['Id', 'Name', 'Nat', 'Glider', 'Sponsor']
        keys = ['ID', 'name', 'nat', 'glider', 'sponsor']
        right_align = [0]
        tbody = []
        for p in participants:
            tbody.append([getattr(p, k) or '' for k in keys])
        participants = dict(
            title=f'{num} Participants', css_class='simple', right_align=right_align, thead=thead, tbody=tbody
        )

        dt = int(time())  # timestamp of generation
        timestamp = epoch_to_string(dt, self.time_offset)

        return filename, dict(title=title, headings=headings, tables=[participants], timestamp=timestamp)


def delete_comp(comp_id, files=True):
    """delete all database entries and files on disk related to comp"""
    from shutil import rmtree

    from compUtils import get_comp_path
    from db.tables import TblForComp as FC
    from db.tables import TblParticipant as P
    from db.tables import TblResultFile as RF
    from db.tables import TblTask as T
    from result import delete_result
    from task import delete_task

    comp_path = get_comp_path(comp_id)

    with db_session() as db:
        tasks = db.query(T.task_id).filter_by(comp_id=comp_id).all()
        if tasks:
            '''delete tasks'''
            for task in tasks:
                delete_task(task.task_id, files=files)
        results = db.query(RF.filename).filter_by(comp_id=comp_id).all()
        if results:
            '''delete result json files'''
            for res in results:
                print(f"result: {res.filename}")
                delete_result(res.filename, delete_file=files)
        '''delete db entries: formula, participants, comp'''
        db.query(P).filter_by(comp_id=comp_id).delete(synchronize_session=False)
        db.query(FC).filter_by(comp_id=comp_id).delete(synchronize_session=False)
        db.query(TblCompetition).filter_by(comp_id=comp_id).delete(synchronize_session=False)
        db.commit()
    if files and Path(TRACKDIR, comp_path).is_dir():
        rmtree(Path(TRACKDIR, comp_path), ignore_errors=True)
