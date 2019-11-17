"""
Route Library
contains
    low level functions for distance calculations

Use: import route

Stuart Mackintosh - 2019
"""

import math
import numpy as np
from geopy.distance import geodesic, ELLIPSOIDS, vincenty
from collections import namedtuple
from geographiclib.geodesic import Geodesic

geod = Geodesic.WGS84

a = 6378137  # WSG84 major meters
b = 6356752.3142  # WGS84 minor meters
f = 0.0033528106647474805  # WGS84 flattening


# a = ELLIPSOIDS['WGS-84'][0] * 1000  # WSG84 major meters: 6378137
# b = ELLIPSOIDS['WGS-84'][1] * 1000  # WGS84 minor meters: 6356752.3142
# f = ELLIPSOIDS['WGS-84'][2] #WGS84 flattening

class Turnpoint:
    """ single turnpoint in a task.
    Attributes:
        id: progressive number
        lat: a float, latitude in degrees
        lon: a float, longitude in degrees
        dlat: a float, latitude (for optimised route)
        dlon: a float, longitude (for optimised route)
        altitude: altitude amsl
        radius: radius of cylinder or line in km
        type: type of turnpoint; "launch",
                                 "speed",
                                 "cylinder",
                                 "endspeed",
                                 "goal"
        shape: "line" or "circle"
        how: "entry" or "exit"
    """

    def __init__(self, lat, lon, radius, type, shape, how):
        self.name           = None
        self.id             = None                  # tawPk
        self.rwpPk          = None
        self.lat            = lat
        self.lon            = lon
        self.flat           = lat * math.pi / 180
        self.flon           = lon * math.pi / 180
        self.radius         = radius
        self.type           = type
        self.shape          = shape
        self.how            = how
        self.altitude       = None
        self.description    = None

        assert type in ["launch", "speed", "waypoint", "endspeed", "goal", "optimised", "restricted"], \
            "turnpoint type is not valid: %r" % type
        assert shape in ["line", "circle", "optimised"], "turnpoint shape is not valid: %r" % shape
        assert how in ["entry", "exit", "optimised"], "turnpoint how (direction) is not valid: %r" % how

    def __str__(self):
        out = ''
        out += f"name: {self.name}, lat: {self.lat}, lon: {self.lon}, radius: {self.radius}"
        return out

    def in_radius(self, fix, t, tm):
        """Checks whether the provided GNSSFix is within the radius"""
        if t < 0:
            tol = min(tm, self.radius * t)
        else:
            tol = max(tm, self.radius * t)

        return distance(self, fix) < self.radius + tol

class polar(object):
    def __init__(self, lat=0, lon=0, flat=0, flon=0, shape=None, radius=0):
        self.lat = lat
        self.lon = lon
        self.flat = flat
        self.flon = flon
        self.shape = shape
        self.radius = radius

class cPoint(object):
    '''object to be used in planar distance calculations
        x       (float)     the x coordinate
        y       (float)     the y coordinate
        radius  (int)       the radius in metres
        fx      (float)     the x coordinate of the fix
        fy      (float)     the y coordinate of the fix
    '''

    def __str__(self):
        print(f'x: {str(self.x)} | y: {str(self.y)} | radius: {str(self.radius)}')

    def __init__(self, x, y, radius=0):
        self.x      = x
        self.y      = y
        self.fx     = x
        self.fy     = y
        self.radius = radius

    @classmethod
    def create(cls, x, y, radius=0):
        return cls(x=x, y=y, radius=radius)

    @staticmethod
    def create_from_center(point):
        return cPoint(point.x, point.y, point.radius)

    @staticmethod
    def create_from_fix(point):
        return cPoint(point.fx, point.fy, point.radius)

    @staticmethod
    def create_from_Turnpoint(tp):
        return cPoint(tp.lon, tp.lat, tp.radius)

def polar2cartesian(P):
    sinPhi = math.sin(P.flat)
    cosPhi = math.cos(P.flat)
    sinLambda = math.sin(P.flon)
    cosLambda = math.cos(P.flon)
    H = 0  # $p1->{'altitude'}

    eSq = (a * a - b * b) / (a * a)
    nu = a / math.sqrt(1 - eSq * sinPhi * sinPhi)

    return np.array([(nu + H) * cosPhi * cosLambda, (nu + H) * cosPhi * sinLambda, ((1 - eSq) * nu + H) * sinPhi])


def cartesian2polar(xyz):
    eSq = (a * a - b * b) / (a * a)
    # FIX: +/- determination?
    flon = math.atan2(xyz[1], xyz[0])
    flat = math.asin(math.sqrt(xyz[2] * xyz[2] / ((1 - eSq) * a * (1 - eSq) * a + xyz[2] * xyz[2] * eSq)))

    if (xyz[2] < 0):
        flat = -flat

    lat = flat * 180 / math.pi
    lon = flon * 180 / math.pi

    return polar(lat, lon, flat, flon)


