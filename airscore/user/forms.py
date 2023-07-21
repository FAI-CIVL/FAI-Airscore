# -*- coding: utf-8 -*-
"""User forms."""
from datetime import date

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, IntegerField, SelectField, DecimalField, BooleanField, SubmitField, \
    FileField, TextAreaField, SelectMultipleField, widgets

from wtforms.fields import DateField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, InputRequired

import Defines
from .models import User


percentage_choices = [(0.1, '10%'), (0.2, '20%'), (0.3, '30%'), (0.4, '40%'), (0.5, '50%'),
                      (0.6, '60%'), (0.7, '70%'), (0.8, '80%'), (0.9, '90%'), (1.0, '100%')]

time_zones = [(-43200, '-12:00'), (-41400, '-11:30'), (-39600, '-11:00'), (-37800, '-10:30'), (-36000, '-10:00'),
              (-34200, '-9:30'), (-32400, '-9:00'), (-30600, '-8:30'), (-28800, '-8:00'), (-27000, '-7:30'),
              (-25200, '-7:00'), (-23400, '-6:30'), (-21600, '-6:00'), (-19800, '-5:30'), (-18000, '-5:00'),
              (-16200, '-4:30'), (-14400, '-4:00'), (-12600, '-3:30'), (-10800, '-3:00'), (-9000, '-2:30'),
              (-7200, '-2:00'), (-5400, '-1:30'), (-3600, '-1:00'), (-1800, '-0:30'), (0, '+0:00'),
              (1800, '+0:30'), (3600, '+1:00'), (5400, '+1:30'), (7200, '+2:00'), (9000, '+2:30'),
              (10800, '+3:00'), (12600, '+3:30'), (14400, '+4:00'), (16200, '+4:30'), (18000, '+5:00'),
              (19800, '+5:30'), (20700, '+5:45'), (21600, '+6:00'), (23400, '+6:30'), (25200, '+7:00'),
              (27000, '+7:30'), (28800, '+8:00'), (30600, '+8:30'), (31500, '+8:45'), (32400, '+9:00'),
              (34200, '+9:30'), (36000, '+10:00'), (37800, '+10:30'), (39600, '+11:00'), (41400, '+11:30'),
              (43200, '+12:00'), (45000, '+12:30'), (45900, '+12:45'), (46800, '+13:00'), (48600, '+13:30'),
              (50400, '+14:00')]


class RegisterForm(FlaskForm):
    """Register form."""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=6, max=40)]
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
    first_name = StringField(
        "First name", validators=[DataRequired(), Length(min=1, max=25)]
    )
    last_name = StringField(
        "Last name", validators=[DataRequired(), Length(min=2, max=25)]
    )
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self, extra_validators=None):
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

    def validate_on_activation(self, user_id):
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user and not user.id == user_id:
            self.email.errors.append("This email is already registered with another user.")
            return False
        return True


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class NonValidatingSelectField(SelectField):
    """
    Attempt to make an open ended select field that can accept dynamic
    choices added by the browser.
    """
    def pre_validate(self, form):
        pass


class NewTaskForm(FlaskForm):
    task_name = StringField("Task Name", description='optional. If you want to give the task a name. '
                                                     'If left blank it will default to "Task #"')
    task_number = IntegerField("Task Number", validators=[NumberRange(min=0, max=50)],
                               description='task number, by default one more than the last task')
    task_comment = StringField('Comment', description='Sometimes you may wish to make a comment that will show up'
                                                      ' in the competition overview page. e.g. "task stopped at 14:34"')
    task_date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    task_region = SelectField('Flying Area', choices=[('1', '1'), ('2', '2')], validators=[DataRequired()],
                              description='If not done yet, please add at least one Flying Area to the event before '
                                          'creating event tasks.',
                              coerce=int, validate_choice=False)
    submit = SubmitField('Add Task')


class NewScorekeeperForm(FlaskForm):
    scorekeeper = SelectField("Scorekeeper", choices=[('1', '1'), ('2', '2')])


