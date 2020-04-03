from dataclasses import dataclass, fields


@dataclass
class Notification:
    not_id: int = 0  # database id
    notification_type: str = 'admin'  # track, airspace, jtg, admin
    flat_penalty: float = 0.0
    percentage_penalty: float = 0.0
    comment: str = None
