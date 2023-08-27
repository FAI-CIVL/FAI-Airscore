def checkbbox(lat, lon, bbox):
    if lat < bbox[0][0]:
        bbox[0][0] = lat
    if lon < bbox[0][1]:
        bbox[0][1] = lon
    if lat > bbox[1][0]:
        bbox[1][0] = lat
    if lon > bbox[1][1]:
        bbox[1][1] = lon

    return bbox


def bbox_centre(bbox):
    return [(bbox[0][0] + bbox[1][0]) / 2, (bbox[0][1] + bbox[1][1]) / 2]


def get_bbox(flight):
    """Gets track boundaries """

    assert flight.valid

    # TODO write objects to the geojson form the flight object
    min_lat = flight.fixes[0].lat
    min_lon = flight.fixes[0].lon
    max_lat = flight.fixes[0].lat
    max_lon = flight.fixes[0].lon

    bbox = [[min_lat, min_lon], [max_lat, max_lon]]

    for fix in flight.fixes:
        bbox = checkbbox(fix.lat, fix.lon, bbox)
    return bbox


def get_route_bbox(task):
    """Gets task boundaries """

    # TODO write objects to the geojson from the flight object
    min_lat = task.optimised_turnpoints[0].lat
    min_lon = task.optimised_turnpoints[0].lon
    max_lat = task.optimised_turnpoints[0].lat
    max_lon = task.optimised_turnpoints[0].lon

    bbox = [[min_lat, min_lon], [max_lat, max_lon]]

    for fix in task.optimised_turnpoints:
        bbox = checkbbox(fix.lat, fix.lon, bbox)
    return bbox


def get_region_bbox(region):
    """Gets region map boundaries """

    wpts = region.turnpoints
    # TODO write objects to the geojson from the flight object
    min_lat = wpts[0].lat
    min_lon = wpts[0].lon
    max_lat = wpts[0].lat
    max_lon = wpts[0].lon

    bbox = [[min_lat, min_lon], [max_lat, max_lon]]

    for wpt in wpts:
        bbox = checkbbox(wpt.lat, wpt.lon, bbox)
    return bbox


def get_airspace_bbox(reader):
    from geographiclib.geodesic import Geodesic

    geod = Geodesic.WGS84
    NM_in_meters = 1852.00
    latitudes = []
    longitudes = []

    for record, _ in reader:
        for element in record['elements']:
            if element['type'] == 'point':
                latitudes.append(element['location'][0])
                longitudes.append(element['location'][1])
            elif element['type'] == 'arc' and element['start']:
                latitudes.append(element['start'][0])
                longitudes.append(element['start'][1])
                latitudes.append(element['end'][0])
                longitudes.append(element['end'][1])
                latitudes.append(element['center'][0])
                longitudes.append(element['center'][1])
            elif (
                element['type'] == 'circle' or element['type'] == 'arc'
            ):  # hopefully capture case of arc defined by radius and angles - treat as circle
                # Get N,E,S & W most points of circle
                cardinals = [0, 90, 180, 270]
                for c in cardinals:
                    p = geod.Direct(element['center'][0], element['center'][1], c, element['radius'] * NM_in_meters)
                    latitudes.append(p['lat2'])
                    longitudes.append(p['lon2'])

    bbox = [[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]]

    return bbox


def map_legend(col_pilot_dict):
    from branca.element import MacroElement, Template

    legend_txt = ""
    for pilot in col_pilot_dict:
        legend_txt += (
            "<li><span style='background:" + col_pilot_dict[pilot] + ";opacity:0.7;'></span>" + pilot + "</li>"
        )

    first_block = """
    {% macro html(this, kwargs) %}

    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>jQuery UI Draggable - Default functionality</title>
      <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
      <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>

      <script>
      $( function() {
        $( "#maplegend" ).draggable({
                        start: function (event, ui) {
                            $(this).css({
                                right: "auto",
                                top: "auto",
                                bottom: "auto"
                            });
                        }
                    });
    });

      </script>
    </head>
    <body>


    <div id='maplegend' class='maplegend'
        style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
         border-radius:6px; padding: 10px; font-size:14px; right: 20px; bottom: 20px;'>

    <div class='legend-title'>Legend (draggable)</div>
    <div class='legend-scale'>
      <ul class='legend-labels'>"""

    second_block = """</ul>
    </div>
    </div>

    </body>
    </html>

    <style type='text/css'>
      .maplegend .legend-title {
        text-align: left;
        margin-bottom: 5px;
        font-weight: bold;
        font-size: 90%;
        }
      .maplegend .legend-scale ul {
        margin: 0;
        margin-bottom: 5px;
        padding: 0;
        float: left;
        list-style: none;
        }
      .maplegend .legend-scale ul li {
        font-size: 80%;
        list-style: none;
        margin-left: 0;
        line-height: 18px;
        margin-bottom: 2px;
        }
      .maplegend ul.legend-labels li span {
        display: block;
        float: left;
        height: 16px;
        width: 30px;
        margin-right: 5px;
        margin-left: 0;
        border: 1px solid #999;
        }
      .maplegend .legend-source {
        font-size: 80%;
        color: #777;
        clear: both;
        }
      .maplegend a {
        color: #777;
        }
    </style>
    {% endmacro %}"""

    template = first_block + legend_txt + second_block
    macro = MacroElement()
    macro._template = Template(template)
    return macro


