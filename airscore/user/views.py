# -*- coding: utf-8 -*-
"""User views."""
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, json, flash, redirect, url_for, session, Markup, \
    current_app, send_file, make_response
from flask_login import login_required, current_user
import frontendUtils
from airscore.user.forms import NewTaskForm, CompForm, TaskForm, NewTurnpointForm, ModifyTurnpointForm, \
    TaskResultAdminForm, NewScorekeeperForm, RegionForm, NewRegionForm, IgcParsingConfigForm, ModifyParticipantForm, \
    EditScoreForm, ModifyUserForm, CompLaddersForm
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
from Defines import SELF_REG_DEFAULT, PILOT_DB, LADDERS
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
        if not session['is_admin']:
            return current_app.login_manager.unauthorized()
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
            return render_template('users/comp_admin.html')
        return func(*args, **kwargs)

    return decorated_function


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
                f"{space['floor_description']} is {int(space['floor']) * 100} ft or {int(space['floor']) * 100 * 0.3048} m ")
            space['floor'] = None

        if space["ceiling_unit"] == "FL":
            fl_messages.append(
                f"{space['ceiling_description']} is {int(space['ceiling']) * 100} ft or {int(space['ceiling']) * 100 * 0.3048} m ")
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
    return render_template('users/comp_admin.html', today=datetime.today().strftime('%Y-%m-%d'))


@blueprint.route('/_create_comp', methods=['PUT'])
@login_required
def _create_comp():
    import compUtils
    data = request.json
    date_from = datetime.strptime(data['datefrom'], '%Y-%m-%d')
    date_to = datetime.strptime(data['dateto'], '%Y-%m-%d')
    if date_to < date_from:
        flash("Start date cannot be after end date. Competition not saved", category='danger')
        return dict(redirect='/users/comp_admin')
    if not frontendUtils.check_short_code(data['code']):
        flash("Short name already in use. Competition not saved", category='danger')
        return dict(redirect='/users/comp_admin')

    new_comp = Comp(comp_name=data['name'],
                    comp_class=data['class'],
                    comp_site=data['location'],
                    comp_code=data['code'],
                    date_from=date_from,
                    date_to=date_to)
    new_comp.comp_path = compUtils.create_comp_path(date_from, data['code'])
    output = new_comp.to_db()
    if type(output) == int:
        Formula(comp_id=output).to_db()
        frontendUtils.set_comp_scorekeeper(output, current_user.id, owner=True)
        return dict(redirect='/users/comp_admin')
    else:
        return render_template('500.html')


