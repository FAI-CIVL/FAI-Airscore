"""
Scoring Formula Script
    Defines a Scoring formula. Gets Parameters and jobs from Formula Libraries in libs folder or contains new ones.
    Name of primary functions has to be mantained:
        - process_result : jobs done of FlightResult obj. before scoring
        - points_allocation : main function called to calculate scoring
    Defines which classes formula applies
    Defines standard parameters values for each class
"""
from formula import FormulaPreset, Preset
from formulas.libs.pwc import *

''' Formula Info'''
# Formula Name: usually the filename in capital letters
formula_name = 'PWC2019'
# Formula Type: pwc, gap, aat, any formula in libs folder
formula_type = 'pwc'
# Formula Version: INT, usually identified with year
formula_version = '2019'
# Comp Class: PG, HG, BOTH
formula_class = 'PG'

''' Default Formula presets
    pg_preset: PG default values, if formula applies for PG or mixed
    hg_preset: HG default values, if formula applies for HG or mixed  
  
    value:      default value of the parameter
    visible:    whether parameter is visible or not in frontend
    editable:   whether parameter is editable by user or not in frontend
    comment:    comment to show in parameter label in frontend'''

pg_preset = FormulaPreset(
    # This part should not be edited
    formula_name=Preset(value=formula_name, visible=True, editable=True),
    formula_type=Preset(value=formula_type, visible=True),
    formula_version=Preset(value=formula_version, visible=True),
    # Editable part starts here
    # Distance Points: on, difficulty, off
    formula_distance=Preset(value='on', visible=False),
    # Arrival Points: position, time, off
    formula_arrival=Preset(value='off', visible=False),
    # Departure Points: on, leadout, off
    formula_departure=Preset(value='leadout', visible=False),
    # Lead Factor: factor for Leadou Points calculation formula
    lead_factor=Preset(value=1.0, visible=False),
    # Squared Distances used for LeadCoeff: factor for Leadou Points calculation formula
    # lead_squared_distance=Preset(value=True, visible=False),
    # Time Points: on, off
    formula_time=Preset(value='on', visible=False),
    # Arrival Altitude Bonus: Bonus points factor on ESS altitude
    arr_alt_bonus=Preset(value=0, visible=False),
    # ESS Min Altitude
    arr_min_height=Preset(value=None, visible=False),
    # ESS Max Altitude
    arr_max_height=Preset(value=None, visible=False),
    # Minimum flight time for task validation (minutes)
    validity_min_time=Preset(value=3600, visible=True, editable=True),
    # Score back time for Stopped Tasks (minutes)
    score_back_time=Preset(value=300, visible=True, editable=True),
    # Max allowed Jump the Gun (seconds)
    max_JTG=Preset(value=0, visible=False),
    # Penalty per Jump the Gun second
    JTG_penalty_per_sec=Preset(value=None, visible=False),
    # Type of Total Validity: ftv, all
    overall_validity=Preset(value='ftv', visible=True, editable=True),
    # FTV Parameter
    validity_param=Preset(value=0.75, visible=True, editable=True),
    # FTV Parameter Reference: day_quality, max_score
    validity_ref=Preset(value='max_score', visible=True, editable=True),
    # Penalty when ESS but not Goal: default is 1 for PG and 0.2 for HG
    no_goal_penalty=Preset(value=1.0, visible=False),
    # Glide Bonus for Stopped Task: default is 4 for PG and 5 for HG
    glide_bonus=Preset(value=4.0, visible=False),
    # Waypoint radius tolerance for validation: FLOAT default is 0.1%
    tolerance=Preset(value=0.002, visible=True, editable=True),
    # Waypoint radius minimum tolerance (meters): INT default = 5
    min_tolerance=Preset(value=5, visible=True, editable=True),
    # Scoring Altitude Type: default is GPS for PG and QNH for HG
    scoring_altitude=Preset(value='GPS', visible=True, editable=True),
    # Decimals to be displayed in Task results: default is 0
    task_result_decimal=Preset(value=0, visible=False, editable=False),
    # Decimals to be displayed in Comp results: default is 0
    comp_result_decimal=Preset(value=0, visible=False, editable=False),
)


def calculate_results(task):
    """Method to get to final results:
        Task validity calculation: day_quality(task);
        Points Weights calculation: points_weight(task);
        Points Allocation: points_allocation(task);
    Methods that are not on the script, are recalled from main library (pwc or gap)"""

    # dist_validity, time_validity, launch_validity, stop_validity, day_quality
    day_quality(task)

    # avail_dist_points, avail_time_points, avail_dep_points, avail_arr_points
    points_weight(task)

    # points allocation to pilots
    points_allocation(task)


