from result import TaskResult
import factory_objects
from unittest.mock import patch


# @patch('airscore.core.task.create_classifications')
# def fake_create_classifications():
#     return []
#
#
# @patch('airscore.core.compUtils.read_rankings')
# def fake_read_rankings():
#     return []


@patch('airscore.core.ranking.create_rankings')
def fake_create_rankings():
    return []


test_task = factory_objects.test_task()
test_task.pilots = [factory_objects.dummy_pilot()]


def test_result_file(task=test_task):
    with patch('ranking.create_rankings', return_value={}) as create_ranking_patched:
        result = task.create_json_elements()
        formula = result['formula']
        for key in TaskResult.formula_list:
            assert formula[key] == getattr(test_task.formula, key)
        info = result['info']
        for key in [k for k in TaskResult.info_list if k != 'date']:
            assert info[key] == getattr(test_task, key)
        stats = result['stats']
        for key in TaskResult.stats_list:
            assert stats[key] == getattr(test_task, key)
        results = result['results']
        for pilot in results:
            el = next(p for p in task.pilots if p.ID == pilot['ID'])
            for key in TaskResult.results_list:
                if hasattr(el, key):
                    assert pilot[key] == getattr(el, key)

