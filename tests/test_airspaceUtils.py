import airspaceUtils
import pytest
# from mock import patch
from igc_lib import GNSSFix


# def test_read_openair():
#     assert False
#
#
# def test_write_openair():
#     assert False

# @patch("convert_height" , return_value=("1000 ft/304.8 m", 304.8, 'm'))
# def test_airspace_info(mock_convert_height):
#


@pytest.mark.parametrize('string, result',
                         [("GND", ('GND / 0 m', 0, 'm')),
                          ("FL45", ('FL45', 45, 'FL')),
                          ("300MSL", ('300 m', 300, 'm')),
                          ("1000 ft", ("1000 ft/304.8 m", 304.8, 'm')),
                          ("1000 m", ("1000 m", 1000, 'm'))]
                         )
def test_convert_height(string, result):
    assert airspaceUtils.convert_height(string) == result


#
# def test_circle_map():
#     assert False
#
#
# def test_circle_check():
#     assert False
#
#
# def test_polygon_map():
#     assert False
#
#
# def test_polygon_check():
#     assert False
#
#
# def test_create_new_airspace_file():
#     assert False


def test_delete_airspace():
    file = """SPACE1
abc

SPACE2
def

SPACE3
ghi"""
    output = """SPACE1
abc

SPACE3
ghi"""

    assert airspaceUtils.delete_airspace(file, 'SPACE2') == output


def test_modify_airspace():
    file = """SPACE1
    abc

    SPACE2
    def

    SPACE3
    ghi"""
    output = """SPACE1
    abc

    SPACE2
    dxy

    SPACE3
    ghi"""
    assert airspaceUtils.modify_airspace(file, 'SPACE2', 'ef', 'xy')


#
# def test_read_airspace_map_file():
#     assert False
#
#
# def test_read_airspace_check_file():
#     assert False
#
#
# def test_check_flight_airspace():
#     assert False


@pytest.mark.parametrize('bbox, fix, result',
                         [([[10, 5], [20, 25]],
                           GNSSFix(rawtime=1234, lat=45, lon=9, press_alt=1000, gnss_alt=1200, validity=1, index=1,
                                   extras=None), False),
                          ([[10, 5], [20, 25]],
                           GNSSFix(rawtime=1234, lat=11, lon=9, press_alt=1000, gnss_alt=1200, validity=1, index=1,
                                   extras=None), True),
                          ([[10, 5], [20, 25]],
                           GNSSFix(rawtime=1234, lat=10, lon=5, press_alt=1000, gnss_alt=1200, validity=1, index=1,
                                   extras=None), True),
                          ([[10, 5], [20, 25]],
                           GNSSFix(rawtime=1234, lat=15, lon=4, press_alt=0, gnss_alt=1200, validity=1, index=1,
                                   extras=None), False)
                          ]
                         )
def test_in_bbox(bbox, fix, result):
    assert airspaceUtils.in_bbox(bbox, fix) == result

@pytest.mark.parametrize('fix, altimeter, result',
                         [(GNSSFix(rawtime=1234, lat=45, lon=9, press_alt=1000, gnss_alt=1200, validity=1, index=1,
                                   extras=None), "gps", 1200),
                          (GNSSFix(rawtime=1234, lat=45, lon=9, press_alt=1000, gnss_alt=1200, validity=1, index=1,
                                   extras=None), "barometric", 1000),
                          (GNSSFix(rawtime=1234, lat=45, lon=9, press_alt=1000, gnss_alt=1200, validity=1, index=1,
                                   extras=None), "baro/gps", 1000),
                          (GNSSFix(rawtime=1234, lat=45, lon=9, press_alt=0, gnss_alt=1200, validity=1, index=1,
                                   extras=None), "baro/gps", 1200)
                          ]
                         )
def test_altitude(fix, altimeter, result):
    assert airspaceUtils.altitude(fix, altimeter) == result


def test_altitude_value_error():
    with pytest.raises(ValueError, match=r".*not one of barometric, baro/gps or gps"):
        airspaceUtils.altitude(GNSSFix(rawtime=1234, lat=45, lon=9,  press_alt=1000, gnss_alt=1200, validity=1, index=1,
                                       extras=None), "radar")
