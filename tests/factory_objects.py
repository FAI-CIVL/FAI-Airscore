from obj_factories import TaskFormulaFactory, TaskFactory, CompFactory, TurnpointFactory, PilotFactory, \
    ParticipantFactory, FlightResultFactory, TrackFactory
from datetime import date
import random


def test_turnpoints():
    return [
        TurnpointFactory(wpt_id=1, name='D05', lat=45.7129, lon=9.93693, radius=400, how='exit', type='launch'),
        TurnpointFactory(wpt_id=2, name='B67', lat=45.7581, lon=9.96171, radius=2000, how='exit', type='speed'),
        TurnpointFactory(wpt_id=3, name='B66', lat=45.8325, lon=9.7675, radius=2000),
        TurnpointFactory(wpt_id=4, name='D05', lat=45.7129, lon=9.93693, radius=2500),
        TurnpointFactory(wpt_id=5, name='D08', lat=45.8296, lon=9.89672, radius=400),
        TurnpointFactory(wpt_id=6, name='P20', lat=45.8569, lon=10.1591, radius=15000),
        TurnpointFactory(wpt_id=7, name='B49', lat=45.698, lon=9.97001, radius=400, type='endspeed'),
        TurnpointFactory(wpt_id=8, name='A02', lat=45.6777, lon=9.94366, radius=400, type='goal')
    ]


def test_partial_distance():
    return [0.0, 4121.5290048586, 18299.550792762, 32644.873379435, 43224.796706005, 50978.622027629,
            61374.106444253, 64360.424222856]


def test_formula():
    f = TaskFormulaFactory()
    f.formula_name = 'PWC2016'
    f.overall_validity = 'ftv'
    f.validity_param = 0.75
    f.formula_distance = 'on'
    f.formula_arrival = 'off'
    f.formula_departure = 'leadout'
    f.lead_factor = 1.0
    f.formula_time = 'on'
    f.arr_alt_bonus = 0.0
    f.arr_min_height = None
    f.arr_max_height = None
    f.validity_min_time = 3600
    f.score_back_time = 300
    f.max_JTG = 0
    f.JTG_penalty_per_sec = None
    f.nominal_goal = 0.3
    f.nominal_dist = 60000
    f.nominal_time = 5400
    f.nominal_launch = 0.96
    f.min_dist = 4000
    f.no_goal_penalty = 1.0
    f.glide_bonus = 4.0
    f.tolerance = 0.001
    f.min_tolerance = 5
    f.scoring_altitude = 'GPS'
    f.task_result_decimal = 0
    f.comp_result_decimal = 0
    f.team_scoring = 0
    f.team_size = 2
    f.max_team_size = None
    f.country_scoring = 1
    f.country_size = 2
    f.max_country_size = 4
    return f


def test_task():
    t = TaskFactory()
    t.turnpoints = test_turnpoints()
    t.partial_distance = test_partial_distance()
    t.formula = test_formula()
    t.comp_id = 1
    t.task_id = 1
    t.date = date(2019, 6, 15)
    t.window_open_time = 28800
    t.window_close_time = 46800
    t.check_launch = 'off'
    t.start_time = 41400
    t.start_close_time = 46800
    t.SS_interval = 0
    t.task_deadline = 57600
    t.stopped_time = None
    t.task_type = 'race'
    t.distance = 101297.0
    t.opt_dist = 64360.4
    t.opt_dist_to_SS = 4121.53
    t.opt_dist_to_ESS = 61374.1
    t.SS_distance = 57252.6
    t.time_offset = 7200
    t.tolerance = 0.001
    t.QNH = 1013.25
    return t


def dummy_pilot():
    dummy1 = FlightResultFactory(
        ID=1, par_id=1, civl_id=1, name='Dummy 1', nat='NAT', sex='M', glider='Dummy Glider', sponsor='Dummy Sponsor',
        nat_team=1, track_id=1, track_file='trackfile1.igc', first_time=37488, real_start_time=41585, SSS_time=41400,
        ESS_time=49228, goal_time=49574, last_time=49574, fixed_LC=192078.500659298, lead_coeff=1.447741539180286,
        distance_flown=81506.1394706916, last_altitude=983
    )
    dummy1.ESS_rank = 111
    dummy1.speed = 33.8974323429738
    dummy1.best_distance_time = 49574
    dummy1.waypoints_achieved = []
    dummy1.total_distance = 81506.1394706916
    dummy1.max_altitude = 2772
    dummy1.ESS_altitude = 972
    dummy1.goal_altitude = 983
    dummy1.landing_time = 49761
    dummy1.landing_altitude = 634
    dummy1.result_type = 'goal'
    dummy1.score = 887.9918762489334
    dummy1.departure_score = 126.40468300276432
    dummy1.arrival_score = 0
    dummy1.distance_score = 360.9733620740743
    dummy1.time_score = 400.6138311720949
    dummy1.penalty = 0.0
    dummy1.notifications = []
    dummy1.still_flying_at_deadline = False
    dummy1.time_after = 569
    return dummy1


def simulate_pilot(task: TaskFactory, result_type: str = 'lo') -> FlightResultFactory:
    """create a random pilot fligtResult based on task and result type"""
    if not task:
        task = test_task()

    ID = random.randint(1, 999)
    dummy = FlightResultFactory(
        ID=ID,
        par_id=random.randint(1, 999),
        civl_id=random.randint(1, 99999),
        name=f'Dummy {ID}',
        nat='NAT', sex='M',
        glider='Dummy Glider',
        sponsor='Dummy Sponsor',
        nat_team=1,
        track_id=random.randint(1, 99999),
        track_file=f'trackfile{ID}.igc',
        first_time=task.window_open_time,
        real_start_time=0,
        SSS_time=0,
        ESS_time=0,
        goal_time=0,
        fixed_LC=0,
        last_altitude=100
    )

    dummy.result_type = result_type
    if result_type == 'goal':
        dummy.real_start_time = task.start_time+random.randint(0, 119)
        dummy.SSS_time = task.start_time
        dummy.ESS_time = random.randint(task.start_time+3600, task.task_deadline-300)
        dummy.goal_time = dummy.ESS_time + 240
        dummy.last_time = dummy.goal_time
        dummy.fixed_LC = random.randint(100000, 200000)
        dummy.distance_flown = task.opt_dist
    elif result_type == 'lo':
        dummy.distance_flown = round(random.uniform(500, task.opt_dist - 1), 1)
        if dummy.distance_flown > task.opt_dist_to_SS:
            dummy.real_start_time = task.start_time + random.randint(0, 119)
            dummy.SSS_time = task.start_time
            dummy.fixed_LC = random.randint(200000, 400000)
        if dummy.distance_flown > task.opt_dist_to_ESS:
            dummy.ESS_time = random.randint(task.start_time+3600, task.task_deadline-300)
        dummy.last_time = random.randint(max(dummy.ESS_time, dummy.real_start_time, dummy.first_time),
                                         task.task_deadline)
    else:
        dummy.distance_flown = round(random.uniform(500, task.formula.min_dist - 1), 1)
        dummy.last_time = random.randint(dummy.first_time+100, task.task_deadline)
        dummy.result_type = 'lo'
    dummy.max_altitude = random.randint(1000, 2453)
    dummy.landing_time = dummy.last_time

    return dummy
