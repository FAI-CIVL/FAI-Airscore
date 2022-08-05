
def lc_calculation(lc, result, fix, next_fix):
    """Leading coefficient
    LC = taskTime(i)*(bestDistToESS(i-1)^2 - bestDistToESS(i)^2 )
    i : i ? TrackPoints In SS"""
    # print(f'Classic LC Calculation')
    if lc.best_dist_to_ess[0] <= lc.best_dist_to_ess[1]:
        return 0
    else:
        task_time = next_fix.rawtime - result.real_start_time
        # return task_time * (lc.best_dist_to_ess[0] ** 2 - lc.best_dist_to_ess[1] ** 2) / (1800 * (lc.ss_distance ** 2))
        return task_time * (lc.best_dist_to_ess[0] ** 2 - lc.best_dist_to_ess[1] ** 2)


def tot_lc_calculation(res, t):
    """Function to calculate final Leading Coefficient for pilots,
    that needs to be done when all tracks have been scored"""
    # print(f'Classic Tot LC Calculation')
    '''Checking if we have a assigned status without a track, and if pilot actually did the start pilon'''
    if res.result_type in ('abs', 'dnf', 'mindist', 'nyp') or not res.SSS_time:
        '''pilot didn't make Start or has no track'''
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

        best_dist_to_ess = max(0, res.best_dist_to_ESS / 1000)   # in Km
        task_time = max_time - res.real_start_time
        landed_out = lead_coeff_area(task_time, best_dist_to_ess, ss_distance)

    return (late_start_area + res.fixed_LC + landed_out) / (1800 * (ss_distance ** 2))


def lead_coeff_area(time, distance, ss_distance):
    # return distance ** 2 * time / (1800 * (ss_distance ** 2))
    return distance ** 2 * time

