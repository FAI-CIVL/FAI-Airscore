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


def result_to_geojson(result, task, flight, second_interval=5):
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
    infringements = []
    point = namedtuple('fix', 'lat lon')

    min_lat = flight.fixes[0].lat
    min_lon = flight.fixes[0].lon
    max_lat = flight.fixes[0].lat
    max_lon = flight.fixes[0].lon
    bbox = [[min_lat, min_lon], [max_lat, max_lon]]

    takeoff = Point((flight.takeoff_fix.lon, flight.takeoff_fix.lat))
    takeoff_landing.append(Feature(geometry=takeoff, properties={"TakeOff": "TakeOff"}))
    landing = Point((flight.landing_fix.lon, flight.landing_fix.lat))
    takeoff_landing.append(Feature(geometry=landing, properties={"Landing": "Landing"}))

    for thermal in flight.thermals:
        thermals.append((thermal.enter_fix.lon, thermal.enter_fix.lat,
                         f'{thermal.vertical_velocity():.1f}m/s gain:{thermal.alt_change():.0f}m'))

    pre_sss = []
    pre_goal = []
    post_goal = []
    waypoints_achieved = []

    # if the pilot did not make goal, goal time will be None. set to after end of track to avoid issues.
    goal_time = flight.fixes[-1].rawtime + 1 if not result.goal_time else result.goal_time
    # if the pilot did not make SSS then it will be 0, set to task start time.
    SSS_time = task.start_time if result.SSS_time == 0 else result.SSS_time

    if len(result.waypoints_achieved) > 0:
        for idx, tp in enumerate(result.waypoints_achieved):
            time = ("%02d:%02d:%02d" % rawtime_float_to_hms(tp.rawtime + task.time_offset))
            achieved = [tp.lon, tp.lat, tp.altitude, tp.name, tp.rawtime, time, f'<b>{tp.name}</b> <br>'
                                                                                f'alt: <b>{tp.altitude:.0f} m.</b><br>'
                                                                                f'time: <b>{time}</b>']
            if idx > 0:
                current = point(lon=tp.lon, lat=tp.lat)
                previous = point(lon=waypoints_achieved[-1][0], lat=waypoints_achieved[-1][1])
                straight_line_dist = distance(previous, current) / 1000
                time_taken = (tp.rawtime - waypoints_achieved[-1][4])
                time_takenHMS = rawtime_float_to_hms(time_taken)
                speed = straight_line_dist / (time_taken / 3600)
                achieved.append(round(straight_line_dist, 2))
                achieved.append("%02d:%02d:%02d" % time_takenHMS)
                achieved.append(round(speed, 2))
            else:
                achieved.extend([0, "0:00:00", '-'])
            waypoints_achieved.append(achieved)

    lastfix = flight.fixes[0]
    for fix in flight.fixes:
        bbox = checkbbox(fix.lat, fix.lon, bbox)
        keep = False
        if (fix.rawtime >= lastfix.rawtime + second_interval
                or any(tp for tp in result.waypoints_achieved if tp.rawtime == fix.rawtime)
                or any(tp for tp in result.infringements if int(tp['rawtime']) == fix.rawtime)):
            '''keep fixes that validate a turnpoint or cause an infringement'''
            ###
            # print(f'rawtime: {fix.rawtime}')
            keep = True
            lastfix = fix

        if keep:
            if fix.rawtime <= SSS_time:
                pre_sss.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))
            if SSS_time <= fix.rawtime <= goal_time:
                pre_goal.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))
            if fix.rawtime >= goal_time:
                post_goal.append((fix.lon, fix.lat, fix.gnss_alt, fix.press_alt))

    pre_sss.append(pre_goal[0])
    post_goal.insert(0, pre_goal[-1])

    route_multilinestring = MultiLineString([pre_sss])
    features.append(Feature(geometry=route_multilinestring, properties={"Track": "Pre_SSS"}))
    route_multilinestring = MultiLineString([pre_goal])
    features.append(Feature(geometry=route_multilinestring, properties={"Track": "Pre_Goal"}))
    route_multilinestring = MultiLineString([post_goal])
    features.append(Feature(geometry=route_multilinestring, properties={"Track": "Post_Goal"}))

    tracklog = FeatureCollection(features)

    '''airspace infringements'''
    if result.infringements:
        for entry in result.infringements:
            time = ("%02d:%02d:%02d" % rawtime_float_to_hms(entry['rawtime'] + task.time_offset))
            infringements.append([entry['lon'], entry['lat'], int(entry['alt']), entry['space'], int(entry['distance']),
                                  entry['separation'], int(entry['rawtime']), time])

    return tracklog, thermals, takeoff_landing, bbox, waypoints_achieved, infringements


def create_trackpoints_layer(file: str, offset: int = 0):
    from igc_lib import Flight
    from calcUtils import sec_to_string
    try:
        flight = Flight.create_from_file(file)
        points = []
        for fix in flight.fixes:
            points.append([fix.lon, fix.lat, fix.rawtime, fix.press_alt, fix.gnss_alt,
                           sec_to_string(fix.rawtime), sec_to_string(fix.rawtime, offset)])
    except FileNotFoundError:
        print(f'Error: file not found {file}')
        return None
    except Exception:
        print(f'Error: cannot create trackpoints map layer from track: {file}')
        return None
    return points
