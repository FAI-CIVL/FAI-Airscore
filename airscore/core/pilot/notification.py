from dataclasses import dataclass, fields
from db_tables import TblNotification as N
from myconn import Database
from sqlalchemy.exc import SQLAlchemyError

@dataclass
class Notification:
    not_id: int = 0  # database id
    notification_type: str = 'admin'  # track, airspace, jtg, admin
    flat_penalty: float = 0.0
    percentage_penalty: float = 0.0
    comment: str = None

    @staticmethod
    def from_dict(d: dict):
        return Notification(**d)


def get_notifications(pilot, session=None):
    """reads notifications from database"""
    if not pilot.track_id:
        return
    notifications = []
    with Database(session) as db:
        try:
            results = db.session.query(N).filter(N.track_id == pilot.track_id).all()
            for n in [el for el in results if el.notification_type in ['jtg', 'airspace']]:
                notification = Notification()
                db.populate_obj(notification, n)
                notifications.append(notification)
            return results
        except SQLAlchemyError as e:
            error = str(e.__dict__)
            print(f"Error reading notifications for track id {pilot.track_id}")
            db.session.rollback()
            db.session.close()
            return error


def update_notifications(pilot, session=None):
    """inserts and / or updates pilot's notifications"""
    if not pilot.track_id:
        return
    with Database(session) as db:
        try:
            if len(pilot.notifications) > 0:
                insert_notifications_mappings = []
                update_notifications_mappings = []
                for n in pilot.notifications:
                    el = dict(track_id=pilot.track_id, notification_type=n.notification_type,
                              flat_penalty=n.flat_penalty, percentage_penalty=n.percentage_penalty,
                              comment=n.comment)
                    if n.not_id:
                        el['not_id'] = n.not_id,
                        update_notifications_mappings.append(el)
                    else:
                        insert_notifications_mappings.append(el)
                if insert_notifications_mappings:
                    db.session.bulk_insert_mappings(N, insert_notifications_mappings, return_defaults=True)
                    db.session.flush()
                    for elem in insert_notifications_mappings:
                        next(n for n in pilot.notifications if n.comment == elem['comment']).not_id = elem['not_id']
                if update_notifications_mappings:
                    db.session.bulk_update_mappings(N, update_notifications_mappings)
                    db.session.flush()
            db.session.commit()
        except SQLAlchemyError as e:
            error = str(e.__dict__)
            print(f"Error storing notifications to database for track id {pilot.track_id}")
            db.session.rollback()
            db.session.close()
            return error
