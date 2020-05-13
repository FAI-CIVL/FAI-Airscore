from route import in_semicircle
from obj_factories import TurnpointFactory, TaskFactory
from igc_lib import GNSSFix

turnpoints = [
    TurnpointFactory(lat=41.3435, lon=21.2568, radius=400, how='entry', shape='circle', type='launch'),
    TurnpointFactory(lat=41.5778, lon=21.333, radius=22000, how='entry', shape='circle', type='speed'),
    TurnpointFactory(lat=41.5778, lon=21.333, radius=4000),
    TurnpointFactory(lat=41.2448, lon=21.5773, radius=3000),
    TurnpointFactory(lat=41.348, lon=21.3042, radius=3000, how='entry', shape='circle', type='endspeed'),
    TurnpointFactory(lat=41.348, lon=21.3042, radius=100, how='entry', shape='line', type='goal')
]

in_radius_out_semi = GNSSFix(rawtime=1, lat=41.348016666666666, lon=21.304666666666666, validity=True, press_alt=1,
                             gnss_alt=1, index=1, extras=None)
in_radius_in_semi = GNSSFix(rawtime=1, lat=41.34801563537799, lon=21.304082328240966, validity=True, press_alt=1,
                            gnss_alt=1, index=1, extras=None)
out_radius = GNSSFix(rawtime=1, lat=41.34809381046268, lon=21.303493968601263, validity=True, press_alt=1, gnss_alt=1,
                     index=1, extras=None)

goal_tp = TurnpointFactory(lat=41.348016666666666, lon=21.304666666666666, radius=50)
previous_tp = TurnpointFactory(lat=41.2448, lon=21.5773)

# check in radius
assert goal_tp.in_radius(in_radius_in_semi, 0, 0) is True
assert goal_tp.in_radius(in_radius_out_semi, 0, 0) is True
assert goal_tp.in_radius(out_radius, 0, 0) is False
waypoint_list = [previous_tp, goal_tp]
assert in_semicircle(waypoint_list, 1, in_radius_in_semi) is True
assert in_semicircle(waypoint_list, 1, in_radius_out_semi) is False

# using task wpt list
assert in_semicircle(turnpoints, 5, in_radius_out_semi) is False
assert in_semicircle(turnpoints, 5, in_radius_in_semi) is True
assert in_semicircle(turnpoints, 5, out_radius) is False
