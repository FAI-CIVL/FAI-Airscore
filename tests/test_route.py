from route import in_goal_sector, cPoint, get_shortest_path, distance
from obj_factories import TurnpointFactory, TaskFactory
import math
from igc_lib import GNSSFix
from geo import Geo
import factory_objects

turnpoints = [
    TurnpointFactory(lat=41.3435, lon=21.2568, radius=400, how='entry', shape='circle', type='launch'),
    TurnpointFactory(lat=41.5778, lon=21.333, radius=22000, how='entry', shape='circle', type='speed'),
    TurnpointFactory(lat=41.5778, lon=21.333, radius=4000),
    TurnpointFactory(lat=41.2448, lon=21.5773, radius=3000),
    TurnpointFactory(lat=41.348, lon=21.3042, radius=3000, how='entry', shape='circle', type='endspeed'),
    TurnpointFactory(lat=41.348, lon=21.3042, radius=100, how='entry', shape='line', type='goal')
]

projected_line = [cPoint(x=-3906.90986083417, y=-6423.21345696099),
                  cPoint(x=-3996.3205467033026, y=-6602.114951142762),
                  cPoint(x=-3947.1426667070477, y=-6514.8994708094115),
                  cPoint(x=-4045.390364525586, y=-6465.428373867)]

test_task = factory_objects.test_task()
test_task.turnpoints = turnpoints
test_task.geo = Geo.from_coords(41.40665, 21.351416666666665)
test_task.projected_line = projected_line

short = GNSSFix(rawtime=1, lat=41.348016666666666, lon=21.304666666666666,
                validity=True, press_alt=1, gnss_alt=1, index=1, extras=None)
after_and_out = GNSSFix(rawtime=1, lat=41.34809381046268, lon=21.300493968601263,
                        validity=True, press_alt=1, gnss_alt=1, index=1, extras=None)
inside = GNSSFix(rawtime=1, lat=41.34809381046268, lon=21.303493968601263,
                 validity=True, press_alt=1, gnss_alt=1, index=1, extras=None)
line = GNSSFix(rawtime=1, lat=41.348, lon=21.3042,
               validity=True, press_alt=1, gnss_alt=1, index=1, extras=None)
meter_short_of_tolerance = GNSSFix(rawtime=1, lat=41.348, lon=21.30428,
                                   validity=True, press_alt=1, gnss_alt=1, index=1, extras=None)
short_but_tolerance = GNSSFix(rawtime=1, lat=41.348, lon=21.30425,
                              validity=True, press_alt=1, gnss_alt=1, index=1, extras=None)

goal_tp = TurnpointFactory(lat=41.348, lon=21.3042, radius=100)
previous_tp = TurnpointFactory(lat=41.2448, lon=21.5773)


def test_route_distance(task=test_task):
    task.calculate_task_length()
    assert math.isclose(task.distance, 94624.2, abs_tol=1)


def test_opt_route(task=test_task):
    task.calculate_optimised_task_length()
    assert math.isclose(task.opt_dist, 81506.1, abs_tol=1)
    assert math.isclose(task.opt_dist_to_SS, 4799.97, abs_tol=1)
    assert math.isclose(task.opt_dist_to_ESS, 78508.1, abs_tol=1)
    assert math.isclose(task.SS_distance, 73708.1, abs_tol=1)
    partial_distances = [0, 4799.9737887617, 23075.284840766, 58796.04787950, 78508.057227873, 81506.139470692]
    for idx, d in enumerate(task.partial_distance):
        assert math.isclose(d, partial_distances[idx], abs_tol=1)


def test_check_in_radius():
    # check in radius
    assert goal_tp.in_radius(short, 0, 0) is True
    assert goal_tp.in_radius(inside, 0, 0) is True
    assert goal_tp.in_radius(after_and_out, 0, 0) is False
    assert goal_tp.in_radius(line, 0, 0) is True


def test_in_goal_sector():
    assert in_goal_sector(test_task, short) is False
    assert in_goal_sector(test_task, after_and_out) is False
    assert in_goal_sector(test_task, inside) is True
    assert in_goal_sector(test_task, line) is True
    assert in_goal_sector(test_task, meter_short_of_tolerance) is False
    assert in_goal_sector(test_task, short_but_tolerance) is True
