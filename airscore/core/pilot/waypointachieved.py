"""
Waypoint Achieved Library

contains WaypointAchieved Dataclass.

Element of FlightResult waipoints_achieved attribute list

- AirScore -
Stuart Mackintosh - Antonio Golfari
2020

"""

from dataclasses import dataclass, asdict
from sqlalchemy.exc import SQLAlchemyError
from myconn import Database


@dataclass
class WaypointAchieved:
    trw_id: int or None  # probably not needed as deleted each full-rescore. maybe to validate wpt by admin?
    wpt_id: int or None
    name: str
    rawtime: int
    lat: float
    lon: float
    altitude: int

    @staticmethod
    def from_dict(d: dict):
        return WaypointAchieved(**d)

def get_waypoints_achieved(track_id, session=None):
    """retrieves a WaypointAchieved obj list for track_id result"""
    from db_tables import TblTrackWaypoint
    from sqlalchemy.orm import aliased
    t = aliased(TblTrackWaypoint)
    achieved = []
    with Database(session) as db:
        try:
            rows = db.session.query(t.trw_id, t.wpt_id, t.name, t.rawtime,
                                    t.lat, t.lon, t.altitude).filter_by(track_id=track_id).all()
            for w in rows:
                achieved.append(WaypointAchieved(**w._asdict()))
        except SQLAlchemyError:
            print("there was a problem retrieving waypoints achieved")
            db.session.rollback()
            db.session.close()
    return achieved


def update_waypoints_achieved(pilot, session=None):
    """deletes old entries and updates TblTrackWaypoint for result"""
    from db_tables import TblTrackWaypoint
    mappings = []
    for w in pilot.waypoints_achieved:
        mappings.append(dict(track_id=pilot.track_id, **asdict(w)))
    with Database(session) as db:
        try:
            '''delete old entries'''
            db.session.query(TblTrackWaypoint).filter_by(track_id=pilot.track_id).delete()
            '''insert new rows'''
            db.session.bulk_insert_mappings(TblTrackWaypoint, mappings)
            db.session.commit()
        except SQLAlchemyError:
            print("there was a problem inserting waypoints achieved")
            db.session.rollback()
            db.session.close()