@blueprint.route('/_import_comp_fsdb/', methods=['POST'])
@login_required
def _import_comp_fsdb():
    from fsdb import FSDB
    if request.method == "POST":
        if request.files:

            if "filesize" in request.cookies:

                if not frontendUtils.allowed_tracklog_filesize(request.cookies["filesize"]):
                    print("Filesize exceeded maximum limit")
                    return redirect(request.url)

            fsdb_file = request.files["fsdb_file"]

            if fsdb_file.filename == "":
                print("No filename")
                return redirect(request.url)
            if frontendUtils.allowed_tracklog(fsdb_file.filename, extension=['fsdb', 'xml']):
                f = FSDB.read(fsdb_file)
                compid = f.add_all()
                if compid:
                    frontendUtils.set_comp_scorekeeper(compid, current_user.id, owner=True)
                    resp = jsonify(success=True)
                    return resp
                else:
                    return render_template('500.html')

            else:
                print("That file extension is not allowed")
                return redirect(request.url)


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
    comp = Comp.read(compid)
    # set session variables for navbar
    session['compid'] = compid
    session['comp_name'] = comp.comp_name
    session['external'] = comp.external

    compform.igc_parsing_file.choices, _ = frontendUtils.get_igc_parsing_config_file_list()
    owner, scorekeepers, scorekeeper_ids = frontendUtils.get_comp_scorekeeper(compid)
    all_scorekeepers = frontendUtils.get_all_scorekeepers()
    all_scorekeepers.remove(owner)
    for scorekeeper in scorekeepers:
        all_scorekeepers.remove(scorekeeper)
    scorekeeper_choices = []
    if all_scorekeepers:
        for scorekeeper in all_scorekeepers:
            scorekeeper_choices.append((scorekeeper['id'],
                                        f"{scorekeeper['first_name']} {scorekeeper['last_name']} ({scorekeeper['username']})"))

    if request.method == 'POST':
        if compform.validate_on_submit():
            comp.comp_name = compform.comp_name.data
            comp.comp_code = compform.comp_code.data
            comp.sanction = compform.sanction.data
            comp.comp_type = compform.comp_type.data
            comp.comp_class = compform.comp_class.data
            comp.comp_site = compform.comp_site.data
            comp.date_from = compform.date_from.data
            comp.date_to = compform.date_to.data
            comp.MD_name = compform.MD_name.data
            comp.cat_id = compform.cat_id.data
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
            formula.score_back_time = int((compform.scoreback_time.data or 0) * 60)
            formula.JTG_penalty_per_sec = compform.JTG_penalty_per_sec.data
            formula.scoring_altitude = compform.scoring_altitude.data
            formula.team_scoring = compform.team_scoring.data
            formula.team_size = compform.team_size.data
            formula.max_team_size = compform.max_team_size.data
            formula.country_scoring = compform.country_scoring.data
            formula.country_size = compform.country_size.data
            formula.max_country_size = compform.max_country_size.data
            formula.team_over = compform.team_over.data
            formula.to_db()

            flash(f"{compform.comp_name.data} saved", category='info')
            return redirect(url_for('user.comp_settings_admin', compid=compid))
        else:
            for item in compform:
                if item.errors:
                    flash(f"{item.label.text}: {', '.join(x for x in item.errors)}", category='danger')
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
        compform.cat_id.data = comp.cat_id
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
        compform.lead_factor.data = formula.lead_factor or 1
        compform.formula_time.data = formula.formula_time
        compform.no_goal_penalty.data = int(formula.no_goal_penalty * 100)
        compform.glide_bonus.data = formula.glide_bonus
        compform.tolerance.data = formula.tolerance * 100
        compform.min_tolerance.data = formula.min_tolerance
        compform.arr_alt_bonus.data = formula.arr_alt_bonus
        compform.arr_max_height.data = formula.arr_max_height
        compform.arr_min_height.data = formula.arr_min_height
        compform.validity_min_time.data = int((formula.validity_min_time or 0) / 60)
        compform.scoreback_time.data = int((formula.score_back_time or 0) / 60)
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
        newScorekeeperform.scorekeeper.choices = scorekeeper_choices
        formulas = list_formulas()
        compform.formula.choices = [(x, x.upper()) for x in formulas[comp.comp_class]]

        if (current_user.id not in scorekeeper_ids) and (current_user.access != 'admin'):
            session['is_scorekeeper'] = False
            compform.submit = None
        else:
            session['is_scorekeeper'] = True

    ''' Ladders if active in settings'''
    if LADDERS:
        ladderform = CompLaddersForm()
        ladderform.ladders.choices = [(el['ladder_id'], el['ladder_name'])
                                      for el in frontendUtils.list_ladders(comp.date_to, comp.comp_class)]
        comp_ladders = frontendUtils.get_comp_ladders(compid)
        ladderform.ladders.data = comp_ladders
    else:
        ladderform = None

    tasks = frontendUtils.get_task_list(comp)
    classifications = frontendUtils.get_classifications_details()
    session['tasks'] = tasks['tasks']
    session['check_g_record'] = comp.check_g_record
    session['track_source'] = comp.track_source

    if not compform.formula.data:
        '''Comp has not been initialised yet'''
        flash(f"Comp has not been properly set yet. Check all parameters and save.", category='warning')
    if comp.external:
        '''External Event'''
        flash(f"This is an External Event. Settings and Results are Read Only.", category='warning')

    return render_template('users/comp_settings.html', compid=compid, compform=compform,
                           taskform=newtaskform, scorekeeperform=newScorekeeperform, ladderform=ladderform,
                           classifications=classifications, error=error,
                           self_register=(SELF_REG_DEFAULT and PILOT_DB))


@blueprint.route('/_get_scorekeepers/<int:compid>', methods=['GET'])
@login_required
def _get_scorekeepers(compid: int):
    owner, scorekeepers, _ = frontendUtils.get_comp_scorekeeper(compid)
    return {'owner': owner, 'scorekeepers': scorekeepers}


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
@admin_required
def _get_users():
    return {'data': frontendUtils.get_all_users()}


@blueprint.route('/user_admin', methods=['GET'])
@login_required
@admin_required
def user_admin():
    from Defines import ADMIN_DB
    modify_user_form = ModifyUserForm()
    return render_template('users/user_admin.html', modify_user_form=modify_user_form, editable=bool(ADMIN_DB))


@blueprint.route('/_add_scorekeeper/<int:compid>', methods=['POST'])
@login_required
def _add_scorekeeper(compid: int):
    data = request.json
    if frontendUtils.set_comp_scorekeeper(compid, data['id']):
        resp = jsonify(success=True)
        return resp
    else:
        return render_template('500.html')


