from factory import PostGenerationMethodCall, Sequence, Factory
from factory.faker import faker
import task
from route import Turnpoint
from datetime import date
from random import random
from myconn import Database
import comp


class DBFactory(Factory):
    """db factory"""
    class Meta:
        model = Database


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


class CompFactory(Factory):
    """Task factory"""
    class Meta:
        model = comp.Comp
