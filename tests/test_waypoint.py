from waypoint import get_turnpoints_from_file
import math

files = [dict(file='/app/tests/data/test.compe.wpt', format='CompeGPS', num=192),
         dict(file='/app/tests/data/test.cup', format='CUP', num=172),
         dict(file='/app/tests/data/test.gpx', format='GPX', num=172),
         dict(file='/app/tests/data/test.GEO.wpt', format='GEO', num=172),
         dict(file='/app/tests/data/test.UTM.wpt', format='UTM', num=107)
         ]


def test_waypoint():
    for el in files:
        f, wpts = get_turnpoints_from_file(el['file'])
        assert f == el['format']
        assert len(wpts) == int(el['num'])
        wpt = wpts[0]
        assert wpt.name == 'T01'
        assert wpt.description == 'TEST WPT'
        assert math.isclose(float(wpt.lat), 46.258333, abs_tol=0.00001)
        assert math.isclose(float(wpt.lon), 12.673611, abs_tol=0.00001)
        assert wpt.altitude == 950