class NewCompForm(FlaskForm):
    comp_name = StringField("Comp Name", validators=[DataRequired()])
    comp_code = StringField('Short name',
                            validators=[Optional(strip_whitespace=True), Length(max=8, message='max 8 chars')],
                            description='An abbreviated name (max 8 chars) e.g. PGEuro20, '
                                        'if empty will be calculated from name')
    comp_class = SelectField('Category', choices=[('PG', 'PG'), ('HG', 'HG')])
    comp_site = StringField('Location', validators=[DataRequired()], description='location of the competition')
    date_from = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    date_to = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)

    submit = SubmitField('Create')

    def validate_on_submit(self):
        result = super(NewCompForm, self).validate()
        if self.date_from.data > self.date_to.data:
            self.date_from.errors.append('Competition end date is before start date')
            return False
        return result


class CompForm(FlaskForm):
    from formula import list_formulas
    from frontendUtils import list_track_sources

    help_overall_validity = "Overall Results can be calculated using different formulas:" \
                            "<li>ALL: score of each valid task will be used;</li>" \
                            "<li>DROPPED TASKS: worst results can be discarded, based on the number of valid tasks " \
                            "and the chosen parameter that indicates number of valid tasks every witch a result more " \
                            "can be discarded;</li>" \
                            "<li>FTV (Fixed Total Validity): a procedure to score pilots on their best task " \
                            "performances, rather than all their tasks. Uses a percentage (selected as parameter, " \
                            "default is 25%) of total validity and determines results used for each pilot based on " \
                            "performance. Details are found in Section 7F of " \
                            "<a href='https://www.fai.org/page/sporting-code-section-7' target='_blank'>FAI Sporting " \
                            "Code</a>.</li>"

    help_nom_launch = "When pilots do not take off for safety reasons, to avoid difficult launch conditions or bad " \
                      "conditions in the air, Launch Validity is reduced. Nominal Launch defines a threshold as a " \
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

    help_nom_time = "Nominal time indicates the expected task duration, the amount of time required to fly the speed " \
                    "section. If the fastest pilot’s time is below nominal time, the task will be devalued. There is " \
                    "no devaluation if the fastest pilot’s time is above nominal time. Nominal time should be set " \
                    "to the expected “normal” task duration for the competition site, and nominal distance / nominal " \
                    "time should be a bit higher than typical average speeds for the area."

    help_score_back = "In a stopped task, this value defines the amount of time before the task stop was announced " \
                      "that will not be considered for scoring. The default is 5 minutes, but depending on local " \
                      "meteorological circumstances, it may be set to a longer period for a whole competition."

    help_lead_factor = "Starting with GAP2023 this is called LeadingTimeRatio. " \
                       "This is a multiplier factor that influences the ratio between leading and time points. " \
                       "Changing this parameter will affect considerably the results, so it is recommended " \
                       "to leave the default value."

    comp_name = StringField('Competition Name')
    comp_code = StringField('Short name', render_kw=dict(maxlength=8), description='An abbreviated name (max 8 chars) '
                                                                                   'e.g. PGEuro20')
    sanction = SelectField('Sanction', choices=[(x, x) for x in Defines.SANCTIONS])
    comp_type = SelectField('Type', choices=[('RACE', 'RACE'), ('ROUTE', 'ROUTE'), ('TEAM RACE', 'TEAM RACE')])
    comp_class = SelectField('Category', choices=[('PG', 'PG'), ('HG', 'HG')],
                             id='select_category')
    comp_site = StringField('Location', validators=[DataRequired()], description='location of the competition')
    date_from = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    date_to = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    MD_name = StringField('Race Director')

    time_offset = SelectField('GMT Offset', choices=time_zones, id='select_time_offset', coerce=int, default=0,
                              description='The default time offset for the comp. Individual tasks will have this '
                              'as a default but can be overridden if your comp spans multiple time zones'
                              ' or over change in daylight savings')

    pilot_registration = SelectField('Pilot Entry', choices=[(1, 'Registered'), (0, 'Open')], coerce=int,
                                     default=1, description='Registered - only pilots registered are flying, '
                                                            'open - all tracklogs uploaded are considered as entires')

    track_sources = list_track_sources()
    track_source = SelectField('Track Source', choices=track_sources, id='select_source',
                               default=None, description='Select Tracks source if available')

    formulas = list_formulas()
    formula = SelectField('Formula', choices=[(x, x.upper()) for x in formulas['ALL']], id='select_formula')
    locked = BooleanField('Scoring Locked',
                          description="If locked, a rescore will not change displayed results")

    # formula object/table
    overall_validity = SelectField('Scoring', choices=[('all', 'ALL'), ('ftv', 'FTV'), ('round', 'DROPPED TASKS')],
                                   description=help_overall_validity)
    validity_param = IntegerField('FTV percentage', validators=[NumberRange(min=0, max=100)])
    nom_dist = IntegerField('Nominal Distance (km)', description=help_nom_distance)
    nom_goal = IntegerField('Nominal Goal (%)', description=help_nom_goal, validators=[NumberRange(min=0, max=100)])
    min_dist = IntegerField('Minimum Distance (km)', description=help_min_distance)
    nom_launch = IntegerField('Nominal Launch (%)', description=help_nom_launch,
                              validators=[NumberRange(min=0, max=100)])
    nom_time = IntegerField('Nominal Time (min)', description=help_nom_time)

    team_scoring = BooleanField('Team Scoring')
    team_size = IntegerField('Pilots Scoring', validators=[Optional(strip_whitespace=True)],
                             description="The number of scores from a task counting towards team score")
    max_team_size = IntegerField('Team size', validators=[Optional(strip_whitespace=True)],
                                 description="Number of pilots in team")

    country_scoring = BooleanField('Nations scoring')
    country_size = IntegerField('Pilots Scoring in Nat Team', validators=[Optional(strip_whitespace=True)],
                                description="The number of scores from a task counting towards nations team score")
    max_country_size = IntegerField('Nat. Team size', validators=[Optional(strip_whitespace=True)],
                                    description="Number of pilots in Nat. team")

    team_over = IntegerField('Team over- what is this??', validators=[Optional(strip_whitespace=True)])

    formula_distance = SelectField('Distance points',
                                   choices=[('on', 'On'), ('difficulty', 'Difficulty'), ('off', 'Off')])
    formula_arrival = SelectField('Arrival points',
                                  choices=[('position', 'Position'), ('time', 'Time'), ('off', 'Off')])
    formula_departure = SelectField('Departure points',
                                    choices=[('leadout', 'Leadout'), ('departure', 'Departure'), ('off', 'Off')])
    formula_time = SelectField('Time points', choices=[('on', 'On'), ('off', 'Off')])

    scoring_altitude = SelectField('Scoring Altitude', choices=[('GPS', 'GPS'), ('QNH', 'QNH')])
    lead_factor = DecimalField('Leadfactor', places=2, default=1, description=help_lead_factor)
    no_goal_penalty = IntegerField('No goal penalty (%)', validators=[NumberRange(min=0, max=100)], default=100)

    tolerance = DecimalField('Turnpoint radius tolerance %', places=1, default=0.1)
    min_tolerance = IntegerField('Minimum turnpoint tolerance (m)')
    glide_bonus = DecimalField('Glide bonus', validators=[InputRequired()], places=1, default=0)
    arr_alt_bonus = DecimalField('Height bonus', validators=[InputRequired()], default=0)
    arr_max_height = IntegerField('ESS height limit - upper', validators=[Optional(strip_whitespace=True)])
    arr_min_height = IntegerField('ESS height limit - lower', validators=[Optional(strip_whitespace=True)])
    validity_min_time = IntegerField('Minimum time (mins)')
    score_back_time = IntegerField('Scoreback time (mins)', description=help_score_back)
    max_JTG = IntegerField("Max Jump the gun (sec)", default=0)
    JTG_penalty_per_sec = DecimalField('Jump the gun penalty per second',
                                       validators=[Optional(strip_whitespace=True)], places=2, default=0)
    check_launch = BooleanField('Check launch', description='If we check pilots leaving launch - i.e. launch is like '
                                                            'an exit cylinder. Individual tasks will have this '
                                                            'as a default but can be overridden.')
    airspace_check = BooleanField('Airspace checking', description='if we check for airspace violations. Individual '
                                                                   'tasks will have this as a default but can be '
                                                                   'overridden. Note that this will only work if '
                                                                   'the flying area includes an airspace file')
    check_g_record = BooleanField('Check G records', description='Check the G Record of the submitted igc files')
    igc_parsing_file = SelectField("IGC parsing config file", choices=[('1', '1'), ('2', '2')])
    self_register = BooleanField("Allow self registration", description='Allow users who are pilots to register '
                                                                        'to the competition')
    website = StringField("Competition website", description='If you have an official website for the comp. e.g.'
                                                             ' Airtribune or other')
    external = BooleanField('External Event', description='External Events are imported, results are not calculated '
                                                          'throught Airscore, and are Read Only. Remove the flag to '
                                                          'reset all task results and recalculate in Airscore.')
    submit = SubmitField('Save')

    def validate_on_submit(self):
        result = super(CompForm, self).validate()
        if self.date_from.data > self.date_to.data:
            self.date_from.errors.append('Competition end date is before start date')
            return False
        return result


