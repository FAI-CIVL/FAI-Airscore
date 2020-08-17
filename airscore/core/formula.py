"""
Module for operations on formula
Use:    import formula
        parameters = Formula.read(task_id)

Antonio Golfari - 2019
"""

import importlib
from dataclasses import dataclass, fields
from os import listdir
from sqlalchemy.orm import aliased
from db.conn import db_session
from calcUtils import c_round


def list_formulas():
    """Lists all formulas present in the formulas folder.
    :returns a dictionary with 3 lists.
        all: a list of all formulas
        pg: a list of all formulas that are of class pg or both
        hg: a list of all formulas that are of class hg or both"""
    all_formulas = []
    hg_formulas = []
    pg_formulas = []
    for file in listdir('formulas'):
        if file[-3:] == '.py':
            formula_lib = get_formula_lib_by_name(file[:-3])
            all_formulas.append(formula_lib.formula_name)
            if formula_lib.formula_class == 'PG' or formula_lib.formula_class == 'BOTH':
                pg_formulas.append(formula_lib.formula_name)
            if formula_lib.formula_class == 'HG' or formula_lib.formula_class == 'BOTH':
                hg_formulas.append(formula_lib.formula_name)
    all_formulas = sorted(all_formulas)
    hg_formulas = sorted(hg_formulas)
    pg_formulas = sorted(pg_formulas)
    return {'ALL': all_formulas, 'PG': pg_formulas, 'HG': hg_formulas}


def get_formula_lib_by_name(formula_name):
    """get formula library to use in scoring"""
    # formula = read_formula(comp_id)
    formula_file = 'formulas.' + formula_name
    try:
        lib = importlib.import_module(formula_file, package=None)
        return lib
    except:
        print(f'formula file {formula_file} not found.')
        exit()


def get_formula_lib(formula_type, formula_version):
    """get formula library to use in scoring"""
    # formula = read_formula(comp_id)
    formula_file = 'formulas.' + formula_type + str(formula_version)
    try:
        lib = importlib.import_module(formula_file, package=None)
        return lib
    except:
        print(f'formula file {formula_file} not found.')
        exit()


@dataclass(frozen=True)
class Preset:
    value: any
    visible: bool = True
    editable: bool = False
    calculated: bool = False
    comment: str = ''


@dataclass(frozen=True)
class FormulaPreset:
    formula_name: Preset
    formula_type: Preset
    formula_version: Preset
    formula_distance: Preset
    formula_arrival: Preset
    formula_departure: Preset
    lead_factor: Preset
    # lead_squared_distance: Preset
    formula_time: Preset
    arr_alt_bonus: Preset
    arr_min_height: Preset
    arr_max_height: Preset
    validity_min_time: Preset
    max_JTG: Preset
    JTG_penalty_per_sec: Preset
    overall_validity: Preset
    validity_param: Preset
    validity_ref: Preset
    score_back_time: Preset
    no_goal_penalty: Preset
    glide_bonus: Preset
    tolerance: Preset
    min_tolerance: Preset
    scoring_altitude: Preset
    task_result_decimal: Preset
    comp_result_decimal: Preset

    def as_formula(self):
        """ gets presets' value"""
        return {x.name: getattr(self, x.name).value for x in fields(self)}


