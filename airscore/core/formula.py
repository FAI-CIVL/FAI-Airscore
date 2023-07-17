"""
Module for operations on formula
Use:    import formula
        parameters = Formula.read(task_id)

Antonio Golfari - 2019
"""

import importlib
from dataclasses import dataclass, fields, asdict
from os import listdir

from calcUtils import c_round
from db.conn import db_session
from sqlalchemy.orm import aliased


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
            try:
                all_formulas.append(formula_lib.formula_name)
                if formula_lib.formula_class == 'PG' or formula_lib.formula_class == 'BOTH':
                    pg_formulas.append(formula_lib.formula_name)
                if formula_lib.formula_class == 'HG' or formula_lib.formula_class == 'BOTH':
                    hg_formulas.append(formula_lib.formula_name)
            except (AttributeError, Exception):
                pass
    all_formulas = sorted(all_formulas)
    hg_formulas = sorted(hg_formulas)
    pg_formulas = sorted(pg_formulas)
    return {'ALL': all_formulas, 'PG': pg_formulas, 'HG': hg_formulas}


def get_formula_lib_by_name(formula_name: str):
    """get formula library to use in scoring"""
    try:
        formula_file = 'formulas.' + formula_name.lower()
        return importlib.import_module(formula_file, package=None)
    except AttributeError as e:
        print(f'Error: formula name is empty')
    except (ModuleNotFoundError, Exception):
        print(f'Error: formula file {formula_file} not found.')
    return None


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
    formula_distance: Preset
    formula_arrival: Preset
    formula_departure: Preset
    lead_factor: Preset
    lc_formula: Preset
    formula_time: Preset
    ss_dist_calc: Preset
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

    def as_formula(self) -> dict:
        """ gets presets' value"""
        return {x.name: getattr(self, x.name).value for x in fields(self)}

    def has_calculated_values(self) -> bool:
        """ returns True if any value needs to be calculated using lib.calculate_parameters()"""
        return any(v.get('calculated') for k, v in asdict(self).items())


