# -*- coding: utf-8 -*-
"""Public forms."""
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired
import Defines
from airscore.user.models import User


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
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False

        self.user = User.query.filter_by(username=self.username.data).first()
        if not self.user:
            self.username.errors.append("Unknown username")
            return False

        if not self.user.check_password(self.password.data):
            self.password.errors.append("Invalid password")
            return False

        if not self.user.active:
            self.username.errors.append("User not activated")
            return False
        return True


class CompForm(FlaskForm):
    name = StringField('Competition Name')
    code = StringField('Short name')
    sanction = SelectField('Sanction', choices=[(x,x) for x in Defines.SANCTIONS], validators=[DataRequired()])
    type = SelectField('Type', choices=[('RACE', 'RACE'), ('ROUTE', 'ROUTE'), ('TEAM RACE', 'TEAM RACE')],
                       validators=[DataRequired()])
    category = SelectField('Category', choices=[('PG', 'PG'), ('HG', 'HG')], validators=[DataRequired()],
                           id='select_category')
    location = StringField('Location', validators=[DataRequired()])
    date_from = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    date_to = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    director = StringField('Race Director')
    time_offset = IntegerField('GMT offset', validators=[DataRequired()])
    pilot_registration = SelectField('Pilot Entry', choices=[('registered', 'registered'), ('open', 'open')])
    formula = SelectField('Formula', validators=[DataRequired()], id='select_formula')
    # username = 'bob'
