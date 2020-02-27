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
            elif element['type'] == 'circle' or element[
                'type'] == 'arc':  # hopefully capture case of arc defined by radius and angles - treat as circle
                # Get N,E,S & W most points of circle
                cardinals = [0, 90, 180, 270]
                for c in cardinals:
                    p = geod.Direct(element['center'][0], element['center'][1], c, element['radius'] * NM_in_meters)
                    latitudes.append(p['lat2'])
                    longitudes.append(p['lon2'])

    bbox = [[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]]

    return bbox


def map_legend(col_pilot_dict):
    from branca.element import Template, MacroElement
    legend_txt = ""
    for pilot in col_pilot_dict:
        legend_txt += (
                "<li><span style='background:" + col_pilot_dict[pilot] + ";opacity:0.7;'></span>" + pilot + "</li>")

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
    from db_tables import FlightResultView as R
    from myconn import Database

    with Database() as db:
        tracks = (db.session.query(R.track_id, R.name).filter(R.task_id == taskid, R.par_id != pilot_parid).all())

    return tracks


def result_to_geojson(result, track, task, second_interval=5):
    """Dumps the flight to geojson format used for mapping.
    Contains tracklog split into pre SSS, pre Goal and post goal parts, thermals, takeoff/landing,
    result object, waypoints achieved, and bounds

    second_interval = resolution of tracklog. default one point every 5 seconds. regardless it will
                        keep points where waypoints were achieved.
    returns the Json string."""

    from collections import namedtuple
    from route import rawtime_float_to_hms, distance
    from geojson import Point, Feature, FeatureCollection, MultiLineString

    features = []
    takeoff_landing = []
    thermals = []
    point = namedtuple('fix', 'lat lon')

    min_lat = track.flight.fixes[0].lat
    min_lon = track.flight.fixes[0].lon
    max_lat = track.flight.fixes[0].lat
    max_lon = track.flight.fixes[0].lon
    bbox = [[min_lat, min_lon], [max_lat, max_lon]]

    takeoff = Point((track.flight.takeoff_fix.lon, track.flight.takeoff_fix.lat))
    takeoff_landing.append(Feature(geometry=takeoff, properties={"TakeOff": "TakeOff"}))
    landing = Point((track.flight.landing_fix.lon, track.flight.landing_fix.lat))
    takeoff_landing.append(Feature(geometry=landing, properties={"Landing": "Landing"}))

    for thermal in track.flight.thermals:
        thermals.append((thermal.enter_fix.lon, thermal.enter_fix.lat,
                         f'{thermal.vertical_velocity():.1f}m/s gain:{thermal.alt_change():.0f}m'))

    pre_sss = []
    pre_goal = []
    post_goal = []
    waypoint_achieved = []

    # if the pilot did not make goal, goal time will be None. set to after end of track to avoid issues.
    if not result.goal_time:
        goal_time = track.flight.fixes[-1].rawtime + 1
    else:
        goal_time = result.goal_time

    # if the pilot did not make SSS then it will be 0, set to task start time.
    if result.SSS_time == 0:
        SSS_time = task.start_time
    else:
        SSS_time = result.SSS_time

    waypoint = 0
    lastfix = track.flight.fixes[0]
    for fix in track.flight.fixes:
        bbox = checkbbox(fix.lat, fix.lon, bbox)
        keep = False
        if fix.rawtime >= lastfix.rawtime + second_interval:
            keep = True
            lastfix = fix

        if len(result.waypoints_achieved) > waypoint and fix.rawtime == result.waypoints_achieved[waypoint][1]:
            time = ("%02d:%02d:%02d" % rawtime_float_to_hms(fix.rawtime + task.time_offset))
            waypoint_achieved.append(
                [fix.lon, fix.lat, fix.gnss_alt, fix.press_alt, result.waypoints_achieved[waypoint][0], time,
                 fix.rawtime,
                 f'{result.waypoints_achieved[waypoint][0]} '
                 f'gps alt: {fix.gnss_alt:.0f}m '
                 f'baro alt: {fix.press_alt:.0f}m '
                 f'time: {time}'])
            keep = True
            if waypoint < len(result.waypoints_achieved) - 1:
                waypoint += 1

        if keep:
            if fix.rawtime <= SSS_time:
                pre_sss.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))
            if SSS_time <= fix.rawtime <= goal_time:
                pre_goal.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))
            if fix.rawtime >= goal_time:
                post_goal.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))

    if len(waypoint_achieved) > 0:
        for w in range(1, len(waypoint_achieved[
                              1:]) + 1):  # this could be expressed as for idx, wp in enumerate(waypoint_achieved[1:], 1)_
            current = point(lon=waypoint_achieved[w][0], lat=waypoint_achieved[w][1])
            previous = point(lon=waypoint_achieved[w - 1][0], lat=waypoint_achieved[w - 1][1])
            straight_line_dist = distance(previous, current) / 1000
            time_taken = (waypoint_achieved[w][6] - waypoint_achieved[w - 1][6]) / 3600
            time_takenHMS = rawtime_float_to_hms(time_taken * 3600)
            speed = straight_line_dist / time_taken
            waypoint_achieved[w].append(round(straight_line_dist, 2))
            waypoint_achieved[w].append("%02d:%02d:%02d" % time_takenHMS)
            waypoint_achieved[w].append(round(speed, 2))

        waypoint_achieved[0].append(0)
        waypoint_achieved[0].append("0:00:00")
        waypoint_achieved[0].append('-')

    route_multilinestring = MultiLineString([pre_sss])
    features.append(Feature(geometry=route_multilinestring, properties={"Track": "Pre_SSS"}))
    route_multilinestring = MultiLineString([pre_goal])
    features.append(Feature(geometry=route_multilinestring, properties={"Track": "Pre_Goal"}))
    route_multilinestring = MultiLineString([post_goal])
    features.append(Feature(geometry=route_multilinestring, properties={"Track": "Post_Goal"}))

    tracklog = FeatureCollection(features)

    return tracklog, thermals, takeoff_landing, bbox, waypoint_achieved


def save_all_geojson_files(task, interval=5):
    """saves geojson map files for all pilots with valid result in task"""
    import jsonpickle

    pilots = [pilot for pilot in task.pilots if pilot.track.flight and pilot.track.flight.valid]
    for pilot in pilots:
        track = pilot.track
        result = pilot.result
        track_id = pilot.track.track_id

        info = {'taskid': task.id, 'task_name': task.task_name, 'comp_name': task.comp_name,
                'pilot_name': pilot.info.name, 'pilot_nat': pilot.info.nat, 'pilot_sex': pilot.info.sex,
                'pilot_parid': pilot.par_id, 'Glider': pilot.info.glider}

        tracklog, thermals, takeoff_landing, bbox, waypoint_achieved = result_to_geojson(result, track, task)
        airspace_plot = result.airspace_plot

        data = {'info': info, 'tracklog': tracklog, 'thermals': thermals, 'takeoff_landing': takeoff_landing,
                'result': jsonpickle.dumps(result), 'bounds': bbox, 'waypoint_achieved': waypoint_achieved,
                'airspace': airspace_plot}

        pilot.result.save_result_file(data, track_id)
