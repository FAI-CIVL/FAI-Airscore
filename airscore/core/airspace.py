"""
OpenAir file reader:

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
colours = {'P': '#d42c31', 'D': '#d42c31', 'R': '#d42c31'}
def read_openair(filename):
    space = None
    with open(filename) as fp:
        space = openair.Reader(fp)
    return space

# def map_airspace(openair):
#     for space in openair:


def circle_map(element, info):
    if element['type'] == 'circle':
        if len(re.sub("[^0-9]", "", info['floor'])) > 0:
            floor_ft = int(re.sub("[^0-9]", "", info['floor']))
            floor = f"{info['floor']}/{(floor_ft * Ft_in_meters)} m"
        else:
            floor = info['floor']

        if len(re.sub("[^0-9]", "", info['ceiling'])) > 0:
            ceiling_ft = int(re.sub("[^0-9]", "", info['ceiling']))
            ceiling = f"{info['ceiling']}/{(ceiling_ft * Ft_in_meters)} m"
        else:
            ceiling = info['ceiling']

        radius = f"{element['radius']} NM/{element['radius'] * NM_in_meters}m"
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
    locations = []
    for element in record['elements']:
        if element['type'] == 'point':
            locations.append(element['location'])

    if locations == []:
        return None

    if len(re.sub("[^0-9]", "", record['floor'])) > 0:
        floor_ft = int(re.sub("[^0-9]", "", record['floor']))
        floor = f"{record['floor']}/{(floor_ft * Ft_in_meters)} m"
    else:
        floor = record['floor']

    if len(re.sub("[^0-9]", "", record['ceiling'])) > 0:
        ceiling_ft = int(re.sub("[^0-9]", "", record['ceiling']))
        ceiling = f"{record['ceiling']}/{(ceiling_ft * Ft_in_meters)} m"
    else:
        ceiling = record['ceiling']

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
