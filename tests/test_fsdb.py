import fsdb
import datetime
from pathlib import Path

test_file = Path('/app/tests/data/test_sm20c5.fsdb')


def test_fsdb_import():
    """testing FSDB importing Routine"""
    test_content = fsdb.FSDB.read(test_file)
    '''comp'''
    assert test_content.comp.comp_name == 'Spring Meeting 2020 (Class 5)'
    assert test_content.comp.comp_class == 'HG'
    assert test_content.comp.date_from == datetime.date(2020, 9, 10)
    '''comp formula'''
    assert test_content.comp.formula.formula_name == 'GAP2020'
    assert test_content.comp.formula.formula_distance == 'difficulty'
    assert test_content.comp.formula.formula_arrival == 'position'
    assert test_content.comp.formula.formula_departure == 'leadout'
    assert test_content.comp.formula.lead_factor == 1.0
    assert test_content.comp.formula.overall_validity == 'all'
    assert test_content.comp.formula.nominal_dist / 1000 == 70  # km
    assert test_content.comp.formula.validity_min_time / 60 == 45  # min
    assert test_content.comp.formula.tolerance * 100 == 0.1  # percentage

    assert len(test_content.tasks) == 4
    '''task'''
    test_task = test_content.tasks[1]
    assert test_task.task_name == 'Task 2'
    assert test_task.date == datetime.date(2020, 9, 11)
    assert test_task.task_type == 'race'
    assert test_task.start_time == 40500
    assert test_task.formula.max_JTG / 60 == 5  # min
    assert len(test_task.pilots) == 11
    assert test_task.pilots_goal == 8
    assert test_task.max_score == 1000

    '''pilot'''
    test_pilot = test_task.pilots[10]
    assert test_pilot.ID == 513
    assert test_pilot.name == 'Christian Kamm'
    assert test_pilot.result_type == 'goal'
    assert test_pilot.ESS_time == 51341
    assert test_pilot.score == 639.2
