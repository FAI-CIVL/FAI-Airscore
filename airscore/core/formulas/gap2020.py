"""
Scoring Formula Script
    Defines a Scoring formula. Gets Parameters and jobs from Formula Libraries in libs folder or contains new ones.
    Name of primary functions has to be mantained:
        - process_result : jobs done of Flight_result obj. before scoring
        - points_allocation : main function called to calculate scoring
    Defines which classes formula applies
    Defines standard parameters values for each class
"""
from formula import FormulaPreset, Preset
from formulas.libs.gap import *
from formulas.libs.leadcoeff import *

''' Formula Info'''
# Formula Name: usually the filename in capital letters
formula_name = 'GAP2020'
# Formula Type: pwc, gap, aat, any formula in libs folder
formula_type = 'gap'
# Formula Version: INT, usually identified with year
formula_version = '2020'
# Comp Class: PG, HG, BOTH
formula_class = 'BOTH'

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
    formula_type=Preset(value=formula_type, visible=True, editable=True),
    formula_version=Preset(value=formula_version, visible=True, editable=True),

    # Editable part starts here
    # Distance Points: on, difficulty, off
    formula_distance=Preset(value='on', visible=True, editable=False),
    # Arrival Points: position, time, off
    formula_arrival=Preset(value='off', visible=False, editable=False),
    # Departure Points: on, leadout, off
    formula_departure=Preset(value='leadout', visible=True, editable=False),
    # Lead Factor: factor for Leadou Points calculation formula
    lead_factor=Preset(value=None, visible=False, editable=False),
    # Squared Distances used for LeadCoeff: factor for Leadou Points calculation formula
    # lead_squared_distance=Preset(value=True, visible=True, editable=True),
    # Time Points: on, off
    formula_time=Preset(value='on', visible=True, editable=False),
    # Arrival Altitude Bonus: Bonus points factor on ESS altitude
    arr_alt_bonus=Preset(value=0, visible=True, editable=True, comment='default: disabled'),
    # ESS Min Altitude
    arr_min_height=Preset(value=None, visible=True, editable=True),
    # ESS Max Altitude
    arr_max_height=Preset(value=None, visible=True, editable=True),
    # Minimum flight time for task validation (minutes)
    validity_min_time=Preset(value=None, visible=True, editable=False,
                             calculated=True, comment='calculated from nominal distance'),
    # Score back time for Stopped Tasks (minutes)
    score_back_time=Preset(value=300, visible=True, editable=True, comment='default: 5 mins'),
    # Jump the Gun: 1 or 0
    max_JTG=Preset(value=0, visible=False, editable=False),
    # Penalty per Jump the Gun second
    JTG_penalty_per_sec=Preset(value=None, visible=False, editable=False),
    # Type of Total Validity: ftv, all
    overall_validity=Preset(value='ftv', visible=True, editable=True),
    # FTV Parameter
    validity_param=Preset(value=0.75, visible=True, editable=True),
    # Penalty when ESS but not Goal: default is 1 for PG and 0.2 for HG
    no_goal_penalty=Preset(value=1.0, visible=True, editable=True),
    # Glide Bonus for Stopped Task: default is 4 for PG and 5 for HG
    glide_bonus=Preset(value=4.0, visible=True, editable=True),
    # Waypoint radius tolerance for validation: FLOAT default is 0.1%
    tolerance=Preset(value=0.001, visible=True, editable=True, comment='0.1 ~ 0.5'),
    # Waypoint radius minimum tolerance (meters): INT default = 5
    min_tolerance=Preset(value=5, visible=True, editable=True, comment='0 ~ 5 m.'),
    # Scoring Altitude Type: default is GPS for PG and QNH for HG
    scoring_altitude=Preset(value='GPS', visible=True, editable=True),
    # Decimals to be displayed in Task results: default is 0
    task_result_decimal=Preset(value=1, visible=False, editable=False),
    # Decimals to be displayed in Comp results: default is 0
    comp_result_decimal=Preset(value=0, visible=False, editable=False)
)

