"""
Scoring Formula Script
    Defines a Scoring formula. Gets Parameters and jobs from Formula Libraries in libs folder or contains new ones.
    Name of primary functions has to be mantained:
        - process_result : jobs done of Flight_result obj. before scoring
        - points_allocation : main function called to calculate scoring
    Defines which classes formula applies
    Defines standard parameters values for each class
"""
from formulas.libs.pwc import *
from formula import FormulaPreset, Preset
from formulas.libs.leadcoeff import lead_coeff_function, tot_lc_calc


''' Formula Info'''
# Formula Name: usually the filename in capital letters
formula_name = 'PWC2017'
# Formula Type: pwc, gap, aat, any formula in libs folder
formula_type = 'pwc'
# Formula Version: INT, usually identified with year
formula_version = '2017'
# Comp Class: PG, HG, BOTH
formula_class = 'PG'

''' Default Formula presets
    pg_preset: PG default values, if formula applies for PG or mixed
    hg_preset: HG default values, if formula applies for HG or mixed'''
# TODO should have switch for each parameter to be editable or not in frontend

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
    lead_squared_distance=Preset(value=True, visible=False),
    # Time Points: on, off
    formula_time=Preset(value='on', visible=False),
    # Arrival Altitude Bonus: Bonus points factor on ESS altitude
    arr_alt_bonus=Preset(value=0, visible=False),
    # ESS Min Altitude
    arr_min_height=Preset(value=None, visible=False),
    # ESS Max Altitude
    arr_max_height=Preset(value=None, visible=False),
    # Minimum flight time for task validation (minutes)
    validity_min_time=Preset(value=60, visible=True, editable=True),
    # Score back time for Stopped Tasks (minutes)
    score_back_time=Preset(value=5, visible=True, editable=True),
    # Max allowed Jump the Gun (seconds)
    max_JTG=Preset(value=0, visible=False),
    # Penalty per Jump the Gun second
    JTG_penalty_per_sec=Preset(value=None, visible=False),
    # Type of Total Validity: ftv, all
    overall_validity=Preset(value='ftv', visible=True, editable=True),
    # FTV Parameter
    validity_param=Preset(value=0.75, visible=True, editable=True),
    # Penalty when ESS but not Goal: default is 1 for PG and 0.2 for HG
    no_goal_penalty=Preset(value=1.0, visible=False),
    # Glide Bonus for Stopped Task: default is 4 for PG and 5 for HG
    glide_bonus=Preset(value=4.0, visible=False),
    # Waypoint radius tolerance for validation: FLOAT default is 0.1%
    tolerance=Preset(value=0.005, visible=True, editable=True),
    # Waypoint radius minimum tolerance (meters): INT default = 5
    min_tol=Preset(value=5, visible=True, editable=True),
    # Scoring Altitude Type: default is GPS for PG and QNH for HG
    scoring_altitude=Preset(value='GPS', visible=True, editable=True)
)


def points_weight(task):
    comp_class = task.comp_class  # HG / PG
    formula = task.formula
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
    ''' PWC 2017: LeadPoints augmented by 50'''
    task.avail_dep_points = 1000 * quality * task.dep_weight  # AvailLeadPoints
    task.avail_dep_points += 50  # PWC2017 Augmented LeadPoints

    task.avail_arr_points = 0  # AvailArrPoints
    task.avail_time_points = 1000 * quality - task.avail_dep_points - task.avail_dist_points  # AvailSpeedPoints


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


# def points_allocation(task):
#     """ Get task with pilots Flight_result obj. and calculates results"""
#
#     ''' Get pilots not ABS or DNF '''
#     results = task.valid_results
#     formula = task.formula
#
#     ''' Get basic GAP allocation values'''
#     # dist_validity, time_validity, launch_validity, stop_validity, day_quality
#     day_quality(task)
#     # avail_dist_points, avail_time_points, avail_dep_points, avail_arr_points
#     points_weight(task)
#     # task.max_score = 0      # max_score is evaluated without penalties. Is it correct?
#
#     ''' Score each pilot now'''
#     for res in results:
#         penalty = res.penalty if res.penalty else 0
#
#         '''initialize'''
#         res.distance_score = 0
#         res.time_score = 0
#         res.arrival_score = 0
#         res.departure_score = 0
#
#         '''Pilot distance score'''
#         res.distance_score = pilot_distance(task, res)
#
#         ''' Pilot leading points'''
#         if task.departure == 'leadout' and res.result_type != 'mindist' and res.SSS_time:
#             res.departure_score = pilot_leadout(task, res)
#
#         if res.ESS_time > 0:
#             ''' Pilot speed points'''
#             res.time_score = pilot_speed(task, res)
#
#             ''' Penalty for not making goal'''
#             if not res.goal_time:
#                 res.goal_time = 0
#                 res.time_score *= (1 - formula.no_goal_penalty)
#
#         ''' Total score'''
#         res.score = res.distance_score + res.time_score + res.arrival_score + res.departure_score
#
#         ''' Apply Penalty'''
#         if penalty:
#             res.score = max(0, res.score - penalty)