def get_other_tracks(taskid, pilot_parid):
    from db.conn import db_session
    from db.tables import FlightResultView as R

    with db_session() as db:
        tracks = db.query(R.track_id, R.name).filter(R.task_id == taskid, R.par_id != pilot_parid).all()

    return tracks


def result_to_geojson(result, task, flight, second_interval=5):
    """Dumps the flight to geojson format used for mapping.
    Contains tracklog split into pre SSS, pre Goal and post goal parts, thermals, takeoff/landing,
    result object, waypoints achieved, and bounds
    second_interval = resolution of tracklog. default one point every 5 seconds. regardless it will
                        keep points where waypoints were achieved.
    returns the Json string."""

    from collections import namedtuple

    from geojson import Feature, FeatureCollection, MultiLineString, Point
    from route import distance, rawtime_float_to_hms

    features = []
    takeoff_landing = []
    thermals = []
    infringements = []
    fixes_to_keep = []
    point = namedtuple('fix', 'lat lon')

    min_lat = flight.fixes[0].lat
    min_lon = flight.fixes[0].lon
    max_lat = flight.fixes[0].lat
    max_lon = flight.fixes[0].lon
    bbox = [[min_lat, min_lon], [max_lat, max_lon]]

    takeoff = Point((flight.takeoff_fix.lon, flight.takeoff_fix.lat))
    time = "%02d:%02d:%02d" % rawtime_float_to_hms(flight.takeoff_fix.rawtime + task.time_offset)
    takeoff_landing.append(Feature(geometry=takeoff, properties={"event": "TakeOff", "time": time}))
    landing = Point((flight.landing_fix.lon, flight.landing_fix.lat))
    time = "%02d:%02d:%02d" % rawtime_float_to_hms(flight.landing_fix.rawtime + task.time_offset)
    takeoff_landing.append(Feature(geometry=landing, properties={"event": "Landing", "time": time}))

    fixes_to_keep.extend([flight.takeoff_fix.rawtime, flight.landing_fix.rawtime])
    # adding best distance fix if not in goal
    if not result.goal_time and hasattr(result, 'best_distance_fix') and result.best_distance_fix:
        best_distance = Point((result.best_distance_fix.lon, result.best_distance_fix.lat))
        time = "%02d:%02d:%02d" % rawtime_float_to_hms(result.best_distance_fix.rawtime + task.time_offset)
        takeoff_landing.append(Feature(geometry=best_distance, properties={"event": "BestDistance", "time": time}))
        fixes_to_keep.append(result.best_distance_fix.rawtime)

    for thermal in flight.thermals:
        thermals.append(
            (
                thermal.enter_fix.lon,
                thermal.enter_fix.lat,
                f'{thermal.vertical_velocity():.1f}m/s gain:{thermal.alt_change():.0f}m',
            )
        )

    pre_sss = []
    pre_goal = []
    post_goal = []
    waypoints_achieved = []

    # if the pilot did not make goal, goal time will be None. set to after end of track to avoid issues.
    goal_time = flight.fixes[-1].rawtime + 1 if not result.goal_time else result.goal_time
    # if the pilot did not make SSS then it will be 0, set to task start time.
    SSS_time = task.start_time if not result.SSS_time else result.SSS_time

    if len(result.waypoints_achieved) > 0:
        for idx, tp in enumerate(result.waypoints_achieved):
            time = "%02d:%02d:%02d" % rawtime_float_to_hms(tp.rawtime + task.time_offset)
            achieved = [
                tp.lon,
                tp.lat,
                tp.altitude,
                tp.name,
                tp.rawtime,
                time,
                f'<b>{tp.name}</b> <br>' f'alt: <b>{tp.altitude:.0f} m.</b><br>' f'time: <b>{time}</b>',
            ]
            fixes_to_keep.append(tp.rawtime)
            if idx > 0:
                current = point(lon=tp.lon, lat=tp.lat)
                previous = point(lon=waypoints_achieved[-1][0], lat=waypoints_achieved[-1][1])
                straight_line_dist = distance(previous, current) / 1000
                time_taken = tp.rawtime - waypoints_achieved[-1][4]
                time_takenHMS = rawtime_float_to_hms(time_taken)
                if time_taken > 0:
                    speed = straight_line_dist / (time_taken / 3600)
                else:
                    speed = 0
                achieved.append(round(straight_line_dist, 2))
                achieved.append("%02d:%02d:%02d" % time_takenHMS)
                achieved.append(round(speed, 2))
            else:
                achieved.extend([0, "0:00:00", '-'])
            waypoints_achieved.append(achieved)

    '''airspace infringements'''
    if result.infringements:
        for entry in result.infringements:
            time = "%02d:%02d:%02d" % rawtime_float_to_hms(entry['rawtime'] + task.time_offset)
            infringements.append(
                [
                    entry['lon'],
                    entry['lat'],
                    int(entry['alt']),
                    entry['space'],
                    int(entry['distance']),
                    entry['separation'],
                    int(entry['rawtime']),
                    time,
                ]
            )
            fixes_to_keep.append(int(entry['rawtime']))

    lastfix = flight.fixes[0]
    for fix in flight.fixes:
        bbox = checkbbox(fix.lat, fix.lon, bbox)
        keep = False
        if (
            fix.rawtime >= lastfix.rawtime + second_interval
            or fix.rawtime in fixes_to_keep
        ):
            '''keep fixes that validate a turnpoint or cause an infringement'''
            ###
            # print(f'rawtime: {fix.rawtime}')
            keep = True
            lastfix = fix

        if keep and fix.rawtime:
            if fix.rawtime <= SSS_time:
                pre_sss.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))
            if SSS_time <= fix.rawtime <= goal_time:
                pre_goal.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))
                if len(pre_goal) == 1:
                    '''adding fix to pre_sss to link polylines'''
                    pre_sss.append(pre_goal[0])
            if fix.rawtime >= goal_time:
                post_goal.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))
                if len(post_goal) == 1:
                    '''adding fix to pre_goal to link polylines'''
                    pre_goal.append(post_goal[0])

    route_multilinestring = MultiLineString([pre_sss])
    features.append(Feature(geometry=route_multilinestring, properties={"Track": "Pre_SSS"}))
    route_multilinestring = MultiLineString([pre_goal])
    features.append(Feature(geometry=route_multilinestring, properties={"Track": "Pre_Goal"}))
    route_multilinestring = MultiLineString([post_goal])
    features.append(Feature(geometry=route_multilinestring, properties={"Track": "Post_Goal"}))

    tracklog = FeatureCollection(features)

    return tracklog, thermals, takeoff_landing, bbox, waypoints_achieved, infringements