@blueprint.route('/task_admin/<int:taskid>', methods=['GET', 'POST'])
@login_required
@check_coherence
def task_admin(taskid: int):
    from calcUtils import sec_to_time, time_to_seconds
    from region import get_openair
    error = None
    taskform = TaskForm()
    turnpointform = NewTurnpointForm()
    modifyturnpointform = ModifyTurnpointForm()

    task = Task.read(taskid)
    taskform.region.choices.extend(frontendUtils.get_region_choices(session['compid'])[0])
    waypoints, _ = frontendUtils.get_waypoint_choices(task.reg_id)
    turnpointform.name.choices = waypoints
    modifyturnpointform.mod_name.choices = waypoints

    owner, scorekeepers, all_scorekeeper_ids = frontendUtils.get_comp_scorekeeper(task.comp_id)

    if request.method == 'POST':
        if taskform.validate_on_submit():
            task.comp_name = taskform.comp_name
            task.task_name = taskform.task_name.data
            task.task_num = taskform.task_num.data
            task.comment = taskform.comment.data
            task.date = taskform.date.data
            task.task_type = taskform.task_type.data
            task.reg_id = taskform.region.data if taskform.region.data not in (0, '', None) else None
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

            for session_task in session['tasks']:
                if session_task['task_id'] == taskid:
                    if (task.opt_dist and task.window_open_time and task.window_close_time and task.start_time and
                            task.start_close_time and task.task_deadline):
                        session_task['ready_to_score'] = True

            flash("Saved", category='info')

            return redirect(url_for('user.task_admin', taskid=taskid))

        else:
            for item in taskform:
                if item.errors:
                    flash(f"{item.label.text} ({item.data}, {type(item.data)}): {', '.join(x for x in item.errors)}", category='danger')

    if request.method == 'GET':
        offset = task.time_offset if task.time_offset else 0
        taskform.comp_name = task.comp_name
        taskform.task_name.data = task.task_name
        taskform.task_num.data = task.task_num
        taskform.comment.data = task.comment
        taskform.date.data = task.date
        taskform.task_type.data = task.task_type
        taskform.region.data = task.reg_id or 0
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

        if not (task.opt_dist and task.window_open_time and task.window_close_time and task.start_time and
                task.start_close_time and task.task_deadline):
            flash("Task is not ready to be scored as it is missing one or more of the following: a route with goal, "
                  "window open/close, start/close and deadline times", category='info')
            for session_task in session['tasks']:
                if session_task['task_id'] == taskid:
                    session_task['ready_to_score'] = False

        if current_user.id not in all_scorekeeper_ids:
            taskform.submit = None
        if session['external']:
            '''External Event'''
            flash(f"This is an External Event. Settings and Results are Read Only.", category='warning')

    return render_template('users/task_admin.html', taskid=taskid, taskform=taskform, turnpointform=turnpointform,
                           modifyturnpointform=modifyturnpointform, compid=task.comp_id, error=error)


@blueprint.route('/_get_admin_comps', methods=['GET'])
@login_required
def _get_admin_comps():
    return frontendUtils.get_admin_comps(current_user.id, current_user.access)


@blueprint.route('/_delete_comp/<int:compid>', methods=['POST', 'GET'])
@login_required
def _delete_comp(compid: int):
    from comp import delete_comp
    owner, _, _ = frontendUtils.get_comp_scorekeeper(compid)
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
def _add_task(compid: int):
    from region import get_openair
    comp = Comp.read(compid)
    data = request.json
    task = Task(comp_id=compid)
    task.task_name = data['task_name']
    task.task_num = int(data['task_num'])
    task.date = datetime.strptime(data['task_date'], '%Y-%m-%d')
    task.comment = data['task_comment']
    task.reg_id = int(data['task_region'])
    task.time_offset = comp.time_offset
    task.airspace_check = comp.airspace_check
    if task.airspace_check and task.reg_id:
        task.openair_file = get_openair(reg_id=task.reg_id)
    task.check_launch = comp.check_launch
    task.igc_config_file = comp.igc_config_file
    task.to_db()
    tasks = frontendUtils.get_task_list(comp)
    session['tasks'] = tasks['tasks']
    return tasks


@blueprint.route('/_del_task/<int:taskid>', methods=['POST'])
@login_required
def _del_task(taskid: int):
    from task import delete_task
    delete_task(taskid)
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_get_tasks/<int:compid>', methods=['GET'])
@login_required
def _get_tasks(compid: int):
    comp = Comp()
    comp.comp_id = compid
    tasks = frontendUtils.get_task_list(comp)
    return tasks


