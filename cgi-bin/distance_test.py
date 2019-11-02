from task import Task as T
from route import distance as calc_dist

class cPoint(object):
    '''object to be used in planar distance calculations
        x       (float)     the x coordinate
        y       (float)     the y coordinate
        radius  (int)       the radius in metres
        fx      (float)     the x coordinate of the fix
        fy      (float)     the y coordinate of the fix
        shape   (string)    circle, line
        type    (string)    launch, speed, waypoint, endspeed, goal
    '''

    def __str__(self):
        print(f'x: {str(self.x)} | y: {str(self.y)} | radius: {str(self.radius)}')

    def __init__(self, x, y, radius=0, shape='circle', type=None):
        self.x      = x
        self.y      = y
        self.fx     = x
        self.fy     = y
        self.radius = radius
        self.type   = type
        self.shape  = shape

    @classmethod
    def create(cls, x, y, radius=0):
        return cls(x=x, y=y, radius=radius)

    @staticmethod
    def create_from_center(point):
        return cPoint(point.x, point.y, point.radius, point.shape, point.type)

    @staticmethod
    def create_from_fix(point):
        return cPoint(point.fx, point.fy, point.radius, point.shape, point.type)

    @staticmethod
    def create_from_Turnpoint(tp):
        return cPoint(tp.lat, tp.lon, tp.radius, tp.shape, tp.type)

def get_proj_center(turnpoints):
    '''finds the fix(lat, lon) rapresenting the center of
        cartesian projection for the waypoint file'''
    from statistics import mean

    lat = mean(t.lat for t in turnpoints)
    lon = mean(t.lon for t in turnpoints)
    return lat, lon

def wgs84_to_tmerc(turnpoints, local):
    ''' transform ellipsoid coordinates to trasverse mercatore planar projection,
        centered on the mean point of the turnpoints list

        input:
        turnpoints      - Turnpoint obj list
        local           - projection calculated on mean turnpoint position'''

    from pyproj import Proj, Transformer

    wgs84 = Proj("+init=EPSG:4326") # LatLon with WGS84 datum used by GPS units and Google Earth
    tmerc = Transformer.from_proj(wgs84, local)
    planar_tp = []
    for tp in turnpoints:
        x, y = tmerc.transform(tp.lon, tp.lat)
        planar_tp.append(cPoint(x=x, y=y, radius=tp.radius, shape=tp.shape, type=tp.type))
    return planar_tp

def get_opt_turnpoints(wpt, points, local):
    ''' transform trasverse mercatore planar projection to ellipsoid coordinates,

        input:
        points      - cPoint obj list
        local       - projection calculated on mean turnpoint position'''

    from route import Turnpoint
    from pyproj import Proj, Transformer, Geod

    wgs84   = Proj("+init=EPSG:4326") # LatLon with WGS84 datum used by GPS units and Google Earth
    ellips  = Transformer.from_proj(local, wgs84)

    opt_turnpoints = []

    for idx, tp in enumerate(points):
        lon, lat = ellips.transform(tp.fx, tp.fy)
        # '''puts the opt. point exactly on the cylinder'''
        # az12, az21, dist = Geod(ellps="WGS84").inv(wpt[idx].lon,wpt[idx].lat,lon,lat)
        # print(f'wpt {idx}: dis {dist}')
        # lon, lat, az = Geod(ellps="WGS84").fwd(wpt[idx].lon,wpt[idx].lat,az12,wpt[idx].radius)
        opt_turnpoints.append(Turnpoint(lat=lat, lon=lon, type='optimised', radius=0, shape='optimised', how='optimised'))

    # for t in opt_turnpoints:
    #     print(f'{t.lat}, {t.lon}')

    return opt_turnpoints

def get_shortest_path(task):
    ''' Inputs:
            turnpoints  - array of point objects
    '''
    import sys
    from myconn import Database
    from pyproj import Proj

    lastDistance    = sys.maxsize   # inizialise to max integer
    finished        = False

    '''get projection center'''
    clat, clon = get_proj_center(task.turnpoints)

    '''calculate planar projection'''
    '''method 1: calculate UTM zone from center coordinates and use corresponding EPSG Projection'''
    # EPSG  = 32700-round((45+clat)/90)*100+round((183+clon)/6)
    # print(f"EPSG: {EPSG}")
    # local = Proj(f"+init=EPSG:{EPSG}")
    '''method 2: create a custom trasverse mercatore projection upon center coordinates'''
    local = Proj(f"+proj=tmerc +lat_0={clat} +lon_0={clon} +k_0=1 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")

    '''create a list of cPoint obj from turnpoint list'''
    points          = wgs84_to_tmerc(task.turnpoints, local)

    count           = len(points)   # numer of waypoints
    ESS_index       = [i for i, e in enumerate(points) if e.type == 'endspeed'][0]
    line = []

    print('***')
    print(f'center {clat} , {clon}')
    print(f'WPT Count: {count}  |  ESS Index: {ESS_index}')
    for idx, tp in enumerate(task.turnpoints):
        print(f'n. {idx}')
        pt = points[idx]
        print(f'tp:   lat {tp.lat} |  lon {tp.lon} |  radius {tp.radius} |  shape {tp.shape} |  type {tp.type}')
        print(f'pt:   x {pt.x} |  y {pt.y} |  radius {pt.radius} |  shape {pt.shape} |  type {pt.type}')

    ''' Settings'''
    opsCount        = count * 10    # number of operations allowed
    tolerance       = 1.0           # meters, difference between results under which iteration will stop

    while ( not finished and opsCount > 0 ):
        distance        = optimize_path(points, count, ESS_index, line)
        ''' See if the difference between the last distance id
            smaller than the tolerance'''
        finished        = (lastDistance - distance < tolerance)
        lastDistance    = distance
        opsCount        -= 1
        print(f'iterations made: {count * 10 - opsCount} | distance: {distance}')

    optimised = get_opt_turnpoints(task.turnpoints, points, local)

    opt_dist = 0.0
    method = "fast_andoyer"
    for i in range(1, len(optimised)):
        leg_dist = calc_dist(optimised[i-1], optimised[i], method)
        opt_dist += leg_dist

    task.optimised_turnpoints = optimised

    ''' update task short route'''
    with Database() as db:
        query = ''
        for idx, item in enumerate(task.turnpoints):
            tp = task.optimised_turnpoints[idx]
            query = """ UPDATE `tblTaskWaypoint`
                        SET
                            `ssrLatDecimal` = %s,
                            `ssrLongDecimal` = %s
                        WHERE `tawPk` = %s
                        LIMIT 1"""

            params = [tp.lat, tp.lon, item.id]
            db.execute(query, params)

    return distance, opt_dist

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

    g1 = line[0], g2 = line[1]
    len2 = (g1.x - g2.x) ** 2 + (g1.y - g2.y) ** 2
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



task = T.read(76)
print(f'org. opt. distance: {task.opt_dist}')
distance, opt_dist = get_shortest_path(task)
print(f'opt. distance on planar projection: {distance}')
print(f'opt. distance on ellipsoid: {opt_dist}')
