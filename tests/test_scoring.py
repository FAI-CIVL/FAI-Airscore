import factory_objects


def simulate_difficulty_calc(task: factory_objects.test_task(), res: list) -> list:
    lib = task.formula.get_lib()
    task.pilots = res
    return lib.difficulty_calculation(task)


def test_diff_calc():
    """testing Difficulty Calculation Routine"""
    test_task = factory_objects.test_task()
    test_task.formula.formula_name = 'GAP2020'
    test_task.formula.formula_type = 'gap'
    test_task.formula.formula_version = 2020

    '''no pilots'''
    pilots = []
    diff = simulate_difficulty_calc(test_task, pilots)
    kmx10 = int(test_task.formula.min_dist/100)
    kmx10r = int((kmx10 + 10) / 10) * 10
    assert len(diff) == kmx10r
    assert diff[kmx10 + 1].diff_score == 0.5

    '''one pilot in goal, no pilot landed out'''
    pilots.append(factory_objects.simulate_pilot(test_task, 'goal'))
    diff = simulate_difficulty_calc(test_task, pilots)
    assert len(diff) == kmx10r
    assert diff[kmx10 + 1].diff_score == 0.5

    '''random pilots distribution, one pilot in goal'''
    for i in range(50):
        pilots.append(factory_objects.simulate_pilot(test_task, 'lo'))
    diff = simulate_difficulty_calc(test_task, pilots)
    best_dist_lo = max(max([p.distance for p in pilots if p.goal_time == 0], default=0), test_task.formula.min_dist)
    kmx10 = int(best_dist_lo / 100)
    kmx10r = int((kmx10 + 10) / 10) * 10
    assert len(diff) == kmx10r
    assert diff[kmx10 + 1].diff_score == 0.5
    assert diff[kmx10 - 1].diff_score < 0.5

    '''random pilots distribution, no pilots in goal'''
    pilots = []
    for i in range(50):
        pilots.append(factory_objects.simulate_pilot(test_task, 'lo'))
    diff = simulate_difficulty_calc(test_task, pilots)
    best_dist_lo = max(max([p.distance for p in pilots if p.goal_time == 0], default=0), test_task.formula.min_dist)
    kmx10 = int(best_dist_lo / 100)
    kmx10r = int((kmx10 + 10) / 10) * 10
    assert len(diff) == kmx10r
    assert diff[kmx10 + 1].diff_score == 0.5
    assert diff[kmx10 - 1].diff_score < 0.5

    '''random pilots distribution, max distance shorter than min_dist'''
    pilots = []
    for i in range(50):
        pilots.append(factory_objects.simulate_pilot(test_task, 'min_dist'))
    diff = simulate_difficulty_calc(test_task, pilots)
    best_dist_lo = max(max([p.distance for p in pilots if p.goal_time == 0], default=0), test_task.formula.min_dist)
    kmx10 = int(best_dist_lo / 100)
    kmx10r = int((kmx10 + 10) / 10) * 10
    assert len(diff) == kmx10r
    assert diff[kmx10 + 1].diff_score == 0.5
    assert diff[kmx10 - 1].diff_score < 0.5