@blueprint.route('/_get_adv_settings', methods=['GET', 'POST'])
@login_required
def _get_adv_settings():
    data = request.json
    formula = Formula.from_preset(data['category'], data['formula'])
    settings = {'formula_distance': formula.formula_distance, 'formula_arrival': formula.formula_arrival,
                'formula_departure': formula.formula_departure, 'lead_factor': formula.lead_factor,
                'formula_time': formula.formula_time, 'no_goal_penalty': formula.no_goal_penalty * 100,
                'glide_bonus': formula.glide_bonus, 'tolerance': formula.tolerance * 100,
                'min_tolerance': formula.min_tolerance, 'arr_alt_bonus': formula.height_bonus,
                'arr_max_height': formula.arr_max_height, 'arr_min_height': formula.arr_min_height,
                'validity_min_time': int(formula.validity_min_time / 60),
                'scoreback_time': int(formula.score_back_time / 60),
                'max_JTG': formula.max_JTG, 'JTG_penalty_per_sec': formula.JTG_penalty_per_sec}

    return settings


@blueprint.route('/_get_task_turnpoints/<int:taskid>', methods=['GET'])
@login_required
def _get_task_turnpoints(taskid: int):
    task = Task.read(taskid)
    if (task.opt_dist and task.window_open_time and task.window_close_time
            and task.start_time and task.start_close_time and task.task_deadline):
        ready_to_score = True
    else:
        ready_to_score = False
    for session_task in session['tasks']:
        if session_task['task_id'] == taskid:
            if session_task['ready_to_score'] != ready_to_score:
                session_task['ready_to_score'] = ready_to_score
                return {'reload': True}

    turnpoints = frontendUtils.get_task_turnpoints(task)
    return turnpoints


@blueprint.route('/_add_turnpoint/<int:taskid>', methods=['POST'])
@login_required
def _add_turnpoint(taskid: int):
    """add turnpoint to the task,if rwp_id is not null then update instead of insert (add)
    if turnpoint is goal or we are updating and goal exists then calculate opt dist and dist."""
    from frontendUtils import get_waypoint
    data = request.json
    rwp_id = None if not data['rwp_id'] else int(data['rwp_id'])
    if data['wpt_id']:
        '''modify waypoint'''
        wpt_id = int(data['wpt_id'])
        if rwp_id:
            '''changing wpt'''
            tp = get_waypoint(rwp_id=rwp_id)
            tp.wpt_id = wpt_id
            tp.task_id = taskid
        else:
            tp = get_waypoint(wpt_id=wpt_id)
    else:
        '''add waypoint'''
        tp = get_waypoint(rwp_id=rwp_id)
        tp.task_id = taskid
    tp.num = int(data['number'])
    tp.radius = int(data['radius'])
    tp.type = data['type']
    if data['direction'] is not None:
        tp.how = data['direction']
    if data['shape'] is not None:
        if data['type'] != 'goal':
            tp.shape = 'circle'
        else:
            tp.shape = data['shape']
    if save_turnpoint(taskid, tp):
        task = Task.read(taskid)
        if task.opt_dist or data['type'] == 'goal':
            task.calculate_optimised_task_length()
            task.calculate_task_length()
            task.update_task_distance()
            write_map_json(taskid)
        turnpoints = frontendUtils.get_task_turnpoints(task)
        return turnpoints
    else:
        return render_template('500.html')


@blueprint.route('/_del_turnpoint/<tpid>', methods=['POST'])
@login_required
def _del_turnpoint(tpid):
    """delete a turnpoint from the task"""
    from route import delete_turnpoint
    data = request.json
    taskid = int(data['taskid'])
    delete_turnpoint(tpid)
    print(f"{data['partial_distance']}")
    if data['partial_distance'] != '':
        task = Task.read(taskid)
        if task.turnpoints[-1].type == 'goal':
            task.calculate_optimised_task_length()
            task.calculate_task_length()
            task.update_task_distance()
            write_map_json(taskid)
        else:
            task.delete_task_distance()
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_del_all_turnpoints/<int:taskid>', methods=['POST'])
@login_required
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


@blueprint.route('/_get_tracks_admin/<int:taskid>', methods=['GET'])
@login_required
def _get_tracks_admin(taskid: int):
    return {'data': frontendUtils.get_pilot_list_for_track_management(taskid)}


@blueprint.route('/_get_tracks_processed/<int:taskid>', methods=['GET'])
@login_required
def _get_tracks_processed(taskid: int):
    tracks, pilots = frontendUtils.number_of_tracks_processed(taskid)
    return {'tracks': tracks, 'pilots': pilots}


