"""
Leading Coefficient Calculation Library

contains
    - All procedures to calculate Leading Coefficient according to PWC GAP Formula


Stuart Mackintosh, Antonio Golfari - 2019
"""


class LeadCoeff(object):
    def __init__(self, task):
        self.ss_distance = task.SS_distance / 1000
        self.opt_dist_to_ess = task.opt_dist_to_ESS / 1000
        self.best_dist_to_ess = [task.SS_distance / 1000]
        self.best_distance_time = 0
        self.best_start_time = task.start_time  # TODO should be t.min_dept_time unknown until all tracks are done
        self.lib = task.formula.get_lib()
        self.summing = 0.0

    # @property
    # def squared_distance(self):
    #     """ defaulting to True if not specified (should always be)"""
    #     if self.lib and self.lib.lead_coeff_parameters:
    #         return self.lib.lead_coeff_parameters.squared_distance
    #     else:
    #         return True

    def reset(self):
        self.summing = 0.0

    def update(self, result, fix, next_fix):
        """ Get lead coeff calculation formula from Formula Library"""
        self.best_dist_to_ess.append(self.opt_dist_to_ess - result.distance_flown / 1000)
        self.best_distance_time = result.best_distance_time if not result.ESS_time else result.ESS_time
        self.summing += self.lib.lead_coeff_function(self, result, fix, next_fix)
        self.best_dist_to_ess.pop(0)


def lead_coeff_function(lc, result, fix, next_fix):
    """ Lead Coefficient formula from GAP2016
        This is the default function if not present in Formula library"""
    '''Leading coefficient
        LC = taskTime(i)*(bestDistToESS(i-1)^2 - bestDistToESS(i)^2 )
        i : i ? TrackPoints In SS'''
    if lc.best_dist_to_ess[0] == lc.best_dist_to_ess[1]:
        return 0
    else:
        task_time = next_fix.rawtime - result.real_start_time
        return task_time * (lc.best_dist_to_ess[0] ** 2 - lc.best_dist_to_ess[1] ** 2) / (1800 * (lc.ss_distance ** 2))


def lead_coeff_area(time, distance, ss_distance):
    return distance ** 2 * time / (1800 * (ss_distance ** 2))


def tot_lc_calc(res, t):
    """ Function to calculate final Leading Coefficient for pilots,
        that needs to be done when all tracks have been scored"""
    '''Checking if we have a assigned status without a track, and if pilot actually did the start pilon'''
    if res.result_type in ('abs', 'dnf', 'mindist') or not res.SSS_time:
        '''pilot did't make Start or has no track'''
        return 0

    ss_distance = t.SS_distance / 1000
    late_start_area = 0
    landed_out = 0

    '''add the leading part, from start time of first pilot to start, to my start time'''
    if res.real_start_time > t.min_dept_time:
        late_start_area = lead_coeff_area((res.real_start_time - t.min_dept_time), ss_distance, ss_distance)

    '''add the trailing part if pilot did not make ESS, from pilot start time to task max time'''
    if not res.ESS_time:
        '''find task_deadline to use for LC calculation'''
        if t.max_ess_time:
            max_time = min(max(res.last_time, t.max_ess_time), t.max_time)  # max_time comparing should't be necessary
        else:
            max_time = t.max_time

        best_dist_to_ess = (t.opt_dist_to_ESS - res.distance) / 1000  # in Km
        task_time = max_time - res.real_start_time
        landed_out = lead_coeff_area(task_time, best_dist_to_ess, ss_distance)

    return late_start_area + res.fixed_LC + landed_out


def store_lc(res_id, lead_coeff):
    """store LC to database"""
    from db.tables import TblTaskResult as R
    from db.conn import db_session
    # It shouldn't be necessary any longer, as we should not store final LC

    with db_session() as db:
        q = db.query(R)
        res = q.get(res_id)
        res.lead_coeff = lead_coeff
        db.commit()

