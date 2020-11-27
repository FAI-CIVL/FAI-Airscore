# -*- coding: utf-8 -*-
import os
import sys

sys.path.append('/home/ubuntu/workspace/igc_lib/')

# import igc_lib.lib.dumpers as dumpers
import itertools

import folium

# using aerofiles library to parse igc to geojson
from aerofiles.igc import Reader

# database connections
from db.conn import db_session
from db.tables import TaskView as T
from flask import Flask, flash, json, redirect, render_template, request, url_for

# using igc_lib library to parse igc to geojson
from igc_lib.igc_lib import Flight
from werkzeug.utils import secure_filename

# import trackUtils


UPLOAD_FOLDER = '/home/ubuntu/workspace/uploads/'
ALLOWED_EXTENSIONS = set(['igc', 'xctsk'])

### select the library to parse the igc to geojson
global IGC_LIB
IGC_LIB = 'aerofiles'
# IGC_LIB ='igc_lib'

app = Flask(__name__)
app.secret_key = "A Super super uper secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


##############################################################################################################

# function to style geojson geometries
def style_function(feature):
    return {'fillColor': 'white', 'weight': 2, 'opacity': 1, 'color': 'red', 'fillOpacity': 0.5, "stroke-width": 3}


# function to return the bbox of geometries
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


# dump flight object to geojson object
def dump_flight_to_geojson(flight, geojson_filename_local):
    """Dumps the flight to geojson format. """

    from geojson import (
        Feature,
        FeatureCollection,
        MultiLineString,
        MultiPoint,
        Point,
        dump,
    )

    assert flight.valid

    # TODO write objects to the geojson form the flight object
    min_lat = flight.takeoff_fix.lat
    min_lon = flight.takeoff_fix.lon
    max_lat = flight.takeoff_fix.lat
    max_lon = flight.takeoff_fix.lon

    bbox = [[min_lat, min_lon], [max_lat, max_lon]]

    features = []
    # features.append(Feature(geometry=point, properties={"country": "Spain"}))

    takeoff = Point((flight.takeoff_fix.lon, flight.takeoff_fix.lat))
    features.append(Feature(geometry=takeoff, properties={"TakeOff": "TakeOff"}))
    bbox = checkbbox(flight.takeoff_fix.lat, flight.takeoff_fix.lon, bbox)
    landing = Point((flight.landing_fix.lon, flight.landing_fix.lat))
    features.append(Feature(geometry=landing, properties={"Landing": "Landing"}))
    bbox = checkbbox(flight.landing_fix.lat, flight.landing_fix.lon, bbox)

    thermals = []
    for i, thermal in enumerate(flight.thermals):
        #        add_point(name="thermal_%02d" % i, fix=thermal.enter_fix)
        thermals.append((thermal.enter_fix.lon, thermal.enter_fix.lat))
        #        add_point(name="thermal_%02d_END" % i, fix=thermal.exit_fix)
        thermals.append((thermal.exit_fix.lon, thermal.exit_fix.lat))

        bbox = checkbbox(thermal.enter_fix.lat, thermal.enter_fix.lon, bbox)
        bbox = checkbbox(thermal.exit_fix.lat, thermal.exit_fix.lon, bbox)

    thermals_multipoint = MultiPoint(thermals)
    features.append(Feature(geometry=thermals_multipoint))

    route = []
    for fix in flight.fixes:
        route.append((fix.lon, fix.lat))

        bbox = checkbbox(fix.lat, fix.lon, bbox)

    route_multilinestring = MultiLineString([route])
    features.append(Feature(geometry=route_multilinestring, properties={"Track": "Track"}))

    # add more features...
    # features.append(...)

    feature_collection = FeatureCollection(features)

    with open(geojson_filename_local, 'w') as f:
        dump(feature_collection, f)

    return bbox


# function to create the map template with optional geojson, circles and points objects
def make_map(layer_geojson=False, circles=False, points=False):
    folium_map = folium.Map(
        location=[45.922207, 8.673952], zoom_start=13, tiles="Stamen Terrain", width='100%', height='75%'
    )

    if layer_geojson:
        geojson = layer_geojson["geojson"]
        bbox = layer_geojson["bbox"]
        folium.GeoJson(geojson, name='Flight', style_function=style_function).add_to(folium_map)
        #        folium.GeoJson(geojson,name='Flight',style_function=style_function,tooltip=folium.features.GeoJsonTooltip(labels=True,sticky=False)).add_to(folium_map)
        folium_map.fit_bounds(bounds=bbox, max_zoom=13)

    if circles:
        for c in circles:
            folium.Circle(
                location=[c['latitude'], c['longitude']],
                radius=c['radius'],
                popup=c['description'] + '<br>' + c['name'] + '<br>' + str(c['altitude']) + 'm.a.s.l.',
                color='#3186cc',
                fill=True,
                fill_color='#3186cc',
            ).add_to(folium_map)

    if points:
        for p in points:
            folium.Marker(
                location=[p['latitude'], p['longitude']],
                popup=p['description'],
                icon=folium.features.DivIcon(
                    icon_size=(20, 20),
                    icon_anchor=(0, 0),
                    html='<div class="waypoint-label">%s</div>' % p['description'],
                ),
            ).add_to(folium_map)

    # path where to save the map
    folium_map.save('templates/map.html')


