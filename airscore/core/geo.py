import math
import numpy as np

from pyproj import Proj, Transformer
from route import cPoint, Turnpoint
from geopy.distance import geodesic, vincenty
from collections import namedtuple
from geographiclib.geodesic import Geodesic
from math import sqrt, hypot, fabs

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
        """ transform Turnpoints position (lon, lat) to projection coordinates (x, y)
            input:
            lat, lon      - coordinates
        """
        t = self.to_proj
        x, y = t.transform(lon, lat)
        return x, y

    def revert(self, x, y, direction='to'):
        """ transform projected coordinates (x, y) to geoid position (lon, lat)
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
            f"+proj=tmerc +lat_0={clat} +lon_0={clon} +k_0=1 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")
        return tmerc

