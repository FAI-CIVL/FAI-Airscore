import pyproj
import geopy

from dataclasses import dataclass
from airspaceUtils import read_airspace_check_file
from pyproj import Proj, Transformer
from shapely import ops
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
from functools import partial
from route import distance, Turnpoint
from math import sqrt, pow, log


@dataclass(frozen=True)
class CheckParams:
    notification_distance: int = 100
    function: str = 'linear'  # linear / non-linear
    h_outer_limit: int = 70
    h_boundary: int = 0
    h_boundary_penalty: float = 0.1
    h_inner_limit: int = -30
    h_max_penalty: float = 1.0
    v_outer_limit: int = 70
    v_boundary: int = 0
    v_boundary_penalty: float = 0.1
    v_inner_limit: int = -30
    v_max_penalty: float = 1.0
    h_outer_band = h_outer_limit - h_boundary
    h_inner_band = h_boundary - h_inner_limit
    h_total_band = h_outer_limit - h_inner_limit
    v_outer_band = v_outer_limit - v_boundary
    v_inner_band = v_boundary - v_inner_limit
    v_total_band = v_outer_limit - v_inner_limit
    h_outer_penalty_per_m = 0 if not h_outer_band else h_boundary_penalty / h_outer_band
    h_inner_penalty_per_m = h_max_penalty if not h_inner_band else (h_max_penalty - h_boundary_penalty) / h_inner_band
    v_outer_penalty_per_m = 0 if not v_outer_band else v_boundary_penalty / v_outer_band
    v_inner_penalty_per_m = v_max_penalty if not v_inner_band else (v_max_penalty - v_boundary_penalty) / v_inner_band

    def penalty(self, distance, direction) -> float:
        """ calculate penalty based on params
            distance: FLOAT distance in meters
            direction: 'h' or 'v'"""
        if ((direction == 'h' and distance >= self.h_outer_limit)
                or (direction == 'v' and distance >= self.v_outer_limit)):
            return 0
        elif ((direction == 'h' and distance <= self.h_inner_limit)
                or (direction == 'v' and distance <= self.v_inner_limit)):
            return self.h_max_penalty if direction == 'h' else self.v_max_penalty

        if self.function == 'linear':
            '''case linear penalty'''
            if direction == 'h':
                outer_limit = self.h_outer_limit
                boundary = self.h_boundary
                border_penalty = self.h_boundary_penalty
                outer_penalty_per_m = self.h_outer_penalty_per_m
                inner_penalty_per_m = self.h_inner_penalty_per_m
            else:
                outer_limit = self.v_outer_limit
                boundary = self.v_boundary
                border_penalty = self.v_boundary_penalty
                outer_penalty_per_m = self.v_outer_penalty_per_m
                inner_penalty_per_m = self.v_inner_penalty_per_m
            if distance > boundary:
                return (outer_limit - distance) * outer_penalty_per_m
            elif distance == boundary:
                return border_penalty
            elif distance < boundary:
                return border_penalty + abs(boundary - distance) * inner_penalty_per_m
        else:
            ''' case non-linear penalty
                needs just outer limit, inner limit and max penalty (default 1.0)
                uses (distance/band)**(ln10/ln2)
                Function gives 0 at outer limit, 1 at inner limit, and 0.1 at half way
                with increasing penalty per meter moving toward inner limit'''

            if direction == 'h':
                outer_limit = self.h_outer_limit
                max_penalty = self.h_max_penalty
                total_band = self.h_total_band
            else:
                outer_limit = self.v_outer_limit
                max_penalty = self.v_max_penalty
                total_band = self.v_total_band
            return round(pow(((outer_limit - distance) / total_band), log(10, 2)), 4) * max_penalty


