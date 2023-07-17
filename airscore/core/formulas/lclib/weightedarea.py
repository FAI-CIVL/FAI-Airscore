from dataclasses import dataclass
from calcUtils import c_round

# integrate_precision is used to determine how many speed section slices will be created to calculate LC
# slices = 10 ^ integrate_precision
integrate_precision = 4

# weight matrix calculation
@dataclass(frozen=True)
class toDoWeight:
    ratio: float
    rising: float
    falling: float

def weight_matrix(precision: int = integrate_precision) -> list:
    matrix = []
    # print(f"precision: {precision} | matrix elements: {10**precision}")
    slices = 10**precision
    for i in range(slices):
        ratio = i/slices
        matrix.append(toDoWeight(ratio, weightRising(ratio), weightFalling(ratio)))
        # print(f"i: {i} | ratio: {ratio} | el ratio: {matrix[i].ratio}")
    return matrix


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
    weight = weight_calc(toDo(lc.best_dist_to_ess[1], lc.ss_distance))
    return 0 if weight == 0 else weight * progress * time


def tot_lc_calculation(res, t) -> float:
    """Function to calculate final Leading Coefficient for pilots,
    that needs to be done when all tracks have been scored"""

    # print(f'Weighted Area Tot LC Calculation')
    if res.result_type in ('abs', 'dnf', 'mindist', 'nyp') or not res.SSS_time:
        '''pilot did't make Start or has no track'''
        return 0

    ss_distance = t.SS_distance / 1000  # in Km
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
    return weightFalling(toDo(best_distance_to_ESS, ss_distance)) * time_interval * best_distance_to_ESS


def toDo(dist_to_ess: float, ss_distance: float) -> float:
    return dist_to_ess / ss_distance


def weightRising(p: float) -> float:
    return (1 - 10 ** (9 * p - 9)) ** 5


def weightFalling(p: float) -> float:
    return (1 - 10 ** (-3 * p)) ** 2


def weight_calc(p: float) -> float:
    return weightRising(p) * weightFalling(p)


def lc_calculation_integrate(lc, result, fix, next_fix) -> float:
    """ Lead Coefficient formula from PWC2023
        A1.1.1 Leading coefficient (LC)
        Each started pilot’s track log is used to calculate the Leading Coefficient (LC), 
        by calculating the area underneath a graph defined by each track point’s time, 
        and the distance to ESS at that time. 
        The times used for this calculation are given in seconds from the moment when the first pilot crossed SSS, 
        to the time when the last pilot reached ESS. For pilots who land out after the last pilot reached ESS, 
        the calculation keeps going until they land. 
        The distances used for the LC calculation are given in Kilometres and are the distance from e
        ach point’s position to ESS, starting from SSS, but never more than any previously reached distance. 
        This means that the graph never “goes back”: even if the pilot flies away from goal for a while, 
        the corresponding points in the graph will use the previously reached best distance towards ESS. 
        Important: Previous versions of the formula used distances to ESS squared to increase the number 
        of Leading Points awarded for leading out early in the task. This version uses a more complex 
        weighting according to distance from ESS to give no leading points at the start, 
        rising rapidly afterwards to give a flat section after about 20% of the speed section and, 
        finally, a similar linear function of distance from ESS after about 60% of the speed section.

        Airscore creates an array of tuples (ratio, weightRising, weightFalling) at fixed best_dist_to_ess / ss_distance
    """

    if lc.best_dist_to_ess[0] - lc.best_dist_to_ess[1] <= 0:
        return 0

    ratio = c_round(toDo(lc.best_dist_to_ess[1], lc.ss_distance), integrate_precision)
    # slices = ratio * 10**integrate_precision
    index = int(ratio * lc.slices)
    if lc.latest_index and index >= lc.latest_index:
        return 0

    time = next_fix.rawtime - lc.best_start_time
    # print(f"time: {time} | dist to ESS: {lc.best_dist_to_ess[1]} | ratio: {ratio} | slice id: {index}")
    result = sum(weight * lc.slice_dist * time for weight in weight_calc_integrate(lc.matrix, lc.latest_index, index))
    lc.latest_index = index
    return result


def missing_area_integrate(matrix: list, id0: int, idx: int) -> list:
    # print(f"id {id0} ratio: {matrix[id0].ratio}")
    # print(f"id {idx} ratio: {matrix[idx].ratio}")
    result = [matrix[i].falling for i in range(id0, idx, -1)]
    # print(f"result elements: {len(result)}")
    return result


def weight_calc_integrate(matrix: list, id0: int, idx: int) -> list:
    # print(f"id {id0} ratio: {matrix[id0].ratio}")
    # print(f"id {idx} ratio: {matrix[idx].ratio}")
    result = [matrix[i].rising * matrix[i].falling for i in range(id0, idx, -1)]
    # print(f"result elements: {len(result)}")
    return result


def tot_lc_calculation_integrate(res, t) -> float:
    """Function to calculate final Leading Coefficient for pilots,
    that needs to be done when all tracks have been scored"""

    # print(f'Weighted Area Tot LC Calculation')
    if res.result_type in ('abs', 'dnf', 'mindist', 'nyp') or not res.SSS_time:
        '''pilot did't make Start or has no track'''
        return 0

    ss_distance = t.SS_distance / 1000  # in Km
    landed_out = 0
    if not res.ESS_time:
        '''pilot did not make ESS'''
        best_dist_to_ess = max(0, res.best_dist_to_ESS / 1000)  # in Km
        if best_dist_to_ess > 0:
            matrix = weight_matrix()
            ratio = c_round(toDo(best_dist_to_ess, ss_distance), integrate_precision)
            slice_dist = ss_distance / len(matrix)
            index = int(ratio * len(matrix))
            missing_time = t.max_time - t.start_time
            landed_out = sum(weight * slice_dist * missing_time for weight in missing_area_integrate(matrix, index, 0))
    return (res.fixed_LC + landed_out) / (1800 * ss_distance)


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

# def lc_calculation_over_time(lc, result, fix, next_fix) -> float:

#     if next_fix.rawtime > fix.rawtime:
#         weight = weight_calc(lc.best_dist_to_ess[1], lc.ss_distance)
#         return lc.best_dist_to_ess[1] * weight * (next_fix.rawtime - fix.rawtime)
#     return 0


# def tot_lc_calculation_over_time(res, t) -> float:

#     if res.result_type in ('abs', 'dnf', 'mindist', 'nyp') or not res.SSS_time:
#         '''pilot did't make Start or has no track'''
#         return 0
#     ss_distance = t.SS_distance / 1000
#     if res.ESS_time:
#         '''nothing to do'''
#         landed_out = 0
#     else:
#         '''pilot did not make ESS'''
#         best_dist_to_ess = max(0, res.best_dist_to_ESS / 1000)  # in Km
#         missing_time = max(0, t.max_time - res.best_distance_time)
#         landed_out = missing_area(missing_time, best_dist_to_ess, ss_distance)
#     return (res.fixed_LC + landed_out) / (1800 * ss_distance)