def distance(p1, p2, method='fast_andoyer'):

    if method == "fast_andoyer":
        #print ("fast andoyer")
        return fast_andoyer(p1, p2)
    elif method == "vincenty":
        #print ("vincenty")
        return vincenty((p1.lat, p1.lon), (p2.lat, p2.lon)).meters
    elif method == "geodesic":
        #print ("geodesic")
        return geodesic((p1.lat, p1.lon), (p2.lat, p2.lon)).meters
    else:
        #print ("other")
        return fast_andoyer(p1, p2)


def plane_normal(c1, c2):
    # Find the normal to the plane created by the two points ..
    # Normal n = u X v =
    #       ( (uy*vz - uz*vy), (uz*vx - ux*vz), (ux*vy - uy*vx) )
    n = np.array([c1[1] * c2[2] - c1[2] * c2[1], c1[2] * c2[0] - c1[0] * c2[2], c1[0] * c2[1] - c1[1] * c2[0]])
    return n


def vecdot(v, w):
    tl = np.dot(v, w)
    bl = np.linalg.norm(v) * np.linalg.norm(w)

    if bl == 0:
        return 1.0

    return tl / bl


def find_closest(P1, P2, P3=None, method='fast_andoyer'):
    C1 = polar2cartesian(P1)
    C2 = polar2cartesian(P2)
    if P2.shape == 'line':
        return P2

    if P3 == None:
        # End of line case ..
        O = C1 - C2
        vl = np.linalg.norm(O)
        if (vl != 0):
            O = (P2.radius / vl) * O
            CL = O + C2

        else:
            return P2
        result = cartesian2polar(CL)
        return result
    C3 = polar2cartesian(P3)
    # What if they have the same centre?
    if np.array_equal(C1, C3):
        O = C1 - C2
        vl = np.linalg.norm(O)
        if (vl < 0.01):
            # They're all the same point .. not much we can do until next iteration
            return P2

        O = (P2.radius / vl) * O
        CL = O + C2

        result = cartesian2polar(CL)
        # Keep radius for next iteration
        result.radius = P2.radius
        return result

    # What if the 1st and 2nd have the same centre?
    T = C1 - C2
    if np.linalg.norm(T) < 0.01:
        O = C3 - C2
        vl = np.linalg.norm(O)
        if vl > 0:
            O = (P2.radius / vl) * O

        CL = O + C2

        result = cartesian2polar(CL)
        return result

    u = ((C2[0] - C1[0]) * (C3[0] - C1[0]) + (C2[1] - C1[1]) * (C3[1] - C1[1]) +
         (C2[2] - C1[2]) * (C3[2] - C1[2])) / ((C3[0] - C1[0]) * (C3[0] - C1[0]) +
                                               + (C3[1] - C1[1]) * (C3[1] - C1[1])
                                               + (C3[2] - C1[2]) * (C3[2] - C1[2]))
    # print "u=$u cart dist=", vector_length($T), " polar dist=", distance($P1, $P2), "\n";

    N = C1 + (u * (C3 - C1))
    CL = N
    PR = cartesian2polar(CL)
    test = distance(PR, P2, method)
    if (u >= 0 and u <= 1) and (distance(PR, P2, method) < P2.radius):
        # Ok - we have a 180deg? connect
        # print("180 deg connect: u= radius=", P2.radius, "\n")
        return P2

    else:
        # find the angle between in/out line
        v = plane_normal(C1, C2)
        w = plane_normal(C3, C2)
        phi = math.acos(vecdot(v, w))
        phideg = phi * 180 / math.pi
        # print "    angle between in/out=$phideg\n";

        # div angle / 2 add to one of them to create new
        # vector and scale to cylinder radius for new point
        a = C1 - C2
        vla = np.linalg.norm(a)
        if vla > 0:
            a = a / vla
        b = C3 - C2
        vlb = np.linalg.norm(b)
        if vlb > 0:
            b = b / vlb
        O = a + b
        vl = np.linalg.norm(O)

        if phideg < 180:
            # print "    p2->radius=", $P2->{'radius'}, "\n";
            O = (P2.radius / vl) * O

        else:
            # print "    -p2->radius=", $P2->{'radius'}, "\n";
            O = (-P2.radius / vl) * O

        CL = O + C2

    result = cartesian2polar(CL)
    return result

