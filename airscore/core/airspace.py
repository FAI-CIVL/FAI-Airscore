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
import jsonpickle

NM_in_meters = 1852.00
Ft_in_meters = 0.3048000
colours = {'P': '#d42c31', 'D': '#d42c31', 'R': '#d42c31', 'GP': '#d42c31', 'C': '#d42c31', 'Z': '#d42c31', 'CTR': '#d42c31'}


def read_openair(filename):
    """reads openair file using the aerofiles library.
    returns airspaces object (openair.reader)"""
    space = None
    with open(filename) as fp:
        space = openair.Reader(fp)
    return space


def airspace_info(record):
    """Creates a dictionary containing details on an airspace for use in front end"""
    return {'name': record['name'], 'class': record['class'], 'floor_description': record['floor'],
            'floor': convert_height(record['floor'])[1], 'floor_unit': convert_height(record['floor'])[2],
            'ceiling_description': record['ceiling'],
            'ceiling': convert_height(record['ceiling'])[1], 'ceiling_unit': convert_height(record['ceiling'])[2]}


# def map_airspace(openair):
#     for space in openair:
def convert_height(height_string):
    """Converts feet in metres, GND into 0. leaves FL essentialy untouched. returns a string that can be used in
    labels etc such as "123 m", a int of height such as 123 and a unit such as "m" """

    if re.search("FL", height_string):
        height = int(re.sub("[^0-9]", "", height_string))
        return height_string, height, "FL"

    elif re.search("ft", height_string):
        if len(re.sub("[^0-9]", "", height_string)) > 0:
            feet = int(re.sub("[^0-9]", "", height_string))
            meters = round(feet * Ft_in_meters,1)
            info = f"{height_string}/{meters} m"

    elif re.search("m", height_string):
        if len(re.sub("[^0-9]", "", height_string)) > 0:
            meters = int(re.sub("[^0-9]", "", height_string))
            info = f"{meters} m"

    elif height_string == 'GND':
            meters = 0 # this should probably be something like -500m to cope with dead sea etc (or less for GPS/Baro error?)
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


def polygon_map(record):
    """Returns folium polygon mapping object from multipoint airspace
    takes entire airspace as input"""
    locations = []
    for element in record['elements']:
        if element['type'] == 'point':
            locations.append(element['location'])

    if locations == []:
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
#
# def modify_openair_file(oldfilename, newfilename, mod_data):
#     with open(oldfilename) as file:
#         for space in mod_data['data']:
#             spacename = space['name']
#             if space['delete'] == True:
#                 delete_airspace(file, spacename)
#         all_lines = file.readlines()
#         for line_number, line in enumerate(all_lines):
#             # if line == 'AN ' + mod_data['data']:



def delete_airspace(file, spacename):
    """Deletes an airspace from file data. Does not write file to disk
    arguments:
    file - file data
    spacename - name of the airspace"""

    all_spaces = file.split("\n\n")
    # print(f'spacename:{spacename}')
    for space in all_spaces:
        # print(space)
        if space.find(spacename) > 0:
            all_spaces.remove(space)
            # print(f'removing {spacename}')
    return "\n\n".join(all_spaces)


def modify_airspace(file, spacename, old, new):
    """modifies airspace. for changing height data.
    arguments:
    file - file data
    spacename - airspace name
    old - string to be relpaced
    new - string to be inserted"""

    all_spaces = file.split("\n\n")
    # print(f'spacename:{spacename}')
    for i, space in enumerate(all_spaces):
        # print(space)
        if space.find(spacename) > 0:
            all_spaces[i] = space.replace(old, new)

    return "\n\n".join(all_spaces)

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