class TaskForm(FlaskForm):
    # general
    comp_name = ""
    task_name = StringField("Task Name", description='optional. If you want to give the task a name. '
                                                     'If left blank it will default to "Task #"')
    task_num = IntegerField("Task Number", validators=[NumberRange(min=0, max=50)],
                            description='task number, by default one more than the last task')
    comment = StringField('Comment', description='Sometimes you may wish to make a comment that will show up'
                                                 ' in the competition overview page. e.g. "task stopped at 14:34"')
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    task_type = SelectField('Type', choices=[('race', 'Race'), ('elapsed time', 'Elapsed time')],
                            validators=[DataRequired()], default='race')
    region = SelectField('Region', id='select_region', choices=[(0, ' -')], default=0, coerce=int,
                         validators=[Optional()], description='Determines the Waypoint listed, and the airspace used')
    training = BooleanField('Training', description='Training Task do not concur to Comp Results')

    # times
    window_open_time = TimeField('Window open', format='%H:%M', render_kw={"step": "300"},
                                 validators=[Optional(strip_whitespace=True)])
    start_time = TimeField('Start time', format='%H:%M', validators=[Optional(strip_whitespace=True)])
    window_close_time = TimeField('Window close', format='%H:%M', validators=[Optional(strip_whitespace=True)])
    start_close_time = TimeField('Start close', format='%H:%M', validators=[Optional(strip_whitespace=True)])
    stopped_time = TimeField('Stopped time', format='%H:%M', validators=[Optional(strip_whitespace=True)])
    task_deadline = TimeField('Deadline', format='%H:%M', validators=[Optional(strip_whitespace=True)])

    # other
    SS_interval = IntegerField('Gate interval (mins)', default=0)
    start_iteration = IntegerField('Number of gates', description='number of start iterations: 0 is indefinite up to '
                                                                  'start close time',
                                   validators=[Optional(strip_whitespace=True)])

    time_offset = SelectField('GMT Offset', choices=time_zones, id='select_time_offset', coerce=int, default=0,
                              description='The time offset for the task. Default value taken from the competition '
                              'time offset')

    check_launch = BooleanField('Check launch', description='If we check pilots leaving launch - i.e. launch is like '
                                                            'an exit cylinder')

    # airspace
    airspace_check = BooleanField('Airspace checking')
    # openair_file = SelectField('Openair file', choices=[(1,'1'), (2,'2')])
    QNH = DecimalField('QNH', validators=[NumberRange(min=900, max=1100)], places=2, default=1013.25)

    # formula overides
    formula_distance = SelectField('Distance points', choices=[('on', 'On'), ('difficulty', 'Difficulty'),
                                                               ('off', 'Off')])
    formula_arrival = SelectField('Arrival points', choices=[('position', 'Position'), ('time', 'Time'),
                                                             ('off', 'Off')])
    formula_departure = SelectField('Departure points', choices=[('leadout', 'Leadout'), ('departure', 'Departure'),
                                                                 ('off', 'Off')])
    formula_time = SelectField('Time points', choices=[('on', 'On'), ('off', 'Off')])
    arr_alt_bonus = DecimalField('Height bonus', validators=[InputRequired()], default=0)
    max_JTG = IntegerField("Max Jump the gun (sec)", default=0)
    no_goal_penalty = IntegerField('No goal penalty (%)', validators=[InputRequired()], default=100)
    tolerance = DecimalField('Turnpoint radius tolerance (%)', places=1)

    submit = SubmitField('Save')

    def validate_on_submit(self):
        result = super(TaskForm, self).validate()
        if any(el.data is not None for el in [self.window_open_time, self.start_time]):
            result = self.validate_timings()
        return result

    def validate_timings(self):
        result = True
        '''check window open time'''
        if self.window_open_time.data is None:
            self.window_open_time.errors.append(f'window open time must be set')
            result = False
        else:
            for el in (self.window_close_time, self.start_time):
                if el.data and self.window_open_time.data > el.data:
                    el.errors.append(f'{el.short_name} is before window open time')
                    result = False
        '''check start time'''
        if self.start_time.data is None:
            self.start_time.errors.append(f'start time must be set')
            result = False
        else:
            if self.start_close_time.data and self.start_close_time.data < self.start_time.data:
                self.start_close_time.errors.append(f'start close time is before start time')
                result = False
        '''check task deadline'''
        if self.task_deadline.data is None:
            self.task_deadline.errors.append(f'task deadline time must be set')
            result = False
        else:
            for el in (self.window_open_time, self.start_time):
                if el.data and self.task_deadline.data < el.data:
                    el.errors.append(f'{el.short_name} is after task deadline')
                    result = False
            for el in (self.window_close_time, self.start_close_time):
                if el.data is None:
                    el.data = self.task_deadline.data
                elif self.task_deadline.data < el.data:
                    el.errors.append(f'{el.short_name} is after task deadline')
                    result = False
        return result


