"""
Scoring Formula Script
    Defines a Scoring formula. Gets Parameters and jobs from Formula Libraries in libs folder or contains new ones.
    Name of primary functions has to be maintained:
        - process_result : jobs done of FlightResult obj. before scoring
        - points_allocation : main function called to calculate scoring
    Defines which classes formula applies
    Defines standard parameters values for each class
"""
from formula import FormulaPreset, Preset
from formulas.libs.gap import *
from formulas.libs.leadcoeff import *

''' Formula Info'''
# Formula Name: usually the filename in capital letters
formula_name = 'GAP2023'
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

    # Editable part starts here
    # Distance Points: on, difficulty, off
    formula_distance=Preset(value='on', visible=True, editable=False),
    # Arrival Points: position, time, off
    formula_arrival=Preset(value='off', visible=False),
    # Departure Points: on, leadout, off
    formula_departure=Preset(value='leadout', visible=True, editable=False),
    # Lead Factor: factor for Leadout Points calculation formula [0 - 0.5, default 0.26]
    lead_factor=Preset(value=0.26, visible=True, editable=True),
    # Lead Coeff formula: classic, weighted, integrated
    lc_formula=Preset(value='weighted', visible=False),
    # Time Points: on, off
    formula_time=Preset(value='on', visible=True, editable=False),
    # SS distance calculation: launch_to_goal, launch_to_ess, sss_to_ess
    ss_dist_calc=Preset(value='launch_to_ess', visible=False),
    # Arrival Altitude Bonus: Bonus points factor on ESS altitude
    arr_alt_bonus=Preset(value=0, visible=True, editable=True, comment='default: disabled'),
    # ESS Min Altitude
    arr_min_height=Preset(value=None, visible=True, editable=True),
    # ESS Max Altitude
    arr_max_height=Preset(value=None, visible=True, editable=True),
    # Minimum flight time for task validation (minutes)
    validity_min_time=Preset(
        value=None, visible=True, editable=False, calculated=True, comment='calculated from nominal distance'
    ),
    # Score back time for Stopped Tasks (minutes)
    score_back_time=Preset(value=300, visible=True, editable=True, comment='default: 5 mins'),
    # Jump the Gun: 1 or 0
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
    task_result_decimal=Preset(value=1, visible=False),
    # Decimals to be displayed in Comp results: default is 0
    comp_result_decimal=Preset(value=1, visible=False),
)

