"""
Region Library
contains
    Region object Definition

Use: import region

Antonio Golfari - 2019
"""

import numpy as np
from route import Turnpoint
from collections import namedtuple

class Region:
    def __init__(self, regPk=None, name=None, filename=None, openair=None, turnpoints=None):
        self.name       = name
        self.regPk      = regPk
        self.filename   = filename
        self.openair    = openair
        self.turnpoints = turnpoints

    @classmethod
    def read_db(cls, region_id):
        """
            reads region waypoints
        """
        from myconn import Database

        turnpoints = []

        query = """ SELECT
                        `regDescription` AS `name`,
                        `regWptFileName` AS `filename`,
                        `regOpenAirFile` AS `openair`
                    FROM
                        `tblRegion`
                    WHERE
                        `regPk` = %s
                    LIMIT 1"""

        with Database() as db:
            t = db.fetchone(query, [region_id])
        if not t:
            print('We could not find the region')
            return None
        name        = t['name']
        filename    = t['filename']
        openair     = t['openair']

        query = """ SELECT
                        `rwpName`           AS `name`,
                        `rwpLatDecimal`     AS `lat`,
                        `rwpLongDecimal`    AS `lon`,
                        `rwpAltitude`       AS `alt`,
                        `rwpDescription`    AS `desc`
                    FROM
                        `tblRegionWaypoint`
                    WHERE
                        `regPk` = %s AND `rwpOld` = 0 """

        with Database() as db:
            t = db.fetchall(query, [region_id])
        if not t:
            print('Region has no Waypoints')
        else:
            for tp in t:
                if      tp['name'][0] == 'D':   type = 'launch'         #brown
                elif    tp['name'][0] == 'A':   type = 'speed'          #green
                elif    tp['name'][0] == 'X':   type = 'restricted'     #red
                else:                           type = 'waypoint'       #blue
                turnpoint = Turnpoint(tp['lat'], tp['lon'], 400, type, 'circle', 'entry')
                turnpoint.name        = tp['name']
                turnpoint.altitude    = tp['alt']
                turnpoint.description = tp['desc']
                turnpoints.append(turnpoint)
        return cls(region_id, name, filename, openair, turnpoints)