class Formula(object):
    """
    Create an object Formula
    """

    def __init__(self, comp_id=None, formula_name=None, formula_type=None, formula_version=None, comp_class=None,
                 formula_distance=None, formula_arrival=None, formula_departure=None, lead_factor=None,
                 formula_time=None, no_goal_penalty=None, glide_bonus=None, tolerance=0.001, min_tolerance=5,
                 arr_alt_bonus=None, arr_min_height=None, arr_max_height=None, validity_min_time=None, max_JTG=0,
                 JTG_penalty_per_sec=None, nominal_goal=None, nominal_dist=None, nominal_time=None, nominal_launch=None,
                 scoring_altitude=None, min_dist=None, score_back_time=None, overall_validity='all', validity_param=1,
                 validity_ref='day_quality', task_result_decimal=0, comp_result_decimal=0):

        self.comp_id = comp_id
        self.formula_name = formula_name
        self.formula_type = formula_type
        self.formula_version = formula_version
        self.comp_class = comp_class  # 'HG', 'PG'
        self.formula_distance = formula_distance  # 'on', 'difficulty', 'off'
        self.formula_arrival = formula_arrival  # 'position', 'time', 'off'
        self.formula_departure = formula_departure  # 'on', 'leadout', 'off'
        self.lead_factor = lead_factor  # float
        self.formula_time = formula_time  # 'on', 'off'
        self.arr_alt_bonus = arr_alt_bonus  # float
        self.arr_min_height = arr_min_height  # int
        self.arr_max_height = arr_max_height  # int
        self.validity_min_time = validity_min_time  # seconds
        self.score_back_time = score_back_time  # seconds
        self.max_JTG = max_JTG
        self.JTG_penalty_per_sec = JTG_penalty_per_sec
        self.overall_validity = overall_validity  # all, round, ftv
        self.validity_param = validity_param  #
        self.validity_ref = validity_ref  # day_quality, max_score
        self.nominal_goal = nominal_goal  # percentage / 100
        self.nominal_dist = nominal_dist  # meters
        self.nominal_time = nominal_time  # seconds
        self.nominal_launch = nominal_launch  # percentage / 100
        self.min_dist = min_dist  # meters
        self.no_goal_penalty = no_goal_penalty
        self.glide_bonus = glide_bonus
        self.tolerance = tolerance  # percentage / 100
        self.min_tolerance = min_tolerance  # meters
        self.scoring_altitude = scoring_altitude  # 'GPS', 'QNH'
        self.task_result_decimal = task_result_decimal  # score decimals displayed in task result
        self.comp_result_decimal = comp_result_decimal  # score decimals displayed in comp result
        self.team_scoring = False
        self.team_size = 0
        self.max_team_size = 0
        self.country_scoring = False
        self.country_size = 0
        self.max_country_size = 0
        self.team_over = None

    def __eq__(self, other):
        if not isinstance(other, Formula):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.formula_name == other.formula_name \
               and self.formula_distance == other.formula_distance \
               and self.formula_arrival == other.formula_arrival \
               and self.formula_departure == other.formula_departure \
               and self.lead_factor == other.lead_factor \
               and self.formula_time == other.formula_time \
               and self.arr_alt_bonus == other.arr_alt_bonus \
               and self.arr_min_height == other.arr_min_height \
               and self.arr_max_height == other.arr_max_height \
               and self.validity_min_time == other.validity_min_time \
               and self.max_JTG == other.max_JTG \
               and self.JTG_penalty_per_sec == other.JTG_penalty_per_sec \
               and self.overall_validity == other.overall_validity \
               and self.validity_param == other.validity_param \
               and self.score_back_time == other.score_back_time \
               and self.no_goal_penalty == other.no_goal_penalty \
               and self.glide_bonus == other.glide_bonus \
               and self.tolerance == other.tolerance \
               and self.min_tolerance == other.min_tolerance \
               and self.scoring_altitude == other.scoring_altitude

    @property
    def type(self):
        return self.formula_type

    @property
    def version(self):
        return self.formula_version

    @property
    def name(self):
        return self.formula_name

    @property
    def distance(self):
        return self.formula_distance

    @property
    def departure(self):
        return self.formula_departure

    @property
    def arrival(self):
        return self.formula_arrival

    @property
    def time(self):
        return self.formula_time

    @property
    def height_bonus(self):
        return self.arr_alt_bonus

    def __str__(self):
        out = ''
        out += 'Formula name:   {} \n'.format(self.formula_name)
        out += 'Arrival:        {}  |  '.format(self.arrival)
        out += 'Departure:      {} \n'.format(self.departure)
        out += 'No goal Penalty:{}% \n'.format(self.no_goal_penalty * 100)
        out += 'Glide Bonus:    1:{} \n'.format(self.glide_bonus)
        out += 'Tolerance:      {}% \n'.format(self.tolerance)
        out += 'Nom. Goal:      {}  |  '.format(self.nominal_goal)
        out += 'Nom. Distance:  {} \n'.format(self.nominal_dist)
        out += 'Nom. Time:      {}  |  '.format(self.nominal_time)
        out += 'Nom. Launch:    {} \n'.format(self.nominal_launch)
        out += 'Min. Dist:      {} \n'.format(self.min_dist)
        out += 'Score back time:{} \n'.format(self.score_back_time)
        return out

    def as_dict(self):
        return self.__dict__

    @staticmethod
    def read(comp_id):
        """reads comp formula from database"""
        from db.tables import TblForComp as F

        formula = Formula(comp_id=comp_id)
        with db_session() as db:
            q = db.query(F).get(comp_id)
            if q is not None:
                q.populate(formula)
        return formula

    @staticmethod
    def from_preset(comp_class, formula_name):
        """ Create Formula obj. from preset values in formula script"""
        preset = None
        lib_name = 'formulas.' + formula_name.lower()
        lib = importlib.import_module(lib_name)
        if comp_class in ('PG', 'mixed'):
            preset = lib.pg_preset
        elif comp_class == 'HG':
            preset = lib.hg_preset
        return Formula(**preset.as_formula())

    @staticmethod
    def from_fsdb(fs_info):
        """Get formula info from FSDB file
            type can be 'comp' or 'task'
        """
        formula = get_fsdb_info(Formula(), fs_info.find('FsScoreFormula'))
        formula.validity_param = 1.0 - float(fs_info.get('ftv_factor'))
        if formula.validity_param < 1:
            formula.overall_validity = 'ftv'
        else:
            formula.overall_validity = 'all'
        return formula

    @staticmethod
    def from_dict(d):
        formula = Formula()
        for key, value in d.items():
            if hasattr(formula, key):
                setattr(formula, key, value)
        return formula

    def to_db(self):
        """stores formula to TblForComp table in AirScore database"""
        from db.tables import TblForComp as FC

        with db_session() as db:
            '''check if we have already a row for the comp'''
            row = db.query(FC).get(self.comp_id)
            if row is None:
                row = FC(comp_id=self.comp_id)
                db.add(row)
                db.flush()
            for k, v in self.as_dict().items():
                if hasattr(row, k):
                    setattr(row, k, v)
            db.flush()
        return self.comp_id

    def get_lib(self):
        """get formula library to use in scoring"""
        # print(f'{self.formula_type}, {self.formula_version}, {self.formula_name}')
        if self.formula_type and self.formula_version:
            formula_type = self.formula_type
            version = str(self.formula_version)
            formula_file = 'formulas.' + formula_type + version
        elif self.formula_name:
            formula_file = 'formulas.' + str(self.formula_name).lower()
        else:
            return None
        try:
            lib = importlib.import_module(formula_file, package=None)
            return lib
        except:
            print('formula file {} not found.'.format(formula_file))
            exit()


