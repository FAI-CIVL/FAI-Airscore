"""
Module for operations on formula
Use:    import formula
        parameters = Formula.read(tasPk)

Antonio Golfari - 2019
"""

import importlib
from dataclasses import dataclass, fields
from os import listdir

from sqlalchemy.exc import SQLAlchemyError

from myconn import Database


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
    score_back_time: Preset
    no_goal_penalty: Preset
    glide_bonus: Preset
    tolerance: Preset
    min_tolerance: Preset
    scoring_altitude: Preset

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
                 scoring_altitude=None, min_dist=None, score_back_time=None, overall_validity='all', validity_param=1):

        self.forPk = None
        self.comp_id = comp_id
        self.formula_name = formula_name
        self.formula_type = formula_type
        self.formula_version = formula_version
        self.comp_class = comp_class  # 'HG', 'PG'
        self.formula_distance = formula_distance  # 'on', 'difficulty', 'off'
        self.formula_arrival = formula_arrival  # 'position', 'time', 'off'
        self.formula_departure = formula_departure  # 'on', 'leadout', 'off'
        self.lead_factor = lead_factor  # float
        # self.lead_squared_distance
        self.formula_time = formula_time  # 'on', 'off'
        self.arr_alt_bonus = arr_alt_bonus  # float
        self.arr_min_height = arr_min_height  # int
        self.arr_max_height = arr_max_height  # int
        self.validity_min_time = validity_min_time  # seconds
        self.score_back_time = score_back_time  # seconds
        self.max_JTG = max_JTG
        self.JTG_penalty_per_sec = JTG_penalty_per_sec
        self.overall_validity = overall_validity
        self.validity_param = validity_param
        self.nominal_goal = nominal_goal  # percentage / 100
        self.nominal_dist = nominal_dist  # meters
        self.nominal_time = nominal_time  # seconds
        self.nominal_launch = nominal_launch  # percentage / 100
        self.min_dist = min_dist  # meters
        self.score_back_time = score_back_time  # seconds
        self.no_goal_penalty = no_goal_penalty
        self.glide_bonus = glide_bonus
        self.tolerance = tolerance  # percentage / 100
        self.min_tolerance = min_tolerance  # meters
        self.scoring_altitude = scoring_altitude  # 'GPS', 'QNH'
        self.start_weight = None
        self.arrival_weight = None
        self.speed_weight = None
        self.TeamScoring = False
        self.TeamSize = None
        self.TeamOver = None
        self.CountryScoring = False

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

    def as_dict(self):
        return self.__dict__

    @staticmethod
    def read(comp_id, session=None):
        """reads comp formula from database"""
        from db_tables import CompFormulaView as F

        formula = Formula(comp_id)
        with Database(session) as db:
            try:
                q = db.session.query(F).get(comp_id)
                if q is not None:
                    db.populate_obj(formula, q)
            except SQLAlchemyError:
                print(f'Read formula from db Error: {SQLAlchemyError.code}')
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
    def from_fsdb(fs_info, type='comp'):
        """Get formula info from FSDB file
            type can be 'comp' or 'task'
        """

        formula = Formula()

        if type == 'comp':
            formula.validity_param = 1.0 - float(fs_info.get('ftv_factor'))
            if formula.validity_param < 1:
                formula.overall_validity = 'ftv'
            else:
                formula.overall_validity = 'all'
            form = fs_info.find('FsScoreFormula')
        else:
            form = fs_info

        formula.formula_name = form.get('id')

        '''scoring parameters'''
        # formula.comp_class = comp.comp_class
        formula.min_dist = 0 + float(form.get('min_dist')) * 1000  # min. distance, meters
        formula.nominal_dist = 0 + float(form.get('nom_dist')) * 1000  # nom. distance, meters
        formula.nominal_time = 0 + int(float(form.get('nom_time')) * 3600)  # nom. time, seconds
        formula.nominal_launch = 0 + float(form.get('nom_launch'))  # nom. launch, perc / 100
        formula.nominal_goal = 0 + float(form.get('nom_goal'))  # nom. goal, perc / 100
        formula.scoring_altitude = 'GPS' if form.get('scoring_altitude') == 'GPS' else 'QNH'

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
        formula.no_goal_penalty = round(1.0 - float(form.get('time_points_if_not_in_goal')), 4)
        formula.arr_alt_bonus = float(form.get('aatb_factor') if form.get('final_glide_decelerator') == 'aatb' else 0)

        '''jump the gun'''
        formula.max_JTG = int(form.get('jump_the_gun_max'))  # seconds
        formula.JTG_penalty_per_sec = (None if form.get('jump_the_gun_factor') == '0'
                                       else round(1 / float(form.get('jump_the_gun_factor')), 4))

        return formula

    @staticmethod
    def from_dict(d):
        formula = Formula()
        for key, value in d.items():
            if hasattr(formula, key):
                setattr(formula, key, value)
        return formula

    def to_db(self):
        """stores formula to tblForComp table in AirScore database"""
        from db_tables import tblForComp as FC

        with Database() as db:
            try:
                '''check if we have already a row for the comp'''
                row = db.session.query(FC).get(self.comp_id)
                if row is None:
                    row = FC(comPk=self.comp_id)
                    db.session.add(row)
                    db.session.flush()

                row.forClass = self.formula_type
                row.forVersion = self.formula_version
                row.forName = self.formula_name
                row.comOverallScore = self.overall_validity
                row.comOverallParam = self.validity_param
                row.forNomGoal = self.nominal_goal
                row.forMinDistance = int(self.min_dist / 1000) if self.min_dist else 0
                row.forNomDistance = int(self.nominal_dist / 1000) if self.nominal_dist else 0
                row.forNomTime = int(self.nominal_time / 60) if self.nominal_time else 0
                row.forNomLaunch = self.nominal_launch
                row.forDistance = self.formula_distance
                row.forArrival = self.formula_arrival
                row.forDeparture = self.formula_departure
                row.forLeadFactor = self.lead_factor
                row.forTime = self.formula_time
                row.forNoGoalPenalty = self.no_goal_penalty
                row.forGlideBonus = self.glide_bonus
                row.forTolerance = self.tolerance * 100 if self.tolerance else 0
                row.forHeightBonus = self.arr_alt_bonus
                row.forESSHeightLo = self.arr_min_height
                row.forESSHeightUp = self.arr_max_height
                row.forMinTime = int(self.validity_min_time / 60) if self.validity_min_time else 0
                row.forScorebackTime = int(self.score_back_time / 60) if self.score_back_time else 0
                row.forMaxJTG = int(self.max_JTG / 60) if self.max_JTG else 0
                row.forJTGPenPerSec = self.JTG_penalty_per_sec
                row.forAltitudeMode = self.scoring_altitude
                row.comTeamScoring = self.TeamScoring
                row.comTeamOver = self.TeamOver
                row.comTeamSize = self.TeamSize
                row.comCountryScoring = self.CountryScoring

                db.session.flush()

            except SQLAlchemyError:
                print('cannot insert or update formula. DB insert error.')
                db.session.rollback()
                return None

        return self.comp_id