class TurnpointForm(FlaskForm):
    wpt_id = IntegerField('wpt_id', validators=[Optional(strip_whitespace=True)], widget=widgets.HiddenInput())
    task_id = IntegerField('task_id', validators=[Optional(strip_whitespace=True)], widget=widgets.HiddenInput())
    num = IntegerField('#', validators=[DataRequired()])
    rwp_id = SelectField('Waypoint', validators=[DataRequired()], choices=[], validate_choice=False)
    radius = IntegerField('Radius (m)', validators=[InputRequired()], default=400)
    type = SelectField('Type', choices=[('launch', 'Launch'), ('speed', 'SSS'), ('waypoint', 'Waypoint'),
                                        ('endspeed', 'ESS'), ('goal', 'Goal')])
    shape = SelectField('Shape', choices=[('circle', 'Cylinder'), ('line', 'Line')])
    how = SelectField('SSS Direction', choices=[('entry', 'Out/Enter'), ('exit', 'In/Exit')])

    submit = SubmitField('Add')


class ResultAdminForm(FlaskForm):
    task_result_file = SelectField('Scoring run')
    comp_result_file = SelectField('Scoring run')


class NewRegionForm(FlaskForm):
    name = StringField("Area name", validators=[DataRequired()],
                       description='This is the name that will appear when choosing an area for a task')
    waypoint_file = FileField("Waypoint file", validators=[DataRequired()])
    openair_file = FileField("Open Air file", description='Open Air airspace file')
    submit = SubmitField('Add')


