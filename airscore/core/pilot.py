"""
Pilot Library

contains Pilot class and methods

Methods:
    read    - reads from database
    to_db   - write result to DB (TblTaskResult) store_result_test - write result to DB in test mode(TblTaskResult_test)

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019

"""

from flightresult import FlightResult
from myconn import Database
from participant import Participant
from track import Track


class Pilot(object):
    """Container class
    Attributes:
        info:           Participant Obj.
        result:         TaskResult Obj.
        track:          Track Obj.
    """

    def __init__(self, task_id=None, info=None, track=None, result=None):
        """
            info: Object
            track_file: String
            result: Object
            flight: Object
        """
        self.task_id = task_id
        self.info = info
        self.track = track
        self.result = result

    def __setattr__(self, attr, value):
        property_names = [p for p in dir(Pilot) if isinstance(getattr(Pilot, p), property)]
        if attr not in property_names:
            self.__dict__[attr] = value

    @property
    def par_id(self):
        if self.info:
            return self.info.par_id
        else:
            return None

    @property
    def ID(self):
        if self.info:
            return self.info.ID
        else:
            return None

    @property
    def nat(self):
        if self.info:
            return self.info.nat
        else:
            return None

    @property
    def name(self):
        if self.info:
            return self.info.name
        else:
            return None

    @property
    def civl_id(self):
        if self.info:
            return self.info.civl_id
        else:
            return None

    @property
    def result_type(self):
        if self.result:
            return self.result.result_type
        else:
            return None

    @property
    def score(self):
        if self.result:
            return self.result.score
        else:
            return 0

    @property
    def track_file(self):
        if self.track:
            return self.track.track_file
        else:
            return None

    @property
    def track_id(self):
        if self.track:
            return self.track.track_id
        else:
            return None

    @property
    def flight(self):
        if self.track:
            return self.track.flight
        else:
            return None

    @property
    def comment(self):
        comment = []
        if self.flight and self.track.comment:
            comment.append(self.track.comment)
        if self.result and self.result.comment:
            comment.append(self.result.comment)
        return '; '.join(comment)

    @property
    def notifications(self):
        notifications = []
        if self.track:
            notifications.extend(self.track.notifications)
        if self.result:
            notifications.extend(self.result.notifications)
        return notifications

    def as_dict(self):
        return self.__dict__

    @staticmethod
    def read(par_id, task_id):
        """reads result from database"""
        from participant import Participant
        from track import Track
        from flightresult import FlightResult, get_waypoints_achieved
        from db_tables import TblParticipant as R, FlightResultView as F
        from sqlalchemy import and_
        from notification import get_notifications
        pilot = Pilot()
        pilot.info = Participant(par_id=par_id)
        pilot.task_id = task_id
        with Database() as db:
            # get result details.
            q = db.session.query(R)
            db.populate_obj(pilot.info, q.get(par_id))
            res = db.session.query(F).filter(and_(F.task_id == task_id, F.par_id == par_id)).first()
            if res:
                pilot.result = FlightResult()
                pilot.track = Track(track_file=res.track_file, track_id=res.track_id)
                db.populate_obj(pilot.result, res)
                pilot.result.notifications = get_notifications(pilot, db.session)
                pilot.result.waypoints_achieved = get_waypoints_achieved(res.track_id, db.session)
        return pilot

    @staticmethod
    def create(task_id=None, info=None, track=None, result=None):
        """ creates a Pilot obj. with all defined inner object"""
        pilot = Pilot()
        pilot.task_id = task_id
        pilot.info = info if info and isinstance(info, Participant) else Participant()
        pilot.track = track if track and isinstance(track, Track) else Track()
        pilot.result = result if result and isinstance(result, FlightResult) else FlightResult()
        return pilot

    @staticmethod
    def from_result(task_id, result):
        """ creates a Pilot obj. from result dict in Task Result json file"""
        pilot = Pilot.create(task_id=task_id)
        pilot.track = Track.from_dict(result)
        pilot.info = Participant.from_dict(result)
        pilot.result = FlightResult.from_dict(result)
        return pilot

    def create_result_dict(self):
        """ creates dict() with participant, result and track information"""
        from result import TaskResult as R
        result = {}
        result.update({x: getattr(self.info, x) for x in R.results_list if x in dir(self.info)})
        result.update({x: getattr(self.track, x) for x in R.results_list if x in dir(self.track)})
        result.update({x: getattr(self.result, x) for x in R.results_list if x in dir(self.result)})
        result['notifications'] = [n.__dict__ for n in self.notifications]
        result['waypoints_achieved'] = [dict(name=w.name, lat=w.lat, lon=w.lon, rawtime=w.rawtime,
                                             altitude=w.altitude) for w in self.result.waypoints_achieved]
        return result

    @staticmethod
    def from_fsdb(task, data):
        """ Creates Pilot from FSDB task result"""
        info = Participant(ID=int(data.get('id')))
        result = FlightResult.from_fsdb(data, task.SS_distance, task.departure, task.arrival, task.time_offset)
        track = Track()
        if data.find('FsFlightData') is not None:
            track.track_file = data.find('FsFlightData').get('tracklog_filename')
        pilot = Pilot.create(task_id=task.id, info=info, track=track, result=result)
        return pilot

    def to_db(self, session=None):
        """ stores pilot result to database.
            we already have FlightResult.to_db()
            but if we organize track reading using Pilot obj. this should be useful.
            We will also be able to delete a lot of redundant info about track filename, pilot ID, task_id and so on"""
        from db_tables import TblTaskResult as R
        from notification import update_notifications
        from flightresult import update_waypoints_achieved
        from sqlalchemy.exc import SQLAlchemyError
        '''checks conformity'''
        if not (self.par_id and self.task_id):
            '''we miss info about pilot and task'''
            print(f"Error: missing info about participant ID and/or task ID")
            return None
        result = self.result
        '''database connection'''
        with Database(session) as db:
            try:
                if self.track_id:
                    '''read db row'''
                    r = db.session.query(R).get(self.track_id)
                    r.comment = self.comment
                    r.track_file = self.track_file
                    for attr in [a for a in dir(r) if not (a[0] == '_' or a in ['track_file', 'comment'])]:
                        if hasattr(result, attr):
                            setattr(r, attr, getattr(result, attr))
                    db.session.flush()
                else:
                    '''create a new result'''
                    r = R(par_id=self.par_id, task_id=self.task_id)
                    db.populate_row(r, result)
                    r.comment = self.comment
                    r.track_file = self.track_file
                    db.session.add(r)
                    db.session.flush()
                    self.track.track_id = r.track_id

                '''notifications'''
                update_notifications(self, db.session)
                '''waypoints_achieved'''
                update_waypoints_achieved(self, db.session)
                db.session.commit()
            except SQLAlchemyError as e:
                error = str(e.__dict__)
                print(f"Error storing result to database")
                db.session.rollback()
                db.session.close()
                return error


