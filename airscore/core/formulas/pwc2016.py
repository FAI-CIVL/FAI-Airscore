from collections import namedtuple
from formulas.libs.pwc import *
from formula import Preset

'''type validity of formula'''
formula_validity = {
    'PG': True,
    'HG': False
}

'''Default Formula presets'''
# TODO should have switch for each parameter to be editable or not in frontend
pg_preset = Preset(
    # Formula Name
    formula_name='PWC2016',
    # Formula Type: pwc, gap, aat, nay formula in libs folder
    formula_type='pwc',
    # Formula Version: INT, usually identified with year
    formula_version='2016',
    # Comp Class: PG, HG,
    comp_class='PG',
    # Distance Points: on, difficulty, off
    formula_distance='on',
    # Arrival Points: position, time, off
    formula_arrival='off',
    # Departure Points: on, leadout, off
    formula_departure='leadout',
    # Lead Factor: factor for Leadou Points calculation formula
    lead_factor=1.0,
    # Time Points: on, off
    formula_time='on',
    # Arrival Altitude Bonus: Bonus points factor on ESS altitude
    arr_alt_bonus=0,
    # ESS Min Altitude
    arr_min_height=None,
    # ESS Max Altitude
    arr_max_height=None,
    # Minimum flight time for task validation (minutes)
    validity_min_time=60,
    # Score back time for Stopped Tasks (minutes)
    score_back_time=5,
    # Jump the Gun: 1 or 0
    jump_the_gun=0,
    # Max allowed Jump the Gun (seconds)
    max_JTG=None,
    # Penalty per Jump the Gun second
    JTG_penalty_per_sec=None,
    # Type of Total Validity: ftv, all
    overall_validity='ftv',
    # FTV Parameter
    validity_param=0.75,
    # Penalty when ESS but not Goal: default is 1 for PG and 0.2 for HG
    no_goal_penalty=1.0,
    # Glide Bonus for Stopped Task: default is 4 for PG and 5 for HG
    glide_bonus=4.0,
    # Waypoint radius tolerance for validation: FLOAT default is 0.1%
    tolerance=0.002,
    # Scoring Altitude Type: default is GPS for PG and QNH for HG
    scoring_altitude='GPS'
)