def check_start (state, fix, tp, tolerance, min_tol_m):
    '''check if pilot
            is in correct position to take the start cylinder [state = 'ready'],
            and if he takes the start [state = 'started']'''

    if tp.how == "entry":
        # pilot must have at least 1 fix outside the start after the start time then enter
        condition = not(tp.in_radius(fix, -tolerance, -min_tol_m))
        started = tp.in_radius(fix, tolerance, min_tol_m)
    else:
        # pilot must have at least 1 fix inside the start after the start time then exit
        condition = tp.in_radius(fix, tolerance, min_tol_m)
        started = not(tp.in_radius(fix, -tolerance, -min_tol_m))

    if state == 'ready':
        return condition
    else:
        return started

def tp_made (fix, tp, tolerance, min_tol_m):
    '''check if pilot is in correct position to take the cylinder'''

    if tp.how == "entry":
        # pilot must have at least 1 fix inside the cylinder
        condition = tp.in_radius(fix, tolerance, min_tol_m)
    else:
        # pilot must have at least 1 fix outside the cylinder
        condition = not(tp.in_radius(fix, -tolerance, -min_tol_m))

    return condition

def start_made_civl (fix, next, start, tolerance, min_tol_m):
    '''check if pilot is in correct position to take the start cylinder
    This version is following the FAI Rules / CIVL Gap Rules 2018 8.1.1

    CIVL rules do not make distinction between start and turnpoints, but this creates
    problems in case of a tesk with enter cylinder and first turnpoint that differs from start wpt.
    FS considers that a exit start.
    We prefer to use XCTrack approach.
    This version DOES USE a Entry/Exit flag (start only)
    '''

    if start.how == "entry":
        #entry start cylinder
        condition = not(start.in_radius(fix, -tolerance, -min_tol_m)) and start.in_radius(next, tolerance, min_tol_m)
    else:
        #exit start cylinder
        condition = start.in_radius(fix, tolerance, min_tol_m) and not(start.in_radius(next, -tolerance, -min_tol_m))

    return condition

def tp_made_civl (fix, next, tp, tolerance, min_tol_m):
    '''check if pilot is in correct position to take the cylinder
    This version is following the FAI Rules / CIVL Gap Rules 2018 8.1.1
    crossingturnpoint[i]: ∃j:
    (distance(center[i],trackpoint[j]) >= innerRadius[i] ∧ distance(center[i] , trackpoint[j+1] ) <= outerRadius[i] )
    ∨
    (distance(center[i] , trackpoint[j+1] ) >= innerRadius[i] ∧ distance(center[i] , trackpoint[j] ) <= outerRadius[i] )

    This version DOES NOT USE a Entry/Exit flag
    '''

    condition = (   (not(tp.in_radius(fix, -tolerance, -min_tol_m)) and (tp.in_radius(next, tolerance, min_tol_m)))
                or
                    (not(tp.in_radius(next, -tolerance, -min_tol_m)) and (tp.in_radius(fix, tolerance, min_tol_m))) )

    return condition

def tp_time_civl (fix, next, tp):

    '''return correct time based on CIVL rules'''

    '''
    The time of a crossing depends on whether it actually cuts across the actual cylinder,
    or whether both points lie within the tolerance band, but on the same side of the actual cylinder.

    (distance(center , trackpoint[j] ) < radius ∧ distance(center , trackpoint[j+1] ) < radius )
    ∨
    (distance(center , trackpoint[j] ) > radius ∧ distance(center , trackpoint[j+1] ) > radius )
    ∧
    turnpoint = ESS: crossing.time = trackpoint[j+1].time

    (distance(center , trackpoint[j] ) < radius ∧ distance(center , trackpoint[j+1] ) < radius )
    ∨
    (distance(center , trackpoint[j] ) > radius ∧ distance(center , trackpoint[j+1] ) > radius )
    ∧
    turnpoint ≠ ESS: crossing.time = trackpoint[j].time

    (distance(center , trackpoint[j] ) < radius ∧ distance(center , trackpoint[j+1] ) > radius )
    ∨
    (distance(center , trackpoint[j] ) > radius ∧ distance(center , trackpoint[j+1] ) < radius )
    crossing.time = interpolateTime(trackpoint[j],trackpoint[j+1])
    '''

    from route import distance

    if (    (tp.in_radius(fix, 0, 0) and tp.in_radius(next, 0, 0))
            or
            (not(tp.in_radius(fix, 0, 0)) and not(tp.in_radius(next, 0, 0)))):
        return (fix.rawtime if tp.type != 'endspeed' else next.rawtime)
    else:
        '''interpolate time:
        Will use distance from radius of the two points, and the proportion of times'''
        d1      = abs(distance(tp, fix)  - tp.radius)
        d2      = abs(distance(tp, next) - tp.radius)
        speed   = (d1+d2)/(next.rawtime - fix.rawtime)
        t       = round((fix.rawtime + d1/speed), 2)
        return t

