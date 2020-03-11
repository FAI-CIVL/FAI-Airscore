# from alchemy_mock.mocking import UnifiedAlchemyMagicMock, mock
import pytest
from datetime import datetime
import frontendUtils
import region
from myconn import Database
from autoapp import create_app


app = create_app()

@pytest.fixture
def app_context():
    with app.app_context():
        yield
#
# session = UnifiedAlchemyMagicMock(data=[
#      (
#          [mock.call.query(c),
#           mock.call.filter(c.comp_id == 1),
#           mock.call.outerjoin(TblTask, c.comp_id == TblTask.comp_id)],
#          [c(comp_id=1, comp_name='testing', comp_site='timbuktu', date_from=datetime(1999,1,1) )]
#      )
#      # ,
#      # (
#      #     [mock.call.query(TblCompetition),
#      #      mock.call.filter(TblCompetition.comp_name == 'hello world')],
#      #     [TblCompetition(note='hello world')]
#      # ),
#      # (
#      #     [mock.call.query(TblTask),
#      #      mock.call.filter(TblTask.foo == 5, TblTask.bar > 10)],
#      #     [TblTask(foo=5, bar=17)]
#      # ),
#  ])


# # @mocker.patch('db.session', new_callable=session)
# def test_get_admin_comps(monkeypatch):
#     # apply the monkeypatch for requests.get to mock_get
#     monkeypatch.setattr(db, "session", session)
#     r = get_admin_comps()
#     assert r


def test_allowed_tracklog_filesize():
    assert frontendUtils.allowed_tracklog_filesize(5*1024*1024) == True
    assert frontendUtils.allowed_tracklog_filesize(5 * 1024 * 1024 + 1) == False
    assert frontendUtils.allowed_tracklog_filesize(5 * 1024 * 1024 - 1) == True


@pytest.mark.parametrize('string, result',
                         [("abc", False),
                          ("test.txt", False),
                          ("file.igc", True)]
                         )
def test_allowed_tracklog(string, result):
    assert frontendUtils.allowed_tracklog(string) == result


def test_get_waypoint_choices(monkeypatch):
    def fake_get_waypoint_choices(reg_id):
        return [{'rwp_id': 123, 'name': 'london', 'description': 'home of big ben'}, {'rwp_id': 456, 'name': 'paris', 'description': 'home of notre dame'}]
    monkeypatch.setattr(region, 'get_region_wpts', fake_get_waypoint_choices)
    result = frontendUtils.get_waypoint_choices(1)
    assert result[0] == (123, 'london - home of big ben')
    assert len(result) == 2


# def test_get_admin_comps(monkeypatch):
#     def fake_query():
#         d1 = datetime(1999,1,2)
#         d2 = datetime(2000,4,5)
#         return 'zero','one','timbuktu', d1, d2
#     monkeypatch.setattr(Database().session, 'query', fake_query)
#     result = frontendUtils.get_admin_comps()
#     assert result['data'][0][1] == '<a href="/users/comp_settings_admin/zero">one</a>'

# @patch.object()
# def test_get_comp():
#     comp = compUtils.get_comp(1)
#     assert comp.comp_id == 1