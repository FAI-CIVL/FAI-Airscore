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

from route import distance, polar, find_closest, cartesian2polar, polar2cartesian, calcBearing, opt_goal, opt_wp, opt_wp_exit, opt_wp_enter, Turnpoint
from myconn import Database
from calcUtils import json, get_datetime, decimal_to_seconds, time_difference
from igc_lib import defaultdict
import  math
import xml.dom.minidom

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
        self.tasPk = None
        self.comPk = None
        self.date = None    # in datetime.date format
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
        self.optimised_legs = []  # opt distance between cylinders
        self.partial_distance = []  # distance from launch to waypoint
        self.legs = []  ##non optimised legs
        self.stats = dict()  #scored task statistics
        #self.results = []  #scored task results
        self.stopped_time = stopped_time  # time task was stopped.
        self.last_start_time = last_start_time  # last start gate when there are more than 1
        self.check_launch = check_launch  # check launch flag. whether we check that pilots leave from launch.
        self.arrival = None
        self.departure = None
        self.height_bonus = None
        self.comment = None
        self.goalalt = 0
        self.time_offset = 0
        self.tolerance = 0
        self.launchvalid = None

    @staticmethod
    def read_task(task_id):
        """Reads Task from database
        takes tasPk as argument"""
        turnpoints = []
        short_route = []
        partial_distance = []
        stats = dict()

        if task_id < 1:
            print("task not present in database ", task_id)

        query = """ SELECT
                        TIME_TO_SEC(`tasStartTime`) AS sstime,
                        TIME_TO_SEC(`tasFinishTime`) AS endtime,
                        TIME_TO_SEC(`tasLastStartTime`) AS LastStartTime,
                        TIME_TO_SEC(`tasStartCloseTime`) AS StartCloseTime,
                        `tasPk`,
                        `comPk`,
                        `tasDate`,
                        `tasName`,
                        `tasTaskStart`,
                        `tasFinishTime`,
                        `tasLaunchClose`,
                        `tasCheckLaunch`,
                        `tasStartTime`,
                        `tasStartCloseTime`,
                        `tasStoppedTime`,
                        `tasLastStartTime`,
                        `tasFastestTime`,
                        `tasFirstDepTime`,
                        `tasFirstArrTime`,
                        `tasLastArrTime`,
                        `tasMaxDistance`,
                        'tasTotalDistanceFlown',
                        `tasResultsType`,
                        `tasTaskType`,
                        `tasDistance`,
                        `tasShortRouteDistance`,
                        `tasStartSSDistance`,
                        `tasEndSSDistance`,
                        `tasSSDistance`,
                        `tasSSInterval`,
                        `tasDeparture`,
                        `tasLaunchValid`,
                        `tasArrival`,
                        `tasHeightBonus`,
                        `tasComment`,
                        `tasGoalAlt`,
                        `comTimeOffset`,
                        `comClass`,
                        `tasMargin`
                    FROM
                        `TaskView`
                    WHERE
                        `tasPk` = %s
                    LIMIT 1"""
        with Database() as db:
            # get the task details.
            t = db.fetchone(query, [task_id])
        if t is None:
            print('Not a valid task')
            return
        time_offset         = t['comTimeOffset']
        task_date           = t['tasDate']
        start_time          = int(t['sstime'] - time_offset*60*60)
        end_time            = t['endtime'] - time_offset*60*60
        task_type           = t['tasTaskType'].upper()
        if t['tasStoppedTime']:
            t['tasStoppedTime'] -= time_offset * 60*60

        stopped_time        = t['tasStoppedTime']
        if t['LastStartTime']:
            t['LastStartTime'] -= time_offset * 60*60
        last_start_time     = t['LastStartTime']
        check_launch        = t['tasCheckLaunch']
        launchvalid         = t['tasLaunchValid']
        distance            = t['tasDistance']
        EndSSDistance       = t['tasEndSSDistance']
        SSDistance          = t['tasSSDistance']
        SSInterval          = t['tasSSInterval']
        ShortRouteDistance  = t['tasShortRouteDistance']
        start_close_time    = t['StartCloseTime'] - time_offset*60*60
        task_start_time     = t['tasStartTime']
        arrival             = t['tasArrival']
        departure           = t['tasDeparture']
        tolerance           = t['tasMargin'] * 0.01
        goalalt             = t['tasGoalAlt']

        if t['tasMaxDistance']:
            '''task has been already scored'''
            stats = dict()
            stats['firstdepart']    = t['tasFirstDepTime']
            stats['lastarrival']    = t['tasLastArrTime']
            stats['maxdist']        = t['tasMaxDistance']
            stats['fastest']        = t['tasFastestTime']
            stats['distovermin']    = t['tasTotalDistanceFlown']

        comPk = t['comPk']

        query = ("""SELECT
                        T.tawPk AS id,
                        T.tawHow,
                        T.tawRadius,
                        T.tawShape,
                        T.tawType,
                        T.ssrLatDecimal,
                        T.ssrLongDecimal,
                        T.ssrCumulativeDist AS partial_distance,
                        R.rwpLatDecimal,
                        R.rwpLongDecimal,
                        R.rwpName AS name
                    FROM
                        tblTaskWaypoint T
                    LEFT OUTER JOIN tblRegionWaypoint R USING(rwpPk)
                    WHERE
                        T.tasPk = %s
                    ORDER BY
                        T.tawNumber""")

        with Database() as db:
            # get the task details.
            tps = db.fetchall(query, [task_id])

        for tp in tps:
            turnpoint = Turnpoint(tp['rwpLatDecimal'], tp['rwpLongDecimal'], tp['tawRadius'], tp['tawType'].strip(),
                                  tp['tawShape'], tp['tawHow'])
            turnpoint.name = tp['name']
            turnpoint.id = tp['id']
            turnpoints.append(turnpoint)
            s_point = polar(lat=tp['ssrLatDecimal'],lon=tp['ssrLongDecimal'])
            #print ("short route fix: {}, {}".format(s_point.lon,s_point.lat))
            short_route.append(s_point)
            if tp['partial_distance']: #this will be None in DB before we optimise route, but we append to this list so we should not fill it with Nones
                partial_distance.append(tp['partial_distance'])

        task = Task(turnpoints, start_time, end_time, task_type, stopped_time, last_start_time, check_launch)
        task.launchvalid = launchvalid
        task.tasPk                  = task_id
        task.comPk                  = comPk
        task.date                   = task_date
        task.distance               = distance
        task.EndSSDistance          = EndSSDistance
        task.SSDistance             = SSDistance
        task.SSInterval             = SSInterval
        task.ShortRouteDistance     = ShortRouteDistance
        task.partial_distance       = partial_distance
        task.optimised_turnpoints   = short_route
        task.start_close_time       = start_close_time
        task.task_start_time        = task_start_time
        task.arrival                = arrival
        task.departure              = departure
        task.time_offset            = time_offset
        task.tolerance              = tolerance
        task.goalalt                = goalalt
        task.stats                  = stats


        return task

    def update_task(self):

        with Database() as db:
            '''add optimised and total distance to task'''
            query = """ UPDATE `tblTask`
                        SET
                            `tasDistance` = %s,
                            `tasShortRouteDistance` = %s,
                            `tasSSDistance` = %s,
                            `tasEndSSDistance` = %s,
                            `tasStartSSDistance` = %s
                        WHERE
                            `tasPk` = %s"""
            params = [self.Distance, self.ShortRouteDistance,   self.SSDistance, self.EndSSDistance, self.StartSSDistance, self.tasPk]
            db.execute(query, params)

            '''add opt legs to task wpt'''
            query = ''
            for idx, item in enumerate(self.turnpoints):
                #print ("  {}  {}  {}  {}   {}".format(item.name, item.type, item.radius, self.optimised_legs[idx], self.partial_distance[idx]))
                query = ("""UPDATE `tblTaskWaypoint` SET `ssrLatDecimal` = {}, `ssrLongDecimal` = {}, `ssrCumulativeDist` = {} WHERE `tawPk` = {} """.format(self.optimised_turnpoints[idx].lat, self.optimised_turnpoints[idx].lon, self.partial_distance[idx], item.id))
                #print (query)
                db.execute(query)
                #print (self.optimised_turnpoints[idx].lat, self.optimised_turnpoints[idx].lon)

    def update_totals(self):
        '''store updated totals to task database'''

        totals = self.stats
        task_id = self.tasPk
        with Database() as db:
            query = "update tblTask set tasTotalDistanceFlown=%s, " \
                    "tasTotDistOverMin= %s, tasPilotsTotal=%s, " \
                    "tasPilotsLaunched=%s, tasPilotsGoal=%s, " \
                    "tasFastestTime=%s, tasMaxDistance=%s " \
                    "where tasPk=%s"

            params = [totals['distance'], totals['distovermin'], totals['pilots'], totals['launched'],
                         totals['goal'], totals['fastest'], totals['maxdist'], task_id]
            db.execute(query, params)

    def update_quality(self):
        '''store new task validities and quality'''
        quality     = self.stats['quality']
        dist        = self.stats['distval']
        time        = self.stats['timeval']
        launch      = self.stats['launchval']
        stop        = self.stats['stopval']
        task_id     = self.tasPk

        query = "UPDATE tblTask " \
                "SET tasQuality = %s, " \
                "tasDistQuality = %s, " \
                "tasTimeQuality = %s, " \
                "tasLaunchQuality = %s, " \
                "tasStopQuality = %s " \
                "WHERE tasPk = %s"
        params = [quality, dist, time, launch, stop, task_id]

        with Database() as db:
            db.execute(query, params)

    def update_points_allocation(self):
        '''store points allocation'''
        query = """ UPDATE tblTask SET  tasAvailDistPoints=%s,
                                        tasAvailLeadPoints=%s,
                                        tasAvailTimePoints=%s
                    WHERE tasPk=%s"""
        params = [self.stats['distp'], self.stats['depp'], self.stats['timep'], self.tasPk]

        with Database() as db:
            db.execute(query, params)

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
                stats['pilots'] = int(p.get('no_of_pilots_present'))
                stats['launched'] = int(p.get('no_of_pilots_flying'))
                stats['goal'] = int(p.get('no_of_pilots_reaching_goal'))
                stats['maxdist'] = float(p.get('best_dist')) * 1000 # in meters
                stats['totdistovermin'] = float(p.get('sum_flown_distance')) * 1000 # in meters
                try:
                    '''happens this values are error strings'''
                    stats['quality'] = float(p.get('day_quality'))
                    stats['distval'] = float(p.get('distance_validity'))
                    stats['timeval'] = float(p.get('time_validity'))
                    stats['launchval'] = float(p.get('launch_validity'))
                    stats['stopval'] = float(p.get('stop_validity'))
                    stats['distp'] = float(p.get('available_points_distance'))
                    stats['depp'] = float(p.get('available_points_leading'))
                    stats['timep'] = float(p.get('available_points_time'))
                    stats['arrp'] = float(p.get('available_points_arrival'))
                except:
                    stats['quality'] = 0
                    stats['distval'] = 0
                    stats['timeval'] = 0
                    stats['launchval'] = 0
                    stats['stopval'] = 0
                    stats['distp'] = 0
                    stats['depp'] = 0
                    stats['timep'] = 0
                    stats['arrp'] = 0
                stats['fastest'] = decimal_to_seconds(float(p.get('best_time'))) if float(p.get('best_time')) > 0 else 0
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
            tas['tasTaskType'] = 'free distance'
            if node.find('FsHeadingpoint') is not None:
                '''open distance with bearing'''
                headingpoint = 1
                tas['tasTaskType'] = 'distance with bearing'
                tas['tasBearingLat'] = float(node.find('FsHeadingpoint').get('lat'))
                tas['tasBearingLon'] = float(node.find('FsHeadingpoint').get('lon'))
        else:
            sswpt = int(node.get('ss'))
            eswpt = int(node.get('es'))
            gtype = node.get('goal')
            tas['gstart'] = int(node.get('groundstart'))
            if node.find('FsStartGate') is None:
                '''elapsed time
                    on start gate, have to get start opening time from ss wpt'''
                tas['tasTaskType'] = 'elapsed time'
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
                if 'free distance' in tas['tasTaskType']:
                    #print('Sono in launch - free')
                    '''get start and close time for free distance task types'''
                    tas['tasStartTime'] = get_datetime(w.get('open'))
                    tas['tasStartCloseTime'] = get_datetime(w.get('close'))
                    tas['tasFinishTime'] = get_datetime(w.get('close'))
            elif wpt['tawNumber'] == sswpt:
                #print('Sono in ss')
                wpt['tawType'] = 'speed'
                tas['tasStartCloseTime'] = get_datetime(w.get('close'))
                if 'elapsed time' in tas['tasTaskType']:
                    '''get start for elapsed time task types'''
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

    def calculate_optimised_task_length_old(self, method="fast_andoyer"):

        it1 = []
        it2 = []
        wpts = self.turnpoints
        self.ShortRouteDistance = 0  #reset in case of recalc.

        closearr = []
        num = len(wpts)

        if num < 1:
            self.partial_distance.append(self.ShortRouteDistance)
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
        self.optimised_legs = []
        self.optimised_legs.append(0)
        self.partial_distance = []
        self.partial_distance.append(0)
        self.ShortRouteDistance = 0
        for opt_wpt in range(1, len(closearr)):
            leg_dist = distance(closearr[opt_wpt - 1], closearr[opt_wpt], method)
            self.optimised_legs.append(leg_dist)
            self.ShortRouteDistance += leg_dist
            self.partial_distance.append(self.ShortRouteDistance)

        # work out which turnpoints are SSS and ESS
        sss_wpt = 0
        ess_wpt = 0
        for wpt in range(len(self.turnpoints)):
            if self.turnpoints[wpt].type == 'speed':
                sss_wpt = wpt+1
            if self.turnpoints[wpt].type == 'endspeed':
                ess_wpt = wpt+1

        # work out self.StartSSDistance, self.EndSSDistance, self.SSDistance
        self.StartSSDistance = sum(self.optimised_legs[0:sss_wpt])
        self.EndSSDistance = sum(self.optimised_legs[0:ess_wpt])
        self.SSDistance = sum(self.optimised_legs[sss_wpt:ess_wpt])
        self.optimised_turnpoints = closearr

    def calculate_optimised_task_length(self, method="fast_andoyer"):
        from geographiclib.geodesic import Geodesic
        geod = Geodesic.WGS84
        wpts = self.turnpoints
        self.ShortRouteDistance = 0  #reset in case of recalc.

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
        optimised = []
        t = 0

        while t < len(self.turnpoints) - 1:

            exit_same = False
            exit_different = False
            enter_same = False
            enter_different = False

            if t == 0:
                t1 = self.turnpoints[t]
                optimised.append(t1)
            else:
                t1 = opt

            if t + 2 > len(self.turnpoints) - 1:
                optimised.append(opt_goal(t1, self.turnpoints[-1]))
                break
            # next wpt has the same centre but a bigger exit radius  (and therefore we are in it)
            if t1.lat == self.turnpoints[t + 1].lat and t1.lon == self.turnpoints[t + 1].lon:
                t += 1
                exit_same = True
            #  we are in the next one but it does not have the same centre
            elif self.turnpoints[t + 1].in_radius(t1, 0, 0):
                t += 1
                exit_different = True
            # or it is the same as the following one (i.e entry large radius followed by smaller like ess and goal often are)
            elif self.turnpoints[t + 2].lat == self.turnpoints[t + 1].lat and self.turnpoints[t + 2].lon == \
                    self.turnpoints[t + 1].lon:
                t += 1
                enter_same = True
            #  we are in the next one but it does not have the same centre
            elif self.turnpoints[t + 2].in_radius(self.turnpoints[t + 1], 0, 0):
                t += 1
                enter_different = True

            #print(f'{t} of{len(self.turnpoints)}')
            t2 = self.turnpoints[t + 1]

            if t + 2 > len(self.turnpoints)-1:
                t3 = None
            else:
                t3 = self.turnpoints[t + 2]

            opt = opt_wp(t1, t2, t3, t2.radius)

            if exit_same:
                p = geod.Direct(t1.lat, t1.lon, calcBearing(t1.lat, t1.lon, opt.lat, opt.lon),
                                self.turnpoints[t].radius)
                opt_exit = Turnpoint(lat=p['lat2'], lon=p['lon2'], type='optimised', radius=0, shape='optimised', how='optimised')
                optimised.append(opt_exit)
            if exit_different:
                opt_exit = opt_wp_exit(opt, t1, self.turnpoints[t])
                optimised.append(opt_exit)
            if enter_same:
                p = geod.Direct(t2.lat, t2.lon, calcBearing(t2.lat, t2.lon, t1.lat, t1.lon), self.turnpoints[t].radius)
                opt_enter = Turnpoint(lat=p['lat2'], lon=p['lon2'], type='optimised', radius=0, shape='optimised', how='optimised')
                optimised.append(opt_enter)
            if enter_different:
                opt_enter = opt_wp_enter(opt, t2, self.turnpoints[t + 1])
                optimised.append(opt_enter)

            optimised.append(opt)

            t += 1
        total = 0
        for o in range(len(optimised) - 1):
            d = geod.Inverse(optimised[o].lat, optimised[o].lon, optimised[o + 1].lat, optimised[o + 1].lon)['s12']
            total += d

        # calculate optimised route distance
        self.optimised_legs = []
        self.optimised_legs.append(0)
        self.partial_distance = []
        self.partial_distance.append(0)
        self.ShortRouteDistance = 0
        for opt_wpt in range(1, len(optimised)):
            leg_dist = distance(optimised[opt_wpt - 1], optimised[opt_wpt], method)
            self.optimised_legs.append(leg_dist)
            self.ShortRouteDistance += leg_dist
            self.partial_distance.append(self.ShortRouteDistance)

        # work out which turnpoints are SSS and ESS
        sss_wpt = 0
        ess_wpt = 0
        for wpt in range(len(self.turnpoints)):
            if self.turnpoints[wpt].type == 'speed':
                sss_wpt = wpt+1
            if self.turnpoints[wpt].type == 'endspeed':
                ess_wpt = wpt+1

        # work out self.StartSSDistance, self.EndSSDistance, self.SSDistance
        self.StartSSDistance = sum(self.optimised_legs[0:sss_wpt])
        self.EndSSDistance = sum(self.optimised_legs[0:ess_wpt])
        self.SSDistance = sum(self.optimised_legs[sss_wpt:ess_wpt])
        self.optimised_turnpoints = optimised


    @property
    def distances_to_go(self):
        """calculates a list of distances from turnpoint to goal (assumes goal is the last turnpoint)"""
        t = len(self.optimised_turnpoints) - 1
        d = 0
        distance_to_go = [0]
        while t >= 1:
            d += distance(self.optimised_turnpoints[t], self.optimised_turnpoints[t - 1])
            distance_to_go.insert(0, d)
            t -= 1
        return distance_to_go