def in_semicircle(self, wpts, wmade, coords):
    wpt = wpts[wmade]
    fcoords = namedtuple('fcoords', 'flat flon')  # wpts don't have flon/flat so make them for polar2cartesian
    f = fcoords(coords.lat * math.pi / 180, coords.lon * math.pi / 180)
    prev = wmade - 1
    while prev > 0 and wpt.lat == wpts[prev].lat and wpt.lon == wpts[prev].lon:
        prev -= prev

    c = polar2cartesian(wpt)
    p = polar2cartesian(wpts[prev])

    # vector that bisects the semi-circle pointing into occupied half plane
    bvec = c - p
    pvec = polar2cartesian(f) - c

    # dot product
    dot = vecdot(bvec, pvec)
    if (dot > 0):
        return 1

    return 0

def rawtime_float_to_hms(timef):
    """Converts time from floating point seconds to hours/minutes/seconds.

    Args:
        timef: A floating point time in seconds to be converted

    Returns:
        A namedtuple with hours, minutes and seconds elements
    """
    time = int(round(timef))
    hms = namedtuple('hms', ['hours', 'minutes', 'seconds'])

     return hms(math.floor(time / 3600), math.floor((time % 3600) / 60), math.floor(time % 60))


def distance_flown(fix, i, short_route, wpt, distances_to_go):
    """Calculate distance flown
        For exit wpts it uses distance from cylinders"""

    if (wpt.how == 'entry'
            or wpt.shape == 'line') :
        dist_to_next = distance(fix, short_route[i])
    else:
        dist_to_center = distance(fix, wpt)
        dist_to_next = max(wpt.radius - dist_to_center, 0)

    dist_flown = distances_to_go[0] - (dist_to_next + distances_to_go[i])

    return dist_flown


def fast_andoyer(p1, p2):
    flattening = f  # ELLIPSOIDS['WGS-84'][2]
    semi_major_axis = a  # ELLIPSOIDS['WGS-84'][0] * 1000

    lat1r = math.radians(p1.lat)
    lon1r = math.radians(p1.lon)
    lat2r = math.radians(p2.lat)
    lon2r = math.radians(p2.lon)

    dlon = lon2r - lon1r
    cos_dlon = math.cos(dlon)
    sin_lat1 = math.sin(lat1r)
    cos_lat1 = math.cos(lat1r)
    sin_lat2 = math.sin(lat2r)
    cos_lat2 = math.cos(lat2r)

    cos_d = sin_lat1 * sin_lat2 + cos_lat1 * cos_lat2 * cos_dlon
    if (cos_d < -1):
        cos_d = -1
    elif (cos_d > 1):
        cos_d = 1

    d = math.acos(cos_d)
    sin_d = math.sin(d)

    diffsinlat = sin_lat1 - sin_lat2
    sumsinlat = sin_lat1 + sin_lat2
    K = diffsinlat * diffsinlat
    L = sumsinlat * sumsinlat
    three_sin_d = 3 * sin_d

    one_minus_cos_d = 1 - cos_d
    one_plus_cos_d = 1 + cos_d

    if one_minus_cos_d == 0:
        H = 0
    else:
        H = (d + three_sin_d) / one_minus_cos_d

    if one_plus_cos_d == 0:
        G = 0
    else:
        G = (d - three_sin_d) / one_plus_cos_d
    dd = -(flattening / 4.0) * (H * K + G * L)
    return semi_major_axis * (d + dd)


def calcBearing(lat1, lon1, lat2, lon2):
    return Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)['azi1']


def opt_goal(p1, p2):
    if p2.shape == 'line':
        #print('last tp is p2. lat{} lon{}'.format(p2.lat, p2.lon)
        return Turnpoint(lat=p2.lat, lon=p2.lon, type='optimised', radius=0, shape='optimised', how='optimised')
    else:
        #print(f'radius:{p2.radius}')
        p = geod.Direct(p2.lat, p2.lon, calcBearing(p2.lat, p2.lon, p1.lat, p1.lon), p2.radius)
        return Turnpoint(lat=p['lat2'], lon=p['lon2'], type='optimised', radius=0, shape='optimised', how='optimised')


