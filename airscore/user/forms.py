# -*- coding: utf-8 -*-
"""User forms."""
from datetime import date

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, IntegerField, SelectField, DecimalField, BooleanField, SubmitField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange

import Defines
from .models import User


class RegisterForm(FlaskForm):
    """Register form."""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=25)]
    )
    email = StringField(
        "Email", validators=[DataRequired(), Email(), Length(min=6, max=40)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6, max=40)]
    )
    confirm = PasswordField(
        "Verify password",
        [DataRequired(), EqualTo("password", message="Passwords must match")],
    )

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append("Username already registered")
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append("Email already registered")
            return False
        return True


class NewTaskForm(FlaskForm):
    task_name = StringField("Task Name", description='optional. If you want to give the task a name. '
                                                     'If left blank it will default to "Task #"')
    task_number = IntegerField("Task Number", validators=[NumberRange(min=0, max=50)],
                               description='task number, by default one more than the last task')
    task_comment = StringField('Comment', description='Sometimes you may wish to make a comment that will show up'
                                                      ' in the competition overview page. e.g. "task stopped at 14:34"')
    task_date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    # task_region = SelectField('Region')


class CompForm(FlaskForm):
    from formula import list_formulas
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
    time_offset = DecimalField('GMT offset', validators=[DataRequired()], places=2, render_kw=dict(maxlength=5),
                               description='The default time offset for the comp. Individual tasks will have this '
                                         'as a default but can be overridden if your comp spans multiple time zones'
                                         ' or over change in daylight savings')
    pilot_registration = SelectField('Pilot Entry', choices=[('registered', 'registered'), ('open', 'open')],
                                     description='Registered - only pilots registered are flying, '
                                                 'open - all tracklogs uploaded are considered as entires')
    formulas = list_formulas()
    formula = SelectField('Formula', choices= [(x, x.upper()) for x in formulas['ALL']], id='select_formula')
    locked = BooleanField('Scoring Locked',
                          description="If locked, a rescore will not change displayed results")

    #formula object/table
    overall_validity = SelectField('Scoring', choices=[('all', 'ALL'), ('ftv', 'FTV'), ('round', 'ROUND')]) # tblForComp comOverallScore  ??what is round?? do we also need old drop tasks?
    validity_param = IntegerField('FTV percentage', validators=[NumberRange(min=0, max=100)])
    nom_dist = IntegerField('Nominal Distance (km):')
    nom_goal = IntegerField('Nominal Goal (%):', validators=[NumberRange(min=0, max=100)])
    min_dist = IntegerField('Minimum Distance (km):')
    nom_launch = IntegerField('Nominal Launch (%):', validators=[NumberRange(min=0, max=100)])
    nom_time = IntegerField('Nominal Time (min):')

    team_scoring = BooleanField('Team Scoring:')
    country_scoring = BooleanField('Country scoring:')
    team_size = IntegerField('Team size:')
    team_over = IntegerField('Team over: what is this??')

    distance = SelectField('Distance points:', choices=[('on','On'), ('difficulty','Difficulty'), ('off','Off')])
    arrival = SelectField('Arrival points:', choices=[('position','Position'), ('time','Time'), ('off','Off')])
    departure = SelectField('Departure points:', choices=[('leadout','Leadout'), ('departure','Departure'), ('off','Off')])
    time = SelectField('Time points:', choices=[('on','On'), ('off', 'Off')])

    alt_mode = SelectField('Instrument Altitude:', choices=[('GPS', 'GPS'), ('QNH', 'QNH')])
    lead_factor = DecimalField('Leadfactor:')
    no_goal_pen = DecimalField('No goal penalty:')

    tolerance = DecimalField('Turnpoint radius tolerance %:')
    min_tolerance = IntegerField('Minimum turnpoint tolerance (m):')
    glide_bonus = DecimalField('Glide bonus:')
    height_bonus = DecimalField('Height bonus:')
    ESS__height_upper = IntegerField('ESS height limit - upper:')
    ESS_height_lower = IntegerField('ESS height limit - lower:')
    min_time = IntegerField('Minimum time:')
    scoreback_time = IntegerField('Scoreback time (sec):')
    max_JTG = IntegerField("Max Jump the gun (sec):")
    JTG_pen_sec = DecimalField('Jump the gun penalty per second:')



    submit = SubmitField('Save')

    def validate_on_submit(self):
        result = super(CompForm, self).validate()
        if self.date_from.data > self.date_to.data:
            return False
        else:
            return result