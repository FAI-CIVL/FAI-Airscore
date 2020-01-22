"""
OpenAir file operations

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019

"""

from logger import Logger
from aerofiles import openair
from pprint import pprint as pp
import folium
import re
from os import path
import jsonpickle
import Defines
from mapUtils import get_airspace_bbox
import json

NM_in_meters = 1852.00
Ft_in_meters = 0.3048000
hPa_in_feet = 27.3053
colours = {'P': '#d42c31', 'D': '#d42c31', 'R': '#d42c31', 'GP': '#d42c31', 'C': '#d42c31', 'Z': '#d42c31',
           'CTR': '#d42c31', 'Q': '#d42c31', }


def read_openair(filename):
    """reads openair file using the aerofiles library.
    returns airspaces object (openair.reader)"""
    space = None
    airspace_path = Defines.AIRSPACEDIR
    fullname = path.join(airspace_path, filename)
    with open(fullname, 'r') as fp:
        space = openair.Reader(fp)
    return space


def write_openair(data, filename):
    """writes file into airspace folder. No checking if file data is valid openair format.
    returns airspaces object (openair.reader)"""
    space = None
    airspace_path = Defines.AIRSPACEDIR
    # airspace_path = '/home/stuart/Documents/projects/Airscore_git/airscore/airscore/data/airspace/openair/'
    fullname = path.join(airspace_path, filename)
    with open(fullname, 'w') as fp:
        fp.write(data)


def airspace_info(record):
    """Creates a dictionary containing details on an airspace for use in front end"""
    return {'name': record['name'], 'class': record['class'], 'floor_description': record['floor'],
            'floor': convert_height(record['floor'])[1], 'floor_unit': convert_height(record['floor'])[2],
            'ceiling_description': record['ceiling'],
            'ceiling': convert_height(record['ceiling'])[1], 'ceiling_unit': convert_height(record['ceiling'])[2]}


def convert_height(height_string):
    """Converts feet in metres, GND into 0. leaves FL essentialy untouched. returns a string that can be used in
    labels etc such as "123 m", a int of height such as 123 and a unit such as "m" """
    info = ''
    meters = None

    if height_string == '0':
        return '0', 0, "m"

    if re.search("FL", height_string):
        height = int(re.sub("[^0-9]", "", height_string))
        return height_string, height, "FL"

    elif re.search("ft", height_string):
        if len(re.sub("[^0-9]", "", height_string)) > 0:
            feet = int(re.sub("[^0-9]", "", height_string))
            meters = round(feet * Ft_in_meters, 1)
            info = f"{height_string}/{meters} m"

    elif re.search("m", height_string) or re.search("MSL", height_string):
        if len(re.sub("[^0-9]", "", height_string)) > 0:
            meters = int(re.sub("[^0-9]", "", height_string))
            info = f"{meters} m"

    elif height_string == 'GND':
        meters = 0  # this should probably be something like -500m to cope with dead sea etc (or less for GPS/Baro error?)
        info = "GND / 0 m"
    else:
        return height_string, None, "Unknown height unit"

    return info, meters, "m"


def circle_map(element, info):
    """Returns folium circle mapping object from circular airspace.
    takes circular airspace as input, which may only be part of an airspace"""
    if element['type'] == 'circle':
        floor, _, _ = convert_height(info['floor'])
        ceiling, _, _ = convert_height(info['ceiling'])
        radius = f"{element['radius']} NM/{round(element['radius'] * NM_in_meters, 1)}m"
        return folium.Circle(
            location=(element['center'][0], element['center'][1]),
            popup=f"{info['name']} Class {info['class']} floor:{floor} ceiling:{ceiling} Radius:{radius}",
            radius=element['radius'] * NM_in_meters,
            color=colours[info['class']],
            weight=2,
            opacity=0.8,
            fill=True,
            fill_opacity=0.2,
            fill_color=colours[info['class']]
        )
    else:
        return None


def circle_check(element, info):
    """Returns circle object for checking igc files from circular airspace.
    takes circular airspace as input, which may only be part of an airspace"""
    if element['type'] == 'circle':

        return {'shape': 'circle',
                'location': (element['center'][0], element['center'][1]),
                'radius': element['radius'] * NM_in_meters,
                'floor': info['floor'],
                'floor_unit': info['floor_unit'],
                'ceiling': info['ceiling'],
                'ceiling_unit': info['ceiling_unit'],
                'name': info['name']}
    else:
        return None


def polygon_map(record):
    """Returns folium polygon mapping object from multipoint airspace
    takes entire airspace as input"""
    locations = []
    for element in record['elements']:
        if element['type'] == 'point':
            locations.append(element['location'])

    if not locations:
        return None

    floor, _, _ = convert_height(record['floor'])
    ceiling, _, _ = convert_height(record['ceiling'])

    return folium.Polygon(
        locations=locations,
        popup=f"{record['name']} Class {record['class']} floor:{floor} ceiling:{ceiling}",
        color=colours[record['class']],
        weight=2,
        opacity=0.8,
        fill=True,
        fill_opacity=0.2,
        fill_color=colours[record['class']]
    )


def polygon_check(record, info):
    """Returns polygon object for checking igc files from multipoint airspace
    takes entire airspace as input"""
    locations = []
    for element in record['elements']:
        if element['type'] == 'point':
            locations.append(element['location'])

    if not locations:
        return None

    floor, _, _ = convert_height(record['floor'])
    ceiling, _, _ = convert_height(record['ceiling'])

    return {'shape': 'polygon',
            'locations': locations,
            'floor': info['floor'],
            'floor_unit': info['floor_unit'],
            'ceiling': info['ceiling'],
            'ceiling_unit': info['ceiling_unit'],
            'name': info['name']}


def create_new_airspace_file(mod_data):
    airspace_path = Defines.AIRSPACEDIR
    # airspace_path = '/home/stuart/Documents/projects/Airscore_git/airscore/airscore/data/airspace/openair/'
    fullname = path.join(airspace_path, mod_data['old_filename'])
    new_file = mod_data['new_filename']

    if new_file[-4:] != '.txt':
        new_file += '.txt'

    with open(fullname, 'r') as file:
        data = file.read()
        for change in mod_data['changes']:
            data = modify_airspace(data, change['name'], change['old'], change['new'])
        for space in mod_data['delete']:
            data = delete_airspace(data, space)
        write_openair(data, new_file)
    return new_file


def delete_airspace(file, spacename):
    """Deletes an airspace from file data. Does not write file to disk
    arguments:
    file - file data
    spacename - name of the airspace"""

    all_spaces = file.split("\n\n")

    for space in all_spaces:
        if space.find(spacename) > -1:
            all_spaces.remove(space)
    return "\n\n".join(all_spaces)


def modify_airspace(file, spacename, old, new):
    """modifies airspace. for changing height data.
    arguments:
    file - file data
    spacename - airspace name
    old - string to be relpaced
    new - string to be inserted"""

    all_spaces = file.split("\n\n")
    for i, space in enumerate(all_spaces):
        if space.find(spacename) > 0:
            all_spaces[i] = space.replace(old, new)

    return "\n\n".join(all_spaces)


def create_airspace_map_check_files(openair_filename):
    """Creates file with folium objects for mapping and file used for checking flights.
    :argument: openair_filename located in AIRSPACEDIR"""
    from itertools import tee

    mapspaces = []
    checkspaces = []

    airspace_path = Defines.AIRSPACEDIR
    mapfile_path = Defines.AIRSPACEMAPDIR
    checkfile_path = Defines.AIRSPACECHECKDIR

    if openair_filename[-4:] != '.txt':
        mapfile_name = openair_filename + '.map'
        checkfile_name = openair_filename + '.check'
    else:
        mapfile_name = openair_filename[:-4] + '.map'
        checkfile_name = openair_filename[:-4] + '.check'

    openair_fullname = path.join(airspace_path, openair_filename)
    mapfile_fullname = path.join(mapfile_path, mapfile_name)
    checkfile_fullname = path.join(checkfile_path, checkfile_name)

    with open(openair_fullname) as fp:
        reader = openair.Reader(fp)

        reader, reader_2 = tee(reader)
        bbox = get_airspace_bbox(reader_2)
        airspace_list = []
        record_number = 0
        for record, error in reader:

            if error:
                raise error  # or handle it otherwise
            if record['type'] == 'airspace':
                details = airspace_info(record)
                details['id'] = record_number
                airspace_list.append(details)
                polygon = polygon_map(record)
                if polygon:
                    mapspaces.append(polygon)
                    checkspaces.append(polygon_check(record, details))
                for element in record['elements']:
                    if element['type'] == 'circle':
                        mapspaces.append(circle_map(element, record))
                        checkspaces.append(circle_check(element, details))
            record_number += 1

        map_data = {'spaces': mapspaces, 'airspace_list': airspace_list, 'bbox': bbox}
        check_data = {'spaces': checkspaces, 'bbox': bbox}
        with open(mapfile_fullname, 'w') as mapfile:
            mapfile.write(jsonpickle.encode(map_data))
        with open(checkfile_fullname, 'w') as checkfile:
            checkfile.write(json.dumps(check_data))