@blueprint.route('/track_admin/<int:taskid>', methods=['GET'])
@login_required
@check_coherence
def track_admin(taskid: int):
    from Defines import TELEGRAM
    task = next((t for t in session['tasks'] if t['task_id'] == taskid), None)
    task_num = task['task_num']
    task_name = task['task_name']
    task_ready_to_score = task['ready_to_score']
    track_source = task['track_source']
    compid = int(session['compid'])

    if not task_ready_to_score:
        return render_template('task_not_ready_to_score.html')

    _, _, all_scorekeeper_ids = frontendUtils.get_comp_scorekeeper(taskid, task_id=True)
    if current_user.id in all_scorekeeper_ids:
        user_is_scorekeeper = True
    else:
        user_is_scorekeeper = None
    return render_template('users/track_admin.html', taskid=taskid, compid=compid,
                           user_is_scorekeeper=user_is_scorekeeper, production=frontendUtils.production(),
                           task_name=task_name, task_num=task_num, track_source=track_source, telegram=TELEGRAM)


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
def _upload_track(taskid: int, parid: int):
    if request.method == "POST":
        if request.files:
            if "filesize" in request.cookies:
                if not frontendUtils.allowed_tracklog_filesize(request.cookies["filesize"]):
                    print("Filesize exceeded maximum limit")
                    return redirect(request.url)
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
                    return redirect(request.url)

                if frontendUtils.allowed_tracklog(tracklog.filename):
                    if frontendUtils.production():
                        file = frontendUtils.save_igc_background(taskid, parid, tracklog,
                                                                 current_user.username,
                                                                 check_g_record=check_g_record)
                        job = current_app.task_queue.enqueue(frontendUtils.process_igc_background,
                                                             taskid, parid, file, current_user.username, check_validity)
                        if not file:
                            resp = jsonify(success=False)
                        else:
                            resp = jsonify(success=True)
                        return resp
                    else:
                        data, error = frontendUtils.process_igc(taskid, parid, tracklog)
                        if data:
                            resp = jsonify(data)
                            return resp
                        else:
                            error = tracklog.filename + ' ' + error
                            resp = jsonify({'error': error})
                            return resp
                else:
                    print("That file extension is not allowed")
                    return redirect(request.url)
            resp = {'error': 'filesize not sent'}
            return resp
        resp = {'error': 'request.files'}
        return resp


@blueprint.route('/_get_xcontest_tracks/<int:taskid>', methods=['POST'])
@login_required
def _get_xcontest_tracks(taskid: int):
    from sources.xcontest import get_zipfile
    if request.method == "POST":
        zip_file = get_zipfile(taskid)

        if not zip_file:
            print("No filename")
            flash("We could not find tracks on XContest for the event", category='danger')
            return redirect(request.url)

        resp = frontendUtils.process_zip_file(zip_file=zip_file,
                                              taskid=taskid,
                                              username=current_user.username,
                                              grecord=session['check_g_record'],
                                              track_source='xcontest')
        return resp


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
            task.calculate_task_length()
            task.update_task_info()
            task.turnpoints_to_db()
            task.to_db()
            write_map_json(taskid)

            resp = jsonify(success=True)
            return resp


@blueprint.route('/_upload_track_zip/<int:taskid>', methods=['POST'])
@login_required
def _upload_track_zip(taskid: int):
    if request.method == "POST":
        if request.files:
            if "filesize" in request.cookies:
                if not frontendUtils.allowed_tracklog_filesize(request.cookies["filesize"], size=50):
                    print("Filesize exceeded maximum limit")
                    return redirect(request.url)
                zip_file = request.files["zip_file"]
                if zip_file.filename == "":
                    print("No filename")
                    return redirect(request.url)

                if frontendUtils.allowed_tracklog(zip_file.filename, extension=['zip']):
                    resp = frontendUtils.process_zip_file(zip_file=zip_file,
                                                          taskid=taskid,
                                                          username=current_user.username,
                                                          grecord=session['check_g_record'])
                    return resp
                else:
                    print("That file extension is not allowed")
                    return redirect(request.url)
            resp = {'error': 'filesize'}
            return resp
        resp = {'error': 'request.files'}
        return resp


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
        if status not in ['dnf', 'abs', 'nyp']:
            pilot = {'rank': rank, 'name': f'<a href="/map/{parid}-{taskid}?back_link=0" target="_blank">{name}</a>'}
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

            pilot['altbonus'] = ""  # altitude bonus
            pilot['distance'] = round(r['distance'] / 1000, 2)
            pilot['speedP'] = c_round(r['time_score'], 2)
            pilot['leadP'] = c_round(r['departure_score'], 2)
            pilot['arrivalP'] = c_round(r['arrival_score'], 2)  # arrival points
            pilot['distanceP'] = c_round(r['distance_score'], 2)
            pilot['penalty'] = c_round(r['penalty'], 2) if r['penalty'] else ""
            pilot['score'] = c_round(r['score'], 2)

        else:
            pilot = dict(rank=rank, name=name, SSS='', ESS='', time='', altbonus='', distance='',
                         speedP='', leadP='', arrivalP='', distanceP='', penalty='', score=status)
        # TODO once result files have a list of comments we can activate these lines and remove the 3 dummy lines below
        # pilot['Track_Comment'] = r['comment'][0]
        # pilot['Penalty_Comment'] = r['comment'][1]
        # pilot['Admin_Comment'] = r['comment'][2]
        # pilot['Track Comment'] = 'test track comment'
        # pilot['Penalty Comment'] = 'test penalt comment'
        # pilot['Admin Comment'] = 'test admin comment'
        pilot['par_id'] = r['par_id']
        pilot['notifications'] = r['notifications']
        all_pilots.append(pilot)
        rank += 1

    return {'data': all_pilots, 'stats': stats, 'info': info}


