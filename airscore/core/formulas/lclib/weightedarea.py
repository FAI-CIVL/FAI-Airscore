
def lc_calculation(lc, result, fix, next_fix):
    """ Lead Coefficient formula from GAP2020
        11.3.1 Leading coefficient
        Each started pilot’s track log is used to calculate the leading coefficient (LC),
        by calculating the area underneath a graph defined by each track point’s time,
        and the distance to ESS at that time. The times used for this calculation are given in seconds
        from the moment when the first pilot crossed SSS, to the time when the last pilot reached ESS.
        For pilots who land out after the last pilot reached ESS, the calculation keeps going until they land.
        The distances used for the LC calculation are given in kilometers and are the distance from each
        point’s position to ESS, starting from SSS, but never more than any previously reached distance.
        This means that the graph never “goes back”: even if the pilot flies away from goal for a while,
        the corresponding points in the graph will use the previously reached best distance towards ESS.
    """
    # print(f'Weighted Area LC Calculation')
    weight = weight_calc(lc.best_dist_to_ess[1], lc.ss_distance)
    # time_interval = next_fix.rawtime - fix.rawtime
    time = next_fix.rawtime - lc.best_start_time
    progress = lc.best_dist_to_ess[0] - lc.best_dist_to_ess[1]
    # print(f'weight: {weight}, progress: {progress}, time: {time}')
    if progress <= 0 or weight == 0:
        return 0
    else:
        return weight * progress * time


def tot_lc_calculation(res, t):
    """Function to calculate final Leading Coefficient for pilots,
    that needs to be done when all tracks have been scored"""
    # print(f'Weighted Area Tot LC Calculation')
    if res.result_type in ('abs', 'dnf', 'mindist', 'nyp') or not res.SSS_time:
        '''pilot did't make Start or has no track'''
        return 0
    ss_distance = t.SS_distance / 1000
    if res.ESS_time:
        '''nothing to do'''
        landed_out = 0
    else:
        '''pilot did not make ESS'''
        best_dist_to_ess = (t.opt_dist_to_ESS - res.distance_flown) / 1000  # in Km
        missing_time = t.max_time - t.start_time  # TODO should be t.min_dept_time but using same as lead_coeff
        landed_out = missing_area(missing_time, best_dist_to_ess, ss_distance)
    return (res.fixed_LC + landed_out) / (1800 * ss_distance)


def missing_area(time_interval, best_distance_to_ESS, ss_distance):
    """calculates medium weight for missing portion, missing area using mean weight value"""
    p = best_distance_to_ESS / ss_distance
    return weightFalling(p) * time_interval * best_distance_to_ESS


def weightRising(p):
    return (1 - 10 ** (9 * p - 9)) ** 5


def weightFalling(p):
    return (1 - 10 ** (-3 * p)) ** 2


def weight_calc(dist_to_ess, ss_distance):
    p = dist_to_ess / ss_distance
    return weightRising(p) * weightFalling(p)