class Formula(object):
    """
    Create an object Formula
    """

    def __init__(
        self,
        comp_id=None,
        formula_name=None,
        comp_class=None,
        formula_distance=None,
        formula_arrival=None,
        formula_departure=None,
        lead_factor=1.0,
        formula_time=None,
        no_goal_penalty=None,
        glide_bonus=None,
        tolerance=0.001,
        min_tolerance=5,
        arr_alt_bonus=None,
        arr_min_height=None,
        arr_max_height=None,
        validity_min_time=None,
        max_JTG=0,
        JTG_penalty_per_sec=None,
        nominal_goal=None,
        nominal_dist=None,
        nominal_time=None,
        nominal_launch=None,
        scoring_altitude=None,
        min_dist=None,
        score_back_time=None,
        overall_validity='all',
        validity_param=1,
        validity_ref='max_score',
        task_result_decimal=0,
        comp_result_decimal=0,
        team_scoring=False,
        team_size=0,
        max_team_size=0,
        country_scoring=False,
        country_size=0,
        max_country_size=0,
        team_over=None,
        **kwargs
    ):

        self.comp_id = comp_id
        self.formula_name = formula_name
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
        self.team_scoring = team_scoring
        self.team_size = team_size
        self.max_team_size = max_team_size
        self.country_scoring = country_scoring
        self.country_size = country_size
        self.max_country_size = max_country_size
        self.team_over = team_over

        for k,v in kwargs.items():
            setattr(self, k, v)

    def __eq__(self, other):
        if not isinstance(other, Formula):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return (
            self.formula_name == other.formula_name
            and self.formula_distance == other.formula_distance
            and self.formula_arrival == other.formula_arrival
            and self.formula_departure == other.formula_departure
            and self.lead_factor == other.lead_factor
            and self.formula_time == other.formula_time
            and self.arr_alt_bonus == other.arr_alt_bonus
            and self.arr_min_height == other.arr_min_height
            and self.arr_max_height == other.arr_max_height
            and self.validity_min_time == other.validity_min_time
            and self.max_JTG == other.max_JTG
            and self.JTG_penalty_per_sec == other.JTG_penalty_per_sec
            and self.overall_validity == other.overall_validity
            and self.validity_param == other.validity_param
            and self.score_back_time == other.score_back_time
            and self.no_goal_penalty == other.no_goal_penalty
            and self.glide_bonus == other.glide_bonus
            and self.tolerance == other.tolerance
            and self.min_tolerance == other.min_tolerance
            and self.scoring_altitude == other.scoring_altitude
        )

    @property
    def formula_type(self):
        import re

        try:
            return re.search(r"[a-zA-Z]*", self.formula_name).group().lower()
        except (TypeError, AttributeError):
            return None

    @property
    def type(self):
        return self.formula_type

    @property
    def formula_version(self):
        import re

        try:
            return int(re.search(r"(\d+)", self.formula_name).group())
        except (TypeError, AttributeError):
            return None

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
        # get further values from preset
        formula.fill_from_preset()
        return formula

    @classmethod
    def from_preset(cls, comp_class: str, formula_name: str):
        """ Create Formula obj. from preset values in formula script"""
        lib = get_formula_lib_by_name(formula_name)
        if lib:
            preset = lib.hg_preset if comp_class == 'HG' else lib.pg_preset
            return cls(**preset.as_formula())

    @classmethod
    def from_fsdb(cls, fs_info, comp_class):
        """Get formula info from FSDB file
        type can be 'comp' or 'task'
        """
        data = fs_info.find('FsScoreFormula')
        formula_name = data.get('id')
        # comp_class = fs_info.get('discipline').upper()
        '''check if formula exists'''
        lib = get_formula_lib_by_name(formula_name)
        if lib:
            '''gets preset values'''
            formula = cls.from_preset(comp_class, formula_name)
        else:
            formula = cls()
        formula = get_fsdb_info(formula, data)
        formula.comp_class = comp_class
        formula.validity_param = 1.0 - float(fs_info.get('ftv_factor') or 0)
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

    def reset(self, comp_class: str, formula_name: str):
        lib = get_formula_lib_by_name(formula_name)
        if lib:
            preset = lib.hg_preset if comp_class == 'HG' else lib.pg_preset
            self.as_dict().update(preset.as_formula())
            self.calculate_parameters(lib)

    def calculate_parameters(self, lib=None):
        if not lib:
            lib = get_formula_lib_by_name(self.formula_name)
        if lib and 'calculate_parameters' in dir(lib):
            lib.calculate_parameters(self.as_dict())

    def fill_from_preset(self):
        preset = self.get_preset()
        if preset:
            for k, v in preset.as_formula().items():
                if v is not None and (not hasattr(self, k) or getattr(self, k) is None):
                    setattr(self, k, v)

    def to_db(self):
        """stores formula to TblForComp table in AirScore database"""
        from db.tables import TblForComp as FC

        row = FC.from_obj(self)
        row.save_or_update()
        return self.comp_id

    def get_lib(self):
        """get formula library to use in scoring"""
        return get_formula_lib_by_name(self.formula_name)

    def get_preset(self):
        """get class formula preset from formula library"""
        lib = get_formula_lib_by_name(self.formula_name)
        if lib:
            return lib.hg_preset if self.comp_class == 'HG' else lib.pg_preset


class TaskFormula(Formula):
    """
    Creates an Object with all task parameters
    """

    task_overrides = [
        'formula_distance',
        'formula_arrival',
        'formula_departure',
        'formula_time',
        'arr_alt_bonus',
        'max_JTG',
        'no_goal_penalty',
        'tolerance',
    ]

    def __init__(self, task_id=None, *args, **kwargs):
        self.task_id = task_id
        super().__init__(*args, **kwargs)

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
                # get further values from preset
                formula.fill_from_preset()
        return formula

    @classmethod
    def from_fsdb(cls, fs_info, f):
        """Get formula info from FSDB file
        type can be 'comp' or 'task'
        """
        return get_fsdb_info(TaskFormula(**f.as_dict()), fs_info.find('FsScoreFormula'))

    @staticmethod
    def read(task_id: int):
        """reads comp formula from database"""
        from db.tables import TaskFormulaView as F

        formula = F.get_by_id(task_id).populate(TaskFormula())
        # get further values from preset
        formula.fill_from_preset()
        return formula

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
        from db.tables import TblForComp, TblTask

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