class TaskFormula(Formula):
    """
    Creates an Object with all task parameters
    """

    task_overrides = ['formula_distance',
                      'formula_arrival',
                      'formula_departure',
                      'formula_time',
                      'arr_alt_bonus',
                      'max_JTG',
                      'no_goal_penalty',
                      'tolerance']

    def __init__(self, task_id=None):
        self.task_id = task_id
        super().__init__()

    @staticmethod
    def from_dict(d):
        formula = TaskFormula()
        formula.as_dict().update({x: d[x] for x in d if hasattr(formula, x)})
        return formula

    @staticmethod
    def from_comp(comp_id):
        """reads comp formula from database"""
        from db.tables import TblForComp as F

        formula = TaskFormula()
        with db_session() as db:
            q = db.query(F).get(comp_id)
            if q is not None:
                q.populate(formula)
        return formula

    @staticmethod
    def from_fsdb(fs_info):
        """Get formula info from FSDB file
            type can be 'comp' or 'task'
        """
        return get_fsdb_info(TaskFormula(), fs_info.find('FsScoreFormula'))

    @staticmethod
    def read(task_id: int):
        """reads comp formula from database"""
        from db.tables import TaskFormulaView as F
        with db_session() as db:
            q = db.query(F).get(task_id)
            if q is not None:
                return q.populate(TaskFormula())

    def to_db(self):
        """stores TaskFormula parameters to TblTask table in AirScore database"""
        from db.tables import TblTask
        with db_session() as db:
            '''check if we have already a row for the task'''
            row = db.query(TblTask).get(self.task_id)
            for k in TaskFormula.task_overrides:
                setattr(row, k, getattr(self, k))
            db.flush()
        return True

    def reset(self):
        """brings back to comp formula"""
        from db.tables import TblTask, TblForComp
        t = aliased(TblTask)
        f = aliased(TblForComp)

        with db_session() as db:
            '''check if we have already a row for the comp'''
            comp_formula = db.query(f).get(self.comp_id)
            task = db.query(t).get(self.task_id)
            for k in TaskFormula.task_overrides:
                setattr(self, k, getattr(comp_formula, k))
                setattr(task, k, getattr(comp_formula, k))
            db.flush()
        return True


