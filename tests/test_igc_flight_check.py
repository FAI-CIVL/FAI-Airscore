from track import Track
from datetime import datetime, date
from flight_result import Flight_result
from obj_factories import TurnpointFactory, TaskFactory


test_task_turnpoints = [TurnpointFactory(lat=45.7129, lon=9.93693, radius=400, how='exit', shape='circle', type='launch'),
                        TurnpointFactory(lat=45.7581, lon=9.96171, radius=2000, how='exit', type='speed'),
                        TurnpointFactory(lat=45.8325, lon=9.7675, radius=2000),
                        TurnpointFactory(lat=45.7129, lon=9.93693, radius=2500),
                        TurnpointFactory(lat=45.8296, lon=9.89672, radius=400),
                        TurnpointFactory(lat=45.8569, lon=10.1591, radius=15000),
                        TurnpointFactory(lat=45.698, lon=9.97001, radius=400, type='endspeed'),
                        TurnpointFactory(lat=45.6777, lon=9.94366, radius=400, type='goal')
                        ]

test_task = TaskFactory()
test_task.turnpoints = test_task_turnpoints
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


def test_track_read():
    test_track = Track.read_file('/app/tests/data/test_igc_1.igc', par_id=1)
    assert len(test_track.fixes) == 13856
    assert test_track.date == date(2019, 3, 9)
    assert test_track.gnss_alt_valid
    assert test_track.press_alt_valid
    assert test_track.flight.valid
    assert len(test_track.flight.fixes)
    assert test_track.flight.glider_type == 'OZONE Zeno'
    assert test_track.flight.date_timestamp == 1552089600.0


def test_track_flight_check():
    test_track = Track.read_file('/app/tests/data/test_igc_2.igc', par_id=1)
    test_result = Flight_result.check_flight(test_track.flight, test_task)
    assert int(test_result.distance_flown) == 64360
    assert test_result.best_waypoint_achieved == 'Goal'
    assert len(test_result.waypoints_achieved) == test_result.waypoints_made
    assert test_result.SSS_time == 41400
    assert test_result.ESS_time == 50555
    assert test_result.ESS_altitude == 880.0
    assert test_result.real_start_time == 41428
    assert test_result.flight_time == 12158.0
    assert test_result.waypoints_achieved[1] == ['TP01', 43947, 1445.0]