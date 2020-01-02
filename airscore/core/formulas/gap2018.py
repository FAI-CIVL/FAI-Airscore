"""
Scoring Formula Script
    Defines a Scoring formula. Gets Parameters and jobs from Formula Libraries in libs folder or contains new ones.
    Name of primary functions has to be mantained:
        - process_result : jobs done of Flight_result obj. before scoring
        - points_allocation : main function called to calculate scoring
    Defines which classes formula applies
    Defines standard parameters values for each class
"""
from formulas.libs.gap import *
from formula import FormulaPreset, Preset

''' Formula Info'''
# Formula Name: usually the filename in capital letters
formula_name = 'GAP2018'
# Formula Type: pwc, gap, aat, any formula in libs folder
formula_type = 'gap'
# Formula Version: INT, usually identified with year
formula_version = '2018'
# Comp Class: PG, HG, BOTH
formula_class = 'BOTH'

''' Default Formula presets
    pg_preset: PG default values, if formula applies for PG or mixed
    hg_preset: HG default values, if formula applies for HG or mixed'''
# TODO should have switch for each parameter to be editable or not in frontend

pg_preset = FormulaPreset(
    # This part should not be edited
    formula_name=Preset(value=formula_name, visible=True, editable=True),
    formula_type=Preset(value=formula_type, visible=True, editable=True),
    formula_version=Preset(value=formula_version, visible=True, editable=True),

    # Editable part starts here
    # Distance Points: on, difficulty, off
    formula_distance=Preset(value='on', visible=True, editable=True),
    # Arrival Points: position, time, off
    formula_arrival=Preset(value='off', visible=True, editable=True),
    # Departure Points: on, leadout, off
    formula_departure=Preset(value='leadout', visible=True, editable=True),
    # Lead Factor: factor for Leadou Points calculation formula
    lead_factor=Preset(value=2.0, visible=True, editable=True),
    # Time Points: on, off
    formula_time=Preset(value='on', visible=True, editable=True),
    # Arrival Altitude Bonus: Bonus points factor on ESS altitude
    arr_alt_bonus=Preset(value=0, visible=True, editable=True),
    # ESS Min Altitude
    arr_min_height=Preset(value=None, visible=True, editable=True),
    # ESS Max Altitude
    arr_max_height=Preset(value=None, visible=True, editable=True),
    # Minimum flight time for task validation (minutes)
    validity_min_time=Preset(value=60, visible=True, editable=True),
    # Score back time for Stopped Tasks (minutes)
    score_back_time=Preset(value=5, visible=True, editable=True),
    # Jump the Gun: 1 or 0
    max_JTG=Preset(value=0, visible=True, editable=True),
    # Penalty per Jump the Gun second
    JTG_penalty_per_sec=Preset(value=None, visible=True, editable=True),
    # Type of Total Validity: ftv, all
    overall_validity=Preset(value='ftv', visible=True, editable=True),
    # FTV Parameter
    validity_param=Preset(value=0.75, visible=True, editable=True),
    # Penalty when ESS but not Goal: default is 1 for PG and 0.2 for HG
    no_goal_penalty=Preset(value=1.0, visible=True, editable=True),
    # Glide Bonus for Stopped Task: default is 4 for PG and 5 for HG
    glide_bonus=Preset(value=4.0, visible=True, editable=True),
    # Waypoint radius tolerance for validation: FLOAT default is 0.1%
    tolerance=Preset(value=0.001, visible=True, editable=True),
    # Scoring Altitude Type: default is GPS for PG and QNH for HG
    scoring_altitude=Preset(value='GPS', visible=True, editable=True)
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
    # Time Points: on, off
    formula_time=Preset(value='on', visible=True, editable=True),
    # Arrival Altitude Bonus: Bonus points factor on ESS altitude
    arr_alt_bonus=Preset(value=0, visible=True, editable=True),
    # ESS Min Altitude
    arr_min_height=Preset(value=None, visible=True, editable=True),
    # ESS Max Altitude
    arr_max_height=Preset(value=None, visible=True, editable=True),
    # Minimum flight time for task validation (minutes)
    validity_min_time=Preset(value=90, visible=True, editable=True),
    # Score back time for Stopped Tasks (minutes)
    score_back_time=Preset(value=15, visible=True, editable=True),
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
    # Scoring Altitude Type: default is GPS for PG and QNH for HG
    scoring_altitude=Preset(value='QNH', visible=True, editable=True)
)