def opt_wp(p1, p2, p3, r2):
    if p3 is None:
        return opt_goal(p1, p2)
    p2_1 = calcBearing(p2.lat, p2.lon, p1.lat, p1.lon)
    #if the next two points have the same center then the angle is given as 180, which is an error.
    # Set to same as p2_1 to force the net angle to be same as first angle.
    if p2.lat == p3.lat and p2.lon == p3.lon:
        p2_3 = p2_1
    else:
        p2_3 = calcBearing(p2.lat, p2.lon, p3.lat, p3.lon)

    if p2_1 < 0:
        p2_1 += 360
    if p2_3 < 0:
        p2_3 += 360

    #print('p2->p1', p2_1)
    #print('p2->p3', p2_3)

    angle = abs(p2_1 - p2_3)
    #print('abs angle:', angle)
    if angle > 180:
        angle = 360 - angle

    angle = angle / 2

    #print('angle/2:', angle)
    major = max(p2_1, p2_3)
    minor = min(p2_1, p2_3)
    if (360 - major + minor) < 180:
        if (360 - major) > angle:
            angle = major + angle
        else:
            angle = minor - angle
    else:
        angle = minor + angle

    #print('final angle:', angle)
    opt_point = geod.Direct(p2.lat, p2.lon, angle, r2)
    return Turnpoint(lat=opt_point['lat2'], lon=opt_point['lon2'], type='optimised', radius=0, shape='optimised', how='optimised')


def opt_wp_exit(opt, t1, exit):
    # search for point that opt line crosses exit cylinder
    bearing = calcBearing(opt.lat, opt.lon, t1.lat, t1.lon)
    distance = geod.Inverse(opt.lat, opt.lon, t1.lat, t1.lon)['s12']
    point = opt
    found = False
    d1 = distance / 2
    direction = ''
    while not found:

        p = geod.Direct(opt.lat, opt.lon, bearing, distance)
        point = Turnpoint(lat=p['lat2'], lon=p['lon2'], type='optimised', radius=0, shape='optimised', how='optimised')
        dist_from_centre = int(round(geod.Inverse(point.lat, point.lon, exit.lat, exit.lon)['s12']))
        if dist_from_centre > exit.radius:
            if direction != 'plus':
                d1 = d1 / 2  # if we change direction halve the increment
            distance = distance + d1
            direction = 'plus'
        elif dist_from_centre < exit.radius:
            if direction != 'minus':
                d1 = d1 / 2  # if we change direction halve the increment
            distance = distance - d1
            direction = 'minus'
        else:
            found = True
    return point


def opt_wp_enter(opt, t1, enter):
    # search for point that opt line crosses enter cylinder
    bearing = calcBearing(opt.lat, opt.lon, t1.lat, t1.lon)
    distance = geod.Inverse(opt.lat, opt.lon, t1.lat, t1.lon)['s12']
    point = opt
    found = False
    d1 = distance / 2
    direction = ''
    while not found:

        p = geod.Direct(opt.lat, opt.lon, bearing, distance)
        point = Turnpoint(lat=p['lat2'], lon=p['lon2'], type='optimised', radius=0, shape='optimised', how='optimised')
        dist_from_centre = int(round(geod.Inverse(point.lat, point.lon, enter.lat, enter.lon)['s12']))
        if dist_from_centre > enter.radius:
            if direction != 'plus':
                d1 = d1 / 2  # if we change direction halve the increment
            distance = distance + d1
            direction = 'plus'
        elif dist_from_centre < enter.radius:
            if direction != 'minus':
                d1 = d1 / 2  # if we change direction halve the increment
            distance = distance - d1
            direction = 'minus'
        else:
            found = True
    return point

def get_line(turnpoints):
    '''returns line segment extremes'''
    if not (turnpoints[-1].shape == 'line'):
        return []

    from pyproj import Geod

    clon, clat  = turnpoints[-1].lon, turnpoints[-1].lat        # center point of the line
    len         = (turnpoints[-1].radius)/2
    g           = Geod(ellps="WGS84")

    for t in reversed(list(turnpoints)):
        if not (t.lat == clat and t.lon == clon):
            flon, flat      = t.lon, t.lat
            az1, az2, d     = g.inv(clon, clat, flon, flat)
            lon1, lat1, az  = g.fwd(clon, clat, az1-90, len)
            lon2, lat2, az  = g.fwd(clon, clat, az1+90, len)
            # print(f'Line: {lat1}, {lon1} - {lat2}, {lon2}')

            return [Turnpoint(lat1, lon1, 0, 'optimised', 'optimised', 'optimised'),
                    Turnpoint(lat2, lon2, 0, 'optimised', 'optimised', 'optimised')]

    ''' if all waypoints have same coordinates, returns a north-south line'''
    lon1, lat1, az = g.fwd(clon, clat, 0, len)
    lon2, lat2, az = g.fwd(clon, clat, 180, len)

    return [Turnpoint(lat1, lon1, 0, 'optimised', 'optimised', 'optimised'),
            Turnpoint(lat2, lon2, 0, 'optimised', 'optimised', 'optimised')]



"""
Procedures for Task Short Distance Calculation
Using John Stevenson's Algorithm

BEGIN HERE
"""