hg_preset = FormulaPreset(
    # This part should not be edited
    formula_name=Preset(value=formula_name, visible=True, editable=True),
    formula_type=Preset(value=formula_type, visible=True, editable=True),
    formula_version=Preset(value=formula_version, visible=True, editable=True),

    # Editable part starts here
    # Distance Points: on, difficulty, off
    formula_distance=Preset(value='difficulty', visible=True, editable=True),
    # Arrival Points: position, time, off
    formula_arrival=Preset(value='position', visible=True, editable=True),
    # Departure Points: on, leadout, off
    formula_departure=Preset(value='leadout', visible=True, editable=True),
    # Lead Factor: factor for Leadou Points calculation formula
    lead_factor=Preset(value=1.0, visible=True, editable=True),
    # Squared Distances used for LeadCoeff: factor for Leadou Points calculation formula
    # lead_squared_distance=Preset(value=True, visible=True, editable=True),
    # Time Points: on, off
    formula_time=Preset(value='on', visible=True, editable=True),
    # Arrival Altitude Bonus: Bonus points factor on ESS altitude
    arr_alt_bonus=Preset(value=0, visible=True, editable=True),
    # ESS Min Altitude
    arr_min_height=Preset(value=None, visible=True, editable=True),
    # ESS Max Altitude
    arr_max_height=Preset(value=None, visible=True, editable=True),
    # Minimum flight time for task validation (minutes)
    validity_min_time=Preset(value=5400, visible=True, editable=True),
    # Score back time for Stopped Tasks (minutes)
    score_back_time=Preset(value=900, visible=True, editable=True),
    # Max allowed Jump the Gun (seconds)
    max_JTG=Preset(value=300, visible=True, editable=True),
    # Penalty per Jump the Gun second
    JTG_penalty_per_sec=Preset(value=0.50, visible=True, editable=True),
    # Type of Total Validity: ftv, all
    overall_validity=Preset(value='all', visible=True, editable=True),
    # FTV Parameter
    validity_param=Preset(value=None, visible=True, editable=True),
    # Penalty when ESS but not Goal: default is 1 for PG and 0.2 for HG
    no_goal_penalty=Preset(value=0.20, visible=True, editable=True),
    # Glide Bonus for Stopped Task: default is 4 for PG and 5 for HG
    glide_bonus=Preset(value=5.0, visible=True, editable=True),
    # Waypoint radius tolerance for validation: FLOAT default is 0.1%
    tolerance=Preset(value=0.001, visible=True, editable=True),
    # Waypoint radius minimum tolerance (meters): INT default = 5
    min_tolerance=Preset(value=5, visible=True, editable=True),
    # Scoring Altitude Type: default is GPS for PG and QNH for HG
    scoring_altitude=Preset(value='QNH', visible=True, editable=True),
    # Decimals to be displayed in Task results: default is 0
    task_result_decimal=Preset(value=0, visible=False, editable=False),
    # Decimals to be displayed in Comp results: default is 0
    comp_result_decimal=Preset(value=0, visible=False, editable=False)
)


''' Function to calculate parameters (if needed)'''
def calculate_parameters(args):
    """
    Args:
        args:   frontend parameters dict
    Returns:    parameter values
    """
    '''validity_min_time = min(1h, nominal_time/2)'''
    if args['nominal_time'] is not None:
        try:
            args['validity_min_time'] = min(3600, int(args['nominal_time'] / 2))
        except BaseException as e:
            print(f'Error trying to calculate parameters: {e}')
    return args


''' Scoring Functions'''
def launch_validity(task):
    """
    9.1 Launch Validity
    ‘Pilots Present’ are pilots arriving on take-off, with their gear, with the intention of flying.
    For scoring purposes, ‘Pilots Present’ are all pilots not in the ‘Absent’ status (ABS):
    Pilots who took off, plus pilots present who did not fly (DNF). DNFs need to be attributed carefully.
    A pilot who does not launch due to illness, for instance, is not a DNF, but an ABS.

    LVR = min (1, num_pilots_flying / (pilots_present * nom_launch) )
    Launch Validity = 0.027*LRV + 2.917*LVR^2 - 1.944*LVR^3
    ?? Setting Nominal Launch = 10 (max number of DNF that still permit full validity) ??
    """
    if task.pilots_present == 0 or task.formula.nominal_launch == 0:
        '''avoid div by zero'''
        return 0

    LVR = min(1, task.pilots_launched / (task.pilots_present * task.formula.nominal_launch))
    launch = 0.027 * LVR + 2.917 * LVR ** 2 - 1.944 * LVR ** 3
    launch = min(launch, 1) if launch > 0 else 0  # sanity
    return launch


def day_quality(task):
    task.dist_validity = 0.000
    task.time_validity = 0.000
    task.launch_validity = 0.000
    task.stop_validity = 1.000
    task.day_quality = 0.000

    if task.cancelled:
        print("Task Cancelled - dist quality set to 0")
        return None

    if task.pilots_present == 0:
        print("No pilots results - quality set to 0")
        return None

    if task.stopped_time:
        task.stop_validity = stopped_validity(task)

    task.launch_validity = launch_validity(task)
    task.dist_validity = distance_validity(task)
    task.time_validity = time_validity(task)
    task.day_quality = min(
        (task.stop_validity * task.launch_validity * task.dist_validity * task.time_validity), 1.000)


def points_weight(task):
    comp_class = task.comp_class  # HG / PG
    formula = task.formula
    quality = task.day_quality

    task.dist_weight = 0
    task.arr_weight = 0
    task.dep_weight = 0
    task.time_weight = 0

    if not task.pilots_launched:  # sanity
        return None

    '''Goal Ratio'''
    goal_ratio = task.pilots_goal / task.pilots_launched

    if comp_class == 'HG':
        '''
        DistWeight:         0.9 - 1.665* goalRatio + 1.713*GolalRatio^2 - 0.587*goalRatio^3
        LeadWeight:         (1 - DistWeight)/8 * 1.4 (lead_factor = 1)
        ArrWeight:          (1 - DistWeight)/8
        TimeWeight:         1 − DistWeight − LeadWeight − ArrWeight
        '''
        ''' Distance Weight'''
        if task.formula.formula_distance != 'off':
            task.dist_weight = 0.9 - 1.665 * goal_ratio + 1.713 * goal_ratio ** 2 - 0.587 * goal_ratio ** 3
        ''' Arrival Weight'''
        if task.formula.formula_arrival != 'off':
            task.arr_weight = (1 - task.dist_weight) / 8
            if task.formula.formula_arrival == 'time':
                task.arr_weight *= 2  # (1 - dist_weight) / 4
        ''' Departure Weight'''
        if task.formula.formula_departure != 'off':
            task.dep_weight = (1 - task.dist_weight) / 8 * 1.4 * formula.lead_factor

    elif comp_class == 'PG':
        '''
        DistWeight:
            GoalRatio = 0:  DistanceWeight = 0.838
            GoalRatio > 0:  DistanceWeight = 0.805 - 1.374*GoalRatio + 1.413*GoalRatio**2 - 0.484*GoalRatio**3
        LeadWeight:         0.162
        ArrWeight:          0
        TimeWeight:         1 − DistWeight − LeadWeight − ArrWeight
        '''
        ''' Distance Weight'''
        if task.formula.formula_distance != 'off':
            if goal_ratio == 0:
                task.dist_weight = 0.838
            else:
                task.dist_weight = 0.805 - 1.374 * goal_ratio + 1.413 * goal_ratio ** 2 - 0.484 * goal_ratio ** 3
        ''' Departure Weight'''
        if task.formula.formula_departure != 'off':
            task.dep_weight = 0.162

    ''' Time weight'''
    if task.formula.formula_departure != 'off':
        task.time_weight = 1 - task.dist_weight - task.dep_weight - task.arr_weight

    ''' Available Points'''
    task.avail_dist_points = 1000 * quality * task.dist_weight  # AvailDistPoints
    task.avail_dep_points = 1000 * quality * task.dep_weight  # AvailLeadPoints
    task.avail_arr_points = 1000 * quality * task.arr_weight  # AvailArrPoints
    task.avail_time_points = 1000 * quality * task.time_weight  # AvailTimePoints


