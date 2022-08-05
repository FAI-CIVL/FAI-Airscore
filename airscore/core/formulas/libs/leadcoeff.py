"""
Leading Coefficient Calculation Library

contains
    - All procedures to calculate Leading Coefficient according to PWC GAP Formula


Stuart Mackintosh, Antonio Golfari - 2019
"""
from formulas import lclib


class LeadCoeff(object):
    def __init__(self, task):
        self.ss_distance = task.SS_distance / 1000
        self.opt_dist_to_ess = task.opt_dist_to_ESS / 1000
        self.best_dist_to_ess = [task.SS_distance / 1000]
        self.best_distance_time = 0
        self.best_start_time = task.start_time
        self.lib = task.formula.get_lib()
        self.comp_class = task.comp_class
        self.summing = 0.0

    @property
    def best_dist_to_ess_m(self):
        return self.best_dist_to_ess[-1] * 1000

    def reset(self):
        self.summing = 0.0

    def update(self, result, fix, next_fix, dist_to_ess):
        """ Get lead coeff calculation formula from Formula Library"""
        dist_to_ess /= 1000
        self.best_dist_to_ess.append(min(dist_to_ess, self.ss_distance, self.best_dist_to_ess[0]))
        self.best_distance_time = result.best_distance_time if not result.ESS_time else result.ESS_time
        self.summing += self.lib.lead_coeff_function(self, result, fix, next_fix)
        self.best_dist_to_ess.pop(0)


def lead_coeff_function(lc, result, fix, next_fix):
    """Lead Coefficient formula from GAP2016
    Default fallback
    This is the default function if not present in Formula library"""
    return lclib.classic.lc_calculation(lc, result, fix, next_fix)


def tot_lc_calc(res, t):
    """Lead Coefficient formula from GAP2016
    Default fallback
    This is the default function if not present in Formula library"""
    return lclib.classic.tot_lc_calculation(res, t)


def store_lc(res_id, lead_coeff):
    """store LC to database"""
    from db.tables import TblTaskResult as R

    # It shouldn't be necessary any longer, as we should not store final LC
    row = R.get_by_id(res_id)
    row.update(lead_coeff=lead_coeff)
