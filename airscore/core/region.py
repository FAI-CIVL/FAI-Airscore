"""
Region Library
contains
    Region object Definition

Use: import region

Antonio Golfari - 2019
"""

from route import Turnpoint
from myconn import Database
from db_tables import TblRegion as R, RegionWaypointView as RWV, TblRegionWaypoint as RW
from sqlalchemy.exc import SQLAlchemyError

class Region:
    def __init__(self, reg_id=None, name=None, filename=None, openair=None, turnpoints=[]):
        self.name = name
        self.reg_id = reg_id
        self.filename = filename
        self.openair = openair
        self.turnpoints = turnpoints

    @classmethod
    def read_db(cls, region_id):
        """
            reads region waypoints
        """

        turnpoints = []

        with Database() as db:
            q = db.session.query(R.description.label('name'),
                                 R.waypoint_file.label('filename'),
                                 R.openair_file.label('openair')).filter(R.reg_id == region_id).first()
            name, filename, openair = q.name, q.filename, q.openair
            w = db.session.query(RWV).filter(RWV.region_id == region_id).all()
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


def get_all_regions():
    with Database() as db:
        try:
            results = db.session.query(R.reg_id,
                                     R.description.label('name'),
                                     R.waypoint_file.label('filename'),
                                     R.openair_file.label('openair')).all()
            if results:
                results = [row._asdict() for row in results]
            return {'regions': results}

        except SQLAlchemyError:
            print("Error trying to retrieve regions")
            return None


def get_comp_regions_and_wpts(compid):
    with Database() as db:
        try:
            region_results = db.session.query(R.reg_id,
                                       R.description.label('name'),
                                       R.waypoint_file.label('filename'),
                                       R.openair_file.label('openair'))\
                                       .filter(R.comp_id == compid).all()

            wpt_results = db.session.query(RW.reg_id,
                                           RW.rwpPk,
                                           RW.rwpName,
                                           RW.rwpDescription).join(R).filter(R.reg_id == RW.reg_id,
                                                                             R.comp_id == compid).all()

            if region_results:
                region_results = [row._asdict() for row in region_results]
            if wpt_results:
                wpt_results = [row._asdict() for row in wpt_results]

            return {'regions': region_results, 'wpts': wpt_results}

        except SQLAlchemyError:
            print("Error trying to retrieve regions")
            return None


def get_region_wpts(reg_id):
    with Database() as db:
        try:
            wpt_results = db.session.query(RW.reg_id,
                                           RW.rwpPk,
                                           RW.rwpName,
                                           RW.rwpDescription).join(R).filter(
                                           RW.reg_id == reg_id).order_by(RW.rwpName).all()

            if wpt_results:
                wpt_results = [row._asdict() for row in wpt_results]

            return wpt_results

        except SQLAlchemyError:
            print("Error trying to retrieve regions")
            return None