def get_shortest_path(task):
    ''' Inputs:
            task  - Obj: task object
    '''
    import sys
    from myconn import Database
    from pyproj import Proj

    last_dist   = sys.maxsize       # inizialise to max integer
    method      = "fast_andoyer"    # method to calculate distance on ellipsoid
    finished    = False

    '''get projection center'''
    clat, clon  = get_proj_center(task.turnpoints)

    '''define earth model'''
    wgs84       = Proj("+init=EPSG:4326") # LatLon with WGS84 datum used by GPS units and Google Earth

    '''calculate planar projection'''
    '''method 1: calculate UTM zone from center coordinates and use corresponding EPSG Projection'''
    # EPSG  = 32700-round((45+clat)/90)*100+round((183+clon)/6)
    # print(f"EPSG: {EPSG}")
    # local = Proj(f"+init=EPSG:{EPSG}")
    '''method 2: create a custom trasverse mercatore projection upon center coordinates'''
    tmerc       = Proj(f"+proj=tmerc +lat_0={clat} +lon_0={clon} +k_0=1 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")

    '''create a list of cPoint obj from turnpoint list'''
    points      = convert(task.turnpoints, wgs84, tmerc)

    count       = len(points)   # numer of waypoints
    ESS_index   = [i for i, e in enumerate(task.turnpoints) if e.type == 'endspeed'][0]
    if not (task.turnpoints[-1].shape == 'line'):
        line    = []
        print(f'is line: {task.turnpoints[-1].shape}')
    else:
        ends    = get_line(task.turnpoints)
        line    = convert(ends, wgs84, tmerc)
        print(f'line: {line[0].x}, {line[0].y} - {line[1].x}, {line[1].y}')

    print('***')
    print(f'center {clat} , {clon}')
    print(f'WPT Count: {count}  |  ESS Index: {ESS_index}')
    for idx, tp in enumerate(task.turnpoints):
        print(f'n. {idx}')
        pt = points[idx]
        print(f'tp:   lat {tp.lat} |  lon {tp.lon} |  radius {tp.radius} |  shape {tp.shape} |  type {tp.type}')
        print(f'pt:   x {pt.x} |  y {pt.y} |  radius {pt.radius}')

    ''' Settings'''
    opsCount        = count * 10    # number of operations allowed
    tolerance       = 1.0           # meters, difference between results under which iteration will stop

    while ( not finished and opsCount > 0 ):
        planar_dist = optimize_path(points, count, ESS_index, line)
        ''' See if the difference between the last distance id
            smaller than the tolerance'''
        finished    = (last_dist - planar_dist < tolerance)
        last_dist   = planar_dist
        opsCount    -= 1
        print(f'iterations made: {count * 10 - opsCount} | distance: {planar_dist}')

    '''create optimised points positions on earth model (lat, lon)'''
    optimised = convert(points, wgs84, tmerc, 'from')

    # opt_dist = 0.0
    # for i in range(1, len(optimised)):
    #     leg_dist = distance(optimised[i-1], optimised[i], method)
    #     opt_dist += leg_dist
    #
    # task.optimised_turnpoints = optimised
    #
    # ''' update task short route'''
    # with Database() as db:
    #     query = ''
    #     for idx, item in enumerate(task.turnpoints):
    #         tp = task.optimised_turnpoints[idx]
    #         query = """ UPDATE `tblTaskWaypoint`
    #                     SET
    #                         `ssrLatDecimal` = %s,
    #                         `ssrLongDecimal` = %s
    #                     WHERE `tawPk` = %s
    #                     LIMIT 1"""
    #
    #         params = [tp.lat, tp.lon, item.id]
    #         db.execute(query, params)
    #
    # return opt_dist

    return optimised

def get_proj_center(turnpoints):
    '''finds the fix(lat, lon) rapresenting the center of
        cartesian projection for the waypoint file'''
    from statistics import mean

    lat = mean(t.lat for t in turnpoints)
    lon = mean(t.lon for t in turnpoints)
    return lat, lon

def convert(elements, earth_model, projection, direction='to'):
    ''' transform Turnpoints position (lon, lat) to projection coordinates (x, y), and back

        input:
        elements    - obj list
        earth model - default is wgs84
        projection  - default is trasverse mercatore calculated on mean turnpoints position
        direction   - 'to' or 'from' projection'''

    from route  import Turnpoint
    from pyproj import Transformer

    result = []

    if direction == 'to':
        t  = Transformer.from_proj(earth_model, projection)
        for tp in elements:
            x, y = t.transform(tp.lon, tp.lat)
            result.append(cPoint(x=x, y=y, radius=tp.radius))
    elif direction == 'from':
        t  = Transformer.from_proj(projection, earth_model)
        for fix in elements:
            lon, lat = t.transform(fix.fx, fix.fy)
            result.append(Turnpoint(lat=lat, lon=lon, type='optimised', radius=0, shape='optimised', how='optimised'))

    return result

