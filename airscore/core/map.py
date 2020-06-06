"""
Map definition
Creates map from track GeoJSON and Task Definition JSON
Use: design_map <track_id> <task_id>

Martino Boni,
Stuart Mackintosh - 2019
"""

import folium
import folium.plugins
from folium.features import CustomIcon
from folium.map import FeatureGroup, Marker, Popup
from mapUtils import bbox_centre


# functions to style geojson geometries
def style_function(feature):
    return {'fillColor': 'white', 'weight': 2, 'opacity': 1, 'color': 'red', 'fillOpacity': 0.5, "stroke-width": 3}


track_style_function = lambda x: {'color': 'red' if x['properties']['Track'] == 'Pre_Goal' else 'grey'}


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
