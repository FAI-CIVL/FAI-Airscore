import obj_factories
import json
from pathlib import Path


def create_test_task(data: dict) -> obj_factories.TaskFactory:
    task = obj_factories.TaskFactory()
    task.as_dict().update(data.get('info'))
    formula = obj_factories.TaskFormulaFactory(task_id=1)
    formula.as_dict().update(data.get('formula'))
    task.formula = formula
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
