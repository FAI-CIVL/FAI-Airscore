"""
Map definition
Creates map from track GeoJSON and Task Definition JSON
Use: design_map <track_id> <task_id>

Martino Boni,
Stuart Mackintosh - 2019
"""


import itertools
import sys

import folium
import folium.plugins
from folium.features import CustomIcon
from folium.map import FeatureGroup, Marker, Popup
from geographiclib.geodesic import Geodesic

from mapUtils import get_region_bbox, get_route_bbox, bbox_centre
from task import Task

geod = Geodesic.WGS84

# select the library to parse the igc to geojson
global IGC_LIB
IGC_LIB = 'igc_lib'


# functions to style geojson geometries
def style_function(feature):
    return {'fillColor': 'white', 'weight': 2, 'opacity': 1, 'color': 'red', 'fillOpacity': 0.5, "stroke-width": 3}


track_style_function = lambda x: {'color':'red' if x['properties']['Track'] == 'Pre_Goal' else 'grey'}


# function to create the map template with optional geojson, circles and points objects
def make_map(layer_geojson=None, points=None, circles=None, polyline=None, goal_line=None, margin=0,
             thermal_layer=False, waypoint_layer=False, extra_tracks=None, airspace_layer=None, bbox=None):
    if points is None:
        points = []

    if bbox:
        location = bbox_centre(bbox)
    else:
        location = [45, 10]
    folium_map = folium.Map(location=location, zoom_start=13, tiles="Stamen Terrain", width='100%',
                            height='75%')
    #     folium.LayerControl().add_to(folium_map)
    '''Define map borders'''
    # at this stage a track (layer_geojason has bbox inside,
    # otherwise (plotting wpts, airspace, task) we can use the bbox variable
    if bbox:
        folium_map.fit_bounds(bounds=bbox, max_zoom=13)

    if layer_geojson:

        '''Define map borders'''
        if layer_geojson["bbox"]:
            bbox = layer_geojson["bbox"]
            folium_map.fit_bounds(bounds=bbox, max_zoom=13)

        """Design track"""
        if layer_geojson["geojson"]:
            track = layer_geojson['geojson']['tracklog']
            folium.GeoJson(track, name='Flight', style_function=track_style_function).add_to(folium_map)
            if extra_tracks:
                extra_track_style_function = lambda colour: (
                    lambda x: {'color': colour if x['properties']['Track'] == 'Pre_Goal' else 'grey'})

                for extra_track in extra_tracks:
                    colour = extra_track['colour']
                    folium.GeoJson(extra_track['track'], name=extra_track['name'],
                                   style_function=extra_track_style_function(colour)).add_to(folium_map)

            if thermal_layer:
                thermals = layer_geojson['geojson']['thermals']
                thermal_group = FeatureGroup(name='Thermals', show=False)

                for t in thermals:
                    # icon = Icon(color='blue', icon_color='black', icon='sync-alt', angle=0, prefix='fas')
                    icon = CustomIcon('/app/airscore/static/img/thermal.png')
                    thermal_group.add_child(Marker([t[1], t[0]], icon=icon, popup=Popup(t[2])))

                folium_map.add_child(thermal_group)

            if waypoint_layer:
                waypoints = layer_geojson['geojson']['waypoint_achieved']
                waypoint_group = FeatureGroup(name='Waypoints Taken', show=False)
                for w in waypoints:
                    waypoint_group.add_child(Marker([w[1], w[0]], popup=Popup(w[5])))

                folium_map.add_child(waypoint_group)
    """Design cylinders"""
    if circles:
        for c in circles:
            """create design based on type"""
            if c['type'] == 'launch':
                col = '#996633'
            elif c['type'] == 'speed':
                col = '#00cc00'
            elif c['type'] == 'endspeed':
                col = '#cc3333'
            elif c['type'] == 'restricted':
                col = '#ff0000'
            else:
                col = '#3186cc'

            popup = folium.Popup(f"<b>{c['name']}</b><br>Radius: {str(c['radius_label'])} m.", max_width=300)

            folium.Circle(
                location=(c['latitude'], c['longitude']),
                radius=0.0 + c['radius'],
                popup=popup,
                color=col,
                weight=2,
                opacity=0.8,
                fill=True,
                fill_opacity=0.2,
                fill_color=col
            ).add_to(folium_map)

    """Plot tolerance cylinders"""
    if margin:
        for c in circles:
            """create two circles based on tolerance value"""
            folium.Circle(
                location=(c['latitude'], c['longitude']),
                radius=0.0 + c['radius'] * (1 + margin),
                popup=None,
                color="#44cc44",
                weight=0.75,
                opacity=0.8,
                fill=False
            ).add_to(folium_map)

            folium.Circle(
                location=(c['latitude'], c['longitude']),
                radius=0.0 + c['radius'] * (1 - margin),
                popup=None,
                color="#44cc44",
                weight=0.75,
                opacity=0.8,
                fill=False
            ).add_to(folium_map)

    """Plot waypoints"""
    if points:
        for p in points:
            folium.Marker(
                location=[p['latitude'], p['longitude']],
                popup=p['name'],
                icon=folium.features.DivIcon(
                    icon_size=(20, 20),
                    icon_anchor=(0, 0),
                    html='<div class="waypoint-label">%s</div>' % p['name'],
                )
            ).add_to(folium_map)

    """Design optimised route"""
    if polyline:
        folium.PolyLine(
            locations=polyline,
            weight=1.5,
            opacity=0.75,
            color='#2176bc'
        ).add_to(folium_map)

    if goal_line:
        folium.PolyLine(
            locations=goal_line,
            weight=1.5,
            opacity=0.75,
            color='#800000'
        ).add_to(folium_map)

    if airspace_layer:
        for space in airspace_layer:
            space.add_to(folium_map)

    # path where to save the map
    # folium_map.save('templates/map.html')
    folium.LayerControl().add_to(folium_map)
    folium.plugins.Fullscreen().add_to(folium_map)
    folium.plugins.MeasureControl().add_to(folium_map)

    return folium_map


