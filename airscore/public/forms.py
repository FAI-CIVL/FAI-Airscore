# -*- coding: utf-8 -*-
"""Public forms."""
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, IntegerField, SelectField
from airscore.user.models import User
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        # from db_tables import User
        # from myconn import Database
        import requests

        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False

        # original flask database
        # with db_session() as db:
        #     self.user = db.query(User).filter_by(username=self.username.data).first()

        self.user = User.query.filter_by(username=self.username.data).first()
        if not self.user:
            self.username.errors.append("Unknown username")
            return False

        url = 'https://legapiloti.it/wp-json/wp/v2/users/me'
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        r = requests.get(url, auth=(self.username.data, self.password.data), headers=headers).json()
        if not r['id'] == self.user.id:
            self.username.errors.append("Invalid password")
            return False
        return True


class ModifyParticipantForm(FlaskForm):
    id_num = IntegerField('ID')
    nat = StringField('Nat', validators=[Length(3)])
    glider = StringField('Glider')
    sponsor = StringField('Sponsor')
    certification = StringField('Certification')

# class LoginForm(FlaskForm):
#     """Login form."""
#
#     username = StringField("Username", validators=[DataRequired()])
#     password = PasswordField("Password", validators=[DataRequired()])
#
#     def __init__(self, *args, **kwargs):
#         """Create instance."""
#         super(LoginForm, self).__init__(*args, **kwargs)
#         self.user = None
#
#     def validate(self):
#         """Validate the form."""
#         initial_validation = super(LoginForm, self).validate()
#         if not initial_validation:
#             return False
#
#         self.user = User.query.filter_by(username=self.username.data).first()
#         if not self.user:
#             self.username.errors.append("Unknown username")
#             return False
#
#         if not self.user.check_password(self.password.data):
#             self.password.errors.append("Invalid password")
#             return False
#
#         if not self.user.active:
#             self.username.errors.append("User not activated")
#             return False
#         return True
