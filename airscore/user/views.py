# -*- coding: utf-8 -*-
"""User views."""
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, json, flash, redirect, url_for, session, Markup, \
    current_app, send_file, make_response
from flask_login import login_required, current_user
import frontendUtils
from airscore.user.forms import NewTaskForm, CompForm, TaskForm, \
    ResultAdminForm, NewScorekeeperForm, RegionForm, NewRegionForm, IgcParsingConfigForm, ParticipantForm, \
    EditScoreForm, CompLaddersForm, NewCompForm, CompRankingForm, AirspaceCheckForm, UserForm, TurnpointForm
from comp import Comp
from formula import list_formulas, Formula
from task import Task, write_map_json, get_task_json_by_filename
from frontendUtils import save_turnpoint
from pilot.flightresult import update_status, delete_track
from os import path, remove, makedirs
from task import get_task_json_by_filename
from calcUtils import sec_to_time
from pathlib import Path
import time
from Defines import SELF_REG_DEFAULT, PILOT_DB, OPEN_EVENT, LADDERS
from airscore.user.models import User

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")


def admin_required(func):
    """
    If you decorate a view with this, it will ensure that the current user is
    an admin before calling the actual view. (If they are
    not, it calls the :attr:`LoginManager.unauthorized` callback.)
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin:
            return current_app.login_manager.unauthorized()
        return func(*args, **kwargs)

    return decorated_view


def manager_required(func):
    """
    If you decorate a view with this, it will ensure that the current user is
    a manager or an admin before calling the actual view. (If they are
    not, it calls the :attr:`LoginManager.unauthorized` callback.)
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not (current_user.is_admin or current_user.is_manager):
            return current_app.login_manager.unauthorized()
        return func(*args, **kwargs)

    return decorated_view


def editor_required(func):
    """
    If you decorate a view with this, it will ensure that the current user is
    authorised to edit the present even, i.e. is admin or scorekeeper in it.
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not session['is_editor']:
            flash(f"You are not authorised to see that page.", category='danger')
            return redirect(url_for('user.comp_settings_admin', compid=session.get('compid')))
        return func(*args, **kwargs)

    return decorated_view


def internal_required(func):
    """
    If you decorate a view with this, it will ensure that the event is not imported.
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if session['external']:
            flash(f"Event is imported, you cannot access that page.", category='danger')
            return redirect(url_for('user.comp_settings_admin', compid=session.get('compid')))
        return func(*args, **kwargs)

    return decorated_view


def check_coherence(func):
    """
    Checks if compid or taskid is coherent with session value
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if (('compid' in kwargs.keys() and session['compid'] and not kwargs['compid'] == session['compid'])
                or ('taskid' in kwargs.keys() and session['tasks']
                    and kwargs['taskid'] not in [el['task_id'] for el in session['tasks']])):
            flash(f"You requested a competition not in your session. Please select the correct one.", category='danger')
            return render_template('users/comp_admin.html',
                                   today=datetime.today().strftime('%Y-%m-%d'), new_comp_form=NewCompForm())
        return func(*args, **kwargs)

    return decorated_function


def session_task(func):
    """
    Checks task info dict is loaded in session and coherent
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            taskid = kwargs.get('taskid') if 'taskid' in kwargs.keys() else request.args.get('taskid')
            session['task'] = next(el for el in session['tasks'] if el['task_id'] == taskid)
        except (KeyError, AttributeError, Exception):
            flash("No task info found", category='danger')
            return render_template('users/comp_admin.html',
                                   today=datetime.today().strftime('%Y-%m-%d'), new_comp_form=NewCompForm())
        return func(*args, **kwargs)

    return decorated_function


def ready_to_score(func):
    """
    Checks if task has all info to be scored, else returns to task settings page
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not session['task']['ready_to_score'] and not session['task']['locked']:
            flash("Task is not ready to be scored as it is missing one or more of the following: "
                  "a route with goal,window open/close, start/close and deadline times", category='warning')
            return redirect(url_for('user.task_admin', taskid=session['task'].get('task_id')))
        return func(*args, **kwargs)

    return decorated_function


def valid_results(func):
    """
    Checks if task has all info to be scored, else returns to task settings page
    """

    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not frontendUtils.task_has_valid_results(session['task']['task_id']):
            flash(message='Task has no valid tracks. Scoring is not possible yet.', category='warning')
            return redirect(url_for('user.task_admin', taskid=session['task'].get('task_id')))
        return func(*args, **kwargs)

    return decorated_function


def check_editor(func):
    """
    If you decorate a view with this, it will add a flashed message notifying editing restrictions
    to non event scorers or admins
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if session['compid'] and 'is_editor' not in session.keys():
            '''should never be here'''
            session['is_editor'] = frontendUtils.check_comp_editor(session['compid'], current_user)
        if not (current_user.is_admin or session['is_editor']):
            flash(f"You are not a scorekeeper for this event. You won't be able to modify settings.",
                  category='warning')
        return func(*args, **kwargs)

    return decorated_view


