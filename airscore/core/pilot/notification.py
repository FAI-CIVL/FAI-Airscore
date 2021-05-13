from dataclasses import dataclass, asdict

from db.conn import db_session
from db.tables import TblNotification as N


@dataclass
class Notification:
    not_id: int = None  # database id
    notification_type: str = 'custom'  # track, auto, jtg, custom
    flat_penalty: float = 0.0
    percentage_penalty: float = 0.0
    comment: str = None

    @staticmethod
    def from_dict(d: dict):
        return Notification(**d)

    def as_dict(self) -> dict:
        return asdict(self)


def get_notifications(pilot):
    """reads notifications from database"""
    if not pilot.track_id:
        return
    notifications = []
    with db_session() as db:
        results = db.query(N).filter(N.track_id == pilot.track_id).all()
        for n in [el for el in results if el.notification_type in ['jtg', 'auto']]:
            notification = Notification()
            n.populate(notification)
            notifications.append(notification)
        return results


def update_notifications(pilot):
    """inserts and / or updates pilot's notifications"""
    if not pilot.track_id:
        return
    with db_session() as db:
        if len(pilot.notifications) > 0:
            insert_notifications_mappings = []
            update_notifications_mappings = []
            for n in pilot.notifications:
                el = dict(
                    track_id=pilot.track_id,
                    notification_type=n.notification_type,
                    flat_penalty=n.flat_penalty,
                    percentage_penalty=n.percentage_penalty,
                    comment=n.comment,
                )
                if n.not_id:
                    el['not_id'] = (n.not_id,)
                    update_notifications_mappings.append(el)
                else:
                    insert_notifications_mappings.append(el)
            if insert_notifications_mappings:
                db.bulk_insert_mappings(N, insert_notifications_mappings, return_defaults=True)
                db.flush()
                for elem in insert_notifications_mappings:
                    next(n for n in pilot.notifications if n.comment == elem['comment']).not_id = elem['not_id']
            if update_notifications_mappings:
                db.bulk_update_mappings(N, update_notifications_mappings)
                db.flush()
        db.commit()
