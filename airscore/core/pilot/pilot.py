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


class Pilot(object):
    """Container class
    Attributes:
        info:           Participant Obj.
        result:         TaskResult Obj.
        track:          Track Obj.
    """

    def __init__(
        self,
        civl_id=None,
        name=None,
        sex=None,
        birthdate=None,
        nat=None,
        fai_id=None,
        fai_valid=1,
        xcontest_id=None,
        telegram_id=None,
        pil_id=None,
        ranking=None,
        hours=None,
    ):

        self.civl_id = civl_id  # int
        self.name = name  # str
        self.sex = sex  # 'M', 'F'
        self.birthdate = birthdate  # in datetime.date (Y-m-d) format
        self.nat = nat  # str
        self.fai_id = fai_id  # str
        self.fai_valid = fai_valid  # bool
        self.xcontest_id = xcontest_id  # str
        self.telegram_id = telegram_id  # int
        self.pil_id = pil_id  # PilotView id
        self.ranking = ranking  # WPRS Ranking?
        self.hours = hours  # flying hours last year?

    def __setattr__(self, attr, value):
        property_names = [p for p in dir(Pilot) if isinstance(getattr(Pilot, p), property)]
        if attr in ('nat', 'sex') and type(value) is str:
            self.__dict__[attr] = value.upper()
        elif attr not in property_names:
            self.__dict__[attr] = value

    @property
    def pilot_birthdate_str(self):
        return '' if isinstance(self.birthdate, (type(None), str)) else self.birthdate.strftime("%Y-%m-%d")

    @property
    def female(self):
        return 1 if self.sex == 'F' else 0

    def as_dict(self):
        return self.__dict__

    def __str__(self):
        out = ''
        out += 'Pilot:'
        out += f'{self.name} - CIVL_ID {self.civl_id} \n'
        return out


