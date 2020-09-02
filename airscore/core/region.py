"""
Region Library
contains
    Region object Definition

Use: import region

Antonio Golfari - 2019
"""

from route import Turnpoint
from db.tables import TblRegion as R, RegionWaypointView as RWV, TblRegionWaypoint as RW


class Region:
    def __init__(self, reg_id=None, comp_id=None, name=None, filename=None, openair=None, turnpoints=[]):
        self.name = name
        self.reg_id = reg_id
        self.comp_id = comp_id
        self.filename = filename
        self.openair = openair
        self.turnpoints = turnpoints

    @classmethod
    def read_db(cls, region_id):
        """
        reads region waypoints
        """

        turnpoints = []

        q = R.query.with_entities(R.description.label('name'),
                                  R.waypoint_file.label('filename'),
                                  R.openair_file.label('openair')).filter_by(reg_id=region_id).first()
        name, filename, openair = q.name, q.filename, q.openair
        w = RWV.get_all(region_id=region_id)
        for tp in w:
            if tp.name[0] == 'D':
                type = 'launch'  # brown
            elif tp.name[0] == 'A':
                type = 'speed'  # green
            elif tp.name[0] == 'X':
                type = 'restricted'  # red
            else:
                type = 'waypoint'  # blue
            turnpoints.append(tp.populate(Turnpoint(radius=400, type=type, shape='circle', how='entry')))
        return cls(region_id, name, filename, openair, turnpoints)

    def to_db(self):
        """Inserts new task or updates existent one"""
        if not self.reg_id:
            region = R(comp_id=self.comp_id, description=self.name, waypoint_file=self.filename,
                       openair_file=self.openair)
        else:
            region = R.query.get(self.reg_id)
        region.save_or_update()
        self.reg_id = region.reg_id
        '''save waypoints'''
        if self.turnpoints:
            self.update_waypoints()

    def update_waypoints(self):
        from db.conn import db_session

        insert_mappings = []
        for idx, tp in enumerate(self.turnpoints):
            wpt = dict(tp.as_dict(), reg_id=self.reg_id)
            insert_mappings.append(wpt)

        with db_session() as db:
            db.bulk_insert_mappings(RW, insert_mappings, return_defaults=True)
            for elem in insert_mappings:
                next(tp for tp in self.turnpoints if tp.num == elem['num']).wpt_id = elem['wpt_id']


def get_all_regions():
    results = R.query.with_entities(R.reg_id,
                                    R.description.label('name'),
                                    R.waypoint_file.label('filename'),
                                    R.openair_file.label('openair')).order_by(R.description).all()
    if results:
        results = [row._asdict() for row in results]
    return {'regions': results}


def get_comp_regions_and_wpts(compid):
    region_results = R.query.with_entities(R.reg_id,
                                           R.description.label('name'),
                                           R.waypoint_file.label('filename'),
                                           R.openair_file.label('openair')) \
        .filter_by(comp_id=compid).all()

    wpt_results = RW.query.with_entities(RW.reg_id,
                                         RW.rwp_id,
                                         RW.name,
                                         RW.description) \
        .join(R) \
        .filter_by(reg_id=RW.reg_id, comp_id=compid).all()

    if region_results:
        region_results = [row._asdict() for row in region_results]
    if wpt_results:
        wpt_results = [row._asdict() for row in wpt_results]

    return {'regions': region_results, 'wpts': wpt_results}


def get_region_wpts(reg_id):
    wpt_results = RW.query.with_entities(RW.reg_id,
                                         RW.rwp_id,
                                         RW.name,
                                         RW.lat,
                                         RW.lon,
                                         RW.altitude,
                                         RW.xccSiteID,
                                         RW.xccToID,
                                         RW.description) \
                          .join(R)\
                          .filter_by(reg_id=reg_id).order_by(RW.name).all()

    if wpt_results:
        return [row._asdict() for row in wpt_results]


def delete_region(reg_id):
    """delete all database entries and files on disk related to comp"""
    from db.tables import TblRegion as R
    from db.tables import TblRegionWaypoint as RW
    from Defines import WAYPOINTDIR, AIRSPACEDIR
    import os
    reg = R.query.get(reg_id)
    waypoint_filename = reg.waypoint_file
    openair_filename = reg.openair_file
    files_to_delete = []
    if waypoint_filename:
        files_to_delete.append(os.path.join(WAYPOINTDIR, waypoint_filename))
    if openair_filename:
        files_to_delete.append(os.path.join(AIRSPACEDIR, openair_filename))
    for file in files_to_delete:
        if os.path.exists(file):
            os.remove(file)
    RW.delete_all(reg_id=reg_id)
    reg.delete()