@blueprint.route('/task_score_admin/<int:taskid>', methods=['GET'])
@login_required
@check_coherence
def task_score_admin(taskid: int):
    task = next((el for el in session['tasks'] if el['task_id'] == taskid), None)
    task_num = task['task_num']
    task_name = task['task_name']
    task_ready_to_score = task['ready_to_score']
    compid = int(session['compid'])

    if not task_ready_to_score:
        return render_template('task_not_ready_to_score.html')

    fileform = TaskResultAdminForm()
    editform = EditScoreForm()
    active_file = None
    choices = [(1, 1), (2, 2)]
    fileform.result_file.choices = choices
    if active_file:
        fileform.result_file.data = active_file
    _, _, all_scorekeeper_ids = frontendUtils.get_comp_scorekeeper(taskid, task_id=True)
    if current_user.id in all_scorekeeper_ids:
        user_is_scorekeeper = True
    else:
        user_is_scorekeeper = None

    if session['external']:
        '''External Event'''
        flash(f"This is an External Event. Settings and Results are Read Only.", category='warning')

    return render_template('users/task_score_admin.html', fileform=fileform, taskid=taskid, compid=compid,
                           active_file=active_file, user_is_scorekeeper=user_is_scorekeeper, task_name=task_name,
                           task_num=task_num, editform=editform, production=frontendUtils.production())


@blueprint.route('/_score_task/<int:taskid>', methods=['POST'])
@login_required
def _score_task(taskid: int):
    if request.method == "POST":
        """score task, request data should contain status: the score status (provisional, official etc),
        autopublish: True or False. indicates if to publish results automatically after scoring"""
        data = request.json
        task = Task.read(taskid)

        if frontendUtils.production() and task.stopped_time:
            job = current_app.task_queue.enqueue(frontendUtils.full_rescore, taskid, background=True,
                                                 user=current_user.username, status=data['status'],
                                                 autopublish=data['autopublish'], compid=session['compid'],
                                                 job_timeout=2000)

            resp = jsonify(success=True, background=True)
            return resp
        ref_id, filename = task.create_results(data['status'])
        if ref_id:
            if data['autopublish']:
                frontendUtils.publish_task_result(taskid, filename)
                frontendUtils.update_comp_result(session['compid'], status=data['status'], name_suffix='Overview')
            return dict(redirect='/users/task_score_admin/' + str(taskid))
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
        frontendUtils.full_rescore(taskid, status=data['status'], autopublish=data['autopublish'],
                                   compid=session['compid'])
        resp = jsonify(success=True)
        return resp


@blueprint.route('/_unpublish_result/<int:taskid>', methods=['POST'])
@login_required
def _unpublish_result(taskid: int):
    if request.method == "POST":
        frontendUtils.unpublish_task_result(taskid)
        header = "No published results"
        resp = jsonify(filename='', header=header)
        frontendUtils.update_comp_result(session['compid'], name_suffix='Overview')
        return resp
    return render_template('500.html')


@blueprint.route('/_unpublish_comp_result/<int:compid>', methods=['POST'])
@login_required
def _unpublish_comp_result(compid: int):
    if request.method == "POST":
        frontendUtils.unpublish_comp_result(compid)
        comp_header = "No overall competition results published"
        resp = jsonify(filename='', comp_header=comp_header)
        return resp
    return render_template('500.html')


@blueprint.route('/_publish_result/<int:taskid>', methods=['POST'])
@login_required
def _publish_result(taskid: int):
    if request.method == "POST":
        data = request.json
        frontendUtils.publish_task_result(taskid, data['filename'])
        refid, _, timestamp = frontendUtils.update_comp_result(session['compid'], name_suffix='Overview')
        if refid:
            comp_published, status = data['filetext'].split('-')
            header = f"Published result ran at:{comp_published} Status:{status}"
            resp = jsonify(filename=data['filename'], header=header)
            return resp
        return jsonify(comp_header='There was a problem creating comp result: do we miss some task results files?')
    return render_template('500.html')


