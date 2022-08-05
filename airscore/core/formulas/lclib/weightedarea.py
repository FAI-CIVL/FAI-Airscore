
def lc_calculation(lc, result, fix, next_fix) -> float:
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

    progress = lc.best_dist_to_ess[0] - lc.best_dist_to_ess[1]
    # print(f'weight: {weight}, progress: {progress}, time: {time}')
    if progress <= 0:
        return 0

    time = next_fix.rawtime - lc.best_start_time
    weight = weight_calc(lc.best_dist_to_ess[1], lc.ss_distance)
    return 0 if weight == 0 else weight * progress * time


def tot_lc_calculation(res, t) -> float:
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
        best_dist_to_ess = max(0, res.best_dist_to_ESS / 1000)  # in Km
        missing_time = t.max_time - t.start_time
        landed_out = missing_area(missing_time, best_dist_to_ess, ss_distance)
    return (res.fixed_LC + landed_out) / (1800 * ss_distance)


def missing_area(time_interval: float, best_distance_to_ESS: float, ss_distance: float) -> float:
    """calculates medium weight for missing portion, missing area using mean weight value"""
    p = best_distance_to_ESS / ss_distance
    return weightFalling(p) * time_interval * best_distance_to_ESS


def weightRising(p: float) -> float:
    return (1 - 10 ** (9 * p - 9)) ** 5


def weightFalling(p: float) -> float:
    return (1 - 10 ** (-3 * p)) ** 2


def weight_calc(dist_to_ess: float, ss_distance: float) -> float:
    p = dist_to_ess / ss_distance
    return weightRising(p) * weightFalling(p)


# these are calculations integrating over time (instead of over distance)
# they are flawed, but can be used for comparing purposes.
# Explanation
#
# 1. Integration
#
# Basically, you cannot use a weight f(distance ratio) on a timeline based integration.
# Doing so, you completely lose one dimension, time
# you would need a weight f(time ratio) but you cannot as timeline is not a task defined data.
#
# So, your "slice" of a time interval could be anywhere along timeline, result won't change.
#
# Opposite way, distance based integration.
# weight gives you exact position of distance improve (interval) on distance line, time is from start, so defined,
# you have all dimensions defined.
#
# I don't see any other option to do this calculation correctly.
#
# As Joerg said, formula description in rules changed in 2020, but I'm not sure any software changed it, apart SVL.
#
# Anyway, integrating over time is simply impossible.
#
# 2. Missing_area calculation for landed out pilots.
#
# In rules until 2019 description was exactly as Airscore does it.
# Again, the other way around has no sense, easy to understand if you understand and agree on what explained above.
#
# Now, we can discuss about fairness, how we would like our LoP curve to be like, and so on.
# But the answer should not be a flawed calculation, in my very humble opinion.
def lc_calculation_over_time(lc, result, fix, next_fix) -> float:

    if next_fix.rawtime > fix.rawtime:
        weight = weight_calc(lc.best_dist_to_ess[1], lc.ss_distance)
        return lc.best_dist_to_ess[1] * weight * (next_fix.rawtime - fix.rawtime)
    return 0


def tot_lc_calculation_over_time(res, t) -> float:

    if res.result_type in ('abs', 'dnf', 'mindist', 'nyp') or not res.SSS_time:
        '''pilot did't make Start or has no track'''
        return 0
    ss_distance = t.SS_distance / 1000
    if res.ESS_time:
        '''nothing to do'''
        landed_out = 0
    else:
        '''pilot did not make ESS'''
        best_dist_to_ess = max(0, res.best_dist_to_ESS / 1000)  # in Km
        missing_time = max(0, t.max_time - res.best_distance_time)
        landed_out = missing_area(missing_time, best_dist_to_ess, ss_distance)
    return (res.fixed_LC + landed_out) / (1800 * ss_distance)
