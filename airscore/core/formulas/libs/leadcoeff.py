"""
Leading Coefficient Calculation Library

contains
    - All procedures to calculate Leading Coefficient according to PWC GAP Formula


Stuart Mackintosh, Antonio Golfari - 2019
"""
from dataclasses import dataclass, asdict, fields


class LeadCoeff(object):
    def __init__(self, task):
        self.ss_distance = task.SS_distance / 1000
        self.best_dist_to_ess = task.SS_distance / 1000
        self.opt_dist_to_ess = task.opt_dist_to_ESS / 1000
        self.best_dist_to_ess = [task.SS_distance / 1000]
        self.lib = task.formula.get_lib()
        self.summing = 0.0

    @property
    def squared_distance(self):
        """ defaulting to True if not specified (should always be)"""
        if self.lib and self.lib.lead_coeff_parameters:
            return self.lib.lead_coeff_parameters.squared_distance
        else:
            return True

    def reset(self):
        self.summing = 0.0

    def update(self, result, next_fix):
        """ Get lead coeff calculation formula from Formula Library"""
        self.best_dist_to_ess.append(self.opt_dist_to_ess - result.distance_flown / 1000)
        self.summing += self.lib.lead_coeff_function(self, result, next_fix)
        self.best_dist_to_ess.pop(0)


def lead_coeff_function(lc, result, fix):
    """ Lead Coefficient formula from GAP2016
        This is the default function if not present in Formula library"""
    '''Leading coefficient
        LC = taskTime(i)*(bestDistToESS(i-1)^2 - bestDistToESS(i)^2 )
        i : i ? TrackPoints In SS'''
    task_time = fix.rawtime - result.real_start_time
    if lc.best_dist_to_ess[0] == lc.best_dist_to_ess[1]:
        return 0
    else:
        return task_time * (lc.best_dist_to_ess[0] ** 2 - lc.best_dist_to_ess[1] ** 2) / (1800 * (lc.ss_distance ** 2))


def lead_coeff_area(time, distance, ss_distance):
    return distance ** 2 * time / (1800 * (ss_distance ** 2))


def tot_lc_calc(res, t):
    late_start = 0
    landed_out = 0
    ss_distance = t.SS_distance / 1000
    first_start = t.min_dept_time

    '''find task_deadline to use for LC calculation'''
    task_deadline = min((t.task_deadline if not t.stopped_time else t.stopped_time), t.max_time)
    if t.max_ess_time and res.last_time:
        if res.last_time < t.max_ess_time:
            task_deadline = t.max_ess_time
        else:
            task_deadline = min(res.last_time, task_deadline)

    '''Checking if we have a assigned status without a track, and if pilot actually did the start pilon'''
    if (res.result_type not in ('abs', 'dnf', 'mindist')) and res.SSS_time:
        my_start = res.real_start_time

        '''add the leading part, from start time of first pilot to start, to my start time'''
        if my_start > first_start:
            late_start = lead_coeff_area((my_start - first_start), ss_distance, ss_distance)
        if not res.ESS_time:
            '''pilot did not make ESS'''
            best_dist_to_ess = (t.opt_dist_to_ESS - res.distance) / 1000  # in Km
            task_time = task_deadline - my_start
            landed_out = lead_coeff_area(task_time, best_dist_to_ess, ss_distance)

        LC = late_start + res.fixed_LC + landed_out

    else:
        '''pilot didn't make SS or has an assigned status without a track'''
        task_time = task_deadline - first_start
        LC = lead_coeff_area(task_time, ss_distance, ss_distance)

    return LC


def store_lc(res_id, lead_coeff):
    """store LC to database"""
    from db_tables import tblTaskResult as R
    from myconn import Database
    # It shouldn't be necessary any longer, as we should not store final LC

    with Database() as db:
        q = db.session.query(R)
        res = q.get(res_id)
        res.tarLeadingCoeff = lead_coeff
        db.session.commit()

