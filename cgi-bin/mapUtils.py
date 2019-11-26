
def checkbbox(lat,lon,bbox):
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

    #TODO write objects to the geojson form the flight object
    min_lat = flight.fixes[0].lat
    min_lon = flight.fixes[0].lon
    max_lat = flight.fixes[0].lat
    max_lon = flight.fixes[0].lon

    bbox = [[min_lat,min_lon],[max_lat,max_lon]]

    for fix in flight.fixes:
        bbox = checkbbox(fix.lat,fix.lon,bbox)
    return bbox

def get_route_bbox(task):
    """Gets task boundaries """

    #TODO write objects to the geojson form the flight object
    min_lat = task.optimised_turnpoints[0].lat
    min_lon = task.optimised_turnpoints[0].lon
    max_lat = task.optimised_turnpoints[0].lat
    max_lon = task.optimised_turnpoints[0].lon

    bbox = [[min_lat,min_lon],[max_lat,max_lon]]

    for fix in task.optimised_turnpoints:
        bbox = checkbbox(fix.lat,fix.lon,bbox)
    return bbox

def get_region_bbox(region):
    """Gets region map boundaries """

    wpts = region.turnpoints
    #TODO write objects to the geojson form the flight object
    min_lat = wpts[0].lat
    min_lon = wpts[0].lon
    max_lat = wpts[0].lat
    max_lon = wpts[0].lon

    bbox = [[min_lat,min_lon],[max_lat,max_lon]]

    for wpt in wpts:
        bbox = checkbbox(wpt.lat,wpt.lon,bbox)
    return bbox

