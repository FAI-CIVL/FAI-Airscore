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
formula_name = 'GAP2018'
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
    formula_distance=Preset(value='on', visible=True, editable=True),
    # Arrival Points: position, time, off
    formula_arrival=Preset(value='off', visible=True, editable=True),
    # Departure Points: on, leadout, off
    formula_departure=Preset(value='leadout', visible=True, editable=True),
    # Lead Factor: factor for Leadout Points calculation formula
    lead_factor=Preset(value=2.0, visible=True, editable=True),
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
    validity_min_time=Preset(value=3600, visible=True, editable=True),
    # Score back time for Stopped Tasks (minutes)
    score_back_time=Preset(value=300, visible=True, editable=True),
    # Jump the Gun: 1 or 0
    max_JTG=Preset(value=0, visible=True, editable=True),
    # Penalty per Jump the Gun second
    JTG_penalty_per_sec=Preset(value=None, visible=True, editable=True),
    # Type of Total Validity: ftv, all
    overall_validity=Preset(value='ftv', visible=True, editable=True),
    # FTV Parameter
    validity_param=Preset(value=0.75, visible=True, editable=True),
    # FTV Parameter Reference: day_quality, max_score
    validity_ref=Preset(value='day_quality', visible=True, editable=True),
    # Penalty when ESS but not Goal: default is 1 for PG and 0.2 for HG
    no_goal_penalty=Preset(value=1.0, visible=True, editable=True),
    # Glide Bonus for Stopped Task: default is 4 for PG and 5 for HG
    glide_bonus=Preset(value=4.0, visible=True, editable=True),
    # Waypoint radius tolerance for validation: FLOAT default is 0.1%
    tolerance=Preset(value=0.001, visible=True, editable=True),
    # Waypoint radius minimum tolerance (meters): INT default = 5
    min_tolerance=Preset(value=5, visible=True, editable=True),
    # Scoring Altitude Type: default is GPS for PG and QNH for HG
    scoring_altitude=Preset(value='GPS', visible=True, editable=True),
    # Decimals to be displayed in Task results: default is 0
    task_result_decimal=Preset(value=0, visible=False),
    # Decimals to be displayed in Comp results: default is 0
    comp_result_decimal=Preset(value=0, visible=False),
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
    validity_ref=Preset(value='day_quality', visible=True, editable=True),
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
    task_result_decimal=Preset(value=0, visible=False),
    # Decimals to be displayed in Comp results: default is 0
    comp_result_decimal=Preset(value=0, visible=False),
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