def points_weight(task):
    quality = task.day_quality

    if not task.pilots_launched:  # sanity
        return 0, 0, 0, 0

    '''Goal Ratio'''
    goal_ratio = task.pilots_goal / task.pilots_launched

    '''
    DistWeight:         0.9 - 1.665* goalRatio + 1.713*GolalRatio^2 - 0.587*goalRatio^3
    LeadWeight:         (1 - DistWeight)/8 * 1.4
    ArrWeight:          0
    TimeWeight:         1 − DistWeight − LeadWeight
    '''
    task.dist_weight = 0.9 - 1.665 * goal_ratio + 1.713 * goal_ratio ** 2 - 0.587 * goal_ratio ** 3
    task.dep_weight = (1 - task.dist_weight) / 8 * 1.4
    task.time_weight = 1 - task.dist_weight - task.dep_weight
    task.arr_weight = 0

    task.avail_dist_points = 1000 * quality * task.dist_weight  # AvailDistPoints
    ''' PWC 2019: LeadPoints augmented by 50'''
    task.avail_dep_points = 1000 * quality * task.dep_weight  # AvailLeadPoints
    task.avail_dep_points += 50  # PWC2017 Augmented LeadPoints

    task.avail_arr_points = 0  # AvailArrPoints
    task.avail_time_points = 1000 * quality - task.avail_dep_points - task.avail_dist_points  # AvailSpeedPoints

    '''Stopped Task'''
    if task.stopped_time and task.pilots_ess:
        """12.3.5
        A fixed amount of points is subtracted from the time points of each pilot that makes goal in a stopped task.
        This amount is the amount of time points a pilot would receive if he had reached ESS exactly at
        the task stop time. This is to remove any discontinuity between pilots just before ESS and pilots who
        had just reached ESS at task stop time.
        """
        task.time_points_reduction = calculate_time_points_reduction(task)
        task.avail_dist_points += task.time_points_reduction
    else:
        task.time_points_reduction = 0


def weightRising(p):
    return (1 - 10 ** (9 * p - 9)) ** 5


def weightFalling(p):
    return (1 - 10 ** (-3 * p)) ** 2


def weight_calc(dist_to_ess, ss_distance):
    p = dist_to_ess / ss_distance
    return weightRising(p) * weightFalling(p)


def lead_coeff_function(lc, result, fix, next_fix):
    """ Lead Coefficient formula from PWC2019"""
    ''' C.6.3.1 Leading Coefficient (LC)
        Each started pilot’s track log is used to calculate the Leading Coefficient (LC), by calculating the area 
        underneath a graph defined by each track point’s time, and the distance to ESS at that time. 
        The times used for this calculation are given in seconds from the moment when the first pilot crossed SSS, 
        to the time when the last pilot reached ESS. For pilots who land out after the last pilot reached ESS, 
        the calculation keeps going until they land. The distances used for the LC calculation are given in Kilometers 
        and are the distance from each point’s position to ESS, starting from SSS, but never more than any previously 
        reached distance. This means that the graph never “goes back”: even if the pilot flies away from goal 
        for a while, the corresponding points in the graph will use the previously reached best distance towards ESS. 
        Important: Previous versions of the formula used distances to ESS squared to increase the number of 
        Leading Points awarded for leading out early in the task. 
        This version uses a more complex weighting according to distance from ESS to give no leading points 
        at the start, rising rapidly afterwards to give a similar linear function of distance from ESS after 
        about 20% of the speed section.
    '''
    weight = weight_calc(lc.best_dist_to_ess[1], lc.ss_distance)
    # time_interval = next_fix.rawtime - fix.rawtime
    time = next_fix.rawtime - lc.best_start_time
    progress = lc.best_dist_to_ess[0] - lc.best_dist_to_ess[1]
    # print(f'weight: {weight}, progress: {progress}, time: {time}')
    if progress <= 0 or weight == 0:
        return 0
    else:
        return weight * progress * time


def missing_area(time_interval, best_distance_to_ESS, ss_distance):
    p = best_distance_to_ESS / ss_distance
    return weightFalling(p) * time_interval * best_distance_to_ESS


def tot_lc_calc(res, t):
    """Function to calculate final Leading Coefficient for pilots,
    that needs to be done when all tracks have been scored"""
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