# funciton to extract flight details from flight object and return formatted html
def extract_flight_details(flight):
    flight_html = ""
    flight_html += "Flight:" + str(flight) + '\n'
    flight_html += "Takeoff:" + str(flight.takeoff_fix) + '\n'
    zipped = itertools.izip_longest(flight.thermals, flight.glides)
    for x, (thermal, glide) in enumerate(zipped):
        if glide:
            flight_html += "  glide[" + str(x) + "]:" + str(glide) + '\n'
        if thermal:
            flight_html += "  thermal[" + str(x) + "]:" + str(thermal) + '\n'
    flight_html += "Landing:" + str(flight.landing_fix)

    return flight_html


# dump flight object to geojson
def dump_flight(flight, input_file):
    input_base_file = os.path.splitext(input_file)[0]
    geojson_file = "%s-flight.geojson" % input_base_file
    bbox = dump_flight_to_geojson(flight, geojson_file)

    return geojson_file, bbox


# allowed uploads
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# parse task file object to formatted html
def get_task(parsed_task):

    has_waypoints = False
    task_coords = []

    table_rows = '<table class="table"><tr>'
    for obj in parsed_task:
        if obj not in ['', [], [[]], None, False]:
            if type(obj) == type({}):
                if obj.has_key('description'):
                    table_rows += '<tr><td>Track Type</td><td>' + str(obj['description']) + '</td></tr>'
                if obj.has_key('declaration_date'):
                    table_rows += '<tr><td>Date</td><td>' + str(obj['declaration_date'].isoformat()) + '</td></tr>'
                if obj.has_key('declaration_time'):
                    table_rows += '<tr><td>Time</td><td>' + str(obj['declaration_time'].isoformat()) + '</td></tr>'
                if obj.has_key('num_turnpoints'):
                    table_rows += '<tr><td>Turn Points</td><td>' + str(obj['num_turnpoints']) + '</td></tr>'
                # check for waypoints, if there are not it is not a task
                if obj.has_key('waypoints'):
                    if len(obj['waypoints']) > 1:
                        has_waypoints = True
                        # waypoints array object >> {'latitude': 45.92196666666667, 'description': 'TAKEOFF ?', 'longitude': 8.673833333333333}
                        for w in obj['waypoints']:
                            table_rows += (
                                '<tr><td>'
                                + str(obj['waypoints'].index(w) + 1)
                                + '</td><td>'
                                + str(w['description'])
                                + '</td></tr>'
                            )
                            task_coords.append(w)

    table_rows += '</tr></table>'

    if has_waypoints:
        return table_rows, task_coords
    else:
        return '<p>No Task for this IGC</p>', None


# funciton to parse json task from file to formatted html
def get_task_fromfile(jsontask):

    table_rows = '<table class="table"><tr>'
    table_rows += '<tr><td><b>SSS</b></td><td>---</td></tr>'
    for k, val in jsontask['sss'].items():
        table_rows += '<tr><td>' + str(k) + '</td><td>' + str(val) + '</td></tr>'
    table_rows += '<tr><td><b>Goal</b></td><td>---</td></tr>'
    for k, val in jsontask['goal'].items():
        table_rows += '<tr><td>' + str(k) + '</td><td>' + str(val) + '</td></tr>'
    table_rows += '<tr><td><b>Turnpoints</b></td><td>---</td></tr>'

    turnpoints = []
    for obj in jsontask['turnpoints']:
        table_rows += (
            '<tr><td>'
            + str(obj['waypoint']['name'])
            + ' | '
            + str(obj['radius'])
            + 'm </td><td>'
            + str('<br>'.join([str(k) + ': ' + str(v) for k, v in obj['waypoint'].items()]))
            + '</td></tr>'
        )
        turnpoints.append(
            {
                'radius': obj['radius'],
                'longitude': obj['waypoint']['lon'],
                'latitude': obj['waypoint']['lat'],
                'description': obj['waypoint']['description'],
                'altitude': obj['waypoint']['altSmoothed'],
                'name': obj['waypoint']['name'],
            }
        )
    table_rows += '</tr></table>'

    return table_rows, turnpoints


