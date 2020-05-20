from datetime import datetime, date
from result import TaskResult
from obj_factories import TurnpointFactory, TaskFactory, TaskFormulaFactory, PilotFactory, ParticipantFactory, \
    FlightResultFactory, NotificationFactory, TrackFactory

test_task_turnpoints = [
    TurnpointFactory(lat=45.7129, lon=9.93693, radius=400, how='exit', shape='circle', type='launch'),
    TurnpointFactory(lat=45.7581, lon=9.96171, radius=2000, how='exit', type='speed'),
    TurnpointFactory(lat=45.8325, lon=9.7675, radius=2000),
    TurnpointFactory(lat=45.8569, lon=10.1591, radius=15000),
    TurnpointFactory(lat=45.698, lon=9.97001, radius=400, type='endspeed'),
    TurnpointFactory(lat=45.6777, lon=9.94366, radius=400, type='goal')
]

dummy1 = PilotFactory(info=ParticipantFactory(ID=1, par_id=1, civl_id=1, name='Dummy 1', nat='NAT',
                                              sex='M', glider='Dummy Glider', sponsor='Dummy Sponsor', nat_team=1),
                      track=TrackFactory(track_id=1, track_file='trackfile1.igc'),
                      result=FlightResultFactory(first_time=37488, real_start_time=41585,
                                                 SSS_time=41400, ESS_time=49228,
                                                 goal_time=49574, last_time=49574,
                                                 fixed_LC=192078.500659298, lead_coeff=1.447741539180286,
                                                 distance_flown=81506.1394706916, last_altitude=983))
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
penalty = 0.0,
dummy1.notifications = []
dummy1.still_flying_at_deadline = False
dummy1.time_after = 569

test_formula = TaskFormulaFactory()
test_formula.formula_name = 'TEST2020'
test_formula.formula_type = 'test'
test_formula.formula_version = 2020
test_formula.overall_validity = 'ftv'
test_formula.validity_param = 0.75
test_formula.formula_distance = 'on'
test_formula.formula_arrival = 'off'
test_formula.formula_departure = 'leadout'
test_formula.lead_factor = 1.0
test_formula.formula_time = 'on'
test_formula.arr_alt_bonus = 0.0
test_formula.arr_min_height = None
test_formula.arr_max_height = None
test_formula.validity_min_time = 3600
test_formula.score_back_time = 300
test_formula.max_JTG = 0
test_formula.JTG_penalty_per_sec = None
test_formula.nominal_goal = 0.3
test_formula.nominal_dist = 60000
test_formula.nominal_time = 5400
test_formula.nominal_launch = 0.96
test_formula.min_dist = 4000
test_formula.no_goal_penalty = 1.0
test_formula.glide_bonus = 4.0
test_formula.tolerance = 0.001
test_formula.min_tolerance = 5
test_formula.scoring_altitude = 'GPS'
test_formula.task_result_decimal = 0
test_formula.comp_result_decimal = 0
test_formula.team_scoring = 0
test_formula.team_size = 2
test_formula.max_team_size = None
test_formula.country_scoring = 1
test_formula.country_size = 2
test_formula.max_country_size = 4

test_task = TaskFactory()
test_task.turnpoints = test_task_turnpoints
test_task.formula = test_formula
test_task.partial_distance = [0.0, 4799.9737887617, 23075.284840766, 58796.04787950, 78508.057227872, 81506.13947069]
test_task.pilots = [dummy1]
test_task.date = date(2019, 6, 15)
test_task.window_open_time = 28800
test_task.window_close_time = 46800
test_task.check_launch = 'off'
test_task.start_time = 41400
test_task.start_close_time = 46800
test_task.SS_interval = 0
test_task.task_deadline = 57600
test_task.stopped_time = None
test_task.task_type = 'race'
test_task.distance = 101297.0
test_task.opt_dist = 64360.4
test_task.opt_dist_to_SS = 4121.53
test_task.opt_dist_to_ESS = 61374.1
test_task.SS_distance = 57252.6
test_task.time_offset = 7200
test_task.tolerance = 0.001
test_task.QNH = 1013.25


def test_result_file(task=test_task):
    result = task.create_json_elements()
    formula = result['formula']
    for key in TaskResult.formula_list:
        assert formula[key] == getattr(test_formula, key)
    info = result['info']
    for key in [k for k in TaskResult.info_list if k != 'date']:
        assert info[key] == getattr(test_task, key)
    stats = result['stats']
    for key in TaskResult.stats_list:
        assert stats[key] == getattr(test_task, key)
    results = result['results']
    for pilot in results:
        el = next(p for p in task.pilots if p.info.ID == pilot['ID'])
        for key in TaskResult.results_list:
            if hasattr(el.result, key):
                assert pilot[key] == getattr(el.result, key)
            elif hasattr(el.track, key):
                assert pilot[key] == getattr(el.track, key)
            elif hasattr(el.info, key):
                assert pilot[key] == getattr(el.info, key)
