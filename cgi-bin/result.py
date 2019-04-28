"""
Results Library

contains
    Task_result class
    Comp_result class

Use: from result import Task_result

Antonio Golfari & Stuart Mackintosh - 2019
"""

class Task_result:
    """
        creates Task Result sheets
        - in JSON format
        - in HTML format for AirTribune
    """

    def __init__(self, lat, lon, radius, type, shape, how):
        self.tasPk = None
        self.comPk = None
        self.date = lat
        self.lon = lon
        self.flat = lat * math.pi / 180
        self.flon = lon * math.pi / 180
        self.radius = radius
        self.type = type
        self.shape = shape
        self.how = how
        self.altitude = None

        assert type in ["launch", "speed", "waypoint", "endspeed", "goal"], \
            "turnpoint type is not valid: %r" % type
        assert shape in ["line", "circle"], "turnpoint shape is not valid: %r" % shape
        assert how in ["entry", "exit"], "turnpoint how (direction) is not valid: %r" % how

    def in_radius(self, fix, t, tm):
        """Checks whether the provided GNSSFix is within the radius"""
        if t < 0:
            tol = min(tm, self.radius * t)
        else:
            tol = max(tm, self.radius * t)

        return distance(self, fix) < self.radius + tol
