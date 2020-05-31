from dataclasses import dataclass
from functools import partial
from math import sqrt, pow, log

import geopy
import pyproj
from shapely import ops
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from airspaceUtils import read_airspace_check_file
from route import distance, Turnpoint


@dataclass(frozen=True)
class CheckParams:
    notification_distance: int  # meters, default 100
    function: str  # linear, non-linear
    h_outer_limit: int  # meters, default 70
    h_boundary: int  # meters, default 0
    h_boundary_penalty: float  # default 0.1
    h_inner_limit: int  # meters, default -30
    h_max_penalty: float  # default 1.0
    v_outer_limit: int  # meters, default 70
    v_boundary: int  # meters, default 0
    v_boundary_penalty: float  # default 0.1
    v_inner_limit: int  # meters, default -30
    v_max_penalty: float  # default 1.0
    h_outer_band: int
    h_inner_band: int
    h_total_band: int
    v_outer_band: int
    v_inner_band: int
    v_total_band: int
    h_outer_penalty_per_m: float
    h_inner_penalty_per_m: float
    v_outer_penalty_per_m: float
    v_inner_penalty_per_m: float

    def penalty(self, distance, direction) -> float:
        """ calculate penalty based on params
            distance: FLOAT distance in meters
            direction: 'h' or 'v'"""
        if not distance or ((direction == 'h' and distance >= self.h_outer_limit)
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
                return round((outer_limit - distance) * outer_penalty_per_m, 5)
            elif distance == boundary:
                return border_penalty
            elif distance < boundary:
                return round(border_penalty + abs(boundary - distance) * inner_penalty_per_m, 5)
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
            return round(pow(((outer_limit - distance) / total_band), log(10, 2)), 5) * max_penalty


class AirspaceCheck(object):
    def __init__(self, control_area=None, params=None, geo=None):
        self.control_area = control_area  # igc_lib openair reader control zones
        self.params = params  # AirspaceCheck object
        self.geo = geo  # Geo object

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

    @staticmethod
    def from_task(task):
        if not (task.airspace_check and task.openair_file):
            print(f'Airspace check disabled or no Openair file set')
            return None
        task_id = task.task_id
        control_area = read_airspace_check_file(task.openair_file)
        params = get_airspace_check_parameters(task_id)
        airspace = AirspaceCheck(control_area, params, task.geo)
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
                if space['shape'] == 'circle':
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
                '''enlarge bbox to contain notification band'''
                pt1 = geopy.distance.distance(meters=dist).destination(pmin, 225)
                pt2 = geopy.distance.distance(meters=dist).destination(pmax, 45)
                space['bbox'] = [[pt1[0], pt1[1]], [pt2[0], pt2[1]]]

    def reproject(self, space):
        """get polygon from space"""
        polygon = Polygon([(pt[1], pt[0]) for pt in space['locations']])
        from_proj = self.geo.geod
        to_proj = self.geo.proj
        tfm = partial(pyproj.transform, from_proj, to_proj)
        return ops.transform(tfm, polygon)

    def check_fix(self, fix, alt=None):
        """check a flight object for airspace violations
        arguments:
        fix - Flight fix object
        alt - flight altitude used in flight checking. If None, fix.gnss_alt is used (GPS altitude)
        :returns
            plot - list, details of airspace infringed
            penalty - the penalty for this infringement
        """
        from airspaceUtils import in_bbox

        notification_band = self.params.notification_distance
        alt = fix.gnss_alt if not alt else alt
        infringement = 0
        penalty = 0
        plot = None

        '''Check if fix is actually in Airspace bounding box'''
        for space in self.spaces:
            violation = 0
            '''check if in altitude range'''
            if space['floor'] - notification_band < alt < space['ceiling'] + notification_band:
                # we are at same alt as the airspace
                '''check if fix is inside bbox'''
                if in_bbox(space['bbox'], fix):
                    '''Check if fix is inside proximity warning area'''
                    if space['shape'] == 'circle':
                        if space['object'].in_radius(fix, 0, notification_band):
                            # fix is inside proximity band (at least)
                            # print(f" in circle --- ")
                            # start_time = tt.time()
                            dist_floor = space['floor'] - alt
                            dist_ceiling = alt - space['ceiling']
                            vert_distance = max(dist_floor, dist_ceiling)
                            horiz_distance = distance(fix, space['object']) - space['object'].radius
                            violation = 1
                    elif space['shape'] == 'polygon':
                        # start_time = tt.time()
                        x, y = self.geo.convert(fix.lon, fix.lat)
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
                            violation = 1
                    if violation:
                        result = min([(vert_distance, self.params.penalty(vert_distance, 'v')),
                                      (horiz_distance, self.params.penalty(horiz_distance, 'h'))], key=lambda p: p[1])
                        pen = result[1]
                        if pen >= penalty:
                            '''new worse infringement'''
                            infringement_space = space
                            if pen == 0:
                                dist = max(vert_distance, horiz_distance)
                                infringement = 'warning'
                            else:
                                if pen > penalty:
                                    penalty = pen
                                    dist = result[0]
                                    if pen < max(self.params.h_max_penalty, self.params.v_max_penalty):
                                        infringement = 'penalty'
                                    else:
                                        '''do not need to check other spaces for the fix'''
                                        infringement = 'full penalty'
                                        break

        if infringement:
            plot = [infringement_space['floor'], infringement_space['ceiling'], infringement_space['name'],
                    infringement, dist]

        return plot, penalty

    def get_infringements_result(self, infringements_list):
        """
        Airspace Warnings and Penalties Managing
        Creates a list of worst infringement for each airspace in infringements_list
        Calculates penalty
        Calculates final penalty and comments
        """
        '''element: [next_fix, airspace_name, infringement_type, distance, penalty]'''
        spaces = list(set([x[1] for x in infringements_list]))
        penalty = 0
        max_pen_fix = None
        infringements_per_space = []
        comments = []
        '''check distance and penalty for each space in which we recorded an infringement'''
        for space in spaces:
            fixes = [fix for fix in infringements_list if fix[1] == space]
            pen = max(x[4] for x in fixes)
            fix = min([x for x in fixes if x[4] == pen], key=lambda x: x[3])
            dist = fix[3]
            rawtime = fix[0].rawtime
            if pen == 0:
                ''' create warning comment'''
                comments.append(f"{space} Warning: separation less than {dist} meters")
            else:
                '''add fix to infringements'''
                infringements_per_space.append({'rawtime': rawtime, 'space': space,
                                                'distance': dist, 'penalty': pen})
                if pen > penalty:
                    penalty = pen
                    max_pen_fix = fix

        '''final calculation'''
        if penalty > 0:
            '''we have a penalty'''
            space = max_pen_fix[1]
            if max_pen_fix[2] == 'full penalty':
                comments = [f"{space}: airspace infringement. penalty {round(penalty * 100)}%"]
            else:
                dist = max_pen_fix[3]
                comments = [f"{space}: {round(dist)}m from limit. penalty {round(penalty * 100)}%"]

        return infringements_per_space, comments, penalty

    def get_infringements_result_new(self, infringements_list):
        """
        Airspace Warnings and Penalties Managing
        Creates a list of worst infringement for each airspace in infringements_list
        Calculates penalty
        Calculates final penalty and comments
        """
        from pilot.notification import Notification
        '''element: [next_fix, airspace_name, infringement_type, distance, penalty]'''
        spaces = list(set([x[1] for x in infringements_list]))
        penalty = 0
        max_pen_fix = None
        infringements_per_space = []
        comments = []
        notifications = []
        '''check distance and penalty for each space in which we recorded an infringement'''
        for space in spaces:
            fixes = [fix for fix in infringements_list if fix[1] == space]
            pen = max(x[4] for x in fixes)
            fix = min([x for x in fixes if x[4] == pen], key=lambda x: x[3])
            dist = fix[3]
            rawtime = fix[0].rawtime
            if pen == 0:
                ''' create warning comment'''
                comment = f"[{space}] Warning: separation less than {dist} meters"
            else:
                '''add fix to infringements'''
                infringements_per_space.append({'rawtime': rawtime, 'space': space,
                                                'distance': dist, 'penalty': pen})
                if fix[2] == 'full penalty':
                    comment = f"[{space}]: airspace infringement. penalty {round(pen * 100)}%"
                else:
                    comment = f"[{space}]: {round(dist)}m from limit. penalty {round(pen * 100)}%"
                if pen > penalty:
                    penalty = pen
                    max_pen_fix = fix
            notifications.append(Notification(notification_type='airspace', percentage_penalty=pen, comment=comment))

        # '''final calculation'''
        # if penalty > 0:
        #     '''we have a penalty'''
        #     space = max_pen_fix[1]
        #     if max_pen_fix[2] == 'full penalty':
        #         comments = [f"{space}: airspace infringement. penalty {round(penalty * 100)}%"]
        #     else:
        #         dist = max_pen_fix[3]
        #         comments = [f"{space}: {round(dist)}m from limit. penalty {round(penalty * 100)}%"]

        return infringements_per_space, notifications, penalty


def get_airspace_check_parameters(task_id):
    from db.conn import db_session
    from db.tables import TaskAirspaceCheckView as A

    with db_session() as db:
        q = db.query(A).get(task_id)
        if q.airspace_check:
            '''calculate parameters'''
            h_outer_band = q.h_outer_limit - q.h_boundary
            h_inner_band = q.h_boundary - q.h_inner_limit
            h_total_band = q.h_outer_limit - q.h_inner_limit
            v_outer_band = q.v_outer_limit - q.v_boundary
            v_inner_band = q.v_boundary - q.v_inner_limit
            v_total_band = q.v_outer_limit - q.v_inner_limit
            h_outer_penalty_per_m = 0 if not h_outer_band else q.h_boundary_penalty / h_outer_band
            h_inner_penalty_per_m = (q.h_max_penalty if not h_inner_band
                                     else (q.h_max_penalty - q.h_boundary_penalty) / h_inner_band)
            v_outer_penalty_per_m = 0 if not v_outer_band else q.v_boundary_penalty / v_outer_band
            v_inner_penalty_per_m = (q.v_max_penalty if not v_inner_band
                                     else (q.v_max_penalty - q.v_boundary_penalty) / v_inner_band)

            return CheckParams(q.notification_distance, q.function, q.h_outer_limit, q.h_boundary,
                               q.h_boundary_penalty, q.h_inner_limit, q.h_max_penalty, q.v_outer_limit,
                               q.v_boundary, q.v_boundary_penalty, q.v_inner_limit, q.v_max_penalty,
                               h_outer_band, h_inner_band, h_total_band, v_outer_band, v_inner_band, v_total_band,
                               h_outer_penalty_per_m, h_inner_penalty_per_m, v_outer_penalty_per_m,
                               v_inner_penalty_per_m)
        else:
            print(f"airspace_check disabled")
            return None


def fl_to_meters(flight_level, qnh=1013.25):
    from airspaceUtils import hPa_in_feet, Ft_in_meters
    d = 1013.25 - qnh
    feet = flight_level * 100 - hPa_in_feet * d
    meters = feet * Ft_in_meters
    return meters