class AirspaceCheck(object):
    def __init__(self, control_area=None, params=None):
        self.control_area = control_area  # igc_lib openair reader control zones
        self.params = params  # AirspaceCheck object
        self.projection = self.get_projection()
        self.transformer = get_cartesian_transformer(self.projection)

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

    # @property
    # def airspace_details(self):
    #     if self.control_area:
    #         if not any(space['object'] for space in self.spaces):
    #             print('I should never be here')
    #             self.get_airspace_details()
    #         return self.control_area['spaces']

    @staticmethod
    def from_task(task):
        if task.airspace_check and task.openair_file:
            task_id = task.task_id
            control_area = read_airspace_check_file(task.openair_file)
            params = get_airspace_check_parameters(task_id)
            airspace = AirspaceCheck(control_area, params)
            airspace.get_airspace_details(qnh=task.QNH)
            return airspace

    @staticmethod
    def read(task_id):
        from task import Task
        try:
            task = Task.read(task_id)
            return AirspaceCheck.from_task(task)
        except:
            print(f'Error trying to get task control zones')

    def get_projection(self):
        """WGS84 to Mercatore Plan Projection"""
        from route import get_utm_proj
        '''get projection center'''
        clat, clon = self.bbox_center
        # '''define projection'''
        # tmerc = Proj(f"+proj=tmerc +lat_0={clat} +lon_0={clon} +k_0=1 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")
        # return tmerc
        '''Get UTM proj'''
        return get_utm_proj(clat, clon)

    def get_airspace_details(self, qnh=1013.25):
        """Writes bbox and Polygon obj for each space"""
        if self.control_area:
            for space in self.spaces:
                ''' check if we have Flight Levels to convert using task QNH'''
                if space['floor_unit'] == 'FL':
                    space['floor'] = fl_to_meters(space['floor'], qnh)
                    space['floor_unit'] = 'm'
                if space['ceiling_unit'] == 'FL':
                    space['ceiling'] = fl_to_meters(space['floor'], qnh)
                    space['ceiling_unit'] = 'm'
                ''' create object and bbox'''
                if space['shape'] == 'circle' or (space['shape'] == 'polygon' and len(space['locations']) == 1):
                    # TODO we get an error if airspace is an Arc. Transforming to circle with radius 1000m
                    if space['shape'] == 'polygon':
                        clat = space['locations'][0][0]
                        clon = space['locations'][0][1]
                        radius = 1000
                    else:
                        clat = space['location'][0]
                        clon = space['location'][1]
                        radius = space['radius']
                    dist = radius + self.params.notification_distance * sqrt(2)
                    pmin = pmax = geopy.Point(clat, clon)
                    space['object'] = Turnpoint(lat=clat, lon=clon, radius=radius)
                else:
                    pmin = geopy.Point(min(pt[0] for pt in space['locations']), min(pt[1] for pt in space['locations']))
                    pmax = geopy.Point(max(pt[0] for pt in space['locations']), max(pt[1] for pt in space['locations']))
                    dist = self.params.notification_distance * sqrt(2)
                    space['object'] = self.reproject(space)
                pt1 = geopy.distance.distance(meters=dist).destination(pmin, 225)
                pt2 = geopy.distance.distance(meters=dist).destination(pmax, 45)
                space['bbox'] = [[pt1[0], pt1[1]], [pt2[0], pt2[1]]]

    def reproject(self, space):
        """get polygon from space"""
        polygon = Polygon([(pt[1], pt[0]) for pt in space['locations']])
        # from_proj = Proj("EPSG:4326")  # LatLon with WGS84 datum used by GPS units and Google Earth
        from_proj = Proj(proj='latlong', datum='WGS84')
        to_proj = self.projection
        tfm = partial(pyproj.transform, from_proj, to_proj)
        return ops.transform(tfm, polygon)

    def check_fix(self, fix, altitude_mode='GPS'):
        """check a flight object for airspace violations
        arguments:
        fix - Flight fix object
        altimeter - flight altitude to use in checking 'barometric' - barometric altitude,
                                                      'gps' - GPS altitude
                                                      'baro/gps' - barometric if present otherwise gps  (default)
        vertical_tolerance: vertical distance in meters that a pilot can be inside airspace without penalty (default 0)
        horizontal_tolerance: horizontal distance in meters that a pilot can be inside airspace without penalty (default 0)
        """
        from airspaceUtils import in_bbox
        import time as tt

        # airspace_plot = []
        notification_band = self.params.notification_distance
        # h_penalty_band = self.params.h_outer_limit
        alt = fix.gnss_alt if altitude_mode == 'GPS' else fix.press_alt
        fix_violation = False
        infringement = 0
        horiz_distance = 0
        vert_distance = 0

        '''Check if fix is actually in Airspace bounding box'''
        for space in self.spaces:
            '''check if in altitude range'''
            if space['floor'] - notification_band < alt < space['ceiling'] + notification_band:
                # we are at same alt as the airspace
                '''check if fix is inside bbox'''
                if in_bbox(space['bbox'], fix):
                    '''Check if fix is inside proximity warning area'''
                    # TODO this type check is needed due to Arcs not recognised
                    if space['shape'] == 'circle' or isinstance(space['object'], Turnpoint):
                        if space['object'].in_radius(fix, 0, notification_band):
                            # fix is inside proximity band (at least)
                            # print(f" in circle --- ")
                            # start_time = tt.time()
                            dist_floor = space['floor'] - alt
                            dist_ceiling = alt - space['ceiling']
                            vert_distance = max(dist_floor, dist_ceiling)
                            horiz_distance = distance(fix, space['object']) - space['object'].radius
                            infringement = [space['name'], vert_distance, horiz_distance]
                            # print(f" airspace circle --- {tt.time() - start_time} seconds ---")
                    elif space['shape'] == 'polygon':
                        # start_time = tt.time()
                        x, y = self.transformer.transform(fix.lon, fix.lat)
                        point = Point(x, y)
                        horiz_distance = space['object'].exterior.distance(point)
                        if point.within(space['object']):
                            '''fix is inside the area'''
                            horiz_distance *= -1
                        if horiz_distance <= notification_band:
                            # print(f" {space['name']}: in polygon --- ")
                            dist_floor = space['floor'] - alt
                            dist_ceiling = alt - space['ceiling']
                            vert_distance = max(dist_floor, dist_ceiling)
                            # print(
                            #     f"alt {alt} floor {dist_floor} ceiling {dist_ceiling} vert {vert_distance} hor {horiz_distance}")
                            infringement = [space['name'], vert_distance, horiz_distance]
                            violation = True
                            fix_violation = True
                        # print(f" polygon airspace check --- {tt.time() - start_time} seconds ---")
                    # TODO insert arc check here. we can use in radius and bearing to
                    # '''check if we are in infringement zone
                    #     we should have at least one negative measure between horiz and vert distance'''
                    # # if min(vert_distance, horiz_distance) < 0:
                    #     infringement = [space['name'], vert_distance, horiz_distance]

        return infringement

    def get_infringements_result(self, infringements_list):
        """
        Airspace Warnings and Penalties Managing
        Creates a list of worst infringement for each airspace in infringements_list
        Calculates penalty
        Claculates final penalty and comments
        """
        spaces = list(set([x[1][0] for x in infringements_list]))
        penalty = 0
        infringements_per_space = []
        comments = []
        '''check distance and penalty for each space in which we recorded a fix'''
        for space in spaces:
            fixes = [p for p in infringements_list if p[1][0] == space and (p[1][1] < 0 or p[1][2] < 0)]
            if fixes:
                dist_h = min(p[1][2] for p in fixes)
                pen_h = self.params.penalty(dist_h, 'h')
                dist_v = min(p[1][1] for p in fixes)
                pen_v = self.params.penalty(dist_v, 'v')
                print(f"{dist_h}, {dist_v} | {pen_h}, {pen_v}")
                if dist_h > dist_v:
                    '''horizontal infringement'''
                    dist = dist_h
                    pen = pen_h
                    p = next(x for x in fixes if x[1][2] == dist_h)
                    direction = 'horizontal'
                else:
                    dist = dist_v
                    pen = pen_v
                    p = next(x for x in fixes if x[1][1] == dist_v)
                    direction = 'vertical'
                print(f"{direction}, {pen}")
                fix = p[0]
                if pen > 0:
                    '''add fix to infringements'''
                    infringements_per_space.append({'rawtime': fix.rawtime, 'space': space, 'distance': dist,
                                                    'type': direction, 'penalty': pen})
                else:
                    ''' create warning comment'''
                    comments.append(f"{space} Warning: {direction} separation less than {dist} meters")
                if pen > penalty:
                    penalty = pen
                    el = infringements_per_space[-1]

        '''final calculation'''
        if penalty > 0:
            '''we have a penalty'''
            comments = [
                f"{''.join([str(round(el['distance'])), 'm from']) if el['distance'] > 0 else ''.join([str(abs(round(el['distance']))), 'm inside'])} {el['space']}: penalty {round(el['penalty'] * 100)}%"]

        return infringements_per_space, comments, penalty