#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#     @staticmethod
#     def from_profile(pilot_id, comp_id=None, session=None):
#         from db_tables import PilotView, TblCountryCode
#         with db_session() as db:
#             try:
#                 result = db.query(PilotView).get(pilot_id)
#                 if result:
#                     pilot = Participant(pil_id=pilot_id, comp_id=comp_id)
#                     pilot.name = ' '.join([result.first_name.title(), result.last_name.title()])
#                     pilot.glider = ' '.join([result.glider_brand.title(), result.glider])
#                     c = aliased(TblCountryCode)
#                     pilot.nat = db.query(c.natIso3).filter(c.natId == result.nat).scalar()
#                     for attr in ['sex', 'civl_id', 'fai_id', 'sponsor', 'xcontest_id', 'glider_cert']:
#                         if hasattr(result, attr):
#                             setattr(pilot, attr, getattr(result, attr))
#                     return pilot
#                 else:
#                     print(f'Error: No result has been found for profile id {pilot_id}')
#                     return None
#             except SQLAlchemyError as e:
#                 error = str(e.__dict__)
#                 print(f"Error storing result to database")
#                 db.rollback()
#                 db.close()
#                 return error
#
#     @staticmethod
#     def read_old(par_id, task_id):
#         """reads result from database"""
#         from pilot.participant import Participant
#         from track import Track
#         from pilot.flightresult import FlightResult, get_waypoints_achieved
#         from db_tables import TblParticipant as R, FlightResultView as F
#         from sqlalchemy import and_
#         from pilot.notification import get_notifications
#         pilot = Pilot()
#         pilot.info = Participant(par_id=par_id)
#         pilot.task_id = task_id
#         with db_session() as db:
#             # get result details.
#             q = db.query(R)
#             db.populate_obj(pilot.info, q.get(par_id))
#             res = db.query(F).filter(and_(F.task_id == task_id, F.par_id == par_id)).first()
#             if res:
#                 pilot.result = FlightResult()
#                 pilot.track = Track(track_file=res.track_file, track_id=res.track_id)
#                 db.populate_obj(pilot.result, res)
#                 pilot.result.notifications = get_notifications(pilot, db.session)
#                 pilot.result.waypoints_achieved = get_waypoints_achieved(res.track_id, db.session)
#         return pilot
#
#     @staticmethod
#     def create(task_id=None, info=None, track=None, result=None):
#         """ creates a Pilot obj. with all defined inner object"""
#         pilot = Pilot()
#         pilot.task_id = task_id
#         pilot.info = info if info and isinstance(info, Participant) else Participant()
#         pilot.track = track if track and isinstance(track, Track) else Track()
#         pilot.result = result if result and isinstance(result, FlightResult) else FlightResult()
#         return pilot
#
#     @staticmethod
#     def from_result(task_id, result):
#         """ creates a Pilot obj. from result dict in Task Result json file"""
#         pilot = Pilot.create(task_id=task_id)
#         pilot.track = Track.from_dict(result)
#         pilot.info = Participant.from_dict(result)
#         pilot.result = FlightResult.from_dict(result)
#         return pilot
#
#     def create_result_dict(self):
#         """ creates dict() with participant, result and track information"""
#         from result import TaskResult as R
#         result = {}
#         result.update({x: getattr(self.info, x) for x in R.results_list if x in dir(self.info)})
#         result.update({x: getattr(self.track, x) for x in R.results_list if x in dir(self.track)})
#         result.update({x: getattr(self.result, x) for x in R.results_list if x in dir(self.result)})
#         result['notifications'] = [n.__dict__ for n in self.notifications]
#         result['waypoints_achieved'] = [dict(name=w.name, lat=w.lat, lon=w.lon, rawtime=w.rawtime,
#                                              altitude=w.altitude) for w in self.result.waypoints_achieved]
#         return result
#
#     @staticmethod
#     def from_fsdb(task, data):
#         """ Creates Pilot from FSDB task result"""
#         info = Participant(ID=int(data.get('id')))
#         result = FlightResult.from_fsdb(data, task.SS_distance, task.departure, task.arrival, task.time_offset)
#         track = Track()
#         if data.find('FsFlightData') is not None:
#             track.track_file = data.find('FsFlightData').get('tracklog_filename')
#         pilot = Pilot.create(task_id=task.id, info=info, track=track, result=result)
#         return pilot
#
#     def to_db(self, session=None):
#         """ stores pilot result to database.
#             we already have FlightResult.to_db()
#             but if we organize track reading using Pilot obj. this should be useful.
#             We will also be able to delete a lot of redundant info about track filename, pilot ID, task_id and so on"""
#         from db_tables import TblTaskResult as R
#         from pilot.notification import update_notifications
#         from pilot.flightresult import update_waypoints_achieved
#         from sqlalchemy.exc import SQLAlchemyError
#         '''checks conformity'''
#         if not (self.par_id and self.task_id):
#             '''we miss info about pilot and task'''
#             print(f"Error: missing info about participant ID and/or task ID")
#             return None
#         result = self.result
#         '''database connection'''
#         with db_session() as db:
#             try:
#                 if self.track_id:
#                     '''read db row'''
#                     r = db.query(R).get(self.track_id)
#                     r.comment = self.comment
#                     r.track_file = self.track_file
#                     for attr in [a for a in dir(r) if not (a[0] == '_' or a in ['track_file', 'comment'])]:
#                         if hasattr(result, attr):
#                             setattr(r, attr, getattr(result, attr))
#                     db.flush()
#                 else:
#                     '''create a new result'''
#                     r = R(par_id=self.par_id, task_id=self.task_id)
#                     db.populate_row(r, result)
#                     r.comment = self.comment
#                     r.track_file = self.track_file
#                     db.add(r)
#                     db.flush()
#                     self.track.track_id = r.track_id
#
#                 '''notifications'''
#                 update_notifications(self, db.session)
#                 '''waypoints_achieved'''
#                 update_waypoints_achieved(self, db.session)
#                 db.commit()
#             except SQLAlchemyError as e:
#                 error = str(e.__dict__)
#                 print(f"Error storing result to database")
#                 db.rollback()
#                 db.close()
#                 return error
#
#
# def update_all_results(task_id, pilots, session=None):
#     """ get results to update from the list
#         It is called from Task.check_all_tracks(), so only during Task full rescoring
#         And from FSDB.add results.
#         We are then deleting all present non admin Notification from database for results, as related to old scoring.
#         """
#     from db_tables import TblTaskResult as R, TblNotification as N, TblTrackWaypoint as W
#     from dataclasses import asdict
#     from sqlalchemy import and_
#     from sqlalchemy.exc import SQLAlchemyError
#     insert_mappings = []
#     update_mappings = []
#     notif_mappings = []
#     achieved_mappings = []
#     for pilot in pilots:
#         res = pilot.result
#         r = dict(track_id=pilot.track_id, task_id=task_id, par_id=pilot.par_id,
#                  track_file=pilot.track_file, comment=pilot.comment)
#         for key in [col for col in R.__table__.columns.keys() if col not in r.keys()]:
#             if hasattr(res, key):
#                 r[key] = getattr(res, key)
#         if r['track_id']:
#             update_mappings.append(r)
#         else:
#             insert_mappings.append(r)
#
#     '''update database'''
#     with db_session() as db:
#         try:
#             if insert_mappings:
#                 db.bulk_insert_mappings(R, insert_mappings, return_defaults=True)
#                 db.flush()
#                 for elem in insert_mappings:
#                     next(pilot for pilot in pilots if pilot.par_id == elem['par_id']).track.track_id = elem['track_id']
#             if update_mappings:
#                 db.bulk_update_mappings(R, update_mappings)
#                 db.flush()
#             '''notifications and waypoints achieved'''
#             '''delete old entries'''
#             db.query(N).filter(and_(N.track_id.in_([r['track_id'] for r in update_mappings]),
#                                             N.notification_type.in_(['jtg', 'auto', 'track']))).delete(
#                 synchronize_session=False)
#             db.query(W).filter(W.track_id.in_([r['track_id'] for r in update_mappings])).delete(
#                 synchronize_session=False)
#             '''collect new ones'''
#             for pilot in pilots:
#                 notif_mappings.extend([dict(track_id=pilot.track_id, **asdict(n))
#                                        for n in pilot.notifications if not n.notification_type == 'admin'])
#                 achieved_mappings.extend([dict(track_id=pilot.track_id, **asdict(w))
#                                           for w in pilot.result.waypoints_achieved])
#             '''bulk insert'''
#             if achieved_mappings:
#                 db.bulk_insert_mappings(W, achieved_mappings)
#             if notif_mappings:
#                 db.bulk_insert_mappings(N, notif_mappings, return_defaults=True)
#                 db.flush()
#                 res_not_list = [i for i in notif_mappings if i['notification_type'] in ['jtg', 'auto']]
#                 trackIds = set([i['track_id'] for i in res_not_list])
#                 for idx in trackIds:
#                     pilot = next(p for p in pilots if p.track_id == idx)
#                     for i, n in enumerate([el for el in res_not_list if el['track_id'] == idx]):
#                         next(e for e in pilot.result.notifications if e.notification_type == n['notification_type']
#                              and e.flat_penalty == n['flat_penalty']
#                              and e.percentage_penalty == n['percentage_penalty']
#                              and e.comment == n['comment']).not_id = n['not_id']
#             db.commit()
#         except SQLAlchemyError as e:
#             error = str(e.__dict__)
#             print(f"Error storing pilots results to database: {error}")
#             db.rollback()
#             db.close()
#             return error
#     return True