class RegionForm(FlaskForm):
    region = SelectField('Area', id='select_region')


class IgcParsingConfigForm(FlaskForm):
    help_min_fixes = 'Minimum number of fixes in a file.'
    help_max_seconds_between_fixes = 'Maximum time between fixes, seconds. Soft limit, some fixes are allowed to' \
                                     ' exceed'
    help_min_seconds_between_fixes = 'Minimum time between fixes, seconds. Soft limit, some fixes are allowed to' \
                                     ' exceed.'
    help_max_time_violations = 'Maximum number of fixes exceeding time between fix constraints.'
    help_max_new_days_in_flight = 'Maximum number of times a file can cross the 0:00 UTC time.'
    help_min_avg_abs_alt_change = 'Minimum average of absolute values of altitude changes in a file. This is needed' \
                                  ' to discover altitude sensors (either pressure or gps) that report either always ' \
                                  'constant altitude, or almost always constant altitude, and therefore are invalid. ' \
                                  'The unit is meters/fix.'
    help_max_alt_change_rate = 'Maximum altitude change per second between fixes, meters per second. Soft limit, ' \
                               'some fixes are allowed to exceed.'
    help_max_alt_change_violations = 'Maximum number of fixes that exceed the altitude change limit.'
    help_max_alt = 'Absolute maximum altitude, meters.'
    help_min_alt = 'Absolute minimum altitude, meters.'
    # Flight detection parameters.
    help_min_gsp_flight = 'Minimum ground speed to switch to flight mode, km/h.'

    help_min_landing_time = 'Minimum idle time (i.e. time with speed below minimum ground speed) to switch to landing,' \
                            ' seconds. Exception: end of the file (tail fixes that do not trigger the above' \
                            ' condition), no limit is applied there.'

    help_which_flight_to_pick = '''In case there are multiple continuous segments with ground speed exceeding the 
                                    limit, which one should be taken?
                                    Available options:
                                     - "first": take the first segment, ignore the part after
                                        the first detected landing.
                                     - "concat": concatenate all segments; will include the down
                                        periods between segments (legacy behavior)'''
    # Thermal detection parameters.
    help_min_bearing_change_circling = 'Minimum bearing change to enter a thermal, deg/sec.'
    help_min_time_for_bearing_change = 'Minimum time between fixes to calculate bearing change, seconds.'
    help_min_time_for_thermal = 'Minimum time to consider circling a thermal, seconds.'

    description = TextAreaField('Description', description='Free text describing the settings file')
    new_name = StringField('New settings name')
    min_fixes = IntegerField('Min number of fixes', description=help_min_fixes)
    max_seconds_between_fixes = IntegerField('Max seconds between fixes', description=help_max_seconds_between_fixes)
    min_seconds_between_fixes = IntegerField('Min seconds between fixes', description=help_min_seconds_between_fixes)
    max_time_violations = IntegerField('Max time violations', description=help_max_time_violations)
    max_new_days_in_flight = IntegerField('Max new days in flight', description=help_max_new_days_in_flight)
    min_avg_abs_alt_change = DecimalField('Min average absolute altitude change',
                                          description=help_min_avg_abs_alt_change)
    max_alt_change_rate = IntegerField('Max alt change rate', description=help_max_alt_change_rate)
    max_alt_change_violations = IntegerField('Max alt change violations', description=help_max_alt_change_violations)
    max_alt = IntegerField('Max alt (m)', description=help_max_alt)
    min_alt = IntegerField('Min alt', description=help_min_alt)
    min_gsp_flight = IntegerField('Min groundspeed in flight (kph)', description=help_min_gsp_flight)
    min_landing_time = IntegerField('Min landing time (sec)', description=help_min_landing_time)
    which_flight_to_pick = SelectField('Which flight to pick', choices=[('concat', 'join flights together'),
                                                                        ('first', 'take the first flight')]
                                       , description=help_which_flight_to_pick)
    min_bearing_change_circling = IntegerField('Min bearing change circling',
                                               description=help_min_bearing_change_circling)
    min_time_for_bearing_change = IntegerField('Min time for bearing change',
                                               description=help_min_time_for_bearing_change)
    min_time_for_thermal = IntegerField('Min time for thermal', description=help_min_time_for_thermal)

    save = SubmitField('Save')
    save_as = SubmitField('Save As')

    def validate_on_submit(self):
        result = super(IgcParsingConfigForm, self).validate()
        return result