# function to extract flight details from flight object and return formatted html
def extract_flight_details(flight):
    flight_html = ""
    flight_html += "Flight:" + str(flight) + '\n'
    flight_html += "Takeoff:" + str(flight.takeoff_fix) + '\n'
    zipped = itertools.izip_longest(flight.thermals, flight.glides)
    for x, (thermal, glide) in enumerate(zipped):
        if glide:
            flight_html+= "  glide[" + str(x) + "]:" + str(glide) + '\n'
        if thermal:
            flight_html+= "  thermal[" + str(x) + "]:" + str(thermal) + '\n'
    flight_html += "Landing:" + str(flight.landing_fix)

    return flight_html


# dump flight object to geojson
def dump_flight(track, task):
    # TODO check if file already exists otherwise create and save it
    from flightresult import FlightResult
    from mapUtils import get_bbox
    lib = task.formula.get_lib()

    task_result = FlightResult.check_flight(track.flight, task)  # check flight against task
    geojson_file = task_result.to_geojson_result(track, task)
    bbox = get_bbox(track.flight)

    return geojson_file, bbox

# allowed uploads
# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_region(region_id):
    from region import Region as Reg

    region = Reg.read_db(region_id)
    wpt_coords = []
    turnpoints = []

    for obj in region.turnpoints:
        wpt_coords.append({
        'longitude' : obj.lon,
        'latitude'  : obj.lat,
        'name'      : obj.name
        })

        turnpoints.append({
        'radius'    : obj.radius,
        'longitude' : obj.lon,
        'latitude'  : obj.lat,
#         'altitude': obj.altitude,
        'name'      : obj.name,
        'type'      : obj.type,
        'shape'     : obj.shape

        })

    return region, wpt_coords,turnpoints

def main(mode, val, track_id):
    """Main module"""
    from task import get_map_json
    from trackUtils import read_tracklog_map_result_file
#     log_dir = d.LOGDIR
#     print("log setup")
#     logging.basicConfig(filename=log_dir + 'main.log',level=logging.INFO,format='%(asctime)s %(message)s')

    short_route = []
    layer={}

    if mode == 'region':
        '''waypoints map'''
        region_id = val
        region, wpt_coords, turnpoints = get_region(region_id)
        layer['geojson'] = None
        layer['bbox'] = get_region_bbox(region)
    else:
        '''create the task map for route or tracklog maps'''
        task_id = val
        wpt_coords, turnpoints, short_route, goal_line, tolerance = get_map_json(task_id)

        if mode == 'tracklog':
            """read task and track objects"""
            layer['geojson'] = read_tracklog_map_result_file(track_id, task_id)

            layer['bbox'] = layer['geojson']['bounds']
        elif mode == 'route':
            task = Task.read(task_id)
            layer['geojson'] = None
            layer['bbox'] = get_route_bbox(task)

    map = make_map(layer_geojson=layer, points=wpt_coords, circles=turnpoints, polyline=short_route, goal_line=goal_line, margin=tolerance)
    #map.save(map_file)
    #os.chown(map_file, 1000, 1000)
    html_string = map.get_root().render()

    print(html_string)


if __name__== "__main__":
    track_id    = None
    val         = None
    mode        = None
    # check parameter is good.
    if len(sys.argv) >= 3 and sys.argv[2].isdigit():
        mode    = str(sys.argv[1])
        val     = int(sys.argv[2])
        if mode == 'tracklog': track_id = int(sys.argv[3])

    else:
        # logging.error("number of arguments != 1 and/or task_id not a number")
        print("Error, incorrect arguments type or number.")
        print("usage: design_map mode (region tracklog, route), val(regionid taskid), track_id")
        exit()
    main(mode, val, track_id)
