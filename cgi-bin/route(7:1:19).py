"""
Route Library
contains
	Task()
	Turnpoint()
	Flight_result()

Use: import route

Stuart Mackintosh - 2018
"""

'''used for finding shortest route and task validation.
as we are using fast_andover we don't need the geopy lib. if we hard code the WSG84 parameters.
Have also included: task object, turnpoint object, a task result object (results for an IGC processed with task.check_flight)
Task object also includes the code to create from XCtrack file. There is old code for creating from LK8000, but we probably don't need this.

will need to adapt to take IGC from aerofiles instead of igc_lib if we decide to use it.

TO DO:

add database write and update to task object,
add database write for shortest route.
Add support for FAI Sphere ???


add support for elapsed time tasks and also jump the gun for HG.

'''

import math
import numpy as np
# from geopy.distance import geodesic, ELLIPSOIDS, vincenty
import json
from collections import namedtuple
from myconn import Database

a = 6378137  # WSG84 major meters
b = 6356752.3142  # WGS84 minor meters
f = 0.0033528106647474805  # WGS84 flattening


# a = ELLIPSOIDS['WGS-84'][0] * 1000  # WSG84 major meters: 6378137
# b = ELLIPSOIDS['WGS-84'][1] * 1000  # WGS84 minor meters: 6356752.3142
# f = ELLIPSOIDS['WGS-84'][2] #WGS84 flattening

class polar(object):
    def __init__(self, lat=0, lon=0, flat=0, flon=0, shape=None, radius=0):
        self.lat = lat
        self.lon = lon
        self.flat = flat
        self.flon = flon
        self.shape = shape
        self.radius = radius


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


def distance(p1, p2):
    # return geodesic((p1.lat, p1.lon), (p2.lat, p2.lon)).meters
    # return vincenty((p1.lat, p1.lon), (p2.lat, p2.lon)).meters
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


def find_closest(P1, P2, P3=None):
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
    test = distance(PR, P2)
    if (u >= 0 and u <= 1) and (distance(PR, P2) < P2.radius):
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


class Turnpoint:
    """ single turnpoint in a task.
    Attributes:
        lat: a float, latitude in degrees
        lon: a float, longitude in degrees
        dlat: a float, latitude (for optimised route)
        dlon: a float, longitude (for optimised route)
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
        self.lat = lat
        self.lon = lon
        self.flat = lat * math.pi / 180
        self.flon = lon * math.pi / 180
        self.radius = radius
        self.type = type
        self.shape = shape
        self.how = how

        assert type in ["launch", "speed", "waypoint", "endspeed", "goal"], \
            "turnpoint type is not valid: %r" % type
        assert shape in ["line", "circle"], "turnpoint shape is not valid: %r" % shape
        assert how in ["entry", "exit"], "turnpoint how (direction) is not valid: %r" % how

    def in_radius(self, fix, t, tm):
        """Checks whether the provided GNSSFix is within the radius"""
        if t < 0:
            tol = min(tm, self.radius * t)
        else:
            tol = max(tm, self.radius * t)

        return distance(self, fix) < self.radius + tol


class Task:
    """Stores a task definition and checks if a flight has achieved the turnpoints in the task.
    Attributes:
        turnpoints: A list of Turnpoint objects.
        start_time: Raw time (seconds past midnight). The time the race starts.
                    The pilots must start at or after this time.
        end_time: Raw time (seconds past midnight). The time the race ends.
                  The pilots must finish the race at or before this time.
                  No credit is given for distance covered after this time.
        task_type: Race to goal, Elapsed time etc.
        ShortRouteDistance: optimised distance, calculated with method find_shortest_route
        StartSSDistance: optimised distance to SSS, calculated with method find_shortest_route
        EndSSDistance: optimised distance to ESS from takeoff, calculated with method find_shortest_route
        SSDistance: optimised distance from SSS to ESS, calculated with method find_shortest_route

    methods:
        read_task(task_id): reads task from DB
        create_from_xctrack_file: reads task from xctrack file.
        create_from_lkt_file: reads task from LK8000 file, old code probably needs fixing, but unlikely to be used now we have xctrack
        find_shortest_route: find optimised distances.
        check_flight: checks a flight against the task
    """
    def __init__(self, turnpoints, start_time, end_time, task_type):
        self.turnpoints = turnpoints
        self.start_time = start_time
        self.end_time = end_time
        self.task_type = task_type
        self.ShortRouteDistance = 0
        self.StartSSDistance = 0
        self.EndSSDistance = 0
        self.SSDistance = 0
        self.Distance = 0
        self.optimised_turnpoints = []

    @staticmethod
    def read_task(task_id):
        """Reads Task from database
        takes tasPk as argument"""
        turnpoints = []
        if task_id < 1:
            print("task not present in database ", task_id)

        query = """SELECT TIME_TO_SEC(T.tasStartTime) AS sstime,
                           TIME_TO_SEC(T.tasFinishTime) AS endtime, 
                           T.*,
                           C.comTimeOffset, 
                           C.comClass, 
                           F.forMargin 
                           FROM 
                            tblTask T 
                            JOIN tblCompetition C USING (comPk) 
                            JOIN tblForComp FC USING (comPk) 
                            LEFT OUTER  JOIN tblFormula F USING (forPk) 
                            WHERE T.tasPk =  %s"""
        params=(task_id,)
        with Database() as db:
            # get the task details.
            t = db.fetchone(query, params)
        if t is None:
            print('Not a valid task')
            return

        start_time = t['sstime']
        end_time = t['endtime']
        task_type = t['tasTaskType']

        query = ("select tawHow, "
                 "tawRadius, "
                 "tawShape, "
                 "tawType, "
                 "rwpLatDecimal, "
                 "rwpLongDecimal "
                 "from tblTaskWaypoint T left outer join tblRegionWaypoint R "
                 "on T.rwpPk=R.rwpPk "
                 "where T.tasPk=%s "
                 "order by T.tawNumber")

        with Database() as db:
            # get the task details.
            tps = db.fetchall(query, params)

        for tp in tps:
            turnpoint = Turnpoint(tp['rwpLatDecimal'], tp['rwpLongDecimal'], tp['tawRadius'], tp['tawType'],
                                  tp['tawShape'], tp['tawHow'])
            turnpoints.append(turnpoint)
        
        task = Task(turnpoints, start_time, end_time, task_type)

        return task

    @staticmethod
    def create_from_xctrack_file(filename):
        """ Creates Task from xctrack file, which is in json format.
        """

        offset = 0

        task_file = filename

        turnpoints = []
        with open(task_file, encoding='utf-8') as json_data:
            # a bit more checking..
            print("file: ", task_file)
            try:
                t = json.load(json_data)
            except:
                print("file is not a valid JSON object")
                exit()

        startopenzulu = t['sss']['timeGates'][0]
        deadlinezulu = t['goal']['deadline']
        task_type = t['sss']['type']

        startzulu_split = startopenzulu.split(":")  # separate hours, minutes and seconds.
        deadlinezulu_split = deadlinezulu.split(":")  # separate hours, minutes and seconds.

        start_time = (int(startzulu_split[0]) + offset) * 3600 + int(startzulu_split[1]) * 60
        end_time = (int(deadlinezulu_split[0]) + offset) * 3600 + int(deadlinezulu_split[1]) * 60

        for tp in t['turnpoints'][:-1]:  # loop through all waypoints except last one which is always goal
            waytype = "waypoint"
            shape = "circle"
            how = "entry"  # default entry .. looks like xctrack doesn't support exit cylinders apart from SSS

            if 'type' in tp:
                if tp['type'] == 'TAKEOFF':
                    waytype = "launch"  # live
                    # waytype = "start"  #aws
                    how = "exit"
                if tp['type'] == 'SSS':
                    waytype = "speed"
                    if t['sss']['direction'] == "EXIT":  # get the direction form the SSS section
                        how = "exit"
                if tp['type'] == 'ESS':
                    waytype = "endspeed"
            turnpoint = Turnpoint(tp['waypoint']['lat'], tp['waypoint']['lon'], tp['radius'], waytype, shape, how)
            turnpoints.append(turnpoint)

        # goal - last turnpoint
        tp = t['turnpoints'][-1]
        waytype = "goal"
        if t['goal']['type'] == 'LINE':
            shape = "line"

        turnpoint = Turnpoint(tp['waypoint']['lat'], tp['waypoint']['lon'], tp['radius'], waytype, shape, how)
        turnpoints.append(turnpoint)

        task = Task(turnpoints, start_time, end_time, task_type)

        return task

    @staticmethod
    def create_from_lkt_file(filename):
        """ Creates Task from LK8000 task file, which is in xml format.
            LK8000 does not have End of Speed Section or task finish time.
            For the goal, at the moment, Turnpoints can't handle goal cones or lines,
            for this reason we default to goal_cylinder.
        """

        # Open XML document using minidom parser
        DOMTree = xml.dom.minidom.parse(filename)
        task = DOMTree.documentElement

        # Get the taskpoints, waypoints and time gate
        taskpoints = task.getElementsByTagName("taskpoints")[0]  # TODO: add code to handle if these tags are missing.
        waypoints = task.getElementsByTagName("waypoints")[0]
        gate = task.getElementsByTagName("time-gate")[0]
        tpoints = taskpoints.getElementsByTagName("point")
        wpoints = waypoints.getElementsByTagName("point")
        start_time = gate.getAttribute("open-time")

        start_hours, start_minutes = start_time.split(':')
        start_time = int(start_hours) * 3600 + int(start_minutes) * 60
        end_time = 23 * 3600 + 59 * 60 + 59  # default end_time of 23:59

        # create a dictionary of names and a list of longitudes and latitudes
        # as the waypoints co-ordinates are stored separate to turnpoint details
        coords = defaultdict(list)

        for point in wpoints:
            name = point.getAttribute("name")
            longitude = float(point.getAttribute("longitude"))
            latitude = float(point.getAttribute("latitude"))
            coords[name].append(longitude)
            coords[name].append(latitude)

        # create list of turnpoints
        turnpoints = []
        for point in tpoints:
            lat = coords[point.getAttribute("name")][1]
            lon = coords[point.getAttribute("name")][0]
            radius = float(point.getAttribute("radius")) / 1000

            if point == tpoints[0]:  # if it is the 1st turnpoint then it is a start
                if point.getAttribute("Exit") == "true":
                    kind = "start_exit"
                else:
                    kind = "start_enter"
            else:
                if point == tpoints[-1]:  # if it is the last turnpoint i.e. the goal
                    if point.getAttribute("type") == "line":
                        kind = "goal_cylinder"  # TODO(kuaka): change to 'line' once we can process it
                    else:
                        kind = "goal_cylinder"
                else:
                    kind = "cylinder"  # All turnpoints other than the 1st and the last are "cylinders".
                    # In theory they could be "End_of_speed_section" but this is not supported by LK8000.
                    # For paragliders it would be safe to assume that the 2nd to last is always "End_of_speed_section"

            turnpoint = Turnpoint(lat, lon, radius, kind)
            turnpoints.append(turnpoint)
        task = Task(turnpoints, start_time, end_time)
        return task

    @property
    def find_shortest_route(self):

        it1 = []
        it2 = []
        wpts = self.turnpoints

        closearr = []
        num = len(wpts)

        if num < 1:
            return 0

        if num == 1:
            first = cartesian2polar(polar2cartesian(wpts[0]))
            closearr.append(first)
            return closearr

        # Work out shortest route!
        # End points don't vary?
        it1.append(wpts[0])
        newcl = wpts[0]
        for i in range(num - 2):
            # print "From it1: $i: ", $wpts->[$i]->{'name'}, "\n";
            if wpts[i + 1].lat == wpts[i + 2].lat and wpts[i + 1].lon == wpts[i + 2].lon:
                newcl = find_closest(newcl, wpts[i + 1])
            else:
                newcl = find_closest(newcl, wpts[i + 1], wpts[i + 2])
            it1.append(newcl)
        # FIX: special case for end point ..
        newcl = find_closest(newcl, wpts[num - 1])
        it1.append(newcl)

        num = len(it1)
        it2.append(it1[0])
        newcl = it1[0]
        for i in range(num - 2):
            # print "From it2: $i: ", $wpts->[$i]->{'name'}, "\n";
            newcl = find_closest(newcl, it1[i + 1], it1[i + 2])
            it2.append(newcl)

        it2.append(it1[num - 1])

        num = len(it2)
        closearr.append(it2[0])
        newcl = it2[0]
        for i in range(num - 2):
            # print "From it3: $i: ", $wpts->[$i]->{'name'}, "\n";
            newcl = find_closest(newcl, it2[i + 1], it2[i + 2])
            closearr.append(newcl)
        closearr.append(it2[num - 1])

        opt_legs = []

        # calculate non optimised route distance.
        for wpt in range(1, len(self.turnpoints)):
            leg_dist = distance(self.turnpoints[wpt - 1], self.turnpoints[wpt])
            self.Distance = self.Distance + leg_dist

        # calculate optimised route distance
        for opt_wpt in range(1, len(closearr)):
            leg_dist = distance(closearr[opt_wpt- 1], closearr[opt_wpt])
            opt_legs.append(leg_dist)
            self.ShortRouteDistance = self.ShortRouteDistance + leg_dist

        # work out which turnpoints are SSS and ESS
        sss_wpt = 0
        ess_wpt = 0
        for wpt in range(len(self.turnpoints)):
            if self.turnpoints[wpt].type == 'speed':
                sss_wpt=wpt
            if self.turnpoints[wpt].type == 'endspeed':
                ess_wpt=wpt

        # work out self.StartSSDistance, self.EndSSDistance, self.SSDistance
        self.StartSSDistance = sum(opt_legs[0:sss_wpt])
        self.EndSSDistance = sum(opt_legs[0:ess_wpt])
        self.SSDistance = sum(opt_legs[sss_wpt:ess_wpt])
        self.optimised_turnpoints = closearr

    def check_flight(self, Flight, short_route, tolerance=0.0, min_tol_m=0):
        """ Checks a Flight object against the task.
            Args:
                   Flight: a Flight object
                   Short_route: output of find_shortest_route. Used to evaluate distance flown and lead_coeff
                   tolerance: percentage radius tolerance, default is 0
                   min_tol: minimum tolerance in meters, default is 0
            Returns:
                    a list of GNSSFixes of when turnpoints were achieved.
        """
        reached_turnpoints = []
        flight_result = Flight_result()
        flight_result.Start_time = self.start_time
        started = False
        waypoint = 1
        proceed_to_start = False
        t = 0
        distances2go = distances_to_go(short_route)
        for fix in Flight.fixes:

            if t >= len(self.turnpoints):
                break  # pilot has arrived in goal (last turnpoint) so we can stop.

            if self.end_time < fix.rawtime:
                # Task has ended
                break
            if self.turnpoints[t].type == "launch":
                # not checking launch yet
                t += 1
            # pilot must have at least 1 fix inside the start after the start time then exit
            if self.turnpoints[t].type == "speed" and self.turnpoints[t].how == "exit":
                if proceed_to_start:
                    if not self.turnpoints[t].in_radius(fix, tolerance, min_tol_m):
                        reached_turnpoints.append(fix)  # pilot has started
                        flight_result.Waypoints_achieved = 'SSS made'
                        flight_result.SSS_time = fix.rawtime
                        flight_result.SSS_time_str = (("%02d:%02d:%02d") % rawtime_float_to_hms(fix.rawtime))
                        started = True
                        t += 1

                if fix.rawtime > self.start_time and not proceed_to_start:
                    if self.turnpoints[t].in_radius(fix, tolerance, min_tol_m):
                        proceed_to_start = True  # pilot is inside start after the start time.

            # pilot must have at least 1 fix outside the start after the start time then enter
            elif self.turnpoints[t].type == "speed" and self.turnpoints[t].how == "entry":
                if proceed_to_start:
                    if self.turnpoints[t].in_radius(fix, tolerance, min_tol_m):
                        reached_turnpoints.append(fix, tolerance, min_tol_m)  # pilot has started
                        flight_result.Waypoints_achieved = 'SSS made'
                        flight_result.SSS_time = fix.rawtime
                        flight_result.SSS_time_str = (("%02d:%02d:%02d") % rawtime_float_to_hms(fix.rawtime))
                        started = True
                        t += 1
                if fix.rawtime > self.start_time and not proceed_to_start:
                    if not self.turnpoints[t].in_radius(fix, -tolerance,
                                                        -min_tol_m):  # negative tolerance so radius is smaller.-tolerance applied always to pilots advantage
                        proceed_to_start = True  # pilot is outside start after the start time.

            elif self.turnpoints[t].shape == "circle" and self.turnpoints[t].how == "entry":
                if self.turnpoints[t].in_radius(fix, tolerance, min_tol_m):
                    reached_turnpoints.append(fix)  # pilot has achieved turnpoint
                    if started:
                        flight_result.Waypoints_achieved = 'waypoint ' + str(waypoint) + ' made'
                        waypoint += waypoint
                        if self.turnpoints[t].type == "endspeed":
                            flight_result.ESS_time = fix.rawtime
                            flight_result.ESS_time_str = (("%02d:%02d:%02d") % rawtime_float_to_hms(fix.rawtime))
                            if self.task_type == 'RACE':
                                flight_result.total_time = fix.rawtime - flight_result.Start_time

                            if self.task_type == 'ELAPSED-TIME':
                                flight_result.total_time = fix.rawtime - flight_result.SSS_time
                            flight_result.total_time_str = (
                                    ("%02d:%02d:%02d") % rawtime_float_to_hms(flight_result.total_time))
                    t += 1

            elif self.turnpoints[t].shape == "circle" and self.turnpoints[t].how == "exit":
                if self.turnpoints[t].in_radius(fix, -tolerance, -min_tol_m):
                    reached_turnpoints.append(fix)  # pilot has achieved turnpoint
                    if started:
                        flight_result.Waypoints_achieved = 'waypoint ' + str(waypoint) + ' made'
                        waypoint += waypoint
                    if self.turnpoints[t].type == "endspeed":
                        flight_result.ESS_time = fix.rawtime
                        flight_result.ESS_time_str = (("%02d:%02d:%02d") % rawtime_float_to_hms(fix.rawtime))
                        if self.task_type == 'RACE':
                            flight_result.total_time = fix.rawtime - flight_result.Start_time
                        if self.task_type == 'ELAPSED-TIME':
                            flight_result.total_time = fix.rawtime - flight_result.SSS_time

                        flight_result.total_time_str = (
                                ("%02d:%02d:%02d") % rawtime_float_to_hms(flight_result.total_time))

                    t += 1
            elif self.turnpoints[t].type == "goal" and self.turnpoints[t].shape == 'line':
                if self.turnpoints[t].in_radius(fix, tolerance, min_tol_m) and in_semicircle(self, self.turnpoints, t,
                                                                                             fix):
                    reached_turnpoints.append(fix)  # pilot has achieved turnpoint
                    if started:
                        flight_result.Waypoints_achieved = 'Goal made'

            elif self.turnpoints[t].type == "goal" and self.turnpoints[t].shape == 'circle' and self.turnpoints[
                t].how == "entry":
                if self.turnpoints[t].in_radius(fix, tolerance, min_tol_m):
                    reached_turnpoints.append(fix)  # pilot has achieved turnpoint
                    if started:
                        flight_result.Waypoints_achieved = 'Goal made'

            else:
                assert False, "Unknown turnpoint type: %s" % self.turnpoints[t].type
            if flight_result.Waypoints_achieved == 'Goal made':
                flight_result.Distance_flown = distances2go[0]
            else:
                flight_result.Distance_flown = max(flight_result.Distance_flown,
                                                   distance_flown(fix, t, short_route, distances2go))
        return reached_turnpoints, flight_result


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


class Flight_result:
    """Set of statistics about a flight with respect a task.
    Attributes:
        Start_time: time the task was started . i.e relevant start gate. (zulu time)
        SSS_time: array of time(s) the pilot started, i.e. crossed the start line (zulu time)
        Waypoints achieved: the last waypoint achieved by the pilot, SSS, ESS, Goal or a waypoint number (wp1 is first wp after SSS)
        ESS_time: the time the pilot crossed the ESS (zulu time)
        total_time: the length of time the pilot took to complete the course. ESS- Start_time (for Race) or ESS - SSS_time (for elapsed)
        Lead_coeff: lead points coeff (for GAP based systems)
        """

    def __init__(self, Start_time=0, SSS_time=[], Start_time_str='', SSS_time_str='',
                 Waypoints_achieved='No waypoints achieved', ESS_time_str='', total_time_str=None, ESS_time=0,
                 total_time=None, Lead_coeff=None, Distance_flown=0):
        """

        :type Lead_coeff: int
        """
        self.Start_time_str = Start_time_str
        self.SSS_time_str = SSS_time_str
        self.Start_time = Start_time
        self.SSS_time = SSS_time
        self.Waypoints_achieved = Waypoints_achieved
        self.ESS_time = ESS_time
        self.total_time = total_time
        self.ESS_time_str = ESS_time_str
        self.total_time_str = total_time
        self.Lead_coeff = Lead_coeff
        self.Distance_flown = Distance_flown


def rawtime_float_to_hms(timef):
    """Converts time from floating point seconds to hours/minutes/seconds.

    Args:
        timef: A floating point time in seconds to be converted

    Returns:
        A namedtuple with hours, minutes and seconds elements
    """
    time = int(round(timef))
    hms = namedtuple('hms', ['hours', 'minutes', 'seconds'])

    return hms((time / 3600), (time % 3600) / 60, time % 60)


def distance_flown(fix, next_waypoint, short_route, distances_to_go):
    """Calculate distance flown"""

    dist_to_next = distance(fix, short_route[next_waypoint])
    dist_flown = distances_to_go[0] - (dist_to_next + distances_to_go[next_waypoint])

    return dist_flown


def distances_to_go(short_route):
    """calculates a list of distances from turnpoint to goal (assumes goal is the last turnpoint)"""
    t = len(short_route) - 1
    d = 0
    distance_to_go = [0]
    while t >= 1:
        d += distance(short_route[t], short_route[t - 1])
        distance_to_go.insert(0, d)
        t -= 1
    return distance_to_go


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
