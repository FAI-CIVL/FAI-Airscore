# -*- coding: utf-8 -*-
"""User forms."""
from datetime import date

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, IntegerField, SelectField, DecimalField, BooleanField, SubmitField

from wtforms.fields.html5 import DateField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

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
    task_region = SelectField('Region')


class CompForm(FlaskForm):
    from formula import list_formulas

    help_nom_launch = "When pilots do not take off for safety reasons, to avoid difficult launch conditions or bad " \
                      "conditions in the air, Launch Validity is reduced.. Nominal Launch defines a threshold as a " \
                      "percentage of the pilots in a competition. Launch Validity is only reduced if fewer pilots " \
                      "than defined by that threshold decide to launch. The recommended default value for Nominal" \
                      " Launch is 96%, which means that Launch Validity will only be reduced if fewer than 96% of" \
                      " the pilots present at launch chose to launch."

    help_nom_distance = "Nominal distance should be set to the expected average task distance for the competition." \
                        " Depending on the other competition parameters and the distances actually flown by pilots, " \
                        "tasks shorter than Nominal Distance will be devalued in most cases. Tasks longer than" \
                        " nominal distance will usually not be devalued, as long as the pilots fly most of the " \
                        "distance. In order for GAP to be able to distinguish between good and not-so-good tasks, " \
                        "and devalue the latter, it is important to set nominal distance high enough"

    help_min_distance = "The minimum distance awarded to every pilot who takes off. It is the distance below which " \
                        "it is pointless to measure a pilot's performance. The minimum distance parameter is set so " \
                        "that pilots who are about to 'bomb out' will not be tempted to fly into the next field to " \
                        "get past a group of pilots – they all receive the same amount of points anyway."

    help_nom_goal = "The percentage of pilots the meet director would wish to have in goal in a well-chosen task. " \
                    "This is typically 20 to 40%. This parameter has a very marginal effect on distance validity."

    help_nom_time = "Nominal time indicates the expected task duration, the amount of time required to fly the speed" \
                    " section. If the fastest pilot’s time is below nominal time, the task will be devalued. There is" \
                    " no devaluation if the fastest pilot’s time is above nominal time. Nominal time should be set to " \
                    "the expected “normal” task duration for the competition site, and nominal distance / nominal time " \
                    "should be a bit higher than typical average speeds for the area."

    help_score_back = "In a stopped task, this value defines the amount of time before the task stop was announced" \
                      " that will not be considered for scoring. The default is 5 minutes, but depending on local " \
                      "meteorological circumstances, it may be set to a longer period for a whole competition."


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
    nom_dist = IntegerField('Nominal Distance (km)', description=help_nom_distance)
    nom_goal = IntegerField('Nominal Goal (%)', description=help_nom_goal, validators=[NumberRange(min=0, max=100)])
    min_dist = IntegerField('Minimum Distance (km)', description=help_min_distance)
    nom_launch = IntegerField('Nominal Launch (%)', description=help_nom_launch, validators=[NumberRange(min=0, max=100)])
    nom_time = IntegerField('Nominal Time (min)', description=help_nom_time)

    team_scoring = BooleanField('Team Scoring')
    country_scoring = BooleanField('Country scoring')
    team_size = IntegerField('Team size',validators=[Optional(strip_whitespace=True)])
    team_over = IntegerField('Team over- what is this??', validators=[Optional(strip_whitespace=True)])

    distance = SelectField('Distance points', choices=[('on','On'), ('difficulty','Difficulty'), ('off','Off')])
    arrival = SelectField('Arrival points', choices=[('position','Position'), ('time','Time'), ('off','Off')])
    departure = SelectField('Departure points', choices=[('leadout','Leadout'), ('departure','Departure'), ('off','Off')])
    time = SelectField('Time points', choices=[('on','On'), ('off', 'Off')])

    alt_mode = SelectField('Instrument Altitude', choices=[('GPS', 'GPS'), ('QNH', 'QNH')])
    lead_factor = DecimalField('Leadfactor')
    no_goal_pen = DecimalField('No goal penalty')

    tolerance = DecimalField('Turnpoint radius tolerance %')
    min_tolerance = IntegerField('Minimum turnpoint tolerance (m)')
    glide_bonus = DecimalField('Glide bonus')
    height_bonus = DecimalField('Height bonus')
    ESS_height_upper = IntegerField('ESS height limit - upper', validators=[Optional(strip_whitespace=True)])
    ESS_height_lower = IntegerField('ESS height limit - lower', validators=[Optional(strip_whitespace=True)])
    min_time = IntegerField('Minimum time')
    scoreback_time = IntegerField('Scoreback time (sec)', description=help_score_back)
    max_JTG = IntegerField("Max Jump the gun (sec)", validators=[Optional(strip_whitespace=True)])
    JTG_pen_sec = DecimalField('Jump the gun penalty per second', validators=[Optional(strip_whitespace=True)])



    submit = SubmitField('Save')

    def validate_on_submit(self):
        result = super(CompForm, self).validate()
        if self.date_from.data > self.date_to.data:
            return False
        else:
            return result