def pilot_speed(task, res):
    """
    Args:
        task: Task obj.
        res: Flight_result object
    Time points are assigned to the pilot as a function of best time and pilot time – the time the pilot took
    to complete the speed section. Slow pilots will get zero points for speed if their time to complete the
    speed section is equal to or longer than the fastest time plus the square root of the fastest time.
    All times are measured in hours.
    """
    if not (res.ESS_time and task.fastest):
        return 0
    Aspeed = task.avail_time_points
    comp_class = task.comp_class  # HG / PG
    # C.11.2 Time points
    Tmin = task.fastest
    Ptime = res.time
    if comp_class == 'HG':
        SF = max(0, 1 - ((Ptime - Tmin) / 3600 / sqrt(Tmin / 3600)) ** (2 / 3))
    else:
        SF = max(0, 1 - ((Ptime - Tmin) / 3600 / sqrt(Tmin / 3600)) ** (5 / 6))
    Pspeed = Aspeed * SF
    return Pspeed


def weightRising(p):
    return (1 - 10 ** (9 * p - 9)) ** 5


def weightFalling(p):
    return (1 - 10 ** (-3 * p)) ** 2


def weight_calc(dist_to_ess, ss_distance):
    p = dist_to_ess / ss_distance
    return weightRising(p) * weightFalling(p)


def lead_coeff_function(lc, result, fix, next_fix):
    """ Lead Coefficient formula from PWC2019"""
    ''' 11.3.1 Leading coefficient
        Each started pilot’s track log is used to calculate the leading coefficient (LC), 
        by calculating the area underneath a graph defined by each track point’s time, 
        and the distance to ESS at that time. The times used for this calculation are given in seconds 
        from the moment when the first pilot crossed SSS, to the time when the last pilot reached ESS. 
        For pilots who land out after the last pilot reached ESS, the calculation keeps going until they land. 
        The distances used for the LC calculation are given in kilometers and are the distance from each 
        point’s position to ESS, starting from SSS, but never more than any previously reached distance. 
        This means that the graph never “goes back”: even if the pilot flies away from goal for a while, 
        the corresponding points in the graph will use the previously reached best distance towards ESS.
    '''
    weight = weight_calc(lc.best_dist_to_ess[1], lc.ss_distance)
    time_interval = next_fix.rawtime - fix.rawtime
    if time_interval == 0 or weight == 0:
        return 0
    else:
        return (weight * time_interval * lc.best_dist_to_ess[1]) / (1800 * lc.ss_distance)


def missing_area(time_interval, best_distance_to_ESS, ss_distance):
    p = best_distance_to_ESS / ss_distance
    return (weightFalling(p) * time_interval * best_distance_to_ESS) / (1800 * ss_distance)


def tot_lc_calc(res, t):
    """ Function to calculate final Leading Coefficient for pilots,
        that needs to be done when all tracks have been scored"""
    if res.ESS_time:
        '''nothing to do'''
        return res.fixed_LC
    elif res.result_type in ('abs', 'dnf', 'mindist') or not res.SSS_time:
        '''pilot did't make Start or has no track'''
        return 0

    '''pilot did not make ESS'''
    ss_distance = t.SS_distance / 1000

    best_dist_to_ess = (t.opt_dist_to_ESS - res.distance) / 1000  # in Km
    missing_time = t.max_time - res.best_distance_time
    landed_out = missing_area(missing_time, best_dist_to_ess, ss_distance)

    return res.fixed_LC + landed_out


def calculate_results(task):
    """ Method to get to final results:
            Task validity calculation: day_quality(task);
            Points Weights calculation: points_weight(task);
            Points Allocation: points_allocation(task);
        Methods that are not on the script, are recalled from main library (pwc or gap) """

    # dist_validity, time_validity, launch_validity, stop_validity, day_quality
    day_quality(task)

    # avail_dist_points, avail_time_points, avail_dep_points, avail_arr_points
    points_weight(task)

    # points allocation to pilots
    points_allocation(task)