def get_fsdb_info(formula, form):
    formula.formula_name = form.get('id')
    '''scoring parameters'''
    # formula.comp_class = comp.comp_class
    formula.min_dist = 0 + float(form.get('min_dist')) * 1000  # min. distance, meters
    formula.nominal_dist = 0 + float(form.get('nom_dist')) * 1000  # nom. distance, meters
    formula.nominal_time = 0 + int(float(form.get('nom_time')) * 3600)  # nom. time, seconds
    formula.nominal_launch = 0 + float(form.get('nom_launch'))  # nom. launch, perc / 100
    formula.nominal_goal = 0 + float(form.get('nom_goal'))  # nom. goal, perc / 100
    formula.scoring_altitude = 'GPS' if form.get('scoring_altitude') == 'GPS' else 'QNH'
    # print(f"min. dist.: {float(form.get('min_dist'))} - {formula.min_dist}")
    # print(f"nom. dist.: {float(form.get('nom_dist'))} - {formula.nominal_dist}")
    # print(f"Altitude.: {formula.scoring_altitude}")
    '''formula parameters'''
    # distance point: on, difficulty, off
    formula.formula_distance = ('difficulty' if form.get('use_difficulty_for_distance_points') == '1'
                                else 'on' if form.get('use_distance_points') == '1' else 'off')
    # arrival points: position, time, off
    formula.formula_arrival = ('position' if form.get('use_arrival_position_points') == '1'
                               else 'time' if form.get('use_arrival_time_points') == '1' else 'off')
    # departure points: leadout, on, off
    formula.formula_departure = ('leadout' if form.get('use_leading_points') == '1'
                                 else 'on' if form.get('use_departure_points') == '1' else 'off')
    # time points: on, off
    formula.formula_time = 'on' if form.get('use_time_points') == '1' else 'off'
    # leading points factor: probably needs to be linked to GAP version
    formula.lead_factor = (None if form.get('use_leading_points') == '0'
                           else float(form.get('leading_weight_factor')
                                      if form.get('leading_weight_factor') else 1))
    '''tolerance'''
    formula.tolerance = 0.0 + float(form.get('turnpoint_radius_tolerance')
                                    if form.get('turnpoint_radius_tolerance') else 0.001)  # tolerance, perc / 100
    '''stopped task parameters'''
    formula.validity_min_time = 0 + int(
        form.get('min_time_span_for_valid_task')) * 60  # min. time for valid task, seconds
    formula.score_back_time = 0 + int(form.get('score_back_time')) * 60  # Scoreback Time, seconds
    formula.glide_bonus = 0.0 + float(form.get('bonus_gr'))  # glide ratio
    '''bonus and penalties'''
    formula.no_goal_penalty = c_round(1.0 - float(form.get('time_points_if_not_in_goal')), 4)
    formula.arr_alt_bonus = float(form.get('aatb_factor') if form.get('final_glide_decelerator') == 'aatb' else 0)
    '''jump the gun'''
    formula.max_JTG = int(form.get('jump_the_gun_max'))  # seconds
    formula.JTG_penalty_per_sec = (None if form.get('jump_the_gun_factor') == '0'
                                   else c_round(1 / float(form.get('jump_the_gun_factor')), 4))
    return formula
