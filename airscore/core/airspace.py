from dataclasses import dataclass

from airspaceUtils import read_airspace_check_file


@dataclass(frozen=True)
class CheckParams:
    notification_distance: int = 100
    h_outer_limit: int = 70
    h_border_penalty: float = 0.1
    h_inner_limit: int = -30
    h_max_penalty: float = 1.0
    v_outer_limit: int = 70
    v_border_penalty: float = 0.1
    v_inner_limit: int = -30
    v_max_penalty: float = 1.0
    h_outer_penalty_per_m = 0 if not h_outer_limit else h_border_penalty / h_outer_limit
    h_inner_penalty_per_m = (h_max_penalty if not h_inner_limit
                             else (h_max_penalty - h_border_penalty) / abs(h_inner_limit))
    v_outer_penalty_per_m = 0 if not v_outer_limit else v_border_penalty / v_outer_limit
    v_inner_penalty_per_m = (v_max_penalty if not v_inner_limit
                             else (v_max_penalty - v_border_penalty) / abs(v_inner_limit))

    def penalty(self, distance, direction) -> float:
        """ calculate penalty based on params
            distance: FLOAT distance in meters
            direction: 'h' or 'v'"""
        if direction == 'h':
            outer_limit = self.h_outer_limit
            border_penalty = self.h_border_penalty
            inner_limit = self.h_inner_limit
            max_penalty = self.h_max_penalty
            outer_penalty_per_m = self.h_outer_penalty_per_m
            inner_penalty_per_m = self.h_inner_penalty_per_m
        else:
            outer_limit = self.v_outer_limit
            border_penalty = self.v_border_penalty
            inner_limit = self.v_inner_limit
            max_penalty = self.v_max_penalty
            outer_penalty_per_m = self.v_outer_penalty_per_m
            inner_penalty_per_m = self.v_inner_penalty_per_m
        if distance >= outer_limit:
            return 0
        elif distance <= inner_limit:
            return max_penalty
        elif distance > 0:
            return (outer_limit - distance) * outer_penalty_per_m
        elif distance == 0:
            return border_penalty
        elif distance < 0:
            return border_penalty + abs(distance * inner_penalty_per_m)