class Task_formula(object):
    """
    Creates an Object with all task parameters
    """

    def __init__(self, formula_name=None, formula_type=None, formula_version=None,
                 formula_distance=None, formula_arrival=None, formula_departure=None, lead_factor=None,
                 formula_time=None, no_goal_penalty=None, glide_bonus=None, tolerance=None, min_tolerance=None,
                 arr_alt_bonus=None, arr_min_height=None, arr_max_height=None, validity_min_time=None, max_JTG=None,
                 JTG_penalty_per_sec=None, nominal_goal=None, nominal_dist=None, nominal_time=None, nominal_launch=None,
                 scoring_altitude=None, min_dist=None, score_back_time=None):
        """
        creates an object with formula parameters
        that will be included in Task_result Object
        """
        self.formula_name = formula_name
        self.formula_type = formula_type
        self.formula_version = formula_version
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
        self.overall_validity = None
        self.validity_param = None
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
    def from_dict(d):
        formula = Task_formula()
        formula.as_dict().update({x: d[x] for x in d if hasattr(formula, x)})
        return formula

    @classmethod
    def read(cls, task_id):
        """reads task formula from DB"""
        from db_tables import TaskFormulaView as F

        formula = cls()
        with Database() as db:
            # get the task details.
            f = db.session.query(F)
            t = f.get(task_id)
            db.populate_obj(formula, t)
        return formula

    def get_lib(self):

        formula_type = self.formula_type
        version = str(self.formula_version)

        '''get formula library to use in scoring'''
        formula_file = 'formulas.' + formula_type + version
        try:
            lib = importlib.import_module(formula_file, package=None)
            return lib
        except:
            print('formula file {} not found.'.format(formula_file))
            exit()