def update_all_results(task_id, pilots, session=None):
    """ get results to update from the list
        It is called from Task.check_all_tracks(), so only during Task full rescoring
        And from FSDB.add results.
        We are then deleting all present non admin Notification from database for results, as related to old scoring.
        """
    from db_tables import TblTaskResult as R, TblNotification as N, TblTrackWaypoint as W
    from dataclasses import asdict
    from sqlalchemy import and_
    from sqlalchemy.exc import SQLAlchemyError
    insert_mappings = []
    update_mappings = []
    notif_mappings = []
    achieved_mappings = []
    for pilot in pilots:
        res = pilot.result
        r = dict(track_id=pilot.track_id, task_id=task_id, par_id=pilot.par_id,
                 track_file=pilot.track_file, comment=pilot.comment)
        for key in [col for col in R.__table__.columns.keys() if col not in r.keys()]:
            if hasattr(res, key):
                r[key] = getattr(res, key)
        if r['track_id']:
            update_mappings.append(r)
        else:
            insert_mappings.append(r)

    '''update database'''
    with Database(session) as db:
        try:
            if insert_mappings:
                db.session.bulk_insert_mappings(R, insert_mappings, return_defaults=True)
                db.session.flush()
                for elem in insert_mappings:
                    next(pilot for pilot in pilots if pilot.par_id == elem['par_id']).track.track_id = elem['track_id']
            if update_mappings:
                db.session.bulk_update_mappings(R, update_mappings)
                db.session.flush()
            '''notifications and waypoints achieved'''
            '''delete old entries'''
            db.session.query(N).filter(and_(N.track_id.in_([r['track_id'] for r in update_mappings]),
                                            N.notification_type.in_(['jtg', 'airspace', 'track']))).delete(
                synchronize_session=False)
            db.session.query(W).filter(W.track_id.in_([r['track_id'] for r in update_mappings])).delete(
                synchronize_session=False)
            '''collect new ones'''
            for pilot in pilots:
                notif_mappings.extend([dict(track_id=pilot.track_id, **asdict(n))
                                       for n in pilot.notifications if not n.notification_type == 'admin'])
                achieved_mappings.extend([dict(track_id=pilot.track_id, **asdict(w))
                                          for w in pilot.result.waypoints_achieved])
            '''bulk insert'''
            if achieved_mappings:
                db.session.bulk_insert_mappings(W, achieved_mappings)
            if notif_mappings:
                db.session.bulk_insert_mappings(N, notif_mappings, return_defaults=True)
                db.session.flush()
                res_not_list = [i for i in notif_mappings if i['notification_type'] in ['jtg', 'airspace']]
                trackIds = set([i['track_id'] for i in res_not_list])
                for idx in trackIds:
                    pilot = next(p for p in pilots if p.track_id == idx)
                    for i, n in enumerate([el for el in res_not_list if el['track_id'] == idx]):
                        next(e for e in pilot.result.notifications if e.notification_type == n['notification_type']
                             and e.flat_penalty == n['flat_penalty']
                             and e.percentage_penalty == n['percentage_penalty']
                             and e.comment == n['comment']).not_id = n['not_id']
            db.session.commit()
        except SQLAlchemyError as e:
            error = str(e.__dict__)
            print(f"Error storing pilots results to database: {error}")
            db.session.rollback()
            db.session.close()
            return error
    return True
