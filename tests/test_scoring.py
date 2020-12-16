import obj_factories
import json
import math
from pathlib import Path


def create_test_task(data: dict) -> obj_factories.TaskFactory:
    task = obj_factories.TaskFactory()
    task.as_dict().update(data.get('info'))
    formula = obj_factories.TaskFormulaFactory(task_id=1)
    formula.as_dict().update(data.get('formula'))
    task.formula = formula
    task.opt_dist_to_SS = 863.525
    task.opt_dist_to_ESS = 84760.5
    return task


def create_test_pilots(data: dict) -> list:
    res = data.get('results')
    pilots = []
    for r in res:
        pilot = obj_factories.FlightResultFactory()
        pilot.as_dict().update(r)
        pilots.append(pilot)
    return pilots


def read_test_results() -> tuple:
    file = Path('/app/tests/data/test_results.json')
    with open(file, 'r') as f:
        content = json.load(f)
    task = create_test_task(content)
    pilots = create_test_pilots(content)
    return task, pilots


def simulate_difficulty_calc(task: obj_factories.TaskFactory, res: list) -> list:
    lib = task.formula.get_lib()
    task.pilots = res
    return lib.difficulty_calculation(task)


def test_diff_calc():
    """testing Difficulty Calculation Routine"""
    test_task, pilots = read_test_results()

    '''no pilots'''
    empty = []
    diff = simulate_difficulty_calc(test_task, empty)
    kmx10 = int(test_task.formula.min_dist/100)
    kmx10r = int((kmx10 + 10) / 10) * 10
    assert len(diff) == kmx10r
    assert diff[kmx10 + 1].diff_score == 0.5

    '''one pilot in goal, no pilot landed out'''
    one_in_goal = [pilots[0]]
    print(f'one in goal pilots: {len(one_in_goal)}')
    diff = simulate_difficulty_calc(test_task, one_in_goal)
    assert len(diff) == kmx10r
    assert diff[kmx10 + 1].diff_score == 0.5

    '''all pilots'''
    print(f'all pilots: {len(pilots)}')
    diff = simulate_difficulty_calc(test_task, pilots)
    lo_pilots = [p for p in pilots if p.result_type == 'lo']
    best_dist_lo = max(max([p.distance for p in lo_pilots], default=0), test_task.formula.min_dist)
    kmx10 = int(best_dist_lo / 100)
    kmx10r = int((kmx10 + 10) / 10) * 10
    assert len(diff) == kmx10r
    assert diff[kmx10 + 1].diff_score == 0.5
    assert diff[kmx10 - 1].diff_score < 0.5

    '''only pilots not in goal'''
    not_in_goal = [p for p in pilots if not p.result_type == 'goal']
    print(f'only not in goal pilots: {len(not_in_goal)}')
    diff = simulate_difficulty_calc(test_task, not_in_goal)
    best_dist_lo = max(max([p.distance for p in not_in_goal], default=0), test_task.formula.min_dist)
    kmx10 = int(best_dist_lo / 100)
    kmx10r = int((kmx10 + 10) / 10) * 10
    assert len(diff) == kmx10r
    assert diff[kmx10 + 1].diff_score == 0.5
    assert diff[kmx10 - 1].diff_score < 0.5

    '''max distance shorter than min_dist'''
    short = [p for p in pilots if 0 < p.distance < test_task.formula.min_dist]
    print(f'only min dist pilots: {len(short)}')
    diff = simulate_difficulty_calc(test_task, short)
    best_dist_lo = max(max([p.distance for p in short], default=0), test_task.formula.min_dist)
    kmx10 = int(best_dist_lo / 100)
    kmx10r = int((kmx10 + 10) / 10) * 10
    assert len(diff) == kmx10r
    assert diff[kmx10 + 1].diff_score == 0.5
    assert diff[kmx10 - 1].diff_score < 0.5


def test_score_calculation():
    """testing scoring Calculation Routine"""
    test_task, pilots = read_test_results()
    lib = test_task.formula.get_lib()
    absents = [p for p in pilots if p.result_type == 'abs']
    valid_results = [p for p in pilots if p.result_type not in ('abs', 'dnf', 'nyp')]
    non_valid_results = [p for p in pilots if p.result_type in ('abs', 'dnf', 'nyp')]
    lo_pilots = [p for p in pilots if not p.goal_time]
    no_ess_pilots = [p for p in pilots if not p.ESS_time]
    original_max_score = max((p.score for p in pilots), default=0)
    for p in valid_results:
        print(f'{p.name} - LC = {p.fixed_LC}')

    '''no pilots'''
    test_task.pilots = []
    lib.calculate_results(test_task)
    assert test_task.valid_results == []
    assert test_task.pilots_present == 0
    assert test_task.day_quality == 0
    assert test_task.max_distance == test_task.formula.min_dist
    assert test_task.std_dev_dist == 0

    '''only abs pilots'''
    test_task.pilots = absents
    lib.calculate_results(test_task)
    assert test_task.valid_results == []
    assert test_task.pilots_present == 0
    assert test_task.day_quality == 0
    assert test_task.max_distance == test_task.formula.min_dist
    assert test_task.std_dev_dist == 0

    '''only non valid pilots'''
    test_task.pilots = non_valid_results
    lib.calculate_results(test_task)
    assert test_task.valid_results == []
    assert test_task.pilots_present == len([p for p in test_task.pilots if p.result_type in ('dnf', 'nyp')])
    assert test_task.day_quality == 0
    assert test_task.max_distance == test_task.formula.min_dist
    assert test_task.std_dev_dist == 0

    '''only landed out pilots'''
    test_task.pilots = lo_pilots
    lib.process_results(test_task)
    lib.calculate_results(test_task)
    assert set(test_task.valid_results) == set(p for p in lo_pilots if p in valid_results)
    assert test_task.pilots_present == len([p for p in lo_pilots if not p.result_type == 'abs'])
    assert test_task.pilots_ess == 0
    assert test_task.pilots_goal == 0
    assert math.isclose(test_task.day_quality, 0.4437791595392983, abs_tol=0.001)
    assert test_task.max_distance == max((p.distance for p in lo_pilots), default=0)
    assert math.isclose(test_task.max_distance, 69391.6, abs_tol=1)
    assert math.isclose(test_task.std_dev_dist, 36021.7899821593, abs_tol=1)
    assert math.isclose(test_task.max_score, 407.1673788773062, abs_tol=0.5)

    '''all pilots'''
    test_task.pilots = pilots
    lib.process_results(test_task)
    lib.calculate_results(test_task)
    assert set(test_task.valid_results) == set(p for p in pilots if p in valid_results)
    assert len(test_task.pilots) == 14
    assert test_task.pilots_present == len([p for p in pilots if not p.result_type == 'abs'])
    assert test_task.pilots_present == 12
    assert test_task.pilots_ss == 10
    assert test_task.pilots_ess == 8
    assert test_task.pilots_goal == 8
    assert math.isclose(test_task.day_quality, 0.9929303958092204, abs_tol=0.001)
    assert test_task.max_distance == max((p.distance for p in pilots), default=0)
    assert test_task.max_distance == test_task.opt_dist
    assert math.isclose(test_task.max_distance, 85360.5, abs_tol=1)
    assert math.isclose(test_task.std_dev_dist, 31344.312107696805, abs_tol=1)
    assert math.isclose(test_task.max_score, 992.9303958092204, abs_tol=0.5)
    assert math.isclose(test_task.max_score, original_max_score, abs_tol=0.5)


