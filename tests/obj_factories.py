from factory import PostGenerationMethodCall, Sequence, Factory
from factory.faker import faker
import task
from route import Turnpoint
from datetime import date
from random import random

class TaskFactory(Factory):
    """Task factory"""
    class Meta:
        model = task.Task

    task_id = 1
    comp_id = 1


class TurnpointFactory(Factory):
    """Turnpoint factory"""
    class Meta:
        model = Turnpoint


    name = Sequence(lambda n: f"TP{n}")
    description = faker.Faker().sentence(nb_words=4)
    altitude = int(random()*1000)
    shape = 'circle'
    type = 'waypoint'
    how = 'entry'


test_task_turnpoints = [TurnpointFactory(lat = 45.7129, lon = 9.93693, radius = 400, how = 'exit', shape = 'circle', type = 'launch'),
                        TurnpointFactory(lat = 45.7581, lon = 9.96171, radius = 2000, how = 'exit', type = 'speed'),
                        TurnpointFactory(lat = 45.8325, lon = 9.7675, radius = 2000),
                        TurnpointFactory(lat = 45.7129, lon = 9.93693, radius = 2500),
                        TurnpointFactory(lat = 45.8296, lon = 9.89672, radius = 400),
                        TurnpointFactory(lat = 45.8569, lon = 10.1591, radius = 15000),
                        TurnpointFactory(lat = 45.698, lon = 9.97001, radius = 400, type = 'endspeed'),
                        TurnpointFactory(lat = 45.6777, lon = 9.94366, radius = 400, type = 'goal')
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