@blueprint.route('/_publish_comp_result/<int:compid>', methods=['POST'])
@login_required
def _publish_comp_result(compid: int):
    if request.method == "POST":
        data = request.json
        offset = (int(data['offset']) / 60 * -1) * 3600
        refid, _, timestamp = frontendUtils.update_comp_result(compid)
        if refid:
            comp_published = time.ctime(timestamp + offset)
            comp_header = f"Overall competition results published: {comp_published}"
            resp = jsonify(comp_header=comp_header)
            return resp
        return jsonify(comp_header='There was a problem creating comp result: do we miss some task results files?')
    return render_template('500.html')


@blueprint.route('/_change_result_status/<int:taskid>', methods=['POST'])
@login_required
def _change_result_status(taskid: int):
    if request.method == "POST":
        from result import update_result_status
        data = request.json
        update_result_status(data['filename'], data['status'])
        frontendUtils.update_comp_result(session['compid'], status=data['status'], name_suffix='Overview')
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

    if request.method == "POST":
        if request.files:
            if not Path(WAYPOINTDIR).is_dir():
                makedirs(WAYPOINTDIR)
            waypoint_file = request.files["waypoint_file"]
            airspace_file = request.files["openair_file"]
            '''airspace file'''
            if airspace_file in ['', None]:
                airspace_file = None
            else:
                airspace_file_data = airspace_file.read().decode('UTF-8')

            '''waypoint file'''
            if waypoint_file:  # there should always be a file as it is a required field
                if not allowed_wpt_extensions(waypoint_file.filename):
                    '''file has not a valid extension'''
                    flash(f"Waypoint file extension not supported ({', '.join(ALLOWED_WPT_EXTENSIONS)} ",
                          category='danger')
                    return render_template('users/region_admin.html', region_select=region_select,
                                           new_region_form=new_region)

                wpt_format, wpts = get_turnpoints_from_file_storage(waypoint_file)

                if not wpts:
                    flash("Waypoint file format not supported or file is not a waypoint file", category='danger')
                    return render_template('users/region_admin.html', region_select=region_select,
                                           new_region_form=new_region)
                '''save file'''
                wpt_filename = unique_filename(waypoint_file.filename, WAYPOINTDIR)
                fullpath = Path(WAYPOINTDIR, wpt_filename)
                waypoint_file.seek(0)
                waypoint_file.save(fullpath)

                if airspace_file:
                    if not Path(AIRSPACEDIR).is_dir():
                        makedirs(AIRSPACEDIR)
                    # save airspace file
                    air_filename = unique_filename(airspace_file.filename, AIRSPACEDIR)
                    fullpath = Path(AIRSPACEDIR, air_filename)
                    airspace_file.seek(0)
                    airspace_file.save(fullpath)
                    # with open(fullpath, 'w') as f:
                    #     f.write(airspace_file_data)
                    flash(Markup(f'Open air file added, please check it <a href="'
                                 f'{url_for("user.airspace_edit", filename=air_filename)}" '
                                 f'class="alert-link">here</a>'), category='info')
                else:
                    air_filename = None

                # write to DB
                region = Region(name=new_region.name.data, comp_id=compid, waypoint_file=wpt_filename,
                                openair_file=air_filename, turnpoints=wpts)
                region.to_db()
                flash(f"Waypoint file format: {wpt_format}, {len(wpts)} waypoints. ", category='info')
                flash(f"Region {new_region.name.data} added", category='info')

    return render_template('users/region_admin.html', region_select=region_select, new_region_form=new_region)


@blueprint.route('/_delete_region/<int:regid>', methods=['POST'])
@login_required
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
    from pilot.track import read_igc_config_yaml, save_igc_config_yaml
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
def pilot_admin(compid: int):
    """ Registered Pilots list
        Add / Edit Pilots"""
    modify_participant_form = ModifyParticipantForm()
    comp = Comp.read(compid)

    if session['external']:
        '''External Event'''
        flash(f"This is an External Event. Settings and Results are Read Only.", category='warning')

    return render_template('users/pilot_admin.html', compid=compid, track_source=comp.track_source,
                           modify_participant_form=modify_participant_form, pilotdb=PILOT_DB)


