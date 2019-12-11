"""
Region Library
contains
    Region object Definition

Use: import region

Antonio Golfari - 2019
"""

import numpy as np
from route import Turnpoint


class Region:
    def __init__(self, regPk=None, name=None, filename=None, openair=None, turnpoints=[]):
        self.name = name
        self.regPk = regPk
        self.filename = filename
        self.openair = openair
        self.turnpoints = turnpoints

    @classmethod
    def read_db(cls, region_id):
        """
            reads region waypoints
        """
        from myconn import Database
        from db_tables import tblRegion as R, RegionWaypointView as RW

        turnpoints = []

        with Database() as db:
            q = db.session.query(R.regDescription.label('name'),
                                 R.regWptFileName.label('filename'),
                                 R.regOpenAirFile.label('openair')).filter(R.regPk == region_id).first()
            name, filename, openair = q.name, q.filename, q.openair
            w = db.session.query(RW).filter(RW.region_id == region_id).all()
            for tp in w:
                if tp.name[0] == 'D':
                    type = 'launch'  # brown
                elif tp.name[0] == 'A':
                    type = 'speed'  # green
                elif tp.name[0] == 'X':
                    type = 'restricted'  # red
                else:
                    type = 'waypoint'  # blue
                turnpoint = Turnpoint(radius=400, type=type, shape='circle', how='entry')
                db.populate_obj(turnpoint, tp)
                turnpoints.append(turnpoint)
        return cls(region_id, name, filename, openair, turnpoints)