def optimize_path(points, count, ESS_index, line):
    ''' Inputs:
            points      - array of point objects
            count       - number of points (not needed)
            ESS_index   - index of the ESS point, or -1 (not needed, we have type)
            line        - goal line endpoints, or empty array'''

    from math import hypot

    distance    = 0
    hasLine     = (len(line) == 2)
    for idx in range(1, count):
        '''Get the target cylinder c and its preceding and succeeding points'''
        c, a, b = get_target_points(points, count, idx, ESS_index)
        if (idx == count - 1 and hasLine):
            process_line(line, c, a)
        else:
            process_cylinder(c, a, b)

        '''Calculate the distance from A to the C fix point'''
        legDistance = hypot(a.x - c.fx, a.y - c.fy)
        distance    += legDistance

    return distance

def get_target_points(points, count, index, ESS_index):
    '''Inputs:
        points  - array of point objects
        count   - number of points
        index   - index of the target cylinder (from 1 upwards)
        ESS_index - index of the ESS point, or -1 '''

    '''Set point C to the target cylinder'''
    c = points[index]
    '''Create point A using the fix from the previous point'''
    a = cPoint.create_from_fix(points[index - 1])
    '''Create point B using the fix from the next point
    use point C center for the lastPoint and ESS_index).'''
    if ((index == count - 1) or (index == ESS_index)):
        b = cPoint.create_from_center(c)
    else:
        b = cPoint.create_from_fix(points[index + 1])

    return c, a, b

def process_cylinder(c, a, b):
    '''Inputs:
        c, a, b - target cylinder, previous point, next point'''

    distAC, distBC, distAB, distCtoAB = get_relative_distances(c, a, b)
    if (distAB == 0.0):
        '''A and B are the same point: project the point on the circle'''
        project_on_circle(c, a.x, a.y, distAC)
    elif (point_on_circle(c, a, b, distAC, distBC, distAB, distCtoAB)):
        '''A or B are on the circle: the fix has been calculated'''
        return
    elif (distCtoAB < c.radius):
        '''AB segment intersects the circle, but is not tangent to it'''
        if (distAC < c.radius and distBC < c.radius):
            '''A and B are inside the circle'''
            set_reflection(c, a, b)
        elif (distAC < c.radius and distBC > c.radius or
             (distAC > c.radius and distBC < c.radius)):
            '''One point inside, one point outside the circle'''
            set_intersection_1(c, a, b, distAB)
        elif (distAC > c.radius and distBC > c.radius):
            '''A and B are outside the circle'''
            set_intersection_2(c, a, b, distAB)
    else:
        '''A and B are outside the circle and the AB segment is
        either tangent to it or or does not intersect it'''
        set_reflection(c, a, b)

def get_relative_distances(c, a, b):
    '''Inputs:
        c, a, b - target cylinder, previous point, next point'''

    from math import sqrt, hypot

    '''Calculate distances AC, BC and AB'''
    distAC  = hypot(a.x - c.x, a.y - c.y)
    distBC  = hypot(b.x - c.x, b.y - c.y)
    len2    = (a.x - b.x) ** 2 + (a.y - b.y) ** 2
    distAB  = sqrt(len2)
    '''Find the shortest distance from C to the AB line segment'''
    if (len2 == 0.0):
        '''A and B are the same point'''
        distCtoAB = distAC
    else:
        t   = ((c.x - a.x) * (b.x - a.x) + (c.y - a.y) * (b.y - a.y)) / len2
        if (t < 0.0):
            '''Beyond the A end of the AB segment'''
            distCtoAB = distAC
        elif (t > 1.0):
            '''Beyond the B end of the AB segment'''
            distCtoAB = distBC
        else:
            '''On the AB segment'''
            cpx = t * (b.x - a.x) + a.x
            cpy = t * (b.y - a.y) + a.y
            distCtoAB = hypot(cpx - c.x, cpy - c.y)

    return distAC, distBC, distAB, distCtoAB

def get_intersection_points(c, a, b, distAB):
    '''Inputs:
            c, a, b - target cylinder, previous point, next point
            distAB  - AB line segment length'''

    from math import sqrt

    '''Find e, which is on the AB line perpendicular to c center'''
    dx = (b.x - a.x) / distAB
    dy = (b.y - a.y) / distAB
    t2 = dx * (c.x - a.x) + dy * (c.y - a.y)
    ex = t2 * dx + a.x
    ey = t2 * dy + a.y
    '''Calculate the intersection points, s1 and s2'''
    dt2 = c.radius ** 2 - (ex - c.x) ** 2 - (ey - c.y) ** 2
    dt  = sqrt(dt2) if dt2 > 0 else 0
    s1x = (t2 - dt) * dx + a.x
    s1y = (t2 - dt) * dy + a.y
    s2x = (t2 + dt) * dx + a.x
    s2y = (t2 + dt) * dy + a.y

    return cPoint.create(s1x, s1y), cPoint.create(s2x, s2y), cPoint.create(ex, ey)