class TaskForm(FlaskForm):
    #general
    comp_name = ""
    task_name = StringField("Task Name", description='optional. If you want to give the task a name. '
                                                     'If left blank it will default to "Task #"')
    task_num = IntegerField("Task Number", validators=[NumberRange(min=0, max=50)],
                               description='task number, by default one more than the last task')
    comment = StringField('Comment', description='Sometimes you may wish to make a comment that will show up'
                                                      ' in the competition overview page. e.g. "task stopped at 14:34"')
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    task_type = SelectField('Type', choices=[('race', 'Race'), ('elapsed_time', 'Elapsed time')])
    # times
    window_open_time = TimeField('Window open', format='%H:%M', validators=[DataRequired()])
    start_time = TimeField('Start time', format='%H:%M', validators=[DataRequired()])
    window_close_time = TimeField('Window close', format='%H:%M', validators=[DataRequired()])
    start_close_time = TimeField('Start close', format='%H:%M', validators=[DataRequired()])
    stopped_time = TimeField('Stopped time', format='%H:%M', validators=[Optional(strip_whitespace=True)])
    task_deadline = TimeField('Deadline', format='%H:%M', validators=[DataRequired()])

    # other
    SS_interval = DecimalField('Gate interval (mins)')
    start_iteration = IntegerField('Number of gates', description='number of start iterations: 0 is indefinite up to '
                                                                  'start close time',
                                   validators=[Optional(strip_whitespace=True)])
    time_offset = DecimalField('GMT offset', validators=[DataRequired()], places=2, render_kw=dict(maxlength=5),
                               description='The time offset for the task. Default value taken from the competition '
                                           'time offset')
    check_launch = BooleanField('Check launch', description='If we check pilots leaving launch - i.e. launch is like '
                                                            'an exit cylinder')
    # region = SelectField('Waypoint file', choices=[(1,'1'), (2,'2')])

    # airspace
    airspace_check = BooleanField('Airspace checking')
    # openair_file = SelectField('Openair file', choices=[(1,'1'), (2,'2')])
    QNH = DecimalField('QNH', validators=[NumberRange(min=900, max=1100)])

    submit = SubmitField('Save')

    def validate_on_submit(self):
        result = super(TaskForm, self).validate()
        return result
        # if self.window_close_time.data > self.window_open_time.data:
        #     return False
        # if self.start_close_time.data > self.start_time.data:
        #     return False
        # if self.task_deadline.data > self.start_time.data:
        #     return False
        # else:
        #     return result


class NewTurnpointForm(FlaskForm):

    id = None
    description = None
    number = IntegerField('#')
    name = SelectField('Waypoint')
    radius = IntegerField('Radius (m)', default=400)
    type = SelectField('Type', choices=[('launch', 'Launch'), ('speed', 'SSS'), ('waypoint', 'Waypoint'),
                                        ('endspeed', 'ESS'), ('goal', 'Goal')])
    shape = SelectField('Shape', choices=[('circle', 'Circle'), ('line', 'Line')])
    how = SelectField('SSS Direction', choices=[('entry', 'Out/Enter'), ('exit', 'In/Exit')])

class ModifyTurnpointForm(FlaskForm):

    id = None
    description = None
    mod_number = IntegerField('#')
    mod_name = SelectField('Waypoint')
    mod_radius = IntegerField('Radius (m)', default=400)
    mod_type = SelectField('Type', choices=[('launch', 'Launch'), ('speed', 'SSS'), ('waypoint', 'Waypoint'),
                                        ('endspeed', 'ESS'), ('goal', 'Goal')])
    mod_shape = SelectField('Shape', choices=[('circle', 'Circle'), ('line', 'Line')])
    mod_how = SelectField('SSS Direction', choices=[('entry', 'Out/Enter'), ('exit', 'In/Exit')])