def state_messages(func):
    """
    If you decorate a view with this, it will add a flashed message notifying task state:
    - external event
    - cancelled
    - locked (official results)
    - not ready to score
    - recheck needed
    - new scoring run needed
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if session['external']:
            '''External Event'''
            flash(f"This is an External Event. Most of Settings and Results are Read Only.", category='warning')
        if not (current_user.is_admin or session['is_editor']):
            flash(f"You are not a scorekeeper for this event. You won't be able to modify settings.",
                  category='warning')
        elif not session['external']:
            if not request.method == 'POST':
                task_info = session.get('task')
                if task_info.get('cancelled'):
                    flash(f"Task has been cancelled.", category='danger')
                elif task_info.get('locked'):
                    flash(f"Task has been locked and results are official.", category='info')
                elif not task_info['ready_to_score']:
                    flash("Task is not ready to be scored as it is missing one or more of the following: "
                          "a route with goal,window open/close, start/close and deadline times", category='warning')
                elif task_info['needs_recheck']:
                    flash("There are tracks evaluated before last changes. They need to be re-checked", category='warning')
                elif task_info['needs_new_scoring']:
                    flash("A new scoring is needed to reflect last task changes.", category='warning')
        return func(*args, **kwargs)

    return decorated_view


@blueprint.route("/")
@login_required
def members():
    """List members."""
    return render_template("users/members.html")


@blueprint.route('/airspace_map/<string:filename>')
@login_required
def airspace_edit(filename: str):
    import map
    import airspaceUtils

    message = ''
    spaces = []
    unknown_flag = False
    fl_detail = ''
    fl_messages = []

    data = airspaceUtils.read_airspace_map_file(filename)
    airspace_list = data['airspace_list']
    spaces = data['spaces']
    bbox = data['bbox']

    for space in airspace_list:
        if space["floor_unit"] == "FL":
            fl_messages.append(
                f"{space['floor_description']} is {int(space['floor']) * 100} ft "
                f"or {int(space['floor']) * 100 * 0.3048} m ")
            space['floor'] = None

        if space["ceiling_unit"] == "FL":
            fl_messages.append(
                f"{space['ceiling_description']} is {int(space['ceiling']) * 100} ft "
                f"or {int(space['ceiling']) * 100 * 0.3048} m ")
            space['ceiling'] = None

        if space["floor_unit"] == "Unknown height unit" or space["ceiling_unit"] == "Unknown height unit":
            unknown_flag = True

    if fl_messages:
        message = 'Attention: There is FL (flight level) units in the file. To use this pilots need to know their ' \
                  'standard altitude, or have an instrument capable of interpreting FL in openair and calculating ' \
                  'correctly their position. Alternativley you could adjust to meters or ' \
                  'feet above sea level'
        fl_detail = ", ".join(set(fl_messages))
        fl_detail += " - Assuming an International Standard Atmosphere pressure of 1013.25 hPa (29.92 inHg) " \
                     "at sea level, and therefore is not necessarily the same as the aircraft's actual altitude, " \
                     "either above sea level or above ground level. " \
                     "You should round down to be conservative and allow for days with lower atmospheric pressure."
    if unknown_flag:
        message += 'Attention: There is unknown height units in the file. You should adjust to meters or ' \
                   'feet above sea level'

    airspace_map = map.make_map(airspace_layer=spaces, show_airspace=True, bbox=bbox)

    return render_template('users/airspace_admin_map.html', airspace_list=airspace_list, file=filename,
                           map=airspace_map._repr_html_(), message=message, FL_message=fl_detail)


@blueprint.route('/airspace_check_admin', methods=['GET', 'POST'])
@login_required
@check_coherence
@internal_required
def airspace_check_admin():
    from airspace import get_airspace_check_parameters
    compid = request.args.get('compid')
    taskid = request.args.get('taskid')

    if request.method == 'POST':
        checkform = AirspaceCheckForm()
        '''adjusting parameters'''
        if checkform.function.data == 'non-linear' or not checkform.double_step.data:
            checkform.h_boundary.data = checkform.h_inner_limit.data
            checkform.h_boundary_penalty.data = checkform.h_max_penalty.data
            checkform.v_boundary.data = checkform.v_inner_limit.data
            checkform.v_boundary_penalty.data = checkform.v_max_penalty.data
        if not checkform.h_v.data:
            params = ['outer_limit', 'boundary', 'inner_limit', 'boundary_penalty', 'max_penalty']
            for el in params:
                getattr(checkform, f'v_{el}').data = getattr(checkform, f'h_{el}').data
        if checkform.validate_on_submit():
            resp = frontendUtils.save_airspace_check(compid, taskid, obj={el.name: el.data for el in checkform})
            flash(f'Settings saved.', 'info') if resp else flash(f'There was an error, saving failed.', 'danger')
        else:
            for item in checkform:
                if item.errors:
                    flash(f"{item.label.text} ({item.data}): {', '.join(x for x in item.errors)}", category='danger')
        return redirect(url_for('user.airspace_check_admin', compid=compid, taskid=taskid))

    elif request.method == 'GET':
        params = get_airspace_check_parameters(compid, taskid)
        checkform = AirspaceCheckForm(obj=params)
        '''adding frontend switches'''
        checkform.double_step.data = (params.h_boundary != params.h_inner_limit
                                      or params.v_boundary != params.v_inner_limit)
        checkform.h_v.data = not all(getattr(params, f"h_{e}") == getattr(params, f"v_{e}")
                                     for e in ('outer_limit', 'boundary', 'inner_limit',
                                               'boundary_penalty', 'max_penalty'))

    return render_template('users/airspace_check_admin.html', compid=compid, taskid=taskid, checkform=checkform)


@blueprint.route('/save_airspace', methods=['PUT'])
@login_required
def save_airspace():
    import airspaceUtils
    data = request.json
    newfile = airspaceUtils.create_new_airspace_file(data)
    airspaceUtils.create_airspace_map_check_files(newfile)
    if data['old_filename'] != data['new_filename']:
        frontendUtils.update_airspace_file(data['old_filename'], newfile)
    return dict(redirect=newfile)


@blueprint.route('/comp_admin', methods=['GET', 'POST'])
@login_required
def comp_admin():
    return render_template('users/comp_admin.html',
                           today=datetime.today().strftime('%Y-%m-%d'), new_comp_form=NewCompForm())


@blueprint.route('/_create_comp', methods=['POST'])
@login_required
def _create_comp():

    form = NewCompForm()
    errors = []

    if request.method == 'POST' and form.validate_on_submit():
        if not frontendUtils.check_short_code(form.comp_code.data):
            errors = {'comp_code': ["Short name is invalid or already in use."]}
        if errors:
            return jsonify(success=False, errors=errors)

        new_comp = Comp(comp_name=form.comp_name.data,
                        comp_class=form.comp_class.data,
                        comp_site=form.comp_site.data,
                        comp_code=form.comp_code.data,
                        date_from=form.date_from.data,
                        date_to=form.date_to.data)
        response = frontendUtils.create_new_comp(new_comp, current_user.id)
        return jsonify(response)

    return jsonify(success=False, errors=form.errors)


@blueprint.route('/_import_comp_fsdb/', methods=['POST'])
@login_required
def _import_comp_fsdb():
    from fsdb import FSDB
    if request.method == "POST":
        if not request.files or "filesize" not in request.cookies:
            return jsonify(success=False, error='No FSDB file was given.')
        elif not frontendUtils.allowed_tracklog_filesize(request.cookies["filesize"], size=50):
            '''Filesize exceeded maximum limit'''
            return jsonify(success=False, error='Filesize exceeded maximum limit.')

        fsdb_file = request.files["fsdb_file"]
        autopublish = bool(request.form.get('autopublish') == 'true')
        if not fsdb_file.filename or not frontendUtils.allowed_tracklog(fsdb_file.filename, extension=['fsdb', 'xml']):
            return jsonify(success=False, error='File is not a valid FSDB file.')

        f = FSDB.read(fsdb_file)
        compid = f.add_all()
        if compid:
            frontendUtils.set_comp_scorekeeper(compid, current_user.id, owner=True)
            if autopublish:
                frontendUtils.publish_all_results(comp_id=compid)
            return jsonify(success=True, autopublish=autopublish, form=request.form)
        return jsonify(success=False, error='There was an error reading or importing FSDB file.')


@blueprint.route('/_get_formulas/')
@login_required
def _get_formulas():
    category = request.args.get('category', '01', type=str)
    formulas = list_formulas()
    formula_choices = [(x, x.upper()) for x in formulas[category]]
    return jsonify(formula_choices)


@blueprint.route('/comp_settings_admin/<int:compid>', methods=['GET', 'POST'])
@login_required
def comp_settings_admin(compid: int):
    error = None
    compform = CompForm()
    newtaskform = NewTaskForm()
    newScorekeeperform = NewScorekeeperForm()
    rankingform = CompRankingForm()
    comp = Comp.read(compid)
    # set session variables for navbar
    session['compid'] = compid
    session['comp_name'] = comp.comp_name
    session['comp_class'] = comp.comp_class
    session['external'] = comp.external

    compform.igc_parsing_file.choices, _ = frontendUtils.get_igc_parsing_config_file_list()
    ids = frontendUtils.get_comp_users_ids(compid)

    certifications = frontendUtils.get_certifications_details()
    rankingform.cert_id.choices = [(x['cert_id'], x['cert_name']) for x in certifications[comp.comp_class]]
    rankingform.attr_id.choices = [(x['attr_id'], x['attr_value']) for x in frontendUtils.get_comp_meta(compid)]

    if request.method == 'POST':
        if comp.external:
            comp.comp_code = compform.comp_code.data
            comp.sanction = compform.sanction.data
            comp.MD_name = compform.MD_name.data
            if compform.website.data.lower()[:7] == 'http://':
                comp.website = compform.website.data.lower()[7:]
            elif compform.website.data.lower()[:8] == 'https://':
                comp.website = compform.website.data.lower()[8:]
            else:
                comp.website = compform.website.data.lower()
            comp.to_db()
            formula = Formula.read(compid)
            formula.team_scoring = compform.team_scoring.data
            formula.team_size = compform.team_size.data
            formula.max_team_size = compform.max_team_size.data
            formula.country_scoring = compform.country_scoring.data
            formula.country_size = compform.country_size.data
            formula.max_country_size = compform.max_country_size.data
            formula.team_over = compform.team_over.data
            formula.to_db()
            flash(f"{comp.comp_name} saved", category='info')

        elif compform.validate_on_submit():
            comp.comp_name = compform.comp_name.data
            comp.comp_code = compform.comp_code.data
            comp.sanction = compform.sanction.data
            comp.comp_type = compform.comp_type.data
            comp.comp_class = compform.comp_class.data
            comp.comp_site = compform.comp_site.data
            comp.date_from = compform.date_from.data
            comp.date_to = compform.date_to.data
            comp.MD_name = compform.MD_name.data
            comp.track_source = compform.track_source.data if compform.track_source.data not in ('', None) else None
            comp.time_offset = compform.time_offset.data
            comp.restricted = compform.pilot_registration.data
            comp.locked = compform.locked.data
            comp.igc_config_file = compform.igc_parsing_file.data
            comp.airspace_check = compform.airspace_check.data
            comp.check_launch = 'on' if compform.check_launch.data else 'off'
            comp.check_g_record = compform.check_g_record.data
            comp.self_register = compform.self_register.data
            comp.external = compform.external.data
            if compform.website.data.lower()[:7] == 'http://':
                comp.website = compform.website.data.lower()[7:]
            elif compform.website.data.lower()[:8] == 'https://':
                comp.website = compform.website.data.lower()[8:]
            else:
                comp.website = compform.website.data.lower()
            comp.to_db()

            formula = Formula.read(compid)
            formula.formula_name = compform.formula.data
            formula.overall_validity = compform.overall_validity.data
            formula.validity_param = round((100 - compform.validity_param.data) / 100, 2)
            formula.nominal_dist = compform.nom_dist.data * 1000
            formula.nominal_goal = compform.nom_goal.data / 100
            formula.min_dist = compform.min_dist.data * 1000
            formula.nominal_launch = compform.nom_launch.data / 100
            formula.nominal_time = compform.nom_time.data * 60
            formula.no_goal_penalty = round(compform.no_goal_penalty.data / 100, 2)
            formula.tolerance = compform.tolerance.data / 100
            formula.max_JTG = compform.max_JTG.data
            formula.formula_distance = compform.formula_distance.data
            formula.formula_arrival = compform.formula_arrival.data
            formula.formula_departure = compform.formula_departure.data
            formula.lead_factor = compform.lead_factor.data
            formula.formula_time = compform.formula_time.data
            formula.glide_bonus = compform.glide_bonus.data
            formula.min_tolerance = compform.min_tolerance.data
            formula.arr_alt_bonus = compform.arr_alt_bonus.data
            formula.arr_max_height = compform.arr_max_height.data
            formula.arr_min_height = compform.arr_min_height.data
            formula.validity_min_time = int((compform.validity_min_time.data or 0) * 60)
            formula.score_back_time = int((compform.score_back_time.data or 0) * 60)
            formula.JTG_penalty_per_sec = compform.JTG_penalty_per_sec.data
            formula.scoring_altitude = compform.scoring_altitude.data
            formula.team_scoring = compform.team_scoring.data
            formula.team_size = compform.team_size.data
            formula.max_team_size = compform.max_team_size.data
            formula.country_scoring = compform.country_scoring.data
            formula.country_size = compform.country_size.data
            formula.max_country_size = compform.max_country_size.data
            formula.team_over = compform.team_over.data
            formula.calculate_parameters()
            formula.to_db()

            flash(f"{compform.comp_name.data} saved", category='info')
            # return redirect(url_for('user.comp_settings_admin', compid=compid))
        else:
            for item in compform:
                if item.errors:
                    flash(f"{item.label.text} ({item.data}): {', '.join(x for x in item.errors)}", category='danger')
        return redirect(url_for('user.comp_settings_admin', compid=compid))

    if request.method == 'GET':
        formula = Formula.read(compid)
        compform.comp_name.data = comp.comp_name
        compform.comp_code.data = comp.comp_code
        compform.sanction.data = comp.sanction
        compform.comp_type.data = comp.comp_type
        compform.comp_class.data = comp.comp_class
        compform.comp_site.data = comp.comp_site
        compform.date_from.data = comp.date_from
        compform.date_to.data = comp.date_to
        compform.MD_name.data = comp.MD_name
        compform.track_source.data = comp.track_source
        compform.time_offset.data = int(comp.time_offset)
        compform.pilot_registration.data = comp.restricted
        compform.formula.data = formula.formula_name
        compform.overall_validity.data = formula.overall_validity
        formula.validity_param = 0 if not formula.validity_param else formula.validity_param
        formula.nominal_dist = 0 if not formula.nominal_dist else formula.nominal_dist
        formula.nominal_goal = 0 if not formula.nominal_goal else formula.nominal_goal
        formula.min_dist = 0 if not formula.min_dist else formula.min_dist
        formula.nominal_launch = 0 if not formula.nominal_launch else formula.nominal_launch
        formula.nominal_time = 0 if not formula.nominal_time else formula.nominal_time
        compform.validity_param.data = 100 - int(formula.validity_param * 100)
        compform.nom_dist.data = int(formula.nominal_dist / 1000)
        compform.nom_goal.data = int(formula.nominal_goal * 100)
        compform.min_dist.data = int(formula.min_dist / 1000)
        compform.nom_launch.data = int(formula.nominal_launch * 100)
        compform.nom_time.data = int(formula.nominal_time / 60)
        compform.team_scoring.data = formula.team_scoring
        compform.team_size.data = formula.team_size
        compform.max_team_size.data = formula.max_team_size
        compform.country_scoring.data = formula.country_scoring
        compform.country_size.data = formula.country_size
        compform.max_country_size.data = formula.max_country_size
        compform.team_over.data = formula.team_over
        compform.formula_distance.data = formula.formula_distance
        compform.formula_arrival.data = formula.formula_arrival
        compform.formula_departure.data = formula.formula_departure
        compform.lead_factor.data = 1 if formula.lead_factor is None else formula.lead_factor  # should not be None
        compform.formula_time.data = formula.formula_time
        compform.no_goal_penalty.data = int(formula.no_goal_penalty * 100)
        compform.glide_bonus.data = formula.glide_bonus
        compform.tolerance.data = formula.tolerance * 100
        compform.min_tolerance.data = formula.min_tolerance
        compform.arr_alt_bonus.data = formula.arr_alt_bonus
        compform.arr_max_height.data = formula.arr_max_height
        compform.arr_min_height.data = formula.arr_min_height
        compform.validity_min_time.data = int((formula.validity_min_time or 0) / 60)
        compform.score_back_time.data = int((formula.score_back_time or 0) / 60)
        compform.max_JTG.data = formula.max_JTG
        compform.JTG_penalty_per_sec.data = formula.JTG_penalty_per_sec
        compform.scoring_altitude.data = formula.scoring_altitude
        compform.igc_parsing_file.data = comp.igc_config_file
        compform.airspace_check.data = comp.airspace_check
        compform.check_launch.data = True if comp.check_launch == 'on' else False
        compform.check_g_record.data = comp.check_g_record
        compform.self_register.data = comp.self_register
        compform.website.data = comp.website
        compform.external.data = comp.external
        newtaskform.task_region.choices, _ = frontendUtils.get_region_choices(compid)
        formulas = [(x, x.upper()) for x in list_formulas().get(comp.comp_class)]
        '''cope with external or converted events with invalid formulas'''
        if formula.formula_name not in (el[0] for el in formulas):
            value = formula.formula_name
            if comp.external:
                text = formula.formula_name
            else:
                text = ' ---'
                flash(f"Please select a valid Scoring Formula from list and Save.", category='warning')
            formulas.append((value, text))
        compform.formula.choices = formulas

        if (current_user.id not in ids) and (current_user.access not in ('admin', 'manager')):
            session['is_editor'] = False
            compform.submit = None
        else:
            session['is_editor'] = True

    ''' Ladders if active in settings'''
    if LADDERS:
        ladderform = CompLaddersForm()
        ladderform.ladders.choices = [(el['ladder_id'], el['ladder_name'])
                                      for el in frontendUtils.list_ladders(comp.date_to, comp.comp_class)]
        comp_ladders = frontendUtils.get_comp_ladders(compid)
        ladderform.ladders.data = comp_ladders
    else:
        ladderform = None

    tasks_info = frontendUtils.get_task_list(comp.comp_id)

    session['tasks'] = tasks_info['tasks']
    session['check_g_record'] = comp.check_g_record
    session['track_source'] = comp.track_source

    formula_preset = comp.formula.get_preset()

    if comp.external:
        '''External Event'''
        flash(f"This is an External Event. Settings and Results are Read Only.", category='warning')
    if not session['is_editor']:
        flash(f"You are not a scorekeeper for this comp. You won't be able to modify settings.", category='warning')
    elif not comp.external:
        if not compform.formula.data:
            '''Comp has not been initialised yet'''
            flash(f"Comp has not been properly set yet. Check all parameters and save.", category='warning')
        elif any(t['needs_full_rescore'] or t['needs_new_scoring'] or t['needs_recheck'] for t in session['tasks']):
            '''there are tasks that do not have final results yet and seem to need to be checked'''
            flash(f"There are tasks that need to be verified.", category='warning')

    return render_template('users/comp_settings.html', compid=compid, compform=compform,
                           taskform=newtaskform, scorekeeperform=newScorekeeperform, ladderform=ladderform,
                           rankingform=rankingform, certifications=certifications, tasks_info=tasks_info, error=error,
                           allow_open_event=OPEN_EVENT, self_register=(SELF_REG_DEFAULT and PILOT_DB),
                           formula_preset=formula_preset)


@blueprint.route('/_convert_external_comp/<int:compid>', methods=['GET', 'POST'])
@login_required
@check_coherence
def convert_external_comp(compid: int):
    if not session['external']:
        flash("Event does not seem to be external. Conversion aborted", category='danger')
        return redirect(url_for('user.comp_settings_admin', compid=compid))

    '''starting conversion'''
    success = frontendUtils.convert_external_comp(compid)

    if success:
        flash("Event converted.", category='success')
    else:
        flash("There was an error trying to convert this event.", category='danger')
    return redirect(url_for('user.comp_settings_admin', compid=compid))


@blueprint.route('/_get_scorekeepers/<int:compid>', methods=['GET'])
@login_required
def _get_scorekeepers(compid: int):
    owner, scorekeepers, available_users = frontendUtils.get_comp_scorekeepers(compid)
    return {'owner': owner, 'scorekeepers': scorekeepers, 'dropdown': available_users}


@blueprint.route('/_add_scorekeeper/<int:compid>', methods=['POST'])
@login_required
@editor_required
def _add_scorekeeper(compid: int):
    data = request.json
    if request.method == "POST":
        return jsonify(success=frontendUtils.set_comp_scorekeeper(compid, data['id']))
    return render_template('500.html')


@blueprint.route('/_delete_scorekeeper', methods=['POST'])
@login_required
@editor_required
def _delete_scorekeeper():
    if request.method == "POST":
        data = request.json
        return jsonify(success=frontendUtils.delete_comp_scorekeeper(data.get('compid'), data.get('id')))
    return render_template('500.html')


@blueprint.route('/_save_comp_ladders/<int:compid>', methods=['POST'])
@login_required
def _save_comp_ladders(compid: int):
    checked = request.json['checked']
    if frontendUtils.save_comp_ladders(compid, checked):
        resp = jsonify(success=True)
    else:
        resp = jsonify(success=False)
    return resp


@blueprint.route('/_get_users', methods=['GET'])
@login_required
@manager_required
def _get_users():
    return {'data': frontendUtils.get_all_users()}


@blueprint.route('/user_admin', methods=['GET'])
@login_required
@manager_required
def user_admin():
    from Defines import ADMIN_DB
    # modify_user_form = ModifyUserForm()
    user_form = UserForm()
    if current_user.is_manager:
        '''will be able to add only scorekeepers or pilots'''
        user_form.access.choices = [('pilot', 'Pilot'), ('pending', 'Pending'), ('scorekeeper', 'Scorekeeper')]
    user_form.nat.choices = [(x['code'], x['name']) for x in frontendUtils.list_countries()]
    return render_template('users/user_admin.html',
                           user_form=user_form, editable=bool(ADMIN_DB))


@blueprint.route('/task_admin/<int:taskid>', methods=['GET', 'POST'])
@login_required
@check_coherence
@session_task
@state_messages
def task_admin(taskid: int):
    from calcUtils import sec_to_time, time_to_seconds
    from region import get_openair
    error = None
    taskform = TaskForm()
    turnpointform = TurnpointForm(task_id=taskid)
    modifyturnpointform = TurnpointForm(task_id=taskid)
    modifyturnpointform.submit.label.text = 'Save'

    task = Task.read(taskid)
    taskform.region.choices.extend(frontendUtils.get_region_choices(session['compid'])[0])
    waypoints, _ = frontendUtils.get_waypoint_choices(task.reg_id)
    turnpointform.rwp_id.choices = waypoints
    modifyturnpointform.rwp_id.choices = waypoints
    task_info = session['task']

    if request.method == 'POST':
        if session['external']:
            task.comment = taskform.comment.data
            task.to_db()
            flash(f"{task.task_name} saved", category='info')

        elif taskform.validate_on_submit():
            task.comp_name = taskform.comp_name
            task.task_name = taskform.task_name.data
            task.task_num = taskform.task_num.data
            task.comment = taskform.comment.data
            task.date = taskform.date.data
            task.task_type = taskform.task_type.data
            task.reg_id = taskform.region.data if taskform.region.data not in (0, '', None) else None
            task.training = taskform.training.data
            if any(el.data is not None for el in (taskform.window_open_time, taskform.start_time)):
                '''save timings only if set'''
                task.window_open_time = time_to_seconds(taskform.window_open_time.data) - taskform.time_offset.data
                task.window_close_time = time_to_seconds(taskform.window_close_time.data) - taskform.time_offset.data
                task.start_time = time_to_seconds(taskform.start_time.data) - taskform.time_offset.data
                task.start_close_time = time_to_seconds(taskform.start_close_time.data) - taskform.time_offset.data
                task.stopped_time = None if taskform.stopped_time.data is None else \
                    time_to_seconds(taskform.stopped_time.data) - taskform.time_offset.data
                task.task_deadline = time_to_seconds(taskform.task_deadline.data) - taskform.time_offset.data
                task.SS_interval = taskform.SS_interval.data * 60  # (convert from min to sec)
                task.start_iteration = taskform.start_iteration.data
            task.time_offset = taskform.time_offset.data
            task.check_launch = 'on' if taskform.check_launch.data else 'off'
            task.airspace_check = taskform.airspace_check.data
            # task.openair_file = taskform.openair_file  # TODO get a list of openair files for this comp (in the case of defines.yaml airspace_file_library: off otherwise all openair files available)
            if task.airspace_check and task.reg_id and not task.openair_file:
                task.openair_file = get_openair(reg_id=task.reg_id)
            task.QNH = taskform.QNH.data
            task.formula.formula_distance = taskform.formula_distance.data
            task.formula.formula_arrival = taskform.formula_arrival.data
            task.formula.formula_departure = taskform.formula_departure.data
            task.formula.formula_time = taskform.formula_time.data
            task.formula.tolerance = (taskform.tolerance.data or 0) / 100
            task.formula.max_JTG = taskform.max_JTG.data
            task.formula.no_goal_penalty = (taskform.no_goal_penalty.data or 0) / 100
            task.formula.arr_alt_bonus = taskform.arr_alt_bonus.data
            task.to_db()

            t = next(el for el in session['tasks'] if el['task_id'] == taskid)
            t['ready_to_score'] = True if task.ready_to_score else False
            t['needs_new_scoring'], t['needs_recheck'], t['needs_full_rescore'] = frontendUtils.check_task(taskid)
            flash("Task Saved", category='info')

        else:
            for item in taskform:
                if item.errors:
                    flash(f"{item.label.text} ({item.data}): {', '.join(x for x in item.errors)}", category='danger')

        return redirect(url_for('user.task_admin', taskid=taskid))

    elif request.method == 'GET':
        offset = task.time_offset if task.time_offset else 0
        taskform.comp_name = task.comp_name
        taskform.task_name.data = task.task_name
        taskform.task_num.data = task.task_num
        taskform.comment.data = task.comment
        taskform.date.data = task.date
        taskform.task_type.data = task.task_type
        taskform.region.data = task.reg_id or 0
        taskform.training.data = task.training
        taskform.window_open_time.data = "" if not task.window_open_time else sec_to_time((task.window_open_time
                                                                                           + offset) % 86400)
        taskform.window_close_time.data = "" if not task.window_close_time else sec_to_time((task.window_close_time
                                                                                             + offset) % 86400)
        taskform.start_time.data = "" if not task.start_time else sec_to_time((task.start_time
                                                                               + offset) % 86400)
        taskform.start_close_time.data = "" if not task.start_close_time else sec_to_time((task.start_close_time
                                                                                           + offset) % 86400)
        taskform.stopped_time.data = "" if not task.stopped_time else sec_to_time((task.stopped_time
                                                                                   + offset) % 86400)
        taskform.task_deadline.data = "" if not task.task_deadline else sec_to_time((task.task_deadline
                                                                                     + offset) % 86400)
        taskform.SS_interval.data = round(task.SS_interval / 60)  # (convert from sec to min)
        taskform.start_iteration.data = task.start_iteration
        taskform.time_offset.data = offset
        taskform.check_launch.data = False if task.check_launch == 'off' else True
        taskform.airspace_check.data = task.airspace_check
        # taskform.openair_file.data = task.openair_file # TODO get a list of openair files for this comp (in the case of defines.yaml airspace_file_library: off otherwise all openair files available)
        taskform.QNH.data = task.QNH
        # taskform.region.data = task.reg_id # TODO get a list of waypoint files for this comp (in the case of defines.yaml waypoint_file_library: off otherwise all regions available)
        # taskform.region.choices = frontendUtils.get_region_choices(compid)
        taskform.formula_distance.data = task.formula.formula_distance
        taskform.formula_arrival.data = task.formula.formula_arrival
        taskform.formula_departure.data = task.formula.formula_departure
        taskform.formula_time.data = task.formula.formula_time
        taskform.tolerance.data = round((task.formula.tolerance or 0) * 100, 1)
        taskform.max_JTG.data = task.formula.max_JTG
        taskform.no_goal_penalty.data = round((task.formula.no_goal_penalty or 0) * 100)
        taskform.arr_alt_bonus.data = task.formula.arr_alt_bonus

        formula_preset = None
        if task_info['cancelled'] or task_info['locked'] or not session['is_editor']:
            taskform.submit = None
        elif not session['external']:
            formula_preset = task.formula.get_preset()

        return render_template('users/task_admin.html', taskid=taskid, compid=task.comp_id, task_info=task_info,
                               taskform=taskform, turnpointform=turnpointform, modifyturnpointform=modifyturnpointform,
                               formula_preset=formula_preset, error=error)


@blueprint.route('/_get_admin_comps', methods=['GET'])
@login_required
def _get_admin_comps():
    return frontendUtils.get_admin_comps(current_user.id, current_user.access)


@blueprint.route('/_delete_comp/<int:compid>', methods=['POST', 'GET'])
@login_required
def _delete_comp(compid: int):
    from comp import delete_comp
    owner, _, _ = frontendUtils.get_comp_scorekeepers(compid)
    if current_user.id == owner['id']:
        delete_comp(compid)
    else:
        flash(f"You are not the owner of this competition. You cannot delete it.", category='danger')
        return redirect(request.url)
    resp = jsonify(success=True)
    return resp


@blueprint.route('/airspace_admin', methods=['GET', 'POST'])
@login_required
def airspace_admin():
    return render_template('users/airspace_admin.html')


@blueprint.route('/waypoint_admin', methods=['GET', 'POST'])
@login_required
def waypoint_admin():
    return render_template('users/waypoint_admin.html')


@blueprint.route('/_register_pilots/<int:compid>', methods=['POST'])
@login_required
def _register_pilots(compid: int):
    from pilot.participant import register_from_profiles_list, unregister_from_profiles_list
    data = request.json
    if data['register']:
        register_from_profiles_list(compid, data['register'])
    if data['unregister']:
        unregister_from_profiles_list(compid, data['unregister'])
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_add_task/<int:compid>', methods=['POST'])
@login_required
@editor_required
def _add_task(compid: int):
    from region import get_openair

    form = NewTaskForm()
    if form.validate_on_submit():
        '''create task entry in database'''
        comp = Comp.read(compid)
        task = Task(comp_id=compid)
        task.task_num = form.task_number.data
        task.task_name = form.task_name.data if form.task_name.data not in [None, ''] else f'Task {task.task_num}'
        task.date = form.task_date.data
        task.task_comment = form.task_comment.data
        task.reg_id = form.task_region.data
        task.time_offset = comp.time_offset
        task.airspace_check = comp.airspace_check
        if task.airspace_check and task.reg_id:
            task.openair_file = get_openair(reg_id=task.reg_id)
        task.check_launch = comp.check_launch
        task.igc_config_file = comp.igc_config_file
        task.to_db()
        return jsonify(success=True)

    return jsonify(success=False, errors=form.errors)


@blueprint.route('/_del_task/<int:taskid>', methods=['POST'])
@login_required
@editor_required
def _del_task(taskid: int):
    from task import delete_task
    if request.method == "POST":
        delete_task(taskid)
        resp = jsonify(success=True)
        return resp
    return jsonify(success=False)


@blueprint.route('/_declare_task_cancelled/<int:taskid>', methods=['POST'])
@login_required
@editor_required
def _declare_task_cancelled(taskid: int):
    if request.method == "POST":
        data = request.json
        old_value = bool(data.get('cancelled'))
        comment = data.get('comment')
        resp = frontendUtils.switch_task_cancelled(taskid, old_value, comment)
        if resp:
            frontendUtils.unpublish_task_result(taskid)
            if not old_value:
                '''update comp results'''
                frontendUtils.update_comp_result(session['compid'], name_suffix='Overview')
            session['tasks'] = frontendUtils.get_task_list(session['compid'])['tasks']
            session['task'] = next(el for el in session['tasks'] if el['task_id'] == taskid)
            return jsonify(success=resp)
    return jsonify(success=False)


@blueprint.route('/_get_tasks/<int:compid>', methods=['GET'])
@login_required
def _get_tasks(compid: int):
    task_list = frontendUtils.get_task_list(compid)
    session['tasks'] = task_list['tasks']
    return task_list


@blueprint.route('/_change_comp_category', methods=['GET', 'POST'])
@login_required
def _change_comp_category():
    data = request.json
    resp = frontendUtils.change_comp_category(data['compid'], data['new_category'], data['formula'])
    if resp:
        flash('Event Category successfully changed.', 'success')
    return jsonify(success=resp)


@blueprint.route('/_update_formula_adv_settings', methods=['GET', 'POST'])
@login_required
def _update_formula_adv_settings():
    data = request.json
    formula, preset = frontendUtils.get_comp_formula_preset(data['compid'], data['formula'], data['category'])
    form = CompForm(obj=formula)
    form.lead_factor.data = 1 if formula.lead_factor is None else formula.lead_factor  # should not be None
    form.no_goal_penalty.data = int(formula.no_goal_penalty * 100)
    form.tolerance.data = formula.tolerance * 100
    form.validity_min_time.data = int((formula.validity_min_time or 0) / 60)
    form.score_back_time.data = int((formula.score_back_time or 0) / 60)
    return jsonify(success=True,
                   formula_preset=preset,
                   render=render_template('users/formula_adv_settings.html',
                                          compid=data['compid'], compform=form, formula_preset=preset))


@blueprint.route('/_get_task_turnpoints/<int:taskid>', methods=['GET'])
@login_required
def _get_task_turnpoints(taskid: int):
    task = Task.read(taskid)
    for session_task in session['tasks']:
        if session_task['task_id'] == taskid:
            if session_task['ready_to_score'] != task.ready_to_score:
                session_task['ready_to_score'] = task.ready_to_score
    return frontendUtils.get_task_turnpoints(task)


@blueprint.route('/_save_turnpoint/<int:taskid>', methods=['POST'])
@login_required
@editor_required
def _save_turnpoint(taskid: int):
    """add turnpoint to the task,if rwp_id is not null then update instead of insert (add)
    if turnpoint is goal or we are updating and goal exists then calculate opt dist and dist."""
    from frontendUtils import get_waypoint
    form = TurnpointForm()

    if form.validate_on_submit():
        tp = get_waypoint(rwp_id=form.rwp_id.data)
        form.populate_obj(tp)

        tpid = save_turnpoint(taskid, tp)
        if tpid:
            turnpoints = frontendUtils.check_task_turnpoints(taskid, tpid)
            return turnpoints

    return jsonify(errors=list(form.errors.items()))


@blueprint.route('/_del_turnpoint/<tpid>', methods=['POST'])
@login_required
@editor_required
def _del_turnpoint(tpid):
    """delete a turnpoint from the task"""
    from route import delete_turnpoint
    data = request.json
    taskid = int(data['taskid'])
    delete_turnpoint(tpid)
    task = Task.read(taskid)
    if data['partial_distance'] != '':
        if task.turnpoints[-1].type == 'goal':
            task.calculate_optimised_task_length()
            task.calculate_task_length()
            task.update_task_distance()
            write_map_json(taskid)
        else:
            task.delete_task_distance()
    return frontendUtils.get_task_turnpoints(task)


@blueprint.route('/_del_all_turnpoints/<int:taskid>', methods=['POST'])
@login_required
@editor_required
def _del_all_turnpoints(taskid: int):
    """delete a turnpoint from the task"""
    from route import delete_all_turnpoints
    from task import Task
    from Defines import MAPOBJDIR
    delete_all_turnpoints(taskid)
    task = Task.read(taskid)
    task.opt_dist = 0
    task.distance = 0
    task.update_task_info()
    task_map = path.join(MAPOBJDIR, 'tasks/' + str(taskid) + '.task')
    if path.isfile(task_map):
        remove(task_map)

    resp = jsonify(success=True)
    return resp


@blueprint.route('/_copy_turnpoints/<int:taskid>', methods=['POST'])
@login_required
@editor_required
def _copy_turnpoints(taskid: int):
    """copy turnpoints from another task"""
    data = request.json
    success = frontendUtils.copy_turnpoints_from_task(taskid, data.get('task_from'))
    if not success:
        return jsonify(success=False)

    task = Task.read(taskid)
    if task.turnpoints and any(tp.type == 'goal' for tp in task.turnpoints):
        task.calculate_optimised_task_length()
        task.calculate_task_length()
        task.update_task_distance()
        write_map_json(taskid)
    else:
        task.opt_dist = 0
        task.distance = 0
        task.SS_distance = 0
        task.opt_dist_to_ESS = 0
        task.opt_dist_to_SS = 0
        task.update_task_distance()

    return jsonify(success=True, data=frontendUtils.get_task_turnpoints(task))


@blueprint.route('/_get_tracks_admin/<int:taskid>', methods=['GET'])
@login_required
def _get_tracks_admin(taskid: int):
    task = next((t for t in session['tasks'] if t['task_id'] == taskid), None)
    data = frontendUtils.get_pilot_list_for_track_management(taskid, task['needs_recheck'])
    if task['needs_recheck'] and all(not el['outdated'] for el in data):
        '''update task recheck status'''
        task['needs_recheck'] = False
    return jsonify(data=data)


@blueprint.route('/_get_tracks_processed/<int:taskid>', methods=['GET'])
@login_required
def _get_tracks_processed(taskid: int):
    tracks, pilots = frontendUtils.number_of_tracks_processed(taskid)
    return {'tracks': tracks, 'pilots': pilots}


@blueprint.route('/track_admin/<int:taskid>', methods=['GET'])
@login_required
@check_coherence
@internal_required
@editor_required
@session_task
@state_messages
def track_admin(taskid: int):
    from Defines import TELEGRAM, LIVETRACKDIR
    compid = int(session['compid'])

    '''check livetracking availability'''
    if session['task'].get('track_source') == 'flymaster':
        session['task']['lt_active'] = False
        if Path(LIVETRACKDIR, str(taskid)).is_file():
            session['task']['lt_active'] = True

    formats = frontendUtils.get_igc_filename_formats_list()

    return render_template('users/track_admin.html', taskid=taskid, compid=compid, filename_formats=formats,
                           production=frontendUtils.production(), task_info=session['task'], telegram=TELEGRAM)


@blueprint.route('/_set_result/<int:taskid>', methods=['POST'])
@login_required
def _set_result(taskid: int):
    data = request.json
    trackid = update_status(data['par_id'], taskid, data['Result'])
    print(trackid)

    if trackid > 0:
        data['track_id'] = trackid
        if data['Result'] == "mindist":
            data['Result'] = "Min Dist"
        else:
            data['Result'] = data['Result'].upper()
        resp = jsonify(data)
        return resp


@blueprint.route('/_delete_track/<trackid>', methods=['POST'])
@login_required
def _delete_track(trackid):
    data = request.json
    if delete_track(trackid, delete_file=True):
        data['Result'] = "Not Yet Processed"
        resp = jsonify(data)
        return resp
    else:
        flash(f"There was an error trying to delete track with ID {trackid}", category='danger')
        return render_template('500.html')


@blueprint.route('/_upload_track/<int:taskid>/<int:parid>', methods=['POST'])
@login_required
@editor_required
def _upload_track(taskid: int, parid: int):
    if request.method == "POST":
        if request.files:
            if "filesize" in request.cookies:
                if not frontendUtils.allowed_tracklog_filesize(request.cookies["filesize"]):
                    print("Filesize exceeded maximum limit")
                    return jsonify(success=False, error="Filesize exceeded maximum limit")
                check_g_record = session['check_g_record']
                check_validity = True

                if request.files.get("tracklog_NO_G"):
                    tracklog = request.files["tracklog_NO_G"]
                    check_g_record = False
                elif request.files.get("tracklog_NO_V"):
                    tracklog = request.files["tracklog_NO_V"]
                    check_validity = False
                    check_g_record = False
                else:
                    tracklog = request.files["tracklog"]

                if tracklog.filename == "":
                    print("No filename")
                    return jsonify(success=False, error="File has no filename")

                if frontendUtils.allowed_tracklog(tracklog.filename):
                    resp, error = frontendUtils.process_igc(taskid, parid, tracklog, current_user.username,
                                                            check_g_record, check_validity)
                    return jsonify(success=resp, error=error)

                print("That file extension is not allowed")
                return jsonify(success=False, error="File extension not allowed")

            return jsonify(success=False, error="filesize not sent or file has no size")
        return jsonify(success=False, error="File not found")


@blueprint.route('/_get_xcontest_tracks/<int:taskid>', methods=['POST'])
@login_required
@editor_required
def _get_xcontest_tracks(taskid: int):
    from sources.xcontest import get_zipfile
    if request.method == "POST":
        zip_file = get_zipfile(taskid)

        if not zip_file:
            return jsonify(success=False)

        resp = frontendUtils.process_zip_file(zip_file=zip_file,
                                              taskid=taskid,
                                              username=current_user.username,
                                              grecord=session['check_g_record'],
                                              track_source='xcontest')
        return jsonify(success=True)


@blueprint.route('/_upload_XCTrack/<int:taskid>', methods=['POST'])
@login_required
def _upload_XCTrack(taskid: int):
    """takes an upload of an xctrack task file and processes it and saves the task to the DB"""
    if request.method == "POST":
        if request.files:
            task_file = json.load(request.files["track_file"])
            task = Task.read(taskid)
            task.update_from_xctrack_data(task_file)
            task.calculate_optimised_task_length()
            task.calculate_task_length()
            task.update_task_info()
            task.to_db()
            write_map_json(taskid)

            resp = jsonify(success=True)
            return resp


@blueprint.route('/_upload_track_zip/<int:taskid>', methods=['POST'])
@login_required
@editor_required
def _upload_track_zip(taskid: int):
    from Defines import track_formats
    if request.method == "POST":
        if not request.files or "filesize" not in request.cookies:
            return jsonify(success=False, error='No Zip file was given.')
        elif not frontendUtils.allowed_tracklog_filesize(request.cookies["filesize"], size=50):
            '''Filesize exceeded maximum limit'''
            return jsonify(success=False, error='Filesize exceeded maximum limit.')
        zip_file = request.files["zip_file"]
        '''check if file is an archive, is not corrupt, and contains files with requested extension'''
        valid, error = frontendUtils.check_zip_file(zip_file, track_formats)
        if not valid:
            return jsonify(success=False, error=error)

        resp = frontendUtils.process_zip_file(zip_file=zip_file,
                                              taskid=taskid,
                                              username=current_user.username,
                                              grecord=session['check_g_record'])
        return resp


@blueprint.route('/_recheck_task_tracks/<int:taskid>', methods=['POST'])
@login_required
@editor_required
def _recheck_task_tracks(taskid: int):
    if not session['external'] and request.method == "POST":
        resp = frontendUtils.recheck_tracks(task_id=taskid, username=current_user.username)
        if resp:
            session['task']['needs_recheck'] = False
        return jsonify(success=resp, session=session['task'])
    return jsonify(success=False)


@blueprint.route('/_recheck_track/<int:trackid>', methods=['POST'])
@login_required
def _recheck_track(trackid: int):
    if not session['external'] and request.method == "POST" and request.json:
        taskid, parid = request.json.get('taskid'), request.json.get('parid')

        resp, error = frontendUtils.recheck_track(task_id=taskid, par_id=parid, user=current_user.username)
        return jsonify(success=resp, error=error)
    return jsonify(success=False, error='There was an error trying to check track.')


@blueprint.route('/_get_comp_result_files/<int:compid>', methods=['POST'])
@login_required
def _get_comp_result_files(compid: int):
    data = request.json
    offset = ((int(data['offset']) / 60 * -1) * 3600)

    return frontendUtils.get_comp_result_files(compid, int(offset))


@blueprint.route('/_get_task_result_files/<int:taskid>', methods=['POST'])
@login_required
def _get_task_result_files(taskid: int):
    data = request.json
    offset = ((int(data['offset']) / 60 * -1) * 3600)
    compid = int(session['compid'])

    return frontendUtils.get_task_result_files(int(taskid), compid, int(offset))


@blueprint.route('/_send_telegram_update/<int:taskid>', methods=['POST'])
@login_required
def _send_telegram_update(taskid: int):
    """sends a telegram message with partial results and missing pilots during tracks processing"""
    from telegram import send_result_status
    if request.method == "POST":
        info = {}
        task = next((t for t in session['tasks'] if t['task_id'] == taskid), None)
        if task:
            info = dict(comp_name=session['comp_name'], task_num=task['task_num'], source=task['track_source'])
        resp = send_result_status(taskid, info)
        return jsonify(success=resp)


@blueprint.route('/_get_task_score_from_file/<int:taskid>/<string:filename>', methods=['GET'])
@login_required
def _get_task_score_from_file(taskid: int, filename: str):
    from result import pretty_format_results
    from calcUtils import c_round
    error = None
    result_file = get_task_json_by_filename(filename)
    if not result_file:
        return {'data': ''}
    rank = 1
    all_pilots = []
    timeoffset = int(result_file['info']['time_offset'])
    stats = pretty_format_results(result_file['stats'], timeoffset)
    info = result_file['info']
    for r in result_file['results']:
        parid = r['par_id']
        name = r['name']
        status = r['result_type']
        pilot = dict(par_id=parid, rank=rank, name=name, SSS='', ESS='', time='', altbonus='', realdist='',
                     distance='', speedP='', leadP='', arrivalP='', distanceP='', penalty='', score=status,
                     notifications=r['notifications'])
        if status not in ['dnf', 'abs', 'nyp']:
            if not session['external']:
                pilot['name'] = f'<a href="/map/{parid}-{taskid}?back_link=0" target="_blank">{name}</a>'
            if r['SSS_time']:
                pilot['SSS'] = sec_to_time(r['SSS_time'] + result_file['info']['time_offset']).strftime("%H:%M:%S")
            else:
                pilot['SSS'] = ""
            if r['ESS_time'] == 0 or r['ESS_time'] is None:
                pilot['ESS'] = ""
                pilot['time'] = ""
            else:
                pilot['ESS'] = sec_to_time(r['ESS_time'] + result_file['info']['time_offset']).strftime("%H:%M:%S")
                pilot['time'] = sec_to_time(r['ESS_time'] - r['SSS_time']).strftime("%H:%M:%S")

            pilot['realdist'] = "" if not r['stopped_distance'] else c_round(r['stopped_distance'] / 1000, 2)
            pilot['altbonus'] = "" if not r['stopped_altitude'] else round(r['stopped_altitude'])
            pilot['distance'] = c_round(r['distance'] / 1000, 2)
            pilot['speedP'] = c_round(r['time_score'], 2)
            pilot['leadP'] = c_round(r['departure_score'], 2)
            pilot['arrivalP'] = c_round(r['arrival_score'], 2)  # arrival points
            pilot['distanceP'] = c_round(r['distance_score'], 2)
            if r.get('before_penalty_score'):  # compatibility older formats results
                pilot['totalP'] = c_round(r['before_penalty_score'], 2)
            else:
                pilot['totalP'] = c_round(sum([pilot['speedP'] or 0, pilot['leadP'] or 0,
                                               pilot['arrivalP'] or 0, pilot['distanceP'] or 0]), 2)
            pilot['penalty'] = c_round(r['penalty'], 2) if r['penalty'] else ""
            pilot['score'] = c_round(r['score'], 2)

        # TODO once result files have a list of comments we can activate these lines and remove the 3 dummy lines below
        # pilot['Track_Comment'] = r['comment'][0]
        # pilot['Penalty_Comment'] = r['comment'][1]
        # pilot['Admin_Comment'] = r['comment'][2]
        # pilot['Track Comment'] = 'test track comment'
        # pilot['Penalty Comment'] = 'test penalt comment'
        # pilot['Admin Comment'] = 'test admin comment'
        all_pilots.append(pilot)
        rank += 1

    return {'data': all_pilots, 'stats': stats, 'info': info}


@blueprint.route('/task_score_admin/<int:taskid>', methods=['GET'])
@login_required
@editor_required
@check_coherence
@session_task
@ready_to_score
@valid_results
@state_messages
def task_score_admin(taskid: int):
    task_info = session['task']
    compid = int(session['compid'])

    fileform = ResultAdminForm()
    editform = EditScoreForm()
    choices = [(1, 1), (2, 2)]
    fileform.task_result_file.choices = choices
    fileform.comp_result_file.choices = choices

    score_active = not (task_info['cancelled'] or session['external'])

    return render_template('users/task_score_admin.html',
                           fileform=fileform, taskid=taskid, compid=compid, task_info=task_info,
                           score_active=score_active, editform=editform, production=frontendUtils.production())


@blueprint.route('/_score_task/<int:taskid>', methods=['POST'])
@login_required
def _score_task(taskid: int):
    if request.method == "POST":
        """score task, request data should contain status: the score status (provisional, official etc),
        autopublish: True or False. indicates if to publish results automatically after scoring"""
        data = request.json
        task = Task.read(taskid)

        if task.stopped_time:
            '''If stopped time, to be sure all pilots are computed with correct task time, we need to reprocedd all 
            tracks. We could do this only once and than only if there are new tracks added.'''
            # TODO: stopped task process could be optimised
            if frontendUtils.production():
                job = current_app.task_queue.enqueue(frontendUtils.full_rescore, taskid, background=True,
                                                     user=current_user.username, status=data['status'],
                                                     autopublish=data['autopublish'], compid=session['compid'],
                                                     job_timeout=2000)
                resp = jsonify(success=True, background=True)
            else:
                frontendUtils.full_rescore(taskid, status=data['status'], autopublish=data['autopublish'],
                                           compid=session['compid'])
                resp = jsonify(success=True)
            session['task']['needs_new_scoring'] = False
            session['task']['needs_full_rescore'] = False
            return resp

        ref_id, filename = task.create_results(data['status'])
        if ref_id:
            if data['autopublish']:
                frontendUtils.publish_task_result(taskid, filename)
                frontendUtils.update_comp_result(session['compid'], status=data['status'], name_suffix='Overview')
            session['task']['needs_new_scoring'] = False
            return jsonify(success=True, redirect='/users/task_score_admin/' + str(taskid))
        return jsonify(success=False)
    return render_template('500.html')


@blueprint.route('/_full_rescore_task/<int:taskid>', methods=['POST'])
@login_required
def _full_rescore_task(taskid: int):
    data = request.json
    if frontendUtils.production():
        job = current_app.task_queue.enqueue(frontendUtils.full_rescore, taskid, background=True,
                                             user=current_user.username, status=data['status'],
                                             autopublish=data['autopublish'], compid=session['compid'],
                                             job_timeout=2000)

        resp = jsonify(success=True, background=True)
        return resp
    else:
        ref_id = frontendUtils.full_rescore(taskid, status=data['status'], autopublish=data['autopublish'],
                                            compid=session['compid'])
        resp = jsonify(success=bool(ref_id))

    session['task']['needs_new_scoring'] = False
    session['task']['needs_full_rescore'] = False
    return resp


@blueprint.route('/_unpublish_result', methods=['POST'])
@login_required
@editor_required
def _unpublish_result():
    if request.method == "POST":
        data = request.json
        iscomp = data['iscomp']
        compid = session['compid']
        taskid = None if iscomp else data['taskid']
        if iscomp:
            '''unpublish comp results'''
            frontendUtils.unpublish_comp_result(compid)
        else:
            '''unpublish task results and update Comp Overview'''
            frontendUtils.unpublish_task_result(taskid)
            frontendUtils.update_comp_result(compid, name_suffix='Overview')
        header = "No published results"
        return jsonify(filename='', header=header)
    return render_template('500.html')


@blueprint.route('/_publish_result', methods=['POST'])
@login_required
@editor_required
def _publish_result():
    if request.method == "POST":
        data = request.json
        iscomp = data['iscomp']
        compid = session['compid']
        taskid = None if iscomp else data['taskid']
        if iscomp:
            '''publish comp results'''
            success = frontendUtils.publish_comp_result(compid, data['filename'])
        else:
            '''publish task results and update Comp Overview'''
            frontendUtils.publish_task_result(taskid, data['filename'])
            success, _, timestamp = frontendUtils.update_comp_result(compid, name_suffix='Overview')
        if success:
            published, status = (data['filetext'], '') if '-' not in data['filetext'] else data['filetext'].split('-')
            if 'Overview' in data['filename']:
                header = 'Auto Generated Result '
                status = status.replace('Auto Generated ', '')
            else:
                header = "Published Result "
            status = 'No status' if status in (None, 'None') or status.lstrip() == '' else status.lstrip()
            header += f"ran at: {published} Status: {status}"
            resp = jsonify(filename=data['filename'], header=header)
            return resp
        return jsonify(header='There was a problem creating comp result: do we miss some task results files?')
    return render_template('500.html')


@blueprint.route('/_task_lock_switch/<int:taskid>', methods=['POST'])
@login_required
@editor_required
def _task_lock_switch(taskid: int):
    if request.method == "POST":
        data = request.json
        old_value = bool(data.get('locked'))
        resp = frontendUtils.switch_task_lock(taskid, old_value)
        if resp:
            session['tasks'] = frontendUtils.get_task_list(session['compid'])['tasks']
            session['task'] = next(el for el in session['tasks'] if el['task_id'] == taskid)
            return jsonify(success=resp)
    return jsonify(success=False)


@blueprint.route('/comp_score_admin/<int:compid>', methods=['GET'])
@login_required
@editor_required
@check_coherence
def comp_score_admin(compid: int):

    fileform = ResultAdminForm()
    editform = EditScoreForm()
    choices = [(1, 1), (2, 2)]
    tasks = session['tasks']
    fileform.task_result_file.choices = choices
    fileform.comp_result_file.choices = choices

    score_active = not session['external']

    return render_template('users/comp_score_admin.html',
                           compid=compid, tasks=tasks, score_active=score_active, fileform=fileform, editform=editform)


@blueprint.route('/_calculate_comp_result/<int:compid>', methods=['POST'])
@login_required
@editor_required
def _calculate_comp_result(compid: int):
    if request.method == "POST":
        data = request.json
        status = data['status']
        refid, filename, timestamp = frontendUtils.update_comp_result(compid, status=status)
        if refid:
            if data['autopublish']:
                success = frontendUtils.publish_comp_result(compid, filename)
            resp = jsonify(success=True, message='Event Results Calculated. You can check using Preview.')
            return resp
        return jsonify(success=False,
                       message='There was a problem creating comp result: do we miss some task results files?')
    return render_template('500.html')


@blueprint.route('/_change_result_status', methods=['POST'])
@login_required
@editor_required
def _change_result_status():
    if request.method == "POST":
        from result import update_result_status, update_tasks_status_in_comp_result
        data = request.json
        filename = data['filename']
        status = data['status']
        update_result_status(filename, status)
        update_tasks_status_in_comp_result(session['compid'])
        # frontendUtils.update_comp_result(session['compid'], status=data['status'], name_suffix='Overview')
        resp = jsonify(success=True)
        return resp
    return render_template('500.html')


@blueprint.route('/_delete_task_result', methods=['POST'])
@login_required
@editor_required
def _delete_task_result():
    if request.method == "POST":
        from result import delete_result
        data = request.json
        delete_result(data['filename'], delete_file=data['deletefile'])
        resp = jsonify(success=True)
        return resp
    return render_template('500.html')


@blueprint.route('/_get_regions', methods=['GET'])
@login_required
def _get_regions():
    compid = session.get('compid')
    choices, details = frontendUtils.get_region_choices(compid)
    return {'choices': choices, 'details': details}


@blueprint.route('/_get_wpts/<int:regid>', methods=['POST'])
@login_required
def _get_wpts(regid: int):
    openair_file = request.json.get('airspace')
    waypoints, region_map, _, _ = frontendUtils.get_region_waypoints(regid, openair_file=openair_file)
    return {'waypoints': waypoints, 'map': region_map._repr_html_(), 'airspace': openair_file}


@blueprint.route('/region_admin', methods=['GET', 'POST'])
@login_required
def region_admin():
    from frontendUtils import get_region_choices, unique_filename
    from waypoint import get_turnpoints_from_file_storage, allowed_wpt_extensions
    from region import Region
    from Defines import WAYPOINTDIR, AIRSPACEDIR, ALLOWED_WPT_EXTENSIONS

    region_select = RegionForm()
    new_region = NewRegionForm()
    compid = session.get('compid')
    regions, _ = get_region_choices(compid)
    region_select.region.choices = regions
    air_filename = None

    if request.method == "POST":
        if request.files:
            if not Path(WAYPOINTDIR).is_dir():
                makedirs(WAYPOINTDIR)
            waypoint_file = request.files["waypoint_file"]
            '''airspace file'''
            if request.files["openair_file"].filename:
                airspace_file = request.files["openair_file"]
            else:
                airspace_file = None

            '''waypoint file'''
            if waypoint_file:  # there should always be a file as it is a required field
                if not allowed_wpt_extensions(waypoint_file.filename):
                    '''file has not a valid extension'''
                    flash(f"Waypoint file extension not supported ({', '.join(ALLOWED_WPT_EXTENSIONS)} ",
                          category='danger')
                    return render_template('users/region_admin.html',
                                           compid=compid, region_select=region_select, new_region_form=new_region)

                wpt_format, wpts = get_turnpoints_from_file_storage(waypoint_file)

                if not wpts:
                    flash("Waypoint file format not supported or file is not a waypoint file", category='danger')
                    return render_template('users/region_admin.html',
                                           compid=compid, region_select=region_select, new_region_form=new_region)

                '''save file'''
                wpt_filename = unique_filename(waypoint_file.filename, WAYPOINTDIR)
                fullpath = Path(WAYPOINTDIR, wpt_filename)
                waypoint_file.seek(0)
                waypoint_file.save(fullpath)

                if airspace_file:
                    if not Path(AIRSPACEDIR).is_dir():
                        makedirs(AIRSPACEDIR)
                    '''check airspace file'''
                    number, air_filename, modified = frontendUtils.check_openair_file(airspace_file)
                    if number > 0:
                        if modified:
                            flash(f'openair file has been modified as it contains error, check result.', 'warning')
                        flash(Markup(f'Open air file added, {number} zones imported. Please check it <a href="'
                                     f'{url_for("user.airspace_edit", filename=air_filename)}" '
                                     f'class="alert-link">here</a>'), category='info')
                    else:
                        flash(f'ERROR importing openair file, check file format is correct and retry.', 'danger')

                '''write to DB'''
                region = Region(name=new_region.name.data, comp_id=compid, waypoint_file=wpt_filename,
                                openair_file=air_filename, turnpoints=wpts)
                region.to_db()
                flash(f"Waypoint file format: {wpt_format}, {len(wpts)} waypoints. ", category='info')
                flash(f"Region {new_region.name.data} added", category='info')

    return render_template('users/region_admin.html',
                           compid=compid, region_select=region_select, new_region_form=new_region)


@blueprint.route('/_delete_region/<int:regid>', methods=['POST'])
@login_required
@editor_required
def _delete_region(regid: int):
    from region import delete_region
    delete_region(regid)
    # flash text goes on the second next page refresh, instead of after deleting.
    flash(f"Region deleted", category='info')
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_get_non_and_registered_pilots/<compid>', methods=['GET', 'POST'])
@login_required
def _get_non_and_registered_pilots_internal(compid: int):
    registered_pilots, _, _ = frontendUtils.get_participants(compid, source='internal')
    non_registered_pilots = frontendUtils.get_non_registered_pilots(compid)
    return jsonify({'non_registered_pilots': non_registered_pilots, 'registered_pilots': registered_pilots})


@blueprint.route('/_get_non_and_registered_pilots/<int:compid>', methods=['GET', 'POST'])
@login_required
def _get_registered_pilots_external(compid: int):
    registered_pilots, _, _ = frontendUtils.get_participants(compid, source='external')
    return {'registered_pilots': registered_pilots}


@blueprint.route('/igc_parsing_config/<string:filename>', methods=['GET', 'POST'])
@login_required
def igc_parsing_config(filename: str):
    from trackUtils import read_igc_config_yaml, save_igc_config_yaml
    igc_config_form = IgcParsingConfigForm()
    filename += '.yaml'
    save = True
    config = read_igc_config_yaml(filename)
    if request.method == 'GET':
        if config is None:
            return render_template('404.html')
        igc_config_form.description.data = config['description']
        igc_config_form.min_fixes.data = config['min_fixes']
        igc_config_form.max_seconds_between_fixes.data = config['max_seconds_between_fixes']
        igc_config_form.min_seconds_between_fixes.data = config['min_seconds_between_fixes']
        igc_config_form.max_time_violations.data = config['max_time_violations']
        igc_config_form.max_new_days_in_flight.data = config['max_new_days_in_flight']
        igc_config_form.min_avg_abs_alt_change.data = config['min_avg_abs_alt_change']
        igc_config_form.max_alt_change_rate.data = config['max_alt_change_rate']
        igc_config_form.max_alt_change_violations.data = config['max_alt_change_violations']
        igc_config_form.max_alt.data = config['max_alt']
        igc_config_form.min_alt.data = config['min_alt']
        igc_config_form.min_gsp_flight.data = config['min_gsp_flight']
        igc_config_form.min_landing_time.data = config['min_landing_time']
        igc_config_form.which_flight_to_pick.data = config['which_flight_to_pick']
        igc_config_form.min_bearing_change_circling.data = config['min_bearing_change_circling']
        igc_config_form.min_time_for_bearing_change.data = config['min_time_for_bearing_change']
        igc_config_form.min_time_for_thermal.data = config['min_time_for_thermal']

        if current_user.username == config['owner']:
            save = True
    if request.method == 'POST':
        config['description'] = igc_config_form.description.data
        config['min_fixes'] = igc_config_form.min_fixes.data
        config['max_seconds_between_fixes'] = igc_config_form.max_seconds_between_fixes.data
        config['min_seconds_between_fixes'] = igc_config_form.min_seconds_between_fixes.data
        config['max_time_violations'] = igc_config_form.max_time_violations.data
        config['max_new_days_in_flight'] = igc_config_form.max_new_days_in_flight.data
        config['min_avg_abs_alt_change'] = float(igc_config_form.min_avg_abs_alt_change.data)
        config['max_alt_change_rate'] = igc_config_form.max_alt_change_rate.data
        config['max_alt_change_violations'] = igc_config_form.max_alt_change_violations.data
        config['max_alt'] = igc_config_form.max_alt.data
        config['min_alt'] = igc_config_form.min_alt.data
        config['min_gsp_flight'] = igc_config_form.min_gsp_flight.data
        config['min_landing_time'] = igc_config_form.min_landing_time.data
        config['which_flight_to_pick'] = igc_config_form.which_flight_to_pick.data
        config['min_bearing_change_circling'] = igc_config_form.min_bearing_change_circling.data
        config['min_time_for_bearing_change'] = igc_config_form.min_time_for_bearing_change.data
        config['min_time_for_thermal'] = igc_config_form.min_time_for_thermal.data
        config['owner'] = current_user.username
        if igc_config_form.save.data and current_user.username == config['owner']:
            save_igc_config_yaml(filename, config)
            flash("saved", category='info')
        if igc_config_form.save_as.data and igc_config_form.new_name.data:
            save_igc_config_yaml(igc_config_form.new_name.data + '.yaml', config)
            flash("saved as " + igc_config_form.new_name.data, category='info')
            return render_template('users/igc_parsing_settings.html', save=save, name=filename,
                                   description=config['description'], configform=igc_config_form)
    return render_template('users/igc_parsing_settings.html', save=save, name=filename[:-5],
                           description=config['description'], configform=igc_config_form)


@blueprint.route('/_del_igc_config/<string:filename>', methods=['POST'])
@login_required
def _del_igc_config(filename: str):
    from Defines import IGCPARSINGCONFIG
    filename += '.yaml'
    comps = frontendUtils.get_comps_with_igc_parsing(filename)
    if comps:
        flash(f"Unable to delete settings file as it is in use in the following comps:{comps}", category='danger')
    else:
        file = path.join(IGCPARSINGCONFIG, filename)
        if path.exists(file):
            remove(file)
    return "File Deleted"


@blueprint.route('/pilot_admin/<int:compid>', methods=['GET', 'POST'])
@login_required
@check_coherence
@check_editor
def pilot_admin(compid: int):
    """ Registered Pilots list
        Add / Edit Pilots"""
    from ranking import CompAttribute

    participant_form = ParticipantForm()
    comp = Comp.read(compid)

    participant_form.nat.choices = [(x['code'], x['name']) for x in frontendUtils.list_countries()]
    participant_form.certification.choices = [(x['cert_name'], x['cert_name'])
                                              for x in frontendUtils.get_certifications_details()[comp.comp_class]]

    attributes = CompAttribute.read_meta(compid)
    already_scored = frontendUtils.comp_has_taskresults(compid)

    if session['external']:
        '''External Event'''
        flash(f"This is an External Event. Settings and Results are Read Only.", category='warning')

    return render_template('users/pilot_admin.html', compid=compid, track_source=comp.track_source,
                           participant_form=participant_form, pilotdb=PILOT_DB, attributes=attributes,
                           already_scored=already_scored)


@blueprint.route('/_modify_participant_details/<int:parid>', methods=['POST'])
@login_required
@editor_required
def _modify_participant_details(parid: int):
    from pilot.participant import Participant, abbreviate

    form = ParticipantForm()

    if request.method == 'POST' and form.validate_on_submit():
        participant = Participant.read(parid)

        participant.ID = form.id_num.data
        participant.name = abbreviate(form.name.data)
        participant.birthdate = form.birthdate.data or None
        participant.civl_id = int(form.CIVL.data) if str(form.CIVL.data).isdigit() else None
        participant.sex = form.sex.data
        participant.nat = form.nat.data
        participant.glider = form.glider.data or None
        participant.glider_cert = form.certification.data or None
        participant.sponsor = abbreviate(form.sponsor.data) or None
        participant.nat_team = bool(form.nat_team.data)
        participant.team = form.team.data or None
        participant.live_id = form.live_id.data or None
        participant.xcontest_id = form.xcontest_id.data or None
        participant.status = form.status.data or None
        participant.paid = form.paid.data or None
        ''' Comp custom attributes'''
        for key, value in participant.custom.items():
            participant.custom[key] = request.form.get('attr_' + str(key)) or None
        participant.to_db()
        return jsonify(success=True)
    return jsonify(success=False, errors=form.errors)


@blueprint.route('/_add_participant/<int:compid>', methods=['POST'])
@login_required
@editor_required
def _add_participant(compid: int):
    from pilot.participant import Participant, assign_id, abbreviate

    form = ParticipantForm()

    if form.validate_on_submit():
        participant = Participant()
        participant.comp_id = compid
        participant.ID = assign_id(compid, given_id=form.id_num.data)
        participant.name = abbreviate(form.name.data)
        participant.birthdate = form.birthdate.data or None
        participant.civl_id = int(form.CIVL.data) if str(form.CIVL.data).isdigit() else None
        participant.sex = form.sex.data
        participant.nat = form.nat.data
        participant.glider = form.glider.data or None
        participant.glider_cert = form.certification.data or None
        participant.sponsor = abbreviate(form.sponsor.data) or None
        participant.nat_team = bool(form.nat_team.data)
        participant.team = form.team.data or None
        participant.live_id = form.live_id.data or None
        participant.xcontest_id = form.xcontest_id.data or None
        if form.status.data:
            participant.status = form.status.data
        if form.paid.data:
            participant.paid = form.paid.data
        ''' Comp custom attributes'''
        for key, value in {k: request.form.get(k) for k in request.form.keys() if 'attr_' in k}.items():
            participant.custom[int(key.split('_')[-1])] = value or None
        participant.to_db()
        return jsonify(success=True)
    return jsonify(success=False, errors=form.errors)


@blueprint.route('/_upload_participants_excel/<int:compid>', methods=['POST'])
@login_required
@editor_required
def _upload_participants_excel(compid: int):
    import tempfile

    if request.method == "POST" and "excel_file" in request.files:
        try:
            excel_file = request.files["excel_file"]
            if not excel_file:
                return jsonify(success=False, error='Error: not a valid excel file.')
            with tempfile.TemporaryDirectory() as tmpdirname:
                file_path = Path(tmpdirname, excel_file.filename)
                comp_class = session['comp_class']
                excel_file.save(file_path)
                return jsonify(frontendUtils.import_participants_from_excel_file(compid, file_path, comp_class))
        except (FileNotFoundError, TypeError, Exception):
            return jsonify(success=False, error='Internal error trying to parse excel file.')
    return jsonify(success=False, error='Error: no file was given.')


@blueprint.route('/_upload_participants_fsdb/<int:compid>', methods=['POST'])
@login_required
@editor_required
def _upload_participants_fsdb(compid: int):
    import tempfile

    if request.method == "POST" and "fsdb_file" in request.files:
        try:
            fsdb_file = request.files["fsdb_file"]
            if not fsdb_file:
                return jsonify(success=False, error='Error: not a valid FSDB file.')
            with tempfile.TemporaryDirectory() as tmpdirname:
                tmp_file = Path(tmpdirname, fsdb_file.filename)
                fsdb_file.save(tmp_file)
                return jsonify(frontendUtils.import_participants_from_fsdb(comp_id=compid, file=tmp_file))
        except (FileNotFoundError, TypeError, Exception):
            # raise
            return jsonify(success=False, error='Internal error trying to parse FSDB file.')
    return jsonify(success=False, error='Error: no file was given.')


@blueprint.route('/_self_register/<int:compid>', methods=['POST'])
@login_required
def _self_register(compid: int):
    from pilot.participant import Participant
    data = request.json
    participant = Participant.from_profile(data['pil_id'], comp_id=compid)
    participant.ID = data.get('id_num')
    participant.nat = data.get('nat')
    participant.glider = data.get('glider')
    participant.glider_cert = data.get('certification')
    participant.sponsor = data.get('sponsor')
    participant.to_db()
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_unregister_participant/<int:compid>', methods=['POST'])
@login_required
@editor_required
def _unregister_participant(compid: int):
    """unregister participant from a comp"""
    from pilot.participant import unregister_participant
    data = request.json
    unregister_participant(compid, data['participant'])
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_unregister_all_external_participants/<int:compid>', methods=['POST'])
@login_required
@editor_required
def _unregister_all_external_participants(compid: int):
    """unregister participant from a comp"""
    from pilot.participant import unregister_all_external_participants
    resp = unregister_all_external_participants(compid)
    return jsonify(success=resp)


@blueprint.route('/_check_nat_team_size/<int:compid>', methods=['GET'])
@login_required
def _check_nat_team_size(compid: int):
    return {'message': frontendUtils.check_team_size(compid, nat=True)}


@blueprint.route('/_check_team_size/<int:compid>', methods=['GET'])
@login_required
def _check_team_size(compid: int):
    return {'message': frontendUtils.check_team_size(compid)}


@blueprint.route('/_adjust_task_result/<int:taskid>', methods=['POST'])
@login_required
def _adjust_task_result(taskid: int):
    data = request.json
    par_id = int(data['par_id'])
    resp = frontendUtils.adjust_task_result(taskid, data['filename'], par_id, data['notifications'])

    return jsonify(success=resp)


@blueprint.route('/_export_fsdb/<int:compid>', methods=['GET'])
@login_required
def _export_fsdb(compid: int):
    from fsdb import FSDB
    import tempfile
    comp_fsdb = FSDB.create(compid)
    if not comp_fsdb:
        '''comp has not been scored yet'''
        flash("Comp has not been scored yet. Aborting FSDB file creation.", category='danger')
        return redirect(f'/users/comp_settings_admin/{compid}')
    filename, data = comp_fsdb.to_file()
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(data)
        resp = make_response(send_file(tmp.name, mimetype="text/xml", attachment_filename=filename, as_attachment=True))
        resp.set_cookie('ServerProcessCompleteChecker', '', expires=0)
        return resp


@blueprint.route('/_add_user/', methods=['POST'])
@login_required
@manager_required
def add_user():
    """Register a new user (admin, scorekeeper."""
    # from email import send_email
    data = request.json
    form = UserForm()
    if form.validate_on_submit():
        '''create user entry in database'''
        user = User(
            username=form.email.data,
            email=form.email.data,
            password=frontendUtils.generate_random_password(),  # create a temporary password
            active=False,
            access=form.access.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            nat=form.nat.data
        )

        email_copy = bool(request.form.get('email_copy'))
        '''send registration email'''
        token = frontendUtils.generate_confirmation_token(user.email)
        confirm_url = url_for('public.confirm_user', token=token, _external=True)
        html = render_template('email/register.html', user=user, confirm_url=confirm_url)
        body = render_template('email/register.txt', user=user, confirm_url=confirm_url)
        subject = "[AirScore Registration] Please confirm your email"
        recipients = [user.email] if not email_copy else [user.email, current_user.email]
        resp, error = frontendUtils.send_email(recipients=recipients, subject=subject, text_body=body, html_body=html)
        if resp:
            user.save()
            return jsonify(success=True)
        else:
            return jsonify(success=False, mail_error=error)
    return jsonify(success=False, errors=form.errors)


@blueprint.route('/_modify_user/<int:user_id>', methods=['POST'])
@login_required
@manager_required
def _modify_user(user_id: int):
    form = UserForm()
    if request.method == 'POST' and form.validate_on_edit(user_id):
        user = User.query.filter_by(id=user_id).first()
        for x in user.__table__.columns.keys():
            if hasattr(form, x):
                setattr(user, x, getattr(form, x).data)
        user.update()
        return jsonify(success=True)
    return jsonify(success=False, errors=form.errors)


@blueprint.route('/_download/<string:filetype>/<filename>', methods=['GET', 'POST'])
@login_required
def _download_file(filetype: str, filename):
    if 'html' in filetype:
        if filetype == 'participants_html':
            comp_id = int(filename)
            name, content = frontendUtils.create_participants_html(comp_id)
        elif filetype == 'task_html':
            name, content = frontendUtils.create_task_html(filename)
        elif filetype == 'comp_html':
            comp_id = int(filename)
            name, content = frontendUtils.create_comp_html(comp_id)
        else:
            return render_template('500.html')

        if isinstance(content, list):
            ''' we need to create a zip file with multiple result files'''
            for el in content:
                el['content'] = frontendUtils.render_html_file(el['content'])
            file = frontendUtils.create_inmemory_zipfile(content)
            mimetype = "application/zip"
        else:
            file = frontendUtils.render_html_file(content)
            mimetype = "text/html"

    elif 'fsdb' in filetype:
        comp_id = int(filename)
        name, file = frontendUtils.create_participants_fsdb(comp_id)
        mimetype = "text/xml"
    else:
        return render_template('500.html')
    mem = frontendUtils.create_stream_content(file)
    resp = make_response(send_file(mem, mimetype=mimetype, attachment_filename=name,
                                   as_attachment=True, cache_timeout=0))
    resp.set_cookie('ServerProcessCompleteChecker', '', expires=0)
    return resp


@blueprint.route('/_get_comp_rankings/<int:compid>', methods=['GET'])
@login_required
def _get_comp_rankings(compid: int):
    return jsonify({'data': frontendUtils.get_comp_rankings(compid)})


@blueprint.route('/_modify_comp_ranking/<int:cranid>', methods=['POST'])
@login_required
def _modify_comp_ranking(cranid: int):
    from ranking import CompRanking
    from result import update_results_rankings

    form = CompRankingForm()

    if request.method == 'POST' and form.validate_on_submit():
        rank = CompRanking.read(cranid)

        rank.rank_name = form.rank_name.data
        rank.rank_type = form.rank_type.data
        rank.cert_id = form.cert_id.data or None
        rank.min_date = form.min_date.data if rank.rank_type == 'birthdate' else None
        rank.max_date = form.max_date.data if rank.rank_type == 'birthdate' else None
        rank.attr_id = form.attr_id.data if rank.rank_type == 'custom' else None
        rank.rank_value = form.rank_value.data or None
        rank.to_db()
        update_results_rankings(comp_id=session['compid'])
        return jsonify(success=True)
    return jsonify(success=False, errors=form.errors)


@blueprint.route('/_add_comp_ranking/<int:compid>', methods=['POST'])
@login_required
@editor_required
def _add_comp_ranking(compid: int):
    from ranking import CompRanking
    from result import update_results_rankings

    form = CompRankingForm()

    if request.method == 'POST' and form.validate_on_submit():
        rank = CompRanking(comp_id=compid)

        rank.rank_name = form.rank_name.data
        rank.rank_type = form.rank_type.data
        rank.cert_id = form.cert_id.data or None
        rank.min_date = form.min_date.data if rank.rank_type == 'birthdate' else None
        rank.max_date = form.max_date.data if rank.rank_type == 'birthdate' else None
        rank.attr_id = form.attr_id.data if rank.rank_type == 'custom' else None
        rank.rank_value = form.rank_value.data or None
        rank.to_db()
        update_results_rankings(comp_id=compid)
        return jsonify(success=True)
    return jsonify(success=False, errors=form.errors)


@blueprint.route('/_get_custom_attributes/<int:compid>', methods=['GET', 'POST'])
@login_required
def _get_custom_attributes(compid: int):
    return jsonify(frontendUtils.get_comp_meta(compid))


@blueprint.route('/_add_custom_attribute/<int:compid>', methods=['GET', 'POST'])
@login_required
@editor_required
def _add_custom_attribute(compid: int):
    data = request.json
    return jsonify(success=bool(frontendUtils.add_custom_attribute(compid, data['attr_value'])))


@blueprint.route('/_edit_custom_attribute/<int:attrid>', methods=['GET', 'POST'])
@login_required
def _edit_custom_attribute(attrid: int):
    data = request.json
    return jsonify(success=bool(frontendUtils.edit_custom_attribute(data)))


@blueprint.route('/_remove_custom_attribute/<int:attrid>', methods=['GET', 'POST'])
@login_required
@editor_required
def _remove_custom_attribute(attrid: int):
    return jsonify(success=bool(frontendUtils.remove_custom_attribute(attrid)))


@blueprint.route('/_delete_ranking/<int:rankid>', methods=['GET', 'POST'])
@login_required
@editor_required
def _delete_ranking(rankid: int):
    from ranking import delete_ranking
    return jsonify(success=delete_ranking(session['compid'], rankid))


@blueprint.route('/_get_lt_info/<int:taskid>', methods=['GET', 'POST'])
@login_required
def _get_lt_info(taskid: int):
    from Defines import LIVETRACKDIR
    from result import open_json_file
    from calcUtils import epoch_to_string

    started = False
    timestamp = None
    scheduled = False
    finished = False
    error = False
    q = current_app.task_queue
    sched = q.scheduled_job_registry
    ended = q.finished_job_registry
    failed = q.failed_job_registry
    job_id = f'livetracking_task_{taskid}'

    '''check if LT started'''
    if Path(LIVETRACKDIR, f'{taskid}').is_file():
        started = True
        data = open_json_file(Path(LIVETRACKDIR, f'{taskid}'))
        timestamp = epoch_to_string(data['file_stats']['timestamp'])
        finished = 'terminated' in data['file_stats']['status']

        '''check if LT is scheduled'''
        if any(el.endswith(job_id) for el in sched.get_job_ids()):
            # sjob = q.fetch(next(el.endswith(job_id) for el in sched.get_job_ids()))
            sjob_id = next(el for el in sched.get_job_ids() if el.endswith(job_id))
            scheduled = sched.get_scheduled_time(sjob_id)
        elif any(el.endswith(job_id) for el in failed.get_job_ids()):
            sjob = q.fetch(next(el for el in failed.get_job_ids() if el.endswith(job_id)))
            error = sjob.exc_info.strip().split('\n')[-1]

    resp = {
        'success': started and (scheduled or finished),
        'status': dict(updated=timestamp, scheduled=scheduled, finished=finished),
        'error': error,
        'registry': {
            'finished': [el for el in ended.get_job_ids() if el.endswith(job_id)],
            'failed': [el for el in failed.get_job_ids() if el.endswith(job_id)],
            'scheduled': [f"{el}: {sched.get_scheduled_time(el)}" for el in sched.get_job_ids() if el.endswith(job_id)]
        }
    }

    return jsonify(resp)


@blueprint.route('/_start_task_livetracking/<int:taskid>', methods=['GET', 'POST'])
@login_required
def start_task_livetracking(taskid: int):

    job = frontendUtils.start_livetracking(taskid, username=current_user.username)
    scheduled = False
    error = None
    status = None
    resp = None
    if job:
        j = current_app.task_queue.fetch_job(job.id)
        status = j.get_status()

        if job.is_failed:
            error = job.exc_info.strip().split('\n')[-1]
    else:
        error = f'Error trying to start LT service, job_id={job.id}'
    return jsonify(success=bool(job.id and resp), job_id=job.id, error=error, status=status, status2=resp, scheduled=scheduled)
