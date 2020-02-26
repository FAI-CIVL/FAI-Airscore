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

from flight_result import Flight_result
from myconn import Database
from participant import Participant
from track import Track


class Pilot(object):
    """Container class
    Attributes:
        info:           Participant Obj.
        result:         Task_result Obj.
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

    def as_dict(self):
        return self.__dict__

    @staticmethod
    def read(par_id, task_id):
        """reads result from database"""
        from participant import Participant
        from track import Track
        from flight_result import Flight_result
        from db_tables import RegisteredPilotView as R
        from db_tables import FlightResultView as F
        from sqlalchemy import and_

        pilot = Pilot()
        pilot.info = Participant(par_id=par_id)
        with Database() as db:
            # get result details.
            q = db.session.query(R)
            db.populate_obj(pilot.info, q.get(par_id))
            res = db.session.query(F).filter(and_(F.task_id == task_id, F.par_id == par_id)).first()
            if res:
                pilot.result = Flight_result()
                pilot.track = Track(track_file=res.track_file)
                db.populate_obj(pilot.result, res)
        return pilot

    @staticmethod
    def create(task_id=None, info=None, track=None, result=None):
        """ creates a Pilot obj. with all defined inner object"""
        pilot = Pilot()
        pilot.task_id = task_id
        pilot.info = info if info and isinstance(info, Participant) else Participant()
        pilot.track = track if track and isinstance(track, Track) else Track()
        pilot.result = result if result and isinstance(result, Flight_result) else Flight_result()
        return pilot

    @staticmethod
    def from_result(task_id, result):
        """ creates a Pilot obj. from result dict in Task Result json file"""
        pilot = Pilot.create(task_id=task_id)
        pilot.track.track_file = Track.from_dict(result)
        pilot.info = Participant.from_dict(result)
        pilot.result = Flight_result.from_dict(result)
        return pilot

    def create_result_dict(self):
        """ creates dict() with participant, result and track information"""
        from result import Task_result as R
        result = {}
        result.update({x: getattr(self.info, x) for x in R.results_list if x in dir(self.info)})
        result.update({x: getattr(self.track, x) for x in R.results_list if x in dir(self.track)})
        result.update({x: getattr(self.result, x) for x in R.results_list if x in dir(self.result)})
        return result

    @staticmethod
    def from_fsdb(task, data):
        """ Creates Pilot from FSDB task result"""

        info = Participant(ID=int(data.get('id')))
        result = Flight_result.from_fsdb(data, task.SS_distance, task.departure, task.arrival, task.time_offset)
        track = Track()
        if data.find('FsFlightData') is not None:
            track.track_file = data.find('FsFlightData').get('tracklog_filename')
        pilot = Pilot.create(task_id=task.id, info=info, track=track, result=result)
        return pilot

    def to_db(self, session=None):
        """ stores pilot result to database.
            we already have Flight_result.to_db()
            but if we organize track reading using Pilot obj. this should be useful.
            We will also be able to delete a lot of redundant info about track filename, pilot ID, task_id and so on"""

        from db_tables import TblTaskResult as R
        from sqlalchemy.exc import SQLAlchemyError

        '''checks conformity'''
        if not (self.par_id and self.task_id):
            '''we miss info about pilot and task'''
            print(f"Error: missing info about participant ID and/or task ID")
            return None

        result = self.result

        if not result.goal_time:
            result.goal_time = 0
        endss = 0 if result.ESS_time is None else result.ESS_time

        '''database connection'''
        with Database(session) as db:
            try:
                if self.track_id:
                    r = db.session.query(R).get(self.track_id)
                else:
                    '''create a new result'''
                    r = R(parPk=self.par_id, tasPk=self.task_id)

                r.tarDistance = result.distance_flown
                r.tarSpeed = result.speed
                r.tarLaunch = result.first_time
                r.tarStart = result.real_start_time
                r.tarGoal = result.goal_time
                r.tarSS = result.SSS_time
                r.tarES = endss
                r.tarTurnpoints = result.waypoints_made
                r.tarFixedLC = result.fixed_LC
                r.tarESAltitude = result.ESS_altitude
                r.tarGoalAltitude = result.goal_altitude
                r.tarMaxAltitude = result.max_altitude
                r.tarLastAltitude = result.last_altitude
                r.tarLastTime = result.last_time
                r.tarLandingAltitude = result.landing_altitude
                r.tarLandingTime = result.landing_time
                r.tarResultType = result.result_type
                r.tarComment = result.comment
                r.traFile = result.track_file

                if not self.track_id:
                    db.session.add(r)
                    db.session.flush()
                    self.track.track_id = r.tarPk
                db.session.commit()

            except SQLAlchemyError:
                print(f"Error storing result to database")
                db.session.rollback()


def update_all_results(task_id, pilots, session=None):
    """get results to update from the list"""
    from db_tables import TblTaskResult as R
    from sqlalchemy.exc import SQLAlchemyError

    update_mappings = []
    insert_mappings = []

    for pilot in pilots:
        res = pilot.result
        par_id = pilot.par_id
        track_file = pilot.track_file
        track_id = pilot.track_id

        '''checks conformity'''
        # TODO need to check this values at the end of scoring process, or probably just put as default in database
        if not res.goal_time:
            res.goal_time = 0
        if not res.ESS_time:
            res.ESS_time = 0

        mapping = {'tarDistance': res.distance_flown,
                   'tarSpeed': res.speed,
                   'tarLaunch': res.first_time,
                   'tarStart': res.real_start_time,
                   'tarGoal': res.goal_time,
                   'tarSS': res.SSS_time,
                   'tarES': res.ESS_time,
                   'tarTurnpoints': res.waypoints_made,
                   'tarFixedLC': res.fixed_LC,
                   'tarESAltitude': res.ESS_altitude,
                   'tarGoalAltitude': res.goal_altitude,
                   'tarMaxAltitude': res.max_altitude,
                   'tarLastAltitude': res.last_altitude,
                   'tarLastTime': res.last_time,
                   'tarLandingAltitude': res.landing_altitude,
                   'tarLandingTime': res.landing_time,
                   'tarResultType': res.result_type,
                   'tarPenalty': res.penalty,
                   'traFile': track_file}

        if track_id is None:
            ''' insert new result'''
            mapping.update({'tasPk': task_id, 'parPk': par_id})
            insert_mappings.append(mapping)
        else:
            ''' update result'''
            mapping.update({'tarPk': track_id})
            update_mappings.append(mapping)

    '''update database'''
    with Database(session) as db:
        try:
            if len(insert_mappings) > 0:
                db.session.bulk_insert_mappings(R, insert_mappings)
            if len(update_mappings) > 0:
                db.session.bulk_update_mappings(R, update_mappings)
            db.session.commit()
        except SQLAlchemyError:
            print(f'update all results on database gave an error')
            db.session.rollback()
            return False

    return True
