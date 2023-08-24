"""
Map definition
Creates map from track GeoJSON and Task Definition JSON

Martino Boni,
Stuart Mackintosh - 2019
"""

import folium
import folium.plugins
from folium.features import CustomIcon
from folium.map import FeatureGroup, Marker, Popup
from folium.plugins import semicircle
from mapUtils import bbox_centre


# functions to style geojson geometries
def style_function(feature):
    return {'fillColor': 'white', 'weight': 2, 'opacity': 1, 'color': 'red', 'fillOpacity': 0.5, "stroke-width": 3}


track_style_function = lambda x: {'color': 'red' if x['properties']['Track'] == 'Pre_Goal' else 'grey'}


# function to create the map template with optional geojson, circles and points objects
def make_map(
    layer_geojson=None,
    points=None,
    circles=None,
    polyline=None,
    goal_line=None,
    margin=0,
    min_margin=5,
    thermal_layer=False,
    show_thermal=False,
    waypoint_layer=False,
    show_waypoint=False,
    extra_tracks=None,
    airspace_layer=None,
    show_airspace=False,
    infringements=None,
    bbox=None,
    trackpoints=None,
):
    """Gets elements and layers from Flask, and returns map object"""
    '''creates layers'''
    if points is None:
        points = []

    if bbox:
        location = bbox_centre(bbox)
    else:
        location = [45, 10]

    folium_map = folium.Map(
        location=location,
        position='relative',
        zoom_start=13,
        tiles="Stamen Terrain",
        max_bounds=True,
        min_zoom=5,
        prefer_canvas=True,
    )
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
                    lambda x: {'color': colour if x['properties']['Track'] == 'Pre_Goal' else 'grey'}
                )

                for extra_track in extra_tracks:
                    colour = extra_track['colour']
                    folium.GeoJson(
                        extra_track['track'],
                        name=extra_track['name'],
                        style_function=extra_track_style_function(colour),
                    ).add_to(folium_map)

            if thermal_layer:
                thermals = layer_geojson['geojson']['thermals']
                thermal_group = FeatureGroup(name='Thermals', show=show_thermal)

                for t in thermals:
                    # icon = Icon(color='blue', icon_color='black', icon='sync-alt', angle=0, prefix='fas')
                    icon = CustomIcon('/app/airscore/static/img/thermal.png')
                    thermal_group.add_child(Marker([t[1], t[0]], icon=icon, popup=Popup(t[2])))

                folium_map.add_child(thermal_group)

            if waypoint_layer:
                waypoints = layer_geojson['geojson']['waypoint_achieved']
                waypoint_group = FeatureGroup(name='Waypoints Taken', show=show_waypoint)
                for w in waypoints:
                    waypoint_group.add_child(Marker([w[1], w[0]], popup=Popup(w[6], max_width='300')))
                if layer_geojson['geojson']['takeoff_landing']:
                    for w in layer_geojson['geojson']['takeoff_landing']:
                        # label = w['properties'].get('label')
                        event = w['properties']['event']
                        color = "green" if event == "TakeOff" else "darkred" if event == "Landing" else "orange"
                        icon = folium.Icon(color=color, icon="times", prefix='fa')
                        coords = w['geometry']['coordinates']
                        label = f"{event} at {w['properties'].get('time')}"
                        coords.reverse()  # changing to [lat, lon]
                        waypoint_group.add_child(Marker(coords, icon=icon, popup=Popup(label, max_width='300')))
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

            if 'radius_label' in c.keys():
                text = f"<b>{c['name']}</b><br>Radius: {str(c['radius_label'])} m."
            elif 'altitude' in c.keys():
                text = f"<b>{c['name']}</b><br>{str(c['description'])}<br>Altitude: {str(c['altitude'])} m."
            else:
                text = f"<b>{c['name']}</b>"
            popup = folium.Popup(text, max_width='300')

            folium.Circle(
                location=(c['latitude'], c['longitude']),
                radius=0.0 + c['radius'],
                popup=popup,
                color=col,
                weight=2,
                opacity=0.8,
                fill=True,
                fill_opacity=0.2,
                fill_color=col,
            ).add_to(folium_map)

    """Plot tolerance cylinders"""
    if margin:
        for c in circles:
            """create two circles based on tolerance value"""
            folium.Circle(
                location=(c['latitude'], c['longitude']),
                radius=c['radius'] + max(c['radius'] * margin, min_margin),
                popup=None,
                color="#44cc44",
                weight=0.75,
                opacity=0.8,
                fill=False,
            ).add_to(folium_map)

            folium.Circle(
                location=(c['latitude'], c['longitude']),
                radius=c['radius'] - max(c['radius'] * margin, min_margin),
                popup=None,
                color="#44cc44",
                weight=0.75,
                opacity=0.8,
                fill=False,
            ).add_to(folium_map)

    """Plot waypoints"""
    if points:
        for p in points:
            if layer_geojson:
                wp = folium.Marker(
                    location=[p['latitude'], p['longitude']],
                    popup=p['name'],
                    icon=folium.features.DivIcon(
                        icon_size=(40, 20), icon_anchor=(0, 0), html=f'<div class="waypoint-label">{p["name"]}</div>'
                    ),
                )
            else:
                wp = folium.Marker(
                    location=[p['latitude'], p['longitude']],
                    icon=folium.features.DivIcon(
                        icon_anchor=(0, 0),
                        html=f'<div style="background-color: darkblue; color: wheat; width: fit-content; padding: .1rem .2rem;">{p["name"]}</div>',
                    ),
                )
            wp.add_to(folium_map)

    """Design optimised route"""
    if polyline:
        folium.PolyLine(locations=polyline, weight=1.5, opacity=0.75, color='#2176bc').add_to(folium_map)

    if goal_line:
        '''create line'''
        folium.PolyLine(locations=goal_line[:2], weight=1.5, opacity=0.8, color='#800000').add_to(folium_map)
        '''add semicircle'''
        if len(goal_line) > 2:
            p = (points[-1]['latitude'], points[-1]['longitude'])
            r = goal_line[4]
            col = '#3186cc'
            angle = goal_line[5] % 360
            semicircle.SemiCircle(p, r,
                                  direction=angle,
                                  arc=180,
                                  color=col,
                                  weight=2,
                                  opacity=0.8,
                                  fill=True,
                                  fill_opacity=0.2,
                                  fill_color=col).add_to(folium_map)

            if margin:
                '''create tolerance area in front of goal line'''
                d = max(r*margin, 5)
                dlat, dlon = p[0] - goal_line[2][0], p[1] - goal_line[2][1]
                poly = [
                    goal_line[0],
                    (goal_line[0][0] - dlat, goal_line[0][1] - dlon),
                    (goal_line[1][0] - dlat, goal_line[1][1] - dlon),
                    goal_line[1]
                ]
                col = "#44cc44"
                folium.PolyLine(locations=poly, weight=0.75, opacity=0.8, color=col).add_to(folium_map)
                '''create tolerance semicircle'''
                r += d
                semicircle.SemiCircle(p, r,
                                      direction=angle,
                                      arc=180,
                                      color=col,
                                      weight=0.75,
                                      opacity=0.8,
                                      fill=False).add_to(folium_map)

    if airspace_layer:
        airspace_group = FeatureGroup(name='Airspaces', show=show_airspace)
        for space in airspace_layer:
            airspace_group.add_child(space)
        if infringements:
            for i in infringements:
                popup = folium.Popup(
                    f"<b>{i[3]}</b><br>{i[5]}. separation: {i[4]} m. <br>" f"{i[7]} - alt. {i[2]} m.", max_width='300'
                )
                icon = folium.Icon(color="red", icon="times", prefix='fa')
                airspace_group.add_child(Marker([i[1], i[0]], icon=icon, popup=popup))
        folium_map.add_child(airspace_group)

    if trackpoints:
        trackpoints_group = FeatureGroup(name='Trackpoints', show=True)
        for i in trackpoints:
            tooltip = folium.Tooltip(
                f"Time UTC: <b>{i[5]}</b> Local Time: <b>{i[6]}</b><br>"
                f"lat: <b>{round(i[1], 4)}</b> lon: <b>{round(i[0], 4)}</b><br>"
                f"GPS alt: <b>{int(i[4])} m.</b> ISA Press alt: <b>{int(i[3])} m.</b>"
            )
            trackpoints_group.add_child(folium.CircleMarker((i[1], i[0]), radius=1, tooltip=tooltip))
        folium_map.add_child(trackpoints_group)

    folium.LayerControl().add_to(folium_map)
    folium.plugins.Fullscreen().add_to(folium_map)
    folium.plugins.MeasureControl().add_to(folium_map)
    return folium_map


def get_map_render(folium_map):
    """ get a Folium Map object and returns a rendered Figure object"""
    '''first, force map to render as HTML, for us to dissect'''
    _ = folium_map._repr_html_()
    '''get definition of map in body'''
    html = folium_map.get_root().html.render()
    '''html to be included in header'''
    header = folium_map.get_root().header
    '''clean up css and unuseful elements'''
    # for el in ['meta_http', 'bootstrap_css', 'bootstrap_theme_css', 'jquery', 'bootstrap', 'css_style', 'map_style']:
    for el in ['meta_http', 'bootstrap_css', 'bootstrap_theme_css', 'bootstrap', 'css_style', 'map_style']:
        try:
            del header._children[el]
        except (NameError, KeyError):
            continue
    header = header.render()
    '''html to be included in <script>'''
    script = folium_map.get_root().script.render()
    return {"header": header, "html": html, "script": script}
