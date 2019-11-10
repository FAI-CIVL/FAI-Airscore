"""
Module for operations on formula
Use:    import formula
        parameters = Formula.read(tasPk)

Antonio Golfari - 2019
"""

# Use your utility module.
from myconn import Database

def get_formula_lib(type):
    import importlib
    #from trackDB import read_formula

    lib = None

    '''get formula library to use in scoring'''
    #formula = read_formula(comp_id)
    formula_file = 'formulas.' + type
    try:
        lib = importlib.import_module(formula_file, package=None)
        return lib
    except:
        print('formula file {} not found.'.format(formula_file))
        exit()

class Formula:
    """
    Create an object Formula
    """
    def __init__(self, id = None, name = None, comp_class = None):
        self.forPk                  = id
        self.name                   = name
        self.comp_class             = comp_class
        self.arrival                = None
        self.departure              = None
        self.linear_distance        = None
        self.diff_distance          = None
        self.distance_measure       = None
        self.diff_ramp              = None
        self.diff_calc              = None
        self.no_goal_penalty        = None
        self.glide_bonus            = None
        self.tolerance              = None
        self.stopped_time_calc      = None
        self.arrival_altitude_bonus = None
        self.arrival_lower_altitude = None
        self.arrival_upper_altitude = None
        self.start_weight           = None
        self.arrival_weight         = None
        self.speed_weight           = None

class Task_formula(object):
    """
    Creates an Object with all task parameters
    """

    def __init__(self, task_id = None, name = None, arrival = None, departure = None,
                    no_goal_penalty = None, glide_bonus = None, tolerance = None,
                    stopped_time_calc = None, arr_alt_bonus = None,
                    nominal_goal = None, nominal_dist = None, nominal_time = None,
                    nominal_launch = None, min_dist = None, score_back_time = None):
        """
        creates an object with formula parameters
        that will be included in Task_result Object
        """
        self.formula_name           = name
        self.type                   = None
        self.version                = None
        self.arrival                = arrival
        self.departure              = departure
        self.no_goal_penalty        = no_goal_penalty
        self.glide_bonus            = glide_bonus
        self.stopped_time_calc      = stopped_time_calc
        self.tolerance              = tolerance             # percentage / 100
        self.arr_alt_bonus          = arr_alt_bonus
        self.nominal_goal           = nominal_goal          # percentage / 100
        self.nominal_dist           = nominal_dist          # meters
        self.nominal_time           = nominal_time          # seconds
        self.nominal_launch         = nominal_launch        # percentage / 100
        self.min_dist               = min_dist              # meters
        self.score_back_time        = score_back_time       # seconds

    def __str__(self):
        out = ''
        out += 'Formula name:   {} \n'.     format(self.formula_name)
        out += 'Arrival:        {}  |  '.   format(self.arrival)
        out += 'Departure:      {} \n'.     format(self.departure)
        out += 'No goal Penalty:{}% \n'.     format(self.no_goal_penalty*100)
        out += 'Glide Bonus:    1:{} \n'.     format(self.glide_bonus)
        out += 'Tolerance:      {}% \n'.     format(self.tolerance)
        out += 'Nom. Goal:      {}  |  '.   format(self.nominal_goal)
        out += 'Nom. Distance:  {} \n'.     format(self.nominal_dist)
        out += 'Nom. Time:      {}  |  '.   format(self.nominal_time)
        out += 'Nom. Launch:    {} \n'.     format(self.nominal_launch)
        out += 'Min. Dist:      {} \n'.     format(self.min_dist)
        out += 'Score back time:{} \n'.     format(self.score_back_time)
        return out

    @classmethod
    def read(cls, task_id):
        """reads task formula from DB"""

        query = """ SELECT
                        `type`,
                        `version`,
                        `formula_name`,
                        `arrival`,
                        `departure`,
                        `no_goal_penalty`,
                        `glide_bonus`,
                        `stopped_time_calc`,
                        `arr_alt_bonus`,
                        `nominal_goal`,
                        `nominal_dist`,
                        `min_dist`,
                        `nominal_time`,
                        `nominal_launch`,
                        `score_back_time`,
                        `tolerance`
                    FROM
                        `TaskFormulaView`
                    WHERE
                        `task_id` = %s
                    LIMIT 1
                """

        with Database() as db:
            # get the task details.
            t = db.fetchone(query, [task_id])
        if t is None:
            print('Task formula error')
            return
        else:
            formula = cls(task_id)
            formula.__dict__.update(t)

            return formula

    def get_lib(self):
        import importlib

        lib     = None
        type    = self.type

        '''get formula library to use in scoring'''
        formula_file = 'formulas.' + type
        try:
            lib = importlib.import_module(formula_file, package=None)
            return lib
        except:
            print('formula file {} not found.'.format(formula_file))
            exit()
