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

    # TODO write objects to the geojson form the flight object
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
    # TODO write objects to the geojson form the flight object
    min_lat = wpts[0].lat
    min_lon = wpts[0].lon
    max_lat = wpts[0].lat
    max_lon = wpts[0].lon

    bbox = [[min_lat, min_lon], [max_lat, max_lon]]

    for wpt in wpts:
        bbox = checkbbox(wpt.lat, wpt.lon, bbox)
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
    from db_tables import ResultView as R
    from myconn import Database

    with Database() as db:
        tracks = (db.session.query(R.tarPk, R.pilName).filter(R.tasPk == taskid, R.parPk != pilot_parid).all())

    return tracks
