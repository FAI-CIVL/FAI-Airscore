import math

from geopy import Point, distance
from geopy.distance import geodesic
from pyproj import Proj, Transformer
from route import calcBearing

'''define earth model'''
# EARTHMODEL = Proj("+init=EPSG:4326")  # LatLon with WGS84 datum used by GPS units and Google Earth
EARTHMODEL = Proj(proj='latlong', datum='WGS84')  # LatLon with WGS84 datum used by GPS units and Google Earth

''' Standard plan projection: UTM or Mercatore.
    If UTM is used, function will calculate the correct UTM projection for the area.
    If Mercatore is used, function will create an 'ad hoc' Mercatore projection centered on the area. 
'''
PROJ = 'Mercatore'


class Geo(object):
    """ Object that contains Earth Model, Projection, and methods to transform between them"""

    def __init__(self, proj):
        self.geod = EARTHMODEL
        self.proj = proj
        self.to_proj = Transformer.from_proj(self.geod, self.proj)
        self.to_geod = Transformer.from_proj(self.proj, self.geod)

    @staticmethod
    def from_coords(lat, lon):
        proj = get_proj(clat=lat, clon=lon)
        return Geo(proj)

    def convert(self, lon, lat):
        """transform Turnpoints position (lon, lat) to projection coordinates (x, y)
        input:
        lat, lon      - coordinates
        """
        t = self.to_proj
        x, y = t.transform(lon, lat)
        return x, y

    def revert(self, x, y, direction='to'):
        """transform projected coordinates (x, y) to geoid position (lon, lat)
        input:
        c1, c2      - coordinates
        """
        t = self.to_geod
        lon, lat = t.transform(x, y)
        return lon, lat


def get_proj(clat, clon, proj=PROJ):
    """
    returns correct projection, UTM or custom Mercatore, using BBox center coordinates
    method 1: calculate UTM zone from center coordinates and use corresponding EPSG Projection
    method 2: create a custom trasverse mercatore projection upon center coordinates
    """

    if proj == 'UTM':
        utm_band = str((math.floor((clon + 180) / 6) % 60) + 1)
        if len(utm_band) == 1:
            utm_band = '0' + utm_band
        if clat >= 0:
            epsg_code = '326' + utm_band
        else:
            epsg_code = '327' + utm_band
        return Proj(f"EPSG:{epsg_code}")
    else:
        '''custom Mercatore projection'''
        tmerc = Proj(
            f"+proj=tmerc +lat_0={clat} +lon_0={clon} +k_0=1 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
        )
        return tmerc


def create_arc_polygon(center, start, end, clockwise=True, tolerance=5):
    """create an arc between two points, given a center
    The Arc is represented as a polyline.
    Points number is calculated as the number that makes maximum distance between arc and segment, tolerance / 2"""
    from statistics import mean

    # points = 50
    center = Point(center[0], center[1])
    start = Point(start[0], start[1])
    end = Point(end[0], end[1])
    bearing1 = calcBearing(center.latitude, center.longitude, start.latitude, start.longitude)
    dist1 = geodesic(center, start).meters
    bearing2 = calcBearing(center.latitude, center.longitude, end.latitude, end.longitude)
    dist2 = geodesic(center, end).meters
    radius = mean([dist1, dist2])
    angle = get_arc_angle(bearing1, bearing2)
    '''angle is negative if it is smaller counterclockwise from start to end'''
    if angle < 0 and clockwise:
        angle += 360
    elif angle > 0 and not clockwise:
        angle -= 360
    # da = angle/points if clockwise else angle/points * -1
    # length = calculate_arc_length(radius, abs(angle))
    points = max(
        1, calculate_min_points(angle, radius, tolerance)
    )  # max distance arc / segment is less than half tolerance
    da = angle / points
    dr = (dist1 - dist2) / points
    print(
        f"center: {center.latitude, center.longitude} | start: {start.latitude, start.longitude} | end: {end.latitude, end.longitude}"
    )
    print(f"radius: {dist1} | clockwise: {clockwise} | angle: {angle}")
    print(f"points: {points} | dAngle: {da} | dRadius: {dr}")
    interpolation_list = []
    for i in range(1, points):
        pt = distance.distance(meters=dist1 + dr * i).destination(center, bearing1 + da * i)
        p = (pt.latitude, pt.longitude)
        interpolation_list.append(p)
    print(interpolation_list)

    return interpolation_list


def get_arc_angle(b1, b2):
    r = (b2 - b1) % 360.0
    # Python modulus has same sign as divisor, which is positive here,
    # so no need to consider negative case
    if r >= 180.0:
        r -= 360.0
    return r


def calculate_arc_length(radius, angle):
    from math import pi

    return (pi * radius * 2) * (angle / 360.0)


def calculate_min_points(angle, radius, tolerance=5):
    """Calculates minimum number of points along the rc to have maximum distance between arc and segment
    less than half tolerance"""
    return math.ceil(math.radians(angle) / (2 * math.acos(1 - tolerance / radius)) + 1) * 2
