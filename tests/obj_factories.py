from factory import Sequence, Factory
from factory.faker import faker
import task
from formula import TaskFormula
from pilot.participant import Participant
from pilot.pilot import Pilot
from pilot.track import Track
from pilot.flightresult import FlightResult
from pilot.notification import Notification
from route import Turnpoint
from random import random
from db.conn import db_session
import comp


class DBFactory(Factory):
    """db factory"""
    class Meta:
        model = db_session


class TaskFactory(Factory):
    """Task factory"""
    class Meta:
        model = task.Task


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


class CompFactory(Factory):
    """Comp factory"""
    class Meta:
        model = comp.Comp

    comp_id = 1


class TaskFormulaFactory(Factory):
    """TaskFormula factory"""
    class Meta:
        model = TaskFormula

    task_id = 1


class PilotFactory(Factory):
    """Pilot factory"""
    class Meta:
        model = Pilot


class TrackFactory(Factory):
    """Track factory"""
    class Meta:
        model = Track


class FlightResultFactory(Factory):
    """FlightResult factory"""
    class Meta:
        model = FlightResult


class ParticipantFactory(Factory):
    """Participant factory"""
    class Meta:
        model = Participant


class NotificationFactory(Factory):
    """Notification factory"""
    class Meta:
        model = Notification