def read_airspace_map_file(openair_filename):
    """Read airspace map file if it exists. Create if not.
        argument: openair file name
        returns: dictionary containing spaces object and bbox """
    from pathlib import Path

    mapfile_path = Defines.AIRSPACEMAPDIR

    if openair_filename[-4:] != '.txt':
        mapfile_name = openair_filename + '.map'
    else:
        mapfile_name = openair_filename[:-4] + '.map'

    mapfile_fullname = path.join(mapfile_path, mapfile_name)

    # if the file does not exist
    if not Path(mapfile_fullname).is_file():
        create_airspace_map_check_files(openair_filename)

    with open(mapfile_fullname, 'r') as f:
        return jsonpickle.decode(f.read())


def read_airspace_check_file(openair_filename):
    """Read airspace check file if it exists. Create if not.
        arguent: openair file name
        returns: dictionary containing spaces object and bbox """
    from pathlib import Path

    checkfile_path = Defines.AIRSPACECHECKDIR

    if openair_filename[-4:] != '.txt':
        checkfile_name = openair_filename + '.check'
    else:
        checkfile_name = openair_filename[:-4] + '.check'

    checkfile_fullname = path.join(checkfile_path, checkfile_name)

    # if the file does not exist
    if not Path(checkfile_fullname).is_file():
        create_airspace_map_check_files(openair_filename)

    with open(checkfile_fullname, 'r') as f:
        return json.loads(f.read())


def check_flight_airspace(flight, openair_filename, altimeter='baro/gps', vertical_tolerance_warning=0,
                          vertical_tolerance_no_penalty=0, vertical_tolerance_full_penalty=0,
                          horizontal_tolerance_warning=0, horizontal_tolerance_no_penalty=0,
                          horizontal_tolerance_full_penalty=0):
    """check a flight object for airspace violations
    arguments:
    flight - flight object
    openair_filename - filename of openair file.
    altimeter - flight altitude to use in checking 'barometric' - barometric altitude,
                                                  'gps' - GPS altitude
                                                  'baro/gps' - barometric if present otherwise gps  (default)
    vertical_tolerance_warning: vertical distance in meters over which a pilot can be inside airspace without penalty
                                    but will be signalled. This can be used for warnings.
                                    If this is negative it will be distance away from airspace.
                                     (default 0)
    vertical_tolerance_no_penalty: vertical distance in meters that a pilot can be inside airspace without penalty,
                                    if this is negative it will be distance away from airspace where penalties start.
                                     (default 0)
    vertical_tolerance_full_penalty: vertical distance in meters over which a pilot will incur a 100% penalty.
    horizontal_tolerance_warning: horizontal distance in meters over which a pilot can be inside airspace without penalty
                                    but will be signalled. This can be used for warnings.
                                    If this is negative it will be distance away from airspace.
                                     (default 0)
    horizontal_tolerance_no_penalty: vertical distance in meters that a pilot can be inside airspace without penalty,
                                    if this is negative it will be distance away from airspace where penalties start.
                                     (default 0)
    horizontal_tolerance_full_penalty: vertical distance in meters over which a pilot will incur a 100% penalty.

    :returns
    airspace_plot: a list of lists of all the fixes, the limit at that point and if there was a violation
    [fix.rawtime, fix.lat, fix.lon, alt, airspace lower limit, airspace upper limit, airspace name,
    type of infringement, infringement distance]
    warning: True if there have been warnings
    violations: True if there have been violations
    full_violation: True if there have been full violations
    """
    from route import Turnpoint, distance
    from shapely.geometry import Point
    from shapely.geometry.polygon import Polygon
    from pyproj import Proj, Transformer
    import numpy as np

    airspace = read_airspace_check_file(openair_filename)
    bounding_box = airspace['bbox']
    airspace_details = airspace['spaces']
    airspace_plot = []

    '''get projection center'''
    clat = bounding_box[0][0] + (bounding_box[1][0] - bounding_box[0][0])
    clon = bounding_box[0][1] + (bounding_box[1][1] - bounding_box[0][1])

    '''define earth model'''
    wgs84 = Proj("+init=EPSG:4326")  # LatLon with WGS84 datum used by GPS units and Google Earth
    tmerc = Proj(
        f"+proj=tmerc +lat_0={clat} +lon_0={clon} "
        f"+k_0=1 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")
    trans = Transformer.from_proj(wgs84, tmerc)

    for space in airspace_details:
        if space['shape'] == 'circle':
            space['object'] = Turnpoint(lat=space['location'][0], lon=space['location'][1], radius=space['radius'])
        elif space['shape'] == 'polygon':
            space['object'] = []
            lats = []
            lons = []
            for p in space['locations']:
                x, y = trans.transform(p[1], p[0])
                lats.append(y)
                lons.append(x)
            lats_vect = np.array(lats)
            lons_vect = np.array(lons)
            lons_lats_vect = np.column_stack((lons_vect, lats_vect))
            polygon = Polygon(lons_lats_vect)
            space['object'] = polygon

    violation = False
    full_violation = False
    warning = False
    for fix in flight.fixes:
        alt = altitude(fix, altimeter)
        fix_violation = False
        if in_bbox(bounding_box, fix):  # check if we are in the bounding box of all airspaces
            for space in airspace_details:
                # we are at same alt as an airspace
                if space['floor'] + vertical_tolerance_warning < alt < space['ceiling'] - vertical_tolerance_warning:
                    if space['shape'] == 'circle':
                        infringement_distance = space['object'].radius - distance(space['object'], fix)
                    if space['shape'] == 'polygon':
                        x, y = trans.transform(fix.lon, fix.lat)
                        point = Point(x, y)
                        infringement_distance = 1 - space['object'].distance(point)
                        # TODO need to get this back into actual geographic distance
                    else:
                        infringement_distance = - 1000
                        # TODO insert arc check here. we can use in radius and bearing to
                    if infringement_distance > horizontal_tolerance_warning:
                        warning = True
                        fix_violation = True
                        infringement = 'warning'
                        if infringement_distance > horizontal_tolerance_no_penalty:
                            violation = True
                            infringement = 'penalty'
                            if infringement_distance > horizontal_tolerance_full_penalty:
                                full_violation = True
                                infringement = 'full penalty'
                        airspace_plot.append([fix.rawtime, fix.lat, fix.lon, alt, space['floor'],
                                              space['ceiling'], space['name'], infringement, infringement_distance])
                    # elif space['shape'] == 'polygon':
                    #     x, y = trans.transform(fix.lon, fix.lat)
                    #     point = Point(y, x)
                    #     if point.within(space['object']):
                    #         airspace_plot.append([fix.rawtime, fix.lat, fix.lon, alt, space['floor'],
                    #                               space['ceiling'], space['name'], infringement, infringement_distance])
                    #         violation = True
                    #         fix_violation = True
                    # TODO insert arc check here. we can use in radius and bearing to

        if not fix_violation:
            airspace_plot.append([fix.rawtime, fix.lat, fix.lon, alt, None, None, None, None])
    return airspace_plot, warning, violation, full_violation


def in_bbox(bbox, fix):
    if bbox[0][0] <= fix.lat <= bbox[1][0] and bbox[0][1] <= fix.lon <= bbox[1][1]:
        return True
    else:
        return False


def altitude(fix, altimeter):
    """returns altitude of specified altimeter from fix"""
    if altimeter == 'barometric' or altimeter == 'baro/gps':
        if fix.press_alt != 0.0:
            return fix.press_alt
        elif altimeter == 'baro/gps':
            return fix.gnss_alt
        else:
            return 'error - no barometric altitude available'
    elif altimeter == 'gps':
        return fix.gnss_alt
    else:
        raise ValueError(f"altimeter choice({altimeter}) not one of barometric, baro/gps or gps")

# def arc_map(element, info):
#     if element['type'] == 'arc':
#         if len(re.sub("[^0-9]", "", info['floor'])) > 0:
#             floor_ft = int(re.sub("[^0-9]", "", info['floor']))
#             floor = f"{info['floor']}/{(floor_ft * Ft_in_meters)} m"
#         else:
#             floor = info['floor']
#
#         if len(re.sub("[^0-9]", "", info['ceiling'])) > 0:
#             ceiling_ft = int(re.sub("[^0-9]", "", info['ceiling']))
#             ceiling = f"{info['ceiling']}/{(ceiling_ft * Ft_in_meters)} m"
#         else:
#             ceiling = info['ceiling']
#
#         radius = f"{element['radius']} NM/{element['radius'] * NM_in_meters}m"
#         return folium.Circle(
#                 location=(element['center'][0], element['center'][1]),
#                 popup=f"{info['name']} Class {info['class']} floor:{floor} ceiling:{ceiling} Radius:{radius}",
#                 radius=element['radius'] * NM_in_meters,
#                 color=colours[info['class']],
#                 weight=2,
#                 opacity=0.8,
#                 fill=True,
#                 fill_opacity=0.2,
#                 fill_color=colours[info['class']]
#                 )
#     else:
#         return None