def point_on_circle(c, a, b, distAC, distBC, distAB, distCtoAB):
    '''Inputs:
        c, a, b - target cylinder, previous point, next point
        Distances between the points'''

    from math import fabs

    if (fabs(distAC - c.radius) < 0.0001):
        '''A on the circle (perhaps B as well): use A position'''
        c.fx = a.x
        c.fy = a.y
        return True

    if (fabs(distBC - c.radius) < 0.0001):
        '''B on the circle'''
        if (distCtoAB < c.radius and distAC > c.radius):
            '''AB segment intersects the circle and A is outside it'''
            set_intersection_2(c, a, b, distAB)
        else:
            '''Use B position'''
            c.fx = b.x
            c.fy = b.y

        return True

    return False

def project_on_circle(c, x, y, len):
    '''Inputs:
        c       - the circle
        x, y    - coordinates of the point to project
        len     - line segment length, from c to the point'''
    if (len == 0.0):
        '''The default direction is eastwards (90 degrees)'''
        c.fx = c.radius + c.x
        c.fy = c.y
    else:
        c.fx = c.radius * (x - c.x) / len + c.x
        c.fy = c.radius * (y - c.y) / len + c.y

def set_intersection_1(c, a, b, distAB):
    '''Inputs:
        c, a, b     - target cylinder, previous point, next point
        distAB      - AB line segment length'''

    from math import fabs, hypot

    '''Get the intersection points (s1, s2)'''
    s1, s2, e = get_intersection_points(c, a, b, distAB)
    as1 = hypot(a.x - s1.x, a.y - s1.y)
    bs1 = hypot(b.x - s1.x, b.y - s1.y)
    '''Find the intersection lying between points a and b'''
    if (fabs(as1 + bs1 - distAB) < 0.0001):
        c.fx = s1.x
        c.fy = s1.y
    else:
        c.fx = s2.x
        c.fy = s2.y

def set_intersection_2(c, a, b, distAB):
    '''Inputs:
         c, a, b    - target cylinder, previous point, next point
         distAB     - AB line segment length'''

    from math import fabs, hypot

    '''Get the intersection points (s1, s2) and midpoint (e)'''
    s1, s2, e = get_intersection_points(c, a, b, distAB)
    as1     = hypot(a.x - s1.x, a.y - s1.y)
    es1     = hypot(e.x - s1.x, e.y - s1.y)
    ae      = hypot(a.x - e.x, a.y - e.y)
    '''Find the intersection between points a and e'''
    if (fabs(as1 + es1 - ae) < 0.0001):
        c.fx = s1.x
        c.fy = s1.y
    else:
        c.fx = s2.x
        c.fy = s2.y

def set_reflection(c, a, b):
    '''Inputs:
        c, a, b - target circle, previous point, next point'''

    from math import hypot

    ''' The lengths of the adjacent triangle sides (af, bf) are
        proportional to the lengths of the cut AB segments (ak, bk)'''
    af = hypot(a.x - c.fx, a.y - c.fy)
    bf = hypot(b.x - c.fx, b.y - c.fy)
    t = af / (af + bf)
    '''Calculate point k on the AB segment'''
    kx = t * (b.x - a.x) + a.x
    ky = t * (b.y - a.y) + a.y
    kc = hypot(kx - c.x, ky - c.y)
    '''Project k on to the radius of c'''
    project_on_circle(c, kx, ky, kc)

def process_line(line, c, a):
    '''Inputs:
        line - array of goal line endpoints
        c, a - target (goal), previous point'''

    g1, g2  = line[0], line[1]
    len2    = (g1.x - g2.x) ** 2 + (g1.y - g2.y) ** 2
    if (len2 == 0.0):
        '''Error trapping: g1 and g2 are the same point'''
        c.fx = g1.x
        c.fy = g1.y
    else:
        t = ((a.x - g1.x) * (g2.x - g1.x) + (a.y - g1.y) * (g2.y - g1.y)) / len2
        if (t < 0.0):
            '''Beyond the g1 end of the line segment'''
            c.fx = g1.x
            c.fy = g1.y
        elif (t > 1.0):
            '''Beyond the g2 end of the line segment'''
            c.fx = g2.x
            c.fy = g2.y
        else:
            '''Projection falls on the line segment'''
            c.fx = t * (g2.x - g1.x) + g1.x
            c.fy = t * (g2.y - g1.y) + g1.y

"""
Procedures for Task Short Distance Calculation
Using John Stevenson's Algorithm

END HERE
"""