class ParticipantForm(FlaskForm):
    name_desc = 'Required, max 100 characters'
    sp_desc = 'Max 100 characters'
    id_num = IntegerField('ID', validators=[DataRequired(), NumberRange(min=0, max=999999)])
    CIVL = IntegerField('CIVL', default=None,
                        validators=[Optional(strip_whitespace=True), NumberRange(min=0, max=999999)])
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=100)], description=name_desc)
    birthdate = DateField('Birthdate', format='%Y-%m-%d', validators=[Optional(strip_whitespace=True)], default=None)
    nat = SelectField('Nationality', coerce=str, validators=[DataRequired(), Length(min=3, max=3)],
                      id='select_country', choices=[], validate_choice=False)
    sex = SelectField('Sex', choices=[('M', 'M'), ('F', 'F')], default='M')
    glider = StringField('Glider', validators=[Optional(strip_whitespace=True), Length(max=100)])
    certification = NonValidatingSelectField('Certification',
                                             validators=[Optional(strip_whitespace=True)], default=None)
    sponsor = StringField('Sponsor', validators=[Optional(strip_whitespace=True), Length(max=100)], description=sp_desc)
    team = StringField('Team', validators=[Optional(strip_whitespace=True)], default=None)
    nat_team = BooleanField('In National Team', default=1, description='Concurring for Country scoring')
    live_id = IntegerField('Live ID', default=None,
                           validators=[Optional(strip_whitespace=True), NumberRange(min=0, max=9999999)])
    xcontest_id = StringField('XContest ID', default=None, validators=[Optional(strip_whitespace=True)])
    status = SelectField('Status', choices=[('', ' -'), ('waiting for payment', 'waiting for payment'),
                                            ('cancelled', 'cancelled'), ('waiting list', 'waiting list'),
                                            ('wild card', 'wild card'), ('confirmed', 'confirmed')], default=None)
    paid = SelectField('Paid', choices=[(1, 'Yes'), (0, 'No')], default=0)

    submit = SubmitField('Save')


