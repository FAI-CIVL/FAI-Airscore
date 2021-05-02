# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt
import jwt
from airscore.settings import SECRET_KEY
from time import time
from flask_login import UserMixin


from airscore.database import (
    Column,
    Model,
    SurrogatePK,
    db,
    reference_col,
    relationship,
)
from airscore.extensions import bcrypt


class Role(SurrogatePK, Model):
    """A role for a user."""

    __tablename__ = "roles"
    name = Column(db.String(80), unique=True, nullable=False)
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref="roles")

    def __init__(self, name, **kwargs):
        """Create instance."""
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Role({self.name})>"


class User(UserMixin, SurrogatePK, Model):
    """A user of the app."""

    __tablename__ = "users"
    id = Column(db.INTEGER, primary_key=True, nullable=False)
    username = Column(db.String(80), unique=True, nullable=False)
    password = Column(db.String(128), nullable=True)
    email = Column(db.String(80), unique=True, nullable=False)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    nat = Column(db.String(10))
    active = Column(db.Boolean(), default=False)
    access = Column(db.Enum('pilot', 'pending', 'scorekeeper', 'manager', 'admin'),
                    nullable=False, server_default=db.text("'pilot'"))

    def __init__(self, username, email, password=None, **kwargs):
        """Create instance."""
        db.Model.__init__(self, username=username, email=email, **kwargs)
        if password:
            self.set_password(password)
        else:
            self.password = None

    def set_password(self, password):
        """Set password."""
        self.password = bcrypt.generate_password_hash(password)

    def check_password(self, value):
        """Check password."""
        return bcrypt.check_password_hash(self.password, value)

    @property
    def full_name(self):
        """Full user name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        """True if access is admin."""
        return bool(self.access == 'admin')

    @property
    def is_manager(self):
        """True if access is manager."""
        return bool(self.access == 'manager')

    @property
    def is_scorekeeper(self):
        """True if access is scorekeeper."""
        return bool(self.access == 'scorekeeper')

    @property
    def has_private_frontend_access(self):
        return (self.is_scorekeeper or self.is_manager or self.is_admin) and self.active

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<User({self.username!r})>"

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            SECRET_KEY, algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, SECRET_KEY,
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    @staticmethod
    def admin_exists():
        return User.query.filter_by(access='admin').count() > 0