# function to create geojson object (mainly for tracks)
def get_track(records, geojson_filename_local):
    from geojson import Feature, FeatureCollection, LineString, dump

    # records structure [[], [{'LAD': 9, 'LOD': 3, 'time': datetime.time(14, 19, 53), 'lat': 45.92198333333333, 'pressure_alt': 0, 'gps_alt': 1155, 'lon': 8.673833333333333, 'validity': 'A'}, { ...
    features = []

    min_lat = records[1][0]['lat']
    min_lon = records[1][0]['lon']
    max_lat = records[1][0]['lat']
    max_lon = records[1][0]['lon']

    bbox = [[min_lat, min_lon], [max_lat, max_lon]]

    route = []
    for fix in records[1]:
        route.append((fix['lon'], fix['lat']))
        bbox = checkbbox(fix['lat'], fix['lon'], bbox)

    route_multilinestring = LineString(route)
    features.append(Feature(geometry=route_multilinestring, properties={"Track": "Track"}))

    # add more features...
    # features.append(...)

    feature_collection = FeatureCollection(features)

    with open(geojson_filename_local, 'w') as f:
        dump(feature_collection, f)

    return bbox


######################################################### flask app init and path
@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':

        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            # return 'No file part'
            return redirect(url_for('index'))
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No IGC file selected')
            # return 'No selected file'
            return redirect(url_for('index'))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_file)

            # check for task file
            if 'task' in request.files:
                task = request.files['task']
                if task and allowed_file(task.filename):
                    taskname = secure_filename(task.filename)
                    save_task = os.path.join(app.config['UPLOAD_FOLDER'], taskname)
                    task.save(save_task)
                flash(
                    'File IGC & TASK have been uploaded: Save this URL to see the result directly (inlcuding parameters)'
                )
                return redirect(url_for('index', filename=filename, taskname=taskname))
            else:
                flash('File IGC has been uploaded')
                return redirect(url_for('index', filename=filename))

    if request.method == 'GET':
        if request.args.get('filename'):
            file_to_open = os.path.join(app.config['UPLOAD_FOLDER'], request.args.get('filename'))
            if os.path.exists(file_to_open):
                flight_results = ""

                # check for task parameter and load task data
                task_filedata = False
                task_to_open = os.path.join(app.config['UPLOAD_FOLDER'], request.args.get('taskname'))
                if os.path.exists(task_to_open):
                    with open(task_to_open) as task_file:
                        task_filedata = json.load(task_file)

                if IGC_LIB == 'igc_lib':
                    flight = Flight.create_from_file(file_to_open)
                    if not flight.valid:
                        flight_results += "Provided flight is invalid:\n" + str(flight.notes) + '\n'
                    else:
                        flight_results = extract_flight_details(flight)
                        layer = {}
                        layer['geojson'], layer['bbox'] = dump_flight(flight, file_to_open)
                        make_map(layer_geojson=layer)
                    return render_template('home.html', flight_data=flight_results, igc_content='')
                else:
                    with open(file_to_open, 'r') as f:
                        parsed_igc_file = Reader().read(f)

                    flight_results += '<div class="btn btn-light" disabled>Your Track (IGC) data:</div>'
                    task, task_coords = get_task(parsed_igc_file['task'])

                    layer = {}
                    geojson_file = "%s-flight.geojson" % os.path.splitext(file_to_open)[0]
                    layer['geojson'] = geojson_file
                    layer['bbox'] = get_track(parsed_igc_file['fix_records'], geojson_file)

                    if task:
                        flight_results += str(task)

                    turnpoints = False
                    if task_filedata:
                        flight_results += '<div class="btn btn-light" disabled>Complete Task file data:</div>'
                        task_html, turnpoints = get_task_fromfile(task_filedata)
                        flight_results += str(task_html)

                    igc_object = '<code>' + str(parsed_igc_file) + '</code>'

                    make_map(layer_geojson=layer, points=task_coords, circles=turnpoints)

                    # testing connection to DB
                    # q = "SELECT * FROM TaskView LIMIT 1"
                    with db_session() as db:
                        t = db.query(T).first()
                        # t = db.fetchall(q)
                    #                    return render_template('home.html',flight_data=flight_results, igc_content=igc_object, mysql_query=t )
                    return render_template('home.html', flight_data=flight_results, igc_content=igc_object)

            else:
                flash('Missing file, please upload it first.')
                return render_template('home.html', flight_data='', igc_content='')
        else:
            make_map()
            return render_template('home.html', flight_data='', igc_content='')


app.debug = True
# app.run()
app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