class EditScoreForm(FlaskForm):
    penalty_bonus = SelectField(choices=[(1, 'Penalty'), (-1, 'Bonus')], id='penalty_bonus', default=1)
    flat_penalty = IntegerField('points', default=0, id='penalty')
    comment = TextAreaField('Comment', render_kw={"rows": 3, "cols": 50}, id='comment')


class UserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=40)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=40)])
    nat = NonValidatingSelectField('Nationality', validators=[Optional(strip_whitespace=True)], default=None)
    username = StringField("Username")
    email = StringField('Email', validators=[DataRequired(), Email()])
    access = SelectField('Access Level', choices=[('pilot', 'Pilot'), ('pending', 'Pending'),
                                                  ('scorekeeper', 'Scorekeeper'), ('manager', 'Manager'),
                                                  ('admin', 'Admin')],
                         default='pilot')
    active = BooleanField('Enabled', default=1)

    submit = SubmitField('Save')

    def validate(self, extra_validators=None):
        """Validate the form."""
        initial_validation = super(UserForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append("Username (email) already registered")
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append("Email already registered")
            return False
        return True

    def validate_on_edit(self, user_id):
        """Validate the form."""
        initial_validation = super(UserForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(email=self.email.data).one_or_none()
        if user and not user.id == user_id:
            self.email.errors.append("Email already in use.")
            return False
        return True


class CompLaddersForm(FlaskForm):
    ladders = MultiCheckboxField('Active Ladders', coerce=int)
    submit = SubmitField('Save')


class CompRankingForm(FlaskForm):
    name_desc = 'Required, max 40 characters'
    rank_name = StringField('Name', validators=[DataRequired(), Length(min=1, max=40)], description=name_desc)
    rank_type = SelectField('Ranking Type', choices=[('overall', 'Overall'), ('cert', 'Certification'),
                                                     ('birthdate', 'Birthdate'), ('female', 'Female'),
                                                     ('nat', 'Nationality'), ('custom', 'Custom')], default='cert')
    cert_id = NonValidatingSelectField('Certification', validators=[Optional(strip_whitespace=True)], default=None)
    min_date = DateField('Starting from', format='%Y-%m-%d', validators=[Optional(strip_whitespace=True)], default=None)
    max_date = DateField('Up to', format='%Y-%m-%d', validators=[Optional(strip_whitespace=True)], default=None)
    attr_id = NonValidatingSelectField('Custom Attribute', validators=[Optional(strip_whitespace=True)], default=None)
    rank_value = StringField('Attribute Value', validators=[Optional(strip_whitespace=True)], default=None)

    submit = SubmitField('Save')


class AirspaceCheckForm(FlaskForm):
    name_desc = 'Required, max 40 characters'
    notification_distance = IntegerField('Proximity Notification Distance (m.)', default=100,
                                         validators=[Optional(strip_whitespace=True), NumberRange(min=-100, max=999)])
    function = SelectField('Function Type', default='linear',
                           choices=[('linear', 'Linear'), ('non-linear', 'Progressive')])
    double_step = BooleanField('Double Step', default=0)
    h_v = BooleanField('Different Vertical Limits', default=0)
    h_outer_limit = IntegerField('Horiz. Outer Limit (m.)', default=50,
                                 validators=[Optional(strip_whitespace=True), NumberRange(min=-100, max=999)])
    h_boundary = IntegerField('Horiz. Boundary (m.)', default=0,
                              validators=[Optional(strip_whitespace=True), NumberRange(min=-100, max=999)])
    h_inner_limit = IntegerField('Horiz. Inner Limit (m.)', default=-30,
                                 validators=[Optional(strip_whitespace=True), NumberRange(min=-100, max=999)])
    h_boundary_penalty = SelectField('Boundary Penalty', choices=percentage_choices, default=0.2)
    h_max_penalty = SelectField('Full Penalty', choices=percentage_choices, default=1)
    v_outer_limit = IntegerField('Vert. Outer Limit (m.)', default=50,
                                 validators=[Optional(strip_whitespace=True), NumberRange(min=-100, max=999)])
    v_boundary = IntegerField('Vert. Boundary (m.)', default=0,
                              validators=[Optional(strip_whitespace=True), NumberRange(min=-100, max=999)])
    v_inner_limit = IntegerField('Vert. Inner Limit (m.)', default=-30,
                                 validators=[Optional(strip_whitespace=True), NumberRange(min=-100, max=999)])
    v_boundary_penalty = SelectField('Boundary Penalty', choices=percentage_choices, default=0.2)
    v_max_penalty = SelectField('Full Penalty', choices=percentage_choices, default=1)

    submit = SubmitField('Save')

    def validate_on_submit(self):
        result = super(AirspaceCheckForm, self).validate()
        if self.h_outer_limit.data < self.h_inner_limit.data:
            self.h_inner_limit.errors.append('cannot be greater than outer limit')
            result = False
        if self.v_outer_limit.data < self.v_inner_limit.data:
            self.v_inner_limit.errors.append('cannot be greater than outer limit')
            result = False
        if self.function.data == 'linear' and self.double_step.data:
            if self.h_outer_limit.data < self.h_boundary.data:
                self.h_boundary.errors.append('cannot be greater than outer limit')
                result = False
            if self.h_boundary.data < self.h_inner_limit.data:
                self.h_boundary.errors.append('cannot be smaller than inner limit')
                result = False
            if self.v_outer_limit.data < self.v_boundary.data:
                self.v_boundary.errors.append('cannot be greater than outer limit')
                result = False
            if self.v_boundary.data < self.v_inner_limit.data:
                self.v_boundary.errors.append('cannot be smaller than inner limit')
                result = False
            if self.h_boundary_penalty.data > self.h_max_penalty.data:
                self.h_boundary_penalty.errors.append('cannot be greater than max penalty')
                result = False
            if self.v_boundary_penalty.data > self.v_max_penalty.data:
                self.v_boundary_penalty.errors.append('cannot be greater than max penalty')
                result = False
        return result
