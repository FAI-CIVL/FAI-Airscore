from dataclasses import dataclass, fields


@dataclass
class Notification:
    notification_type: str = 'admin'  # track, result, admin
    flat_penalty: float = 0.0
    percentage_penalty: float = 0.0
    comment: str = None