def get_airspace_check_parameters(task_id):
    from myconn import Database
    from db_tables import TaskAirspaceCheckView as A
    from sqlalchemy.exc import SQLAlchemyError

    with Database() as db:
        try:
            q = db.session.query(A).get(task_id)
            if q.airspace_check:
                return CheckParams(q.notification_distance, q.function, q.h_outer_limit, q.h_boundary,
                                   q.h_boundary_penalty, q.h_inner_limit, q.h_max_penalty, q.v_outer_limit,
                                   q.v_boundary, q.v_boundary_penalty, q.v_inner_limit, q.v_max_penalty)
            else:
                return None
        except SQLAlchemyError:
            print(f'SQL Error trying to get Airspace Params from database')
            return None


def get_cartesian_transformer(projection):
    """WGS84 to Mercatore Plan Projection"""
    '''define earth model'''
    # wgs84 = Proj("EPSG:4326")  # LatLon with WGS84 datum used by GPS units and Google Earth
    wgs84 = Proj(proj='latlong', datum='WGS84')
    my_proj = projection
    return Transformer.from_proj(wgs84, my_proj)


def fl_to_meters(flight_level, qnh=1013.25):
    from airspaceUtils import hPa_in_feet, Ft_in_meters
    d = 1013.25 - qnh
    feet = flight_level * 100 - hPa_in_feet * d
    meters = feet * Ft_in_meters
    return meters