def create_trackpoints_layer(file: str, offset: int = 0) -> list:
    from calcUtils import sec_to_string
    from pilot.track import Track, Path

    try:
        flight = Track.create_from_file(Path(file))
        points = []
        for fix in flight.fixes:
            points.append(
                [
                    fix.lon,
                    fix.lat,
                    fix.rawtime,
                    fix.press_alt,
                    fix.gnss_alt,
                    sec_to_string(fix.rawtime),
                    sec_to_string(fix.rawtime, offset),
                ]
            )
    except FileNotFoundError:
        print(f'Error: file not found {file}')
        return []
    except Exception:
        print(f'Error: cannot create trackpoints map layer from track: {file}')
        return []
    return points


def get_points_and_bbox(waypoints: list, radius: int = 250) -> tuple:
    bbox = [[waypoints[0].lat, waypoints[0].lon], [waypoints[0].lat, waypoints[0].lon]]
    points = []
    for wp in waypoints:
        type = (
            'launch'
            if wp.name[0] == 'D'
            else 'speed'
            if wp.name[0] in ('A', 'L')
            else 'restricted'
            if wp.name[0] == 'X'
            else 'waypoint'
        )
        points.append(
            {
                'name': wp.name,
                'description': wp.description,
                'longitude': wp.lon,
                'latitude': wp.lat,
                'altitude': wp.altitude,
                'radius': radius,
                'type': type,
            }
        )
        bbox = checkbbox(wp.lat, wp.lon, bbox)
    return points, bbox


def create_waypoints_layer(reg_id: int, region=None, radius: int = 250) -> tuple:
    from db.conn import db_session
    from db.tables import TblRegionWaypoint as R

    points, bbox = [], []
    if region:
        points, bbox = get_points_and_bbox(region.turnpoints, radius)
    else:
        with db_session() as db:
            results = db.query(R).filter_by(reg_id=reg_id, old=False).all()
            if results:
                points, bbox = get_points_and_bbox(results, radius)
    return points, bbox


def create_airspace_layer(openair_file: str) -> tuple:
    from airspaceUtils import read_airspace_map_file

    try:
        data = read_airspace_map_file(openair_file)
        airspace_layer = data['spaces']
        airspace_list = data['airspace_list']
        bbox = data['bbox']
    except (TypeError, Exception):
        print(f"Error creating airspace error. Is the file missing?")
        airspace_layer = None
        airspace_list = None
        bbox = None
    return airspace_layer, airspace_list, bbox