class AirspaceCheck(object):
    def __init__(self, control_area=None, params=None):
        self.control_area = control_area  # igc_lib openair reader control zones
        self.params = params  # AirspaceCheck object
        self.get_airspace_details()

    @property
    def bounding_box(self):
        if self.control_area:
            return self.control_area['bbox']

    @property
    def bbox_center(self):
        from statistics import mean
        lat = mean(t[0] for t in self.bounding_box)
        lon = mean(t[1] for t in self.bounding_box)
        return lat, lon

    @property
    def spaces(self):
        if self.control_area:
            return self.control_area['spaces']

    @property
    def airspace_details(self):
        if self.control_area:
            if not any(space['object'] for space in self.spaces):
                self.get_airspace_details()
            return self.control_area['spaces']

    @property
    def projection(self):
        """WGS84 to Mercatore Plan Projection"""
        from route import get_utm_proj
        '''get projection center'''
        clat, clon = self.bbox_center
        # '''define projection'''
        # tmerc = Proj(f"+proj=tmerc +lat_0={clat} +lon_0={clon} +k_0=1 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")
        # return tmerc
        '''Get UTM proj'''
        return get_utm_proj(clat, clon)

    @staticmethod
    def from_task(task):
        if task.airspace_check and task.openair_file:
            task_id = task.task_id
            control_area = read_airspace_check_file(task.openair_file)
            params = get_airspace_check_parameters(task_id)
            return AirspaceCheck(control_area, params)

    @staticmethod
    def read(task_id):
        from task import Task
        try:
            task = Task.read(task_id)
            return AirspaceCheck.from_task(task)
        except:
            print(f'Error trying to get task control zones')

    def get_airspace_details(self):
        from route import Turnpoint
        from shapely.geometry.polygon import Polygon
        import numpy as np

        if self.control_area:
            for space in self.control_area['spaces']:
                if space['shape'] == 'circle':
                    space['object'] = Turnpoint(lat=space['location'][0], lon=space['location'][1],
                                                radius=space['radius'])
                elif space['shape'] == 'polygon':
                    # TODO we get an error if airspace is an Arc. Transforming to circle with radius 1000m
                    if len(space['locations']) == 1:
                        # Arc
                        space['object'] = Turnpoint(lat=space['locations'][0][0], lon=space['locations'][0][1],
                                                    radius=1000)
                    else:
                        space['object'] = []
                        space['object'] = self.reproject(space)

    def to_mercatore(self):
        """WGS84 to Mercatore Plan Projection"""
        from pyproj import Proj, Transformer
        '''define earth model'''
        # wgs84 = Proj("EPSG:4326")  # LatLon with WGS84 datum used by GPS units and Google Earth
        wgs84 = Proj(proj='latlong', datum='WGS84')
        my_proj = self.projection
        return Transformer.from_proj(wgs84, my_proj)

    def to_geo(self):
        """WGS84 to Mercatore Plan Projection"""
        from pyproj import Proj, Transformer
        '''define earth model'''
        # wgs84 = Proj("EPSG:4326")  # LatLon with WGS84 datum used by GPS units and Google Earth
        wgs84 = Proj(proj='latlong', datum='WGS84')
        my_proj = self.projection
        return Transformer.from_proj(my_proj, wgs84)

    def reproject(self, space):
        from functools import partial
        import pyproj
        from pyproj import Proj
        from shapely import ops
        from shapely.geometry.polygon import Polygon
        '''get polygon from space'''
        polygon = Polygon([(pt[1], pt[0]) for pt in space['locations']])
        # from_proj = Proj("EPSG:4326")  # LatLon with WGS84 datum used by GPS units and Google Earth
        from_proj = Proj(proj='latlong', datum='WGS84')
        to_proj = self.projection
        tfm = partial(pyproj.transform, from_proj, to_proj)
        return ops.transform(tfm, polygon)

    def check_fix(self, fix, altitude_mode='gps'):
        """check a flight object for airspace violations
        arguments:
        fix - Flight fix object
        altimeter - flight altitude to use in checking 'barometric' - barometric altitude,
                                                      'gps' - GPS altitude
                                                      'baro/gps' - barometric if present otherwise gps  (default)
        vertical_tolerance: vertical distance in meters that a pilot can be inside airspace without penalty (default 0)
        horizontal_tolerance: horizontal distance in meters that a pilot can be inside airspace without penalty (default 0)
        """
        from airspaceUtils import altitude, in_bbox
        from shapely.geometry import Point
        from route import distance, Turnpoint

        # airspace_plot = []
        notification_band = self.params.notification_distance
        # h_penalty_band = self.params.h_outer_limit

        alt = altitude(fix, altitude_mode)
        fix_violation = False
        infringement = 0

        '''Check if fix is actually in Airspace bounding box'''
        if in_bbox(self.bounding_box, fix):
            for space in self.airspace_details:
                '''Check if fix is inside proximity warning area'''
                if space['floor'] - notification_band < alt < space['ceiling'] + notification_band:
                    # we are at same alt as an airspace
                    # TODO this type check is needed due to Arcs not recognised
                    if space['shape'] == 'circle' or isinstance(space['object'], Turnpoint):
                        if space['object'].in_radius(fix, 0, notification_band):
                            # fix is inside proximity band (at least)
                            dist_floor = space['floor'] - alt
                            dist_ceiling = alt - space['ceiling']
                            vert_distance = max(dist_floor, dist_ceiling)
                            horiz_distance = distance(fix, space['object']) - space['object'].radius
                            infringement = [space['name'], vert_distance, horiz_distance, 'circle']
                    elif space['shape'] == 'polygon':
                        x, y = self.to_mercatore().transform(fix.lon, fix.lat)
                        point = Point(x, y)
                        horiz_distance = point.distance(space['object'])
                        if horiz_distance <= notification_band:
                            dist_floor = space['floor'] - alt
                            dist_ceiling = alt - space['ceiling']
                            vert_distance = max(dist_floor, dist_ceiling)
                            if point.within(space['object']):
                                '''fix is inside the area'''
                                horiz_distance *= -1

                            '''test: get distance in ellypsoid reference '''
                            dp = Point(point.x+horiz_distance, point.y)
                            dlon, dlat = self.to_geo().transform(dp.x, dp.y)
                            dwp = Turnpoint(lat=dlat, lon=dlon)
                            geo_dist = distance(fix, dwp)
                            '''test going back'''
                            x, y = self.to_mercatore().transform(dwp.lon, dwp.lat)
                            p2 = Point(x, y)
                            d2 = p2.distance(point)

                            infringement = [space['name'], vert_distance, horiz_distance, geo_dist, d2]
                            violation = True
                            fix_violation = True
                    # TODO insert arc check here. we can use in radius and bearing to

        return infringement


def get_airspace_check_parameters(task_id):
    from myconn import Database
    from db_tables import TaskAirspaceCheckView as A
    from sqlalchemy.exc import SQLAlchemyError

    with Database() as db:
        try:
            q = db.session.query(A).get(task_id)
            if q.airspace_check:
                return CheckParams(q.notification_distance, q.h_outer_limit, q.h_border_penalty,
                                   q.h_inner_limit, q.h_max_penalty, q.v_outer_limit, q.v_border_penalty,
                                   q.v_inner_limit, q.v_max_penalty)
            else:
                return None
        except SQLAlchemyError:
            print(f'SQL Error trying to get Airspace Params from database')
            return None
