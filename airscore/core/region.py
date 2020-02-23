"""
Region Library
contains
    Region object Definition

Use: import region

Antonio Golfari - 2019
"""

from route import Turnpoint
from myconn import Database
from db_tables import tblRegion as R, RegionWaypointView as RWV, tblRegionWaypoint as RW
from sqlalchemy.exc import SQLAlchemyError

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

        turnpoints = []

        with Database() as db:
            q = db.session.query(R.regDescription.label('name'),
                                 R.regWptFileName.label('filename'),
                                 R.regOpenAirFile.label('openair')).filter(R.regPk == region_id).first()
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
            results = db.session.query(R.regPk,
                                     R.regDescription.label('name'),
                                     R.regWptFileName.label('filename'),
                                     R.regOpenAirFile.label('openair')).all()
            if results:
                results = [row._asdict() for row in results]
            return {'regions': results}

        except SQLAlchemyError:
            print("Error trying to retrieve regions")
            return None


def get_comp_regions_and_wpts(compid):
    with Database() as db:
        try:
            region_results = db.session.query(R.regPk,
                                       R.regDescription.label('name'),
                                       R.regWptFileName.label('filename'),
                                       R.regOpenAirFile.label('openair'))\
                                       .filter(R.comPk == compid).all()

            wpt_results = db.session.query(RW.regPk,
                                           RW.rwpPk,
                                           RW.rwpName,
                                           RW.rwpDescription).join(R).filter(R.regPk == RW.regPk, R.comPk == compid).all()

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
            wpt_results = db.session.query(RW.regPk,
                                           RW.rwpPk,
                                           RW.rwpName,
                                           RW.rwpDescription).join(R).filter(RW.regPk == reg_id).order_by(RW.rwpName).all()

            if wpt_results:
                wpt_results = [row._asdict() for row in wpt_results]

            return wpt_results

        except SQLAlchemyError:
            print("Error trying to retrieve regions")
            return None