@blueprint.route('/_modify_participant_details/<int:parid>', methods=['POST'])
@login_required
def _modify_participant_details(parid: int):
    from pilot.participant import Participant
    data = request.json
    participant = Participant.read(parid)
    if data.get('id_num'):
        participant.ID = int(data.get('id_num')) if str(data.get('id_num')).isdigit() else None
    if data.get('name'):
        participant.name = data.get('name')
    participant.civl_id = int(data.get('CIVL')) if str(data.get('CIVL')).isdigit() else None
    if data.get('sex'):
        participant.sex = data.get('sex')
    if data.get('nat'):
        participant.nat = data.get('nat')
    participant.glider = data.get('glider') or None
    participant.glider_cert = data.get('certification') or None
    participant.sponsor = data.get('sponsor') or None
    participant.nat_team = bool(data.get('nat_team'))
    participant.team = data.get('team') or None
    participant.live_id = data.get('live_id') or None
    participant.xcontest_id = data.get('xcontest_id') or None
    if data.get('status'):
        participant.status = data.get('status')
    if data.get('paid'):
        participant.paid = data.get('paid')
    participant.to_db()
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_add_participant/<int:compid>', methods=['POST'])
@login_required
def _add_participant(compid: int):
    from pilot.participant import Participant
    data = request.json
    participant = Participant()
    participant.comp_id = compid
    if data.get('id_num'):
        participant.ID = int(data.get('id_num')) if str(data.get('id_num')).isdigit() else None
    if data.get('name'):
        participant.name = data.get('name')
    participant.civl_id = int(data.get('CIVL')) if str(data.get('CIVL')).isdigit() else None
    if data.get('sex'):
        participant.sex = data.get('sex')
    if data.get('nat'):
        participant.nat = data.get('nat')
    participant.glider = data.get('glider') or None
    participant.glider_cert = data.get('certification') or None
    participant.sponsor = data.get('sponsor') or None
    participant.nat_team = bool(data.get('nat_team'))
    participant.team = data.get('team') or None
    participant.live_id = data.get('live_id') or None
    participant.xcontest_id = data.get('xcontest_id') or None
    if data.get('status'):
        participant.status = data.get('status')
    if data.get('paid'):
        participant.paid = data.get('paid')
    participant.to_db()
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_upload_participants_excel/<int:compid>', methods=['POST'])
@login_required
def _upload_participants_excel(compid: int):
    from pilot.participant import extract_participants_from_excel, mass_import_participants
    import tempfile
    if request.method == "POST":
        if request.files:
            excel_file = request.files["excel_file"]
            with tempfile.TemporaryDirectory() as tmpdirname:
                # filename = secure_filename(excel_file.filename)
                excel_file.save(path.join(tmpdirname, excel_file.filename))
                pilots = extract_participants_from_excel(compid, path.join(tmpdirname, excel_file.filename))
                mass_import_participants(compid, pilots)
            resp = jsonify(success=True)
            return resp
        resp = jsonify(success=False)
        return resp


@blueprint.route('/_upload_participants_fsdb/<int:compid>', methods=['POST'])
@login_required
def _upload_participants_fsdb(compid: int):
    from pilot.participant import mass_import_participants
    import tempfile
    if request.method == "POST":
        if request.files:
            fsdb_file = request.files["fsdb_file"]
            with tempfile.TemporaryDirectory() as tmpdirname:
                tmp_file = Path(tmpdirname, fsdb_file.filename)
                fsdb_file.save(tmp_file)
                participants = frontendUtils.import_participants_from_fsdb(tmp_file)
                if participants:
                    mass_import_participants(compid, participants)
            resp = jsonify(success=True)
            return resp
        resp = jsonify(success=False)
        return resp


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
def _unregister_participant(compid: int):
    """unregister participant from a comp"""
    from pilot.participant import unregister_participant
    data = request.json
    unregister_participant(compid, data['participant'])
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_unregister_all_external_participants/<int:compid>', methods=['POST'])
@login_required
def _unregister_all_external_participants(compid: int):
    """unregister participant from a comp"""
    from pilot.participant import unregister_all_external_participants
    unregister_all_external_participants(compid)
    resp = jsonify(success=True)
    return resp


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
    from result import update_result_file
    data = request.json
    if data['changes']:
        for change in data['changes']:
            notification = dict(not_id=change['not_id'], flat_penalty=change['penalty'],
                                comment=change['comment'])
            update_result_file(filename=data['filename'], par_id=int(data['par_id']), notification=notification)
    if data['new']:
        if data['new']['sign'] == 'penalty':
            points = data['new']['penalty'] * -1
        else:
            points = data['new']['penalty']
        notification = dict(flat_penalty=points, comment=data['new']['comment'])
        update_result_file(filename=data['filename'], par_id=int(data['par_id']), notification=notification)

    resp = jsonify(success=True)
    return resp


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


@blueprint.route('/_modify_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def _modify_user(user_id: int):
    data = request.json
    user = User.query.filter_by(id=user_id).first()
    user.email = data.get('email')
    user.access = data.get('access')
    user.active = data.get('active')
    user.update()
    resp = jsonify(success=True)
    return resp


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
