"""
Module for operations on formula
Use:    import formula
        parameters = Formula.read(comPk, <test>)

Antonio Golfari - 2018
"""

# Use your utility module.
from myconn import Database

class Formula:
    """
    Create an object Formula
    """
    def __init__(self, id = None, name = None, comp_class = None, test = 0):
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

class Task_formula:
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
        self.task_id                = task_id
        self.name                   = name
        self.arrival                = arrival
        self.departure              = departure
        self.no_goal_penalty        = no_goal_penalty
        self.glide_bonus            = glide_bonus
        self.tolerance              = tolerance
        self.stopped_time_calc      = stopped_time_calc
        self.arr_alt_bonus          = arr_alt_bonus
        self.nominal_goal           = nominal_goal
        self.nominal_dist           = nominal_dist
        self.nominal_time           = nominal_time
        self.nominal_launch         = nominal_launch
        self.min_dist               = min_dist
        self.score_back_time        = score_back_time

    def __str__(self):
        out = ''
        out += 'Formula name:   {} \n'.     format(self.name)
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
    def read(cls, task_id, test = 0):
        """reads task formula from DB"""

        query = (""" SELECT
                        `tasPk`,
                        `forName`,
                        `tasArrival`,
                        `tasDeparture`,
                        `forLinearDist`,
                        `forDiffDist`,
                        `forGoalSSpenalty`,
                        `forStoppedGlideBonus`,
                        `forStoppedElapsedCalc`,
                        `tasHeightBonus`,
                        `comOverallScore`,
                        `comOverallParam`,
                        `forNomGoal`,
                        `forMinDistance`,
                        `forNomDistance`,
                        `forNomTime`,
                        `forNomLaunch`,
                        `forScorebackTime`,
                        `tasMargin`
                    FROM
                        `TaskView`
                    WHERE
                        `tasPk` = {}
                    LIMIT 1
                """.format(task_id))

        if test:
            print('task formula:')
            print('Query:')
            print(query)

        with Database() as db:
            # get the task details.
            t = db.fetchone(query)
        if t is None:
            print('Task formula error')
            return
        else:
            formula = cls(  task_id             = t['tasPk'],
                            name                = t['forName'],
                            arrival             = t['tasArrival'],
                            departure           = t['tasDeparture'],
                            no_goal_penalty     = t['forGoalSSpenalty'],
                            glide_bonus         = t['forStoppedGlideBonus'],
                            tolerance           = t['tasMargin'],
                            stopped_time_calc   = t['forStoppedElapsedCalc'],
                            arr_alt_bonus       = t['tasHeightBonus'],
                            nominal_goal        = t['forNomGoal'],
                            nominal_dist        = t['forNomDistance'],
                            nominal_time        = t['forNomTime'],
                            nominal_launch      = t['forNomLaunch'],
                            min_dist            = t['forMinDistance'],
                            score_back_time     = t['forScorebackTime'])

            return formula