hg_preset = FormulaPreset(
    # This part should not be edited
    formula_name=Preset(value=formula_name, visible=True, editable=True),

    # Editable part starts here
    # Distance Points: on, difficulty, off
    formula_distance=Preset(value='difficulty', visible=True, editable=True),
    # Arrival Points: position, time, off
    formula_arrival=Preset(value='position', visible=True, editable=True),
    # Departure Points: on, leadout, off
    formula_departure=Preset(value='leadout', visible=True, editable=True),
    # Lead Factor: factor for Leadout Points calculation formula
    lead_factor=Preset(value=1.0, visible=True, editable=True),
    # Lead Coeff formula: classic, weighted, integrated
    lc_formula=Preset(value='classic', visible=False),
    # Time Points: on, off
    formula_time=Preset(value='on', visible=True, editable=True),
    # SS distance calculation: launch_to_goal, launch_to_ess, sss_to_ess
    ss_dist_calc=Preset(value='launch_to_ess', visible=False),
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
    validity_param=Preset(value=1, visible=True, editable=True),
    # FTV Parameter Reference: day_quality, max_score
    validity_ref=Preset(value='max_score', visible=True, editable=True),
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
    task_result_decimal=Preset(value=1, visible=False),
    # Decimals to be displayed in Comp results: default is 0
    comp_result_decimal=Preset(value=1, visible=False),
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
    task.day_quality = min((task.stop_validity * task.launch_validity * task.dist_validity * task.time_validity), 1.000)


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

    ''' Distance Weight'''
    if task.formula.formula_distance != 'off':
        task.dist_weight = 0.9 - 1.665 * goal_ratio + 1.713 * goal_ratio ** 2 - 0.587 * goal_ratio ** 3

    if comp_class == 'HG':
        """
        DistWeight:         0.9 - 1.665* goalRatio + 1.713*GolalRatio^2 - 0.587*goalRatio^3
        LeadWeight:         (1 - DistWeight)/8 * 1.4 (lead_factor = 1)
        ArrWeight:          (1 - DistWeight)/8
        TimeWeight:         1 − DistWeight − LeadWeight − ArrWeight
        """

        ''' Arrival Weight'''
        if task.formula.formula_arrival != 'off':
            task.arr_weight = (1 - task.dist_weight) / 8
            if task.formula.formula_arrival == 'time':
                task.arr_weight *= 2  # (1 - dist_weight) / 4
        ''' Departure Weight'''
        if task.formula.formula_departure != 'off':
            task.dep_weight = (1 - task.dist_weight) / 8 * 1.4 * formula.lead_factor

    elif comp_class == 'PG':
        """
        DistWeight:
            In paragliding, the parameter LeadingTimeRatio is set for each task, 
            with a value between 0 and 50%, default is 26%. 
            This parameter defines the ratio between leading and time weight. 
            A value of 26% means that 26% of the weight not allocated to distance weight is allocated to leading weight, 
            and the remaining 74% to time weight.

        GoalRatio = 0: LeadingWeight = (1-DistanceWeight)
        GoalRatio > 0: LeadingWeight = (1-DistanceWeight)*LeadingTimeRatio
        ArrivalWeight=0

        TimeWeight:         1 − DistWeight − LeadWeight − ArrWeight
        """

        LeadingTimeRatio = task.formula.lead_factor
        ''' Departure Weight'''
        if task.formula.formula_departure != 'off':
            if goal_ratio == 0:
                task.dep_weight = 1 - task.dist_weight
            else:
                task.dep_weight = (1 - task.dist_weight) * LeadingTimeRatio

    ''' Time weight'''
    if task.formula.formula_departure != 'off':
        task.time_weight = 1 - task.dist_weight - task.dep_weight - task.arr_weight

    ''' Available Points'''
    task.avail_dist_points = 1000 * quality * task.dist_weight  # AvailDistPoints
    task.avail_dep_points = 1000 * quality * task.dep_weight  # AvailLeadPoints
    task.avail_arr_points = 1000 * quality * task.arr_weight  # AvailArrPoints
    task.avail_time_points = 1000 * quality * task.time_weight  # AvailTimePoints

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


def pilot_speed(task, res):
    """
    Args:
        task: Task obj.
        res: FlightResult object
    Time points are assigned to the pilot as a function of best time and pilot time – the time the pilot took
    to complete the speed section. Slow pilots will get zero points for speed if their time to complete the
    speed section is equal to or longer than the fastest time plus the square root of the fastest time.
    All times are measured in hours.

    GAP2020 has been amended. V2.0 has same formula for both HG and PG:
    SF = max(0, 1 - ((Ptime - MinTime)/sqrt(MinTime))**(5/6))
    """
    if not res.ESS_time:
        return 0
    Aspeed = task.avail_time_points

    # 11.2 Time points
    ''' min speed section time
        If no goal penalty = 100% (PG): min ss_time if goal
    '''
    if task.formula.no_goal_penalty < 1 or (task.stopped_time and not task.fastest_in_goal):
        Tmin = task.fastest / 3600  # decimal hours
    else:
        Tmin = task.fastest_in_goal / 3600 or 0

    Ptime = res.ss_time / 3600  # decimal hours
    if Ptime < Tmin:
        # in fastest_in_goal condition, pilot was faster than first in goal, if not checked it will cause exception
        return 0
    SF = max(0, 1 - ((Ptime - Tmin) / sqrt(Tmin)) ** (5 / 6))
    Pspeed = Aspeed * SF - task.time_points_reduction if SF > 0 else 0

    return Pspeed


def points_allocation(task):
    """ Get task with pilots FlightResult obj. and calculates results"""

    ''' Get pilot.result not ABS or DNF '''
    results = task.valid_results
    formula = task.formula

    if task.formula.formula_distance == 'difficulty':
        '''Difficulty Calculation'''
        task.difficulty = difficulty_calculation(task)

    ''' Calculate Min Dist Score '''
    min_dist_score = calculate_min_dist_score(task)

    ''' Score each pilot now'''
    for res in results:

        '''initialize'''
        res.distance_score = 0
        res.time_score = 0
        res.arrival_score = 0
        res.departure_score = 0
        res.penalty = 0

        if res.result_type == 'mindist':
            res.distance_score = min_dist_score
        else:
            '''Pilot distance score'''
            res.distance_score = pilot_distance(task, res)

            ''' Pilot leading points'''
            if task.departure == 'leadout' and res.SSS_time:
                res.departure_score = pilot_leadout(task, res)

            if res.ESS_time:
                ''' Pilot speed points'''
                res.time_score = pilot_speed(task, res)

                ''' Pilot departure points'''
                if task.departure == 'departure' and res.SSS_time:
                    # does it even still exist dep. points?
                    res.departure_score = pilot_departure(task, res)

                ''' Pilot arrival points'''
                if not (task.arrival == 'off'):
                    res.arrival_score = pilot_arrival(task, res)

                ''' Penalty for not making goal'''
                if not res.goal_time:
                    res.goal_time = 0
                    res.time_score *= 1 - formula.no_goal_penalty
                    res.arrival_score *= 1 - formula.no_goal_penalty

        ''' Total score'''
        score = res.distance_score + res.time_score + res.arrival_score + res.departure_score

        ''' Apply Penalty'''
        if res.jtg_penalty or res.flat_penalty or res.percentage_penalty:
            """Jump the Gun Penalty:
            totalScore p = max(totalScore p − jumpTheGunPenalty p , scoreForMinDistance)"""
            score_after_jtg = score if res.jtg_penalty == 0 else max(min_dist_score, score - res.jtg_penalty)
            ''' Other penalties'''
            # applying flat penalty after percentage ones
            other_penalty = score_after_jtg * res.percentage_penalty + res.flat_penalty
            res.score = max(0, score_after_jtg - other_penalty)
            res.penalty = score - res.score
            # print(f'jtg: {res.jtg_penalty}, flat: {res.flat_penalty}, perc: {res.percentage_penalty}')
            # print(f'pre penalty: {score}, after jtg: {score_after_jtg}, penalty: {res.penalty}, score: {res.score}')
        else:
            res.score = score


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
