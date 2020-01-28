# -*- coding: utf-8 -*-
"""Public forms."""
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SelectField, IntegerField, SubmitField, FloatField, RadioField, BooleanField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, NumberRange, Length
import Defines
from airscore.user.models import User
from datetime import date


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
    comp_name = StringField('Competition Name')
    comp_code = StringField('Short name', render_kw=dict(maxlength=8), description='An abbreviated name (max 8 chars) e.g. PGEuro20')
    sanction = SelectField('Sanction', choices=[(x, x) for x in Defines.SANCTIONS])
    comp_type = SelectField('Type', choices=[('RACE', 'RACE'), ('ROUTE', 'ROUTE'), ('TEAM RACE', 'TEAM RACE')])
    comp_class = SelectField('Category', choices=[('PG', 'PG'), ('HG', 'HG')],
                           id='select_category')
    comp_site = StringField('Location', validators=[DataRequired()], description='location of the competition')
    date_from = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    date_to = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    MD_name = StringField('Race Director')
    time_offset = FloatField('GMT offset', validators=[DataRequired()], render_kw=dict(maxlength=5),
                             description='The default time offset for the comp. Individual tasks will have this '
                                         'as a default but can be overridden if your comp spans multiple time zones'
                                         ' or over change in daylight savings')
    pilot_registration = SelectField('Pilot Entry', choices=[('registered', 'registered'), ('open', 'open')],
                                     description='Registered - only pilots registered are flying, '
                                                 'open - all tracklogs uploaded are considered as entires')
    formula = SelectField('Formula', id='select_formula')
    overall_validity = SelectField('Scoring', choices=[('all', 'ALL'), ('ftv', 'FTV'), ('round', 'ROUND')]) # tblForComp comOverallScore  ??what is round?? do we also need old drop tasks?
    validity_param = IntegerField('FTV percentage', validators=[NumberRange(min=0, max=100)])
    nom_dist = IntegerField('Nominal Distance (km):')
    nom_goal = IntegerField('Nominal Goal (%):', validators=[NumberRange(min=0, max=100)])
    min_dist = IntegerField('Minimum Distance (km):')
    nom_launch = IntegerField('Nominal Launch (%):', validators=[NumberRange(min=0, max=100)])
    nom_time = IntegerField('Nominal Time (min):')
    team_scoring = SelectField('Team Scoring:', choices=[('aggregate', 'aggregate'), ()])
    locked = BooleanField('Competition Locked', description="i'm not 100 percnet what this does") #TODO
    submit = SubmitField('Save')

    def validate_on_submit(self):
        result = super(CompForm, self).validate()
        if self.date_from.data > self.date_to.data:
            return False
        else:
            return result