def get_fsdb_info(formula: Formula or TaskFormula, fsdb_data) -> Formula or TaskFormula:
    """Updates a Formula or TaskFormula object with data from an FSDB file"""
    from calcUtils import get_int

    formula.formula_name = fsdb_data.get('id')
    '''scoring parameters'''
    formula.min_dist = float(fsdb_data.get('min_dist')) * 1000  # min. distance, meters
    formula.nominal_dist = float(fsdb_data.get('nom_dist')) * 1000  # nom. distance, meters
    formula.nominal_time = int(float(fsdb_data.get('nom_time')) * 3600)  # nom. time, seconds
    formula.nominal_launch = float(fsdb_data.get('nom_launch'))  # nom. launch, perc / 100
    formula.nominal_goal = float(fsdb_data.get('nom_goal'))  # nom. goal, perc / 100
    formula.scoring_altitude = 'GPS' if fsdb_data.get('scoring_altitude') == 'GPS' else 'QNH'
    # print(f"min. dist.: {float(fsdb_data.get('min_dist'))} - {formula.min_dist}")
    # print(f"nom. dist.: {float(fsdb_data.get('nom_dist'))} - {formula.nominal_dist}")
    # print(f"Altitude.: {formula.scoring_altitude}")
    '''formula parameters'''
    '''distance point: on, difficulty, off'''
    formula.formula_distance = (
        'difficulty'
        if fsdb_data.get('use_difficulty_for_distance_points') == '1'
        else 'on'
        if fsdb_data.get('use_distance_points') == '1'
        else 'off'
        if fsdb_data.get('use_distance_points') == '0'
        else formula.formula_distance
    )
    '''arrival points: position, time, off'''
    formula.formula_arrival = (
        'position'
        if fsdb_data.get('use_arrival_position_points') == '1'
        else 'time'
        if fsdb_data.get('use_arrival_time_points') == '1'
        else 'off'
        if fsdb_data.get('use_arrival_time_points') == '0' and fsdb_data.get('use_arrival_position_points') == '0'
        else formula.formula_arrival
    )
    # departure points: leadout, on, off
    formula.formula_departure = (
        'leadout'
        if fsdb_data.get('use_leading_points') == '1'
        else 'on'
        if fsdb_data.get('use_departure_points') == '1'
        else 'off'
        if fsdb_data.get('use_departure_points') == '0' and fsdb_data.get('use_leading_points') == '0'
        else formula.formula_departure
    )
    '''time points: on, off'''
    formula.formula_time = ('on' if fsdb_data.get('use_time_points') == '1'
                            else 'off'if fsdb_data.get('use_time_points') == '0'
                            else formula.formula_time)
    '''leading points factor'''
    if fsdb_data.get('leading_weight_factor'):
        formula.lead_factor = float(fsdb_data.get('leading_weight_factor'))
    '''tolerance'''
    if fsdb_data.get('turnpoint_radius_tolerance'):
        formula.tolerance = float(fsdb_data.get('turnpoint_radius_tolerance'))  # tolerance, perc / 100
    if fsdb_data.get('turnpoint_radius_minimum_absolute_tolerance'):
        formula.min_tolerance = get_int(fsdb_data.get('turnpoint_radius_minimum_absolute_tolerance'))  # m
    '''stopped task parameters'''
    if fsdb_data.get('min_time_span_for_valid_task'):
        formula.validity_min_time = (
            get_int(fsdb_data.get('min_time_span_for_valid_task')) * 60
        )  # min. time for valid task, seconds
    if fsdb_data.get('score_back_time'):
        formula.score_back_time = get_int(fsdb_data.get('score_back_time')) * 60  # Scoreback Time, seconds
    if fsdb_data.get('bonus_gr'):
        formula.glide_bonus = float(fsdb_data.get('bonus_gr'))  # glide ratio
    '''bonus and penalties'''
    if fsdb_data.get('time_points_if_not_in_goal'):
        formula.no_goal_penalty = c_round(1.0 - float(fsdb_data.get('time_points_if_not_in_goal')), 4)
    if fsdb_data.get('final_glide_decelerator') == 'aatb':
        formula.arr_alt_bonus = float(fsdb_data.get('aatb_factor'))
    '''jump the gun'''
    if not fsdb_data.get('jump_the_gun_factor') == '0':
        formula.max_JTG = get_int(fsdb_data.get('jump_the_gun_max'))  # seconds
        formula.JTG_penalty_per_sec = c_round(1 / float(fsdb_data.get('jump_the_gun_factor')), 4)
    '''results decimals'''
    if fsdb_data.get('number_of_decimals_task_results'):
        formula.task_result_decimal = get_int(fsdb_data.get('number_of_decimals_task_results'))
        formula.comp_result_decimal = get_int(fsdb_data.get('number_of_decimals_competition_results'))

    return formula
