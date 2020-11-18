# from alchemy_mock.mocking import UnifiedAlchemyMagicMock, mock
import pytest
from datetime import datetime
import frontendUtils
import region
# from myconn import Database
from autoapp import create_app
from unittest.mock import patch, MagicMock
from frontendUtils import db_session
from faker import Faker
from random import random
from json import loads
fake = Faker()
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
        return [{'rwp_id': 123, 'name': 'london', 'description': 'home of big ben', 'altitude': 123, 'lat': 55.23, 'lon': 150.44, 'blahblah': 'abc'}, {'rwp_id': 456, 'name': 'paris', 'description': 'home of notre dame', 'altitude': 8848, 'lat': 5.23, 'lon': 15.44, 'blahblah': 'xyz'}]
    monkeypatch.setattr(region, 'get_region_wpts', fake_get_waypoint_choices)
    result, wpts = frontendUtils.get_waypoint_choices(1)
    assert result[0] == (123, 'london - home of big ben')
    assert len(result) == 2


def query(*args, **kwargs):
    rows = []
    for n in range(1, 10):
        rows.append(row())
    return rows


def row():
    id = int(random()*10)
    name = fake.name()
    place = fake.word()
    d1 = fake.date_object()
    d2 = fake.date_object()
    tasks = int(random()*10)
    owner = 123
    return id, name, place, d1, d2, tasks, owner


def test_get_admin_comps(monkeypatch):
    MockResponse = MagicMock(autospec=True)
    myquery = query()
    MockResponse.return_value.__enter__.return_value.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value = myquery
    with app.app_context():
        with patch('frontendUtils.db_session', MockResponse):
            result = frontendUtils.get_admin_comps(123)
        # print(result)
        assert result.json['data'][0][1] == '<a href="/users/comp_settings_admin/' + str(myquery[0][0])+'">'\
            + myquery[0][1] + '</a>'
        assert result.json['data'][0][3] == myquery[0][3].strftime("%Y-%m-%d")
        assert result.json['data'][0][4] == myquery[0][4].strftime("%Y-%m-%d")
        assert result.json['data'][0][0] == myquery[0][0]
        assert result.json['data'][0][6] == 'delete'
        assert result.json['data'][1][1] == '<a href="/users/comp_settings_admin/' + str(myquery[1][0])+'">' \
            + myquery[1][1] + '</a>'
        assert result.json['data'][1][3] == myquery[1][3].strftime("%Y-%m-%d")
        assert result.json['data'][1][4] == myquery[1][4].strftime("%Y-%m-%d")
        assert result.json['data'][1][0] == myquery[1][0]
        assert result.json['data'][1][6] == 'delete'

        with patch('frontendUtils.db_session', MockResponse):
            result = frontendUtils.get_admin_comps(111)
        assert result.json['data'][1][6] == ''
# @patch.object()
# def test_get_comp():
#     comp = compUtils.get_comp(1)
#     assert comp.comp_id == 1