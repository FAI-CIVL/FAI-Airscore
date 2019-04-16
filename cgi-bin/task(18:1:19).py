"""
Route Library
contains
    Task class
    Turnpoint class

Use: from task import Task

Stuart Mackintosh - 2019
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

from route import *
import json
from myconn import Database
from calcUtils import *


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
        self.name = None
        self.id = None
        self.lat = lat
        self.lon = lon
        self.flat = lat * math.pi / 180
        self.flon = lon * math.pi / 180
        self.radius = radius
        self.type = type
        self.shape = shape
        self.how = how
        self.altitude = None

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
        ShortRouteDistance: optimised distance, calculated with method calculate_optimised_task_length
        StartSSDistance: optimised distance to SSS, calculated with method calculate_optimised_task_length
        EndSSDistance: optimised distance to ESS from takeoff, calculated with method calculate_optimised_task_length
        SSDistance: optimised distance from SSS to ESS, calculated with method calculate_optimised_task_length

    methods:
        read_task(task_id): reads task from DB
        create_from_xctrack_file: reads task from xctrack file.
        create_from_lkt_file: reads task from LK8000 file, old code probably needs fixing, but unlikely to be used now we have xctrack
        calculate_task_length: calculate non optimised distances.
        calculate_optimised_task_length: find optimised distances and waypoints.
        check_flight: checks a flight against the task
    """

    def __init__(self, turnpoints, start_time, end_time, task_type, stopped_time=None, last_start_time=None,
                 check_launch='off'):
        self.turnpoints = turnpoints
        self.task_name = None
        self.task_start_time = None
        self.start_time = start_time
        self.start_close_time = None
        self.end_time = end_time
        self.task_type = task_type
        self.ShortRouteDistance = 0
        self.StartSSDistance = 0
        self.SSInterval = 0
        self.EndSSDistance = 0
        self.SSDistance = 0
        self.Distance = 0  # non optimised distance
        self.optimised_turnpoints = []
        self.optimised_legs = []
        self.legs = []  ##non optimised legs
        self.stats = dict()  #scored task statistics
        self.results = []  #scored task results
        self.stopped_time = stopped_time  # time task was stopped.
        self.last_start_time = last_start_time  # last start gate when there are more than 1
        self.check_launch = check_launch  # check launch flag. whether we check that pilots leave from launch.
        self.arrival = None
        self.departure = None
        self.height_bonus = None
        self.comment = None

    @staticmethod
    def read_task(task_id):
        """Reads Task from database
        takes tasPk as argument"""
        turnpoints = []
        if task_id < 1:
            print("task not present in database ", task_id)

        query = """SELECT TIME_TO_SEC(T.tasStartTime) AS sstime,
                           TIME_TO_SEC(T.tasFinishTime) AS endtime, 
                           TIME_TO_SEC(T.tasLastStartTime) as LastStartTime
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
        params = (task_id,)
        with Database() as db:
            # get the task details.
            t = db.fetchone(query, params)
        if t is None:
            print('Not a valid task')
            return

        start_time = t['sstime']
        end_time = t['endtime']
        task_type = t['tasTaskType']
        stopped_time = t['tasStoppedTime']
        last_start_time = t['LastStartTime']
        check_launch = t['tasCheckLaunch']

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

        task = Task(turnpoints, start_time, end_time, task_type, stopped_time, last_start_time, check_launch)

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

    @classmethod
    def create_from_fsdb(cls, t):
        """ Creates Task from FSDB FsTask element, which is in xml format.
            Unfortunately the fsdb format isn't published so much of this is simply an
            exercise in reverse engineering.
        """
        import lxml.etree as ET
        from route import Flight_result

        tas = dict()
        stats = dict()
        turnpoints = []
        optimised_legs = []
        #results = []

        #t = tree.getroot()
        tas['tasCheckLaunch'] = 0
        tas['tasName'] = t.get('name')
        tas['id'] = 0 + int(t.get('id'))
        #print ("task id: {} - name: {}".format(tas['id'], tas['tasName']))

        """formula info"""
        f = t.find('FsScoreFormula')
        tas['tasHeightBonus'] = 'off' 
        if ((f.get('use_arrival_altitude_points') is not None and float(f.get('use_arrival_altitude_points')) > 0) 
            or f.get('use_arrival_altitude_points') is 'aatb'):
            tas['tasHeightBonus'] = 'on'
        """Departure and Arrival from formula"""
        tas['tasArrival'] = 'on' if float(f.get('use_arrival_position_points') + f.get('use_arrival_position_points')) > 0 else 'off'
        #not sure if and which type Airscore is supporting at the moment

        if float(f.get('use_departure_points')) > 0:
            tas['tasDeparture'] = 'on'
        elif float(f.get('use_leading_points')) > 0:
            tas['tasDeparture'] = 'leadout'
        else:
            tas['tasDeparture'] = 'off'

        """Task Status"""
        node = t.find('FsTaskState')
        tas['tasComment'] = None
        tas['forScorebackTime'] = int(node.get('score_back_time'))
        tas['state'] = node.get('task_state')
        tas['tasComment'] = node.get('cancel_reason')
        if tas['state'] is not 'CANCELLED':
            """I don't need if cancelled"""
            tas['tasStoppedTime'] = get_datetime(node.get('stop_time')) if not (tas['state'] == 'REGULAR') else None
            """Task Stats"""
            p = t.find('FsTaskScoreParams')
            if p is not None:
                '''a non scored task could miss this element'''
                tas['tasShortRouteDistance'] = float(p.get('task_distance'))
                tas['tasDistance'] = float(p.get('task_distance')) #need to calculate distance through centers
                tas['tasSSDistance'] = float(p.get('ss_distance'))
                stats['tasPilotsTotal'] = int(p.get('no_of_pilots_present'))
                stats['tasPilotsLaunched'] = int(p.get('no_of_pilots_flying'))
                stats['tasPilotsGoal'] = int(p.get('no_of_pilots_reaching_goal'))
                stats['tasMaxDistance'] = float(p.get('best_dist')) * 1000 # in meters
                stats['tasTotalDistanceFlown'] = float(p.get('sum_flown_distance')) * 1000 # in meters
                try:
                    '''happens this values are error strings'''
                    stats['tasQuality'] = float(p.get('day_quality'))
                    stats['tasDistQuality'] = float(p.get('distance_validity'))
                    stats['tasTimeQuality'] = float(p.get('time_validity'))
                    stats['tasLaunchQuality'] = float(p.get('launch_validity'))
                    stats['tasStopQuality'] = float(p.get('stop_validity'))
                    stats['tasAvailDistPoints'] = float(p.get('available_points_distance'))
                    stats['tasAvailLeadPoints'] = float(p.get('available_points_leading'))
                    stats['tasAvailTimePoints'] = float(p.get('available_points_time'))
                except:
                    stats['tasQuality'] = 0
                    stats['tasDistQuality'] = 0
                    stats['tasTimeQuality'] = 0
                    stats['tasLaunchQuality'] = 0
                    stats['tasStopQuality'] = 0
                    stats['tasAvailDistPoints'] = 0
                    stats['tasAvailLeadPoints'] = 0
                    stats['tasAvailTimePoints'] = 0
                stats['tasFastestTime'] = decimal_to_seconds(float(p.get('best_time'))) if float(p.get('best_time')) > 0 else 0
            for l in p.iter('FsTaskDistToTp'):
                optimised_legs.append(float(l.get('distance'))*1000)

        node = t.find('FsTaskDefinition')
        tas['qnh'] = float(node.get('qnh_setting').replace(',', '.'))
        #tas['tasDate'] = get_datetime(node.find('FsStartGate').get('open'))
        """guessing type from startgates"""
        tas['tasSSInterval'] = 0
        startgates = 0
        headingpoint = 0
        if node.get('ss') is None:
            '''open distance
                not yet implemented in Airscore'''
            tas['tasTaskType'] = 'free'
            if node.find('FsHeadingpoint') is not None:
                '''open distance with bearing'''
                headingpoint = 1
                tas['tasTaskType'] = 'free-bearing'
                tas['tasBearingLat'] = float(node.find('FsHeadingpoint').get('lat'))
                tas['tasBearingLon'] = float(node.find('FsHeadingpoint').get('lon'))
        else:
            sswpt = int(node.get('ss'))
            eswpt = int(node.get('es'))
            gtype = node.get('goal')
            tas['gstart'] = int(node.get('groundstart'))
            if node.find('FsStartGate') is None:
                '''speedrun
                    on start gate, have to get start opening time from ss wpt'''
                tas['tasTaskType'] = 'speedrun'
            else:
                '''race'''
                startgates = len(node.findall('FsStartGate'))
                tas['tasTaskType'] = 'race'
                tas['tasStartTime'] = get_datetime(node.find('FsStartGate').get('open'))
                #print ("gates: {}".format(startgates))
                if startgates > 1:
                    '''race with multiple start gates'''
                    #print ("MULTIPLE STARTS")
                    time = get_datetime(node.findall('FsStartGate')[1].get('open')).time()
                    interval = time_difference(tas['tasStartTime'].time(), time)
                    '''if prefer minutes: time_difference(tas['tasStartTime'], time).total_seconds()/60'''
                    print ("    **** interval: {}".format(interval))
                    tas['tasSSInterval'] = interval
        #print ("task type: {} - Interval: {}".format(tas['tasTaskType'], tas['tasSSInterval']))

        """Task Route"""
        for w in node.iter('FsTurnpoint'):
            wpt = dict()
            wpt['tawNumber'] = len(turnpoints) + 1
            #wpt['ssrCumulativeDist'] = c_dist.pop(0)
            wpt['rwpName'] = w.get('id')
            #print ("wpt id: {} ".format(wpt['id']))
            wpt['rwpLatDecimal'] = float(w.get('lat'))
            wpt['rwpLonDecimal'] = float(w.get('lon'))
            wpt['rwpAltitude'] = int(w.get('altitude'))
            wpt['tawRadius'] = int(w.get('radius'))
            #print ("radius: {} \n".format(wpt['radius']))
            wpt['tawShape'] = 'circle'
            #print ("   len(node) = {} - wpt['tawNumber'] = {} \n".format(len(node), wpt['tawNumber']))
            if wpt['tawNumber'] == 1:
                #print('Sono in launch')
                wpt['tawType'] = 'launch'
                tas['tasDate'] = get_datetime(w.get('open')).date()
                tas['tasTaskStart'] = get_datetime(w.get('open'))
                if 'free' in tas['tasTaskType']:
                    #print('Sono in launch - free')
                    '''get start and close time for free distance task types'''
                    tas['tasStartTime'] = get_datetime(w.get('open'))
                    tas['tasStartCloseTime'] = get_datetime(w.get('close'))
                    tas['tasFinishTime'] = get_datetime(w.get('close'))
            elif wpt['tawNumber'] == sswpt:
                #print('Sono in ss')
                wpt['tawType'] = 'speed'
                tas['tasStartCloseTime'] = get_datetime(w.get('close'))
                if 'speedrun' in tas['tasTaskType']:
                    '''get start for speedrun task types'''
                    tas['tasStartTime'] = get_datetime(w.get('open'))
            elif wpt['tawNumber'] == eswpt:
                #print('Sono in es')
                wpt['tawType'] = 'endspeed'
                tas['tasFinishTime'] = get_datetime(w.get('close'))
            elif wpt['tawNumber'] == len(node) - startgates - headingpoint: #need to remove FsStartGate and FsHeadingpoint nodes from count
                #print('Sono in goal')
                wpt['tawType'] = 'goal'
                if gtype == 'LINE':
                    wpt['tawShape'] = 'line'
            else:
                wpt['tawType'] = 'waypoint'

            turnpoint = Turnpoint(wpt['rwpLatDecimal'], wpt['rwpLonDecimal'], wpt['tawRadius'], wpt['tawType'], wpt['tawShape'], 'entry')
            turnpoint.name = wpt['rwpName']
            turnpoint.id = wpt['tawNumber']
            turnpoint.altitude = wpt['rwpAltitude']
            turnpoints.append(turnpoint)

        #tas['route'] = route
        task = cls(turnpoints, tas['tasStartTime'], tas['tasFinishTime'], tas['tasTaskType'], tas['tasStoppedTime'])
        task.task_name = tas['tasName']
        task.task_start_time = tas['tasTaskStart']
        task.start_close_time = tas['tasStartCloseTime']
        task.ShortRouteDistance = tas['tasShortRouteDistance'] * 1000 # in meters
        task.SSDistance = tas['tasSSDistance'] * 1000 # in meters
        task.arrival = tas['tasArrival']
        task.departure = tas['tasDeparture']
        task.height_bonus = tas['tasHeightBonus']
        task.comment = tas['tasComment']
        task.calculate_task_length()
        #print ("Tot. Dist.: {}".format(task.Distance))
        task.stats = stats
        task.optimised_legs = optimised_legs
        #task.results = results
        #print ("{} - date: {} - type: {} - dist.: {} - opt. dist.: {}".format(task.task_name, task.task_start_time.date(), task.task_type, task.Distance, task.ShortRouteDistance))
        #print ("open: {} - start: {} - close: {} - end: {} \n".format(task.task_start_time, task.start_time, task.start_close_time, task.end_time))

        return task

    def calculate_task_length(self, method="fast_andoyer"):
        # calculate non optimised route distance.
        for wpt in range(1, len(self.turnpoints)):
            leg_dist = distance(self.turnpoints[wpt - 1], self.turnpoints[wpt], method)
            self.legs.append(leg_dist)
            self.Distance += leg_dist
            #print ("leg dist.: {} - Dist.: {}".format(leg_dist, self.Distance))

    def calculate_optimised_task_length(self, method="fast_andoyer"):

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
                newcl = find_closest(newcl, wpts[i + 1], None, method)
            else:
                newcl = find_closest(newcl, wpts[i + 1], wpts[i + 2], method)
            it1.append(newcl)
        # FIX: special case for end point ..
        newcl = find_closest(newcl, wpts[num - 1], None, method)
        it1.append(newcl)

        num = len(it1)
        it2.append(it1[0])
        newcl = it1[0]
        for i in range(num - 2):
            # print "From it2: $i: ", $wpts->[$i]->{'name'}, "\n";
            newcl = find_closest(newcl, it1[i + 1], it1[i + 2], method)
            it2.append(newcl)

        it2.append(it1[num - 1])

        num = len(it2)
        closearr.append(it2[0])
        newcl = it2[0]
        for i in range(num - 2):
            # print "From it3: $i: ", $wpts->[$i]->{'name'}, "\n";
            newcl = find_closest(newcl, it2[i + 1], it2[i + 2], method)
            closearr.append(newcl)
        closearr.append(it2[num - 1])

        # calculate optimised route distance
        for opt_wpt in range(1, len(closearr)):
            leg_dist = distance(closearr[opt_wpt - 1], closearr[opt_wpt], method)
            self.optimised_legs.append(leg_dist)
            self.ShortRouteDistance = self.ShortRouteDistance + leg_dist

        # work out which turnpoints are SSS and ESS
        sss_wpt = 0
        ess_wpt = 0
        for wpt in range(len(self.turnpoints)):
            if self.turnpoints[wpt].type == 'speed':
                sss_wpt = wpt
            if self.turnpoints[wpt].type == 'endspeed':
                ess_wpt = wpt

        # work out self.StartSSDistance, self.EndSSDistance, self.SSDistance
        self.StartSSDistance = sum(self.optimised_legs[0:sss_wpt])
        self.EndSSDistance = sum(self.optimised_legs[0:ess_wpt])
        self.SSDistance = sum(self.optimised_legs[sss_wpt:ess_wpt])
        self.optimised_turnpoints = closearr

    def check_flight(self, Flight, formula_parameters, tolerance=0.0, min_tol_m=0):
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
        if not self.optimised_turnpoints:
            self.find_shortest_route()

        distances2go = distances_to_go(self.optimised_turnpoints)
        for fix in Flight.fixes:

            # handle stopped task
            maxtime = None
            if self.stopped_time is not None and flight_result.ESS_time is None:
                if formula_parameters.stopped_elapsed_calc == 'shortest_time':
                    maxtime = self.stopped_time - self.last_start_time

                if fix.rawtime > self.stopped_time or \
                        (maxtime is not None and flight_result.SSS_time is not None
                         and (fix.rawtime > flight_result.SSS_time + maxtime)):
                    flight_result.Stopped_time = fix.rawtime
                    flight_result.Stopped_altitude = max(fix.gnss_alt,
                                                         fix.press_alt)  # check the rules on this point..which alt to

            # check if pilot has arrived in goal (last turnpoint) so we can stop.
            if t >= len(self.turnpoints):
                break

            # check if task deadline has passed
            if self.end_time < fix.rawtime:
                # Task has ended
                break

            if self.turnpoints[t].type == "launch":
                # not checking launch yet
                if self.check_launch == 'on':
                    # Set radius to check to 200m (in the task def it will be 0)
                    # could set this in the DB or even formula if needed..???
                    self.turnpoints[t].radius = 0.2
                    if self.turnpoints[t].in_radius(fix, -tolerance, -min_tol_m):
                        reached_turnpoints.append(fix)  # pilot has achieved turnpoint
                        t += 1

                else:
                    t += 1

            # to do check for restarts for elapsed time tasks and those that allow jump the gun
            # if started and self.task_type != 'race' or flight_result.Jumped_the_gun is not None:

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

                if fix.rawtime > self.start_time - formula_parameters.max_jump_the_gun and not proceed_to_start:
                    if self.turnpoints[t].in_radius(fix, tolerance, min_tol_m):
                        proceed_to_start = True  # pilot is inside start after the start time.
                        if fix.rawtime < self.start_time:
                            flight_result.Jumped_the_gun = self.start_time - fix.rawtime

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
                if fix.rawtime > self.start_time - formula_parameters.max_jump_the_gun and not proceed_to_start:
                    if not self.turnpoints[t].in_radius(fix, -tolerance,
                                                        -min_tol_m):  # negative tolerance so radius is smaller.-tolerance applied always to pilots advantage
                        proceed_to_start = True  # pilot is outside start after the start time.
                        if fix.rawtime < self.start_time:
                            flight_result.Jumped_the_gun = self.start_time - fix.rawtime


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
            taskTime = fix.rawtime - self.start_time
            best_dist_to_ess = (self.EndSSDistance - flight_result.Distance_flown) / 1000
            if flight_result.Waypoints_achieved == 'Goal made':
                flight_result.Distance_flown = distances2go[0]
            else:
                flight_result.Distance_flown = max(flight_result.Distance_flown,
                                                   distance_flown(fix, t, self.optimised_turnpoints, distances2go))
                if best_dist_to_ess > 0 and started:
                    flight_result.Lead_coeff += formula_parameters.coef_func(taskTime, best_dist_to_ess, (
                                self.EndSSDistance - flight_result.Distance_flown) / 1000)

        return reached_turnpoints, flight_result


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