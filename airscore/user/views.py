# -*- coding: utf-8 -*-
"""User views."""
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, json, flash, redirect, url_for, session, Markup, \
    current_app, send_file, make_response
from flask_login import login_required, current_user
import frontendUtils
from airscore.user.forms import NewTaskForm, CompForm, TaskForm, NewTurnpointForm, ModifyTurnpointForm, \
    TaskResultAdminForm, NewAdminForm, RegionForm, NewRegionForm, IgcParsingConfigForm, ModifyParticipantForm, \
    EditScoreForm
from comp import Comp
from formula import list_formulas, Formula
from task import Task, write_map_json, get_task_json_by_filename
from frontendUtils import save_turnpoint
from flightresult import update_status, delete_track
from os import path, remove, makedirs
from task import get_task_json_by_filename
from calcUtils import sec_to_time
import time
from Defines import SELF_REG_DEFAULT, PILOT_DB

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")


@blueprint.route("/test")
@login_required
def test():
    return render_template('users/socketio_demo.html')


@blueprint.route("/")
@login_required
def members():
    """List members."""
    return render_template("users/members.html")


@blueprint.route('/airspace_map/<filename>')
@login_required
def airspace_edit(filename):
    import design_map
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
        message = 'Attention: There is FL (flight level) units in the file. You should adjust to meters or ' \
                  'feet above sea level'
        fl_detail = ", ".join(set(fl_messages))
        fl_detail += " - Assuming an International Standard Atmosphere pressure of 1013.25 hPa (29.92 inHg) " \
                     "at sea level, and therefore is not necessarily the same as the aircraft's actual altitude, " \
                     "either above sea level or above ground level. " \
                     "You should round down to be conservative and allow for days with lower atmospheric pressure."
    if unknown_flag:
        message += 'Attention: There is unknown height units in the file. You should adjust to meters or ' \
                   'feet above sea level'

    airspace_map = design_map.make_map(airspace_layer=spaces, bbox=bbox)

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
    return render_template('users/comp_admin.html', today=datetime.today().strftime('%d-%m-%Y'))


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
        frontendUtils.set_comp_admin(output, current_user.id, owner=True)
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
            if frontendUtils.allowed_tracklog(fsdb_file.filename, extension=['fsdb']):
                f = FSDB.read(fsdb_file)
                compid = f.add_all()
                if compid:
                    frontendUtils.set_comp_admin(compid, current_user.id, owner=True)
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


@blueprint.route('/comp_settings_admin/<compid>', methods=['GET', 'POST'])
@login_required
def comp_settings_admin(compid):
    error = None
    compid = int(compid)
    compform = CompForm()
    newtaskform = NewTaskForm()
    newadminform = NewAdminForm()
    comp = Comp.read(compid)
    # set session variables for navbar
    session['compid'] = compid
    session['comp_name'] = comp.comp_name

    compform.igc_parsing_file.choices, _ = frontendUtils.get_igc_parsing_config_file_list()
    owner, administrators, admin_ids = frontendUtils.get_comp_admins(compid)
    all_admins = frontendUtils.get_all_admins()
    all_admins.remove(owner)
    for admin in administrators:
        all_admins.remove(admin)
    admin_choices = []
    if all_admins:
        for admin in all_admins:
            admin_choices.append((admin['id'], f"{admin['first_name']} {admin['last_name']} ({admin['username']})"))
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
            comp.time_offset = compform.time_offset.data * 3600
            comp.restricted = 1 if compform.pilot_registration.data == 'registered' else None
            comp.formula = compform.formula.data
            comp.locked = compform.locked.data
            comp.igc_config_file = compform.igc_parsing_file.data
            # comp.airspace_check = compform.airspace_check.data
            comp.check_launch = 'on' if compform.check_launch.data else 'off'
            comp.check_g_record = compform.check_g_record.data
            comp.self_register = compform.self_register.data
            if compform.website.data.lower()[:7] == 'http://':
                comp.website = compform.website.data.lower()[7:]
            else:
                comp.website = compform.website.data.lower()
            comp.to_db()
            formula = Formula.read(compid)
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
            formula.validity_min_time = compform.validity_min_time.data
            formula.score_back_time = compform.scoreback_time.data
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
        compform.time_offset.data = comp.time_offset / 3600
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
        compform.lead_factor.data = formula.lead_factor
        compform.formula_time.data = formula.formula_time
        compform.no_goal_penalty.data = int(formula.no_goal_penalty * 100)
        compform.glide_bonus.data = formula.glide_bonus
        compform.tolerance.data = formula.tolerance * 100
        compform.min_tolerance.data = formula.min_tolerance
        compform.arr_alt_bonus.data = formula.arr_alt_bonus
        compform.arr_max_height.data = formula.arr_max_height
        compform.arr_min_height.data = formula.arr_min_height
        compform.validity_min_time.data = formula.validity_min_time
        compform.scoreback_time.data = formula.score_back_time
        compform.max_JTG.data = formula.max_JTG
        compform.JTG_penalty_per_sec.data = formula.JTG_penalty_per_sec
        compform.scoring_altitude.data = formula.scoring_altitude
        compform.igc_parsing_file.data = comp.igc_config_file
        compform.airspace_check.data = comp.airspace_check
        compform.check_launch.data = comp.check_launch
        compform.check_g_record.data = comp.check_g_record
        compform.self_register.data = comp.self_register
        compform.website.data = comp.website
        newtaskform.task_region.choices, _ = frontendUtils.get_region_choices(compid)
        newadminform.admin.choices = admin_choices
        formulas = list_formulas()
        compform.formula.choices = [(x, x.upper()) for x in formulas[comp.comp_class]]

        if current_user.id not in admin_ids:
            session['is_admin'] = False
            compform.submit = None
        else:
            session['is_admin'] = True

    tasks = frontendUtils.get_task_list(comp)
    session['tasks'] = tasks['tasks']
    session['check_g_record'] = comp.check_g_record

    return render_template('users/comp_settings.html', compid=compid, compform=compform,
                           taskform=newtaskform, adminform=newadminform, error=error,
                           self_register=(SELF_REG_DEFAULT and PILOT_DB))


@blueprint.route('/_get_admins/<compid>', methods=['GET'])
@login_required
def _get_admins(compid):
    owner, admins, _ = frontendUtils.get_comp_admins(compid)
    return {'owner': owner, 'admins': admins}


@blueprint.route('/_add_admin/<compid>', methods=['POST'])
@login_required
def _add_admin(compid):
    data = request.json
    if frontendUtils.set_comp_admin(compid, data['id']):
        resp = jsonify(success=True)
        return resp
    else:
        return render_template('500.html')


@blueprint.route('/task_admin/<taskid>', methods=['GET', 'POST'])
@login_required
def task_admin(taskid):
    from calcUtils import sec_to_time, time_to_seconds
    error = None
    taskform = TaskForm()
    turnpointform = NewTurnpointForm()
    modifyturnpointform = ModifyTurnpointForm()
    taskid = int(taskid)

    task_in_comp = False
    for task in session['tasks']:
        if task['task_id'] == taskid:
            task_in_comp = True

    if not task_in_comp:
        return render_template('out_of_comp.html')

    task = Task.read(taskid)
    waypoints, _ = frontendUtils.get_waypoint_choices(task.reg_id)
    turnpointform.name.choices = waypoints
    modifyturnpointform.mod_name.choices = waypoints

    owner, administrators, all_admin_ids = frontendUtils.get_comp_admins(task.comp_id)

    if request.method == 'POST':
        if taskform.validate_on_submit():
            task.comp_name = taskform.comp_name
            task.task_name = taskform.task_name.data
            task.task_num = taskform.task_num.data
            task.comment = taskform.comment.data
            task.date = taskform.date.data
            task.task_type = taskform.task_type.data
            task.window_open_time = time_to_seconds(taskform.window_open_time.data) - taskform.time_offset.data * 3600
            task.window_close_time = time_to_seconds(taskform.window_close_time.data) - taskform.time_offset.data * 3600
            task.start_time = time_to_seconds(taskform.start_time.data) - taskform.time_offset.data * 3600
            task.start_close_time = time_to_seconds(taskform.start_close_time.data) - taskform.time_offset.data * 3600
            task.stopped_time = None if taskform.stopped_time.data is None else \
                time_to_seconds(taskform.stopped_time.data) - taskform.time_offset.data * 3600
            task.task_deadline = time_to_seconds(taskform.task_deadline.data) - taskform.time_offset.data * 3600
            task.SS_interval = taskform.SS_interval.data * 60  # (convert from min to sec)
            task.start_iteration = taskform.start_iteration.data
            task.time_offset = taskform.time_offset.data * 3600
            task.check_launch = 'on' if taskform.check_launch.data else 'off'
            task.airspace_check = taskform.airspace_check.data
            # task.openair_file = taskform.openair_file  # TODO get a list of openair files for this comp (in the case of defines.yaml airspace_file_library: off otherwise all openair files available)
            task.QNH = taskform.QNH.data
            task.formula.formula_distance = taskform.formula_distance.data
            task.formula.formula_arrival = taskform.formula_arrival.data
            task.formula.formula_departure = taskform.formula_departure.data
            task.formula.formula_time = taskform.formula_time.data
            task.formula.tolerance = taskform.tolerance.data or 0 / 100
            task.formula.max_JTG = taskform.max_JTG.data
            task.formula.no_goal_penalty = taskform.no_goal_penalty.data
            task.formula.arr_alt_bonus = taskform.arr_alt_bonus.data
            task.to_db()

            flash("Saved", category='info')

            return redirect(url_for('user.task_admin', taskid=taskid))

        else:
            for item in taskform:
                if item.errors:
                    flash(f"{item.label.text}: {', '.join(x for x in item.errors)}", category='danger')

    if request.method == 'GET':
        offset = task.time_offset if task.time_offset else 0
        taskform.comp_name = task.comp_name
        taskform.task_name.data = task.task_name
        taskform.task_num.data = task.task_num
        taskform.comment.data = task.comment
        taskform.date.data = task.date
        taskform.task_type.data = task.task_type
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
        taskform.SS_interval.data = task.SS_interval / 60  # (convert from sec to min)
        taskform.start_iteration.data = task.start_iteration
        taskform.time_offset.data = offset / 3600
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
        taskform.tolerance.data = task.formula.tolerance or 0 * 100
        taskform.max_JTG.data = task.formula.max_JTG
        taskform.no_goal_penalty.data = task.formula.no_goal_penalty
        taskform.arr_alt_bonus.data = task.formula.arr_alt_bonus

        if current_user.id not in all_admin_ids:
            taskform.submit = None

    return render_template('users/task_admin.html', taskid=taskid, taskform=taskform, turnpointform=turnpointform,
                           modifyturnpointform=modifyturnpointform, compid=task.comp_id, error=error)


@blueprint.route('/_get_admin_comps', methods=['GET'])
@login_required
def _get_admin_comps():
    return frontendUtils.get_admin_comps(current_user.id)


@blueprint.route('/_delete_comp/<compid>', methods=['POST', 'GET'])
@login_required
def _delete_comp(compid):
    from comp import delete_comp
    owner, _, _ = frontendUtils.get_comp_admins(int(compid))
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


@blueprint.route('/_register_pilots/<compid>', methods=['POST'])
@login_required
def _register_pilots(compid):
    from participant import register_from_profiles_list, unregister_from_profiles_list
    data = request.json
    if data['register']:
        register_from_profiles_list(compid, data['register'])
    if data['unregister']:
        unregister_from_profiles_list(compid, data['unregister'])
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_add_task/<compid>', methods=['POST'])
@login_required
def _add_task(compid):
    comp = Comp.read(int(compid))
    # comp.comp_id = compid
    data = request.json
    task = Task(comp_id=compid)
    task.task_name = data['task_name']
    task.task_num = int(data['task_num'])
    task.date = datetime.strptime(data['task_date'], '%Y-%m-%d')
    task.comment = data['task_comment']
    task.reg_id = int(data['task_region'])
    task.time_offset = comp.time_offset
    task.airspace_check = comp.airspace_check
    task.check_launch = comp.check_launch
    task.igc_config_file = comp.igc_config_file
    task.to_db()
    tasks = frontendUtils.get_task_list(comp)
    session['tasks'] = tasks['tasks']
    return tasks


@blueprint.route('/_del_task/<taskid>', methods=['POST'])
@login_required
def _del_task(taskid):
    from task import delete_task
    delete_task(taskid)
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_get_tasks/<compid>', methods=['GET'])
@login_required
def _get_tasks(compid):
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
                'formula_time': formula.formula_time, 'no_goal_penalty': formula.no_goal_penalty,
                'glide_bonus': formula.glide_bonus, 'tolerance': formula.tolerance * 100,
                'min_tolerance': formula.min_tolerance, 'arr_alt_bonus': formula.height_bonus,
                'arr_max_height': formula.arr_max_height, 'arr_min_height': formula.arr_min_height,
                'validity_min_time': formula.validity_min_time, 'scoreback_time': formula.score_back_time,
                'max_JTG': formula.max_JTG, 'JTG_penalty_per_sec': formula.JTG_penalty_per_sec}

    return settings


@blueprint.route('/_get_task_turnpoints/<taskid>', methods=['GET'])
@login_required
def _get_task_turnpoints(taskid):
    task = Task(task_id=int(taskid))
    turnpoints = frontendUtils.get_task_turnpoints(task)
    return turnpoints


@blueprint.route('/_add_turnpoint/<taskid>', methods=['POST'])
@login_required
def _add_turnpoint(taskid):
    """add turnpoint to the task,if rwp_id is not null then update instead of insert (add)
    if turnpoint is goal or we are updating and goal exists then calculate opt dist and dist."""
    from frontendUtils import get_waypoint
    data = request.json
    taskid = int(taskid)
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
        tp.shape = data['shape']
    if save_turnpoint(taskid, tp):
        task = Task.read(taskid)
        if task.opt_dist > 0 or data['type'] == 'goal':
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
    if data['partial_distance'] != '':
        task = Task.read(taskid)
        task.calculate_optimised_task_length()
        task.calculate_task_length()
        task.update_task_distance()
        write_map_json(taskid)

    resp = jsonify(success=True)
    return resp


@blueprint.route('/_del_all_turnpoints/<taskid>', methods=['POST'])
@login_required
def _del_all_turnpoints(taskid):
    """delete a turnpoint from the task"""
    taskid = int(taskid)
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


@blueprint.route('/_get_tracks_admin/<taskid>', methods=['GET'])
@login_required
def _get_tracks_admin(taskid):
    return {'data': frontendUtils.get_pilot_list_for_track_management(taskid)}


@blueprint.route('/_get_tracks_processed/<taskid>', methods=['GET'])
@login_required
def _get_tracks_processed(taskid):
    tracks, pilots = frontendUtils.number_of_tracks_processed(taskid)
    return {'tracks': tracks, 'pilots': pilots}


@blueprint.route('/track_admin/<taskid>', methods=['GET'])
@login_required
def track_admin(taskid):
    taskid = int(taskid)
    task_in_comp = False
    for task in session['tasks']:
        if task['task_id'] == taskid:
            task_num = task['task_num']
            task_name = task['task_name']
            task_in_comp = True

    if not task_in_comp:
        return render_template('out_of_comp.html')

    _, _, all_admin_ids = frontendUtils.get_comp_admins(taskid, task_id=True)
    if current_user.id in all_admin_ids:
        user_is_admin = True
    else:
        user_is_admin = None
    return render_template('users/track_admin.html', taskid=taskid, user_is_admin=user_is_admin,
                           production=frontendUtils.production(), task_name=task_name, task_num=task_num)


@blueprint.route('/_set_result/<taskid>', methods=['POST'])
@login_required
def _set_result(taskid):
    data = request.json
    taskid = int(taskid)
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


@blueprint.route('/_upload_track/<taskid>/<parid>', methods=['POST'])
@login_required
def _upload_track(taskid, parid):
    taskid = int(taskid)
    parid = int(parid)
    if request.method == "POST":
        if request.files:
            if "filesize" in request.cookies:

                if not frontendUtils.allowed_tracklog_filesize(request.cookies["filesize"]):
                    print("Filesize exceeded maximum limit")
                    return redirect(request.url)
                check_g_record = session['check_g_record']

                if request.files.get("tracklog_NO_G"):
                   tracklog = request.files["tracklog_NO_G"]
                   check_g_record = False
                else:
                    tracklog = request.files["tracklog"]

                if tracklog.filename == "":
                    print("No filename")
                    return redirect(request.url)

                if frontendUtils.allowed_tracklog(tracklog.filename):
                    if frontendUtils.production():
                        filename, full_file_name = frontendUtils.save_igc_background(taskid, parid, tracklog,
                                                                                     current_user.username,
                                                                                     check_g_record=check_g_record)
                        job = current_app.task_queue.enqueue(frontendUtils.process_igc_background, taskid, parid,
                                                             filename, full_file_name, current_user.username)
                        if not filename:
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


@blueprint.route('/_upload_XCTrack/<taskid>', methods=['POST'])
@login_required
def _upload_XCTrack(taskid):
    """takes an upload of an xctrack task file and processes it and saves the task to the DB"""
    taskid = int(taskid)
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


@blueprint.route('/_upload_track_zip/<taskid>', methods=['POST'])
@login_required
def _upload_track_zip(taskid):
    taskid = int(taskid)
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
                    if frontendUtils.production():
                        tracksdir = frontendUtils.unzip_igc(zip_file)
                        job = current_app.task_queue.enqueue(frontendUtils.process_igc_from_zip, taskid, tracksdir,
                                                             current_user.username, job_timeout=2000)
                        resp = jsonify(success=True)
                        return resp
                    else:
                        task = Task.read(taskid)
                        data = frontendUtils.process_igc_zip(task, zip_file)
                        resp = data
                        return resp

                else:
                    print("That file extension is not allowed")
                    return redirect(request.url)
            resp = {'error': 'filesize'}
            return resp
        resp = {'error': 'request.files'}
        return resp


@blueprint.route('/_get_task_result_files/<taskid>', methods=['POST'])
@login_required
def _get_task_result_files(taskid):
    from compUtils import get_comp_json
    data = request.json
    offset = (int(data['offset']) / 60 * -1) * 3600
    files = frontendUtils.get_task_result_file_list(int(taskid))
    comp_file = get_comp_json(int(session['compid']))

    if comp_file == 'error':
        comp_header = "No overall competition results published"
        display_comp_unpublish = False
    else:
        comp_published = time.ctime(comp_file['file_stats']['timestamp'] + offset)
        comp_header = f"Overall competition results published: {comp_published}"
        display_comp_unpublish = True
    header, active = frontendUtils.get_score_header(files, data['offset'])
    choices = []

    for file in files:
        published = time.ctime(file['created'] + offset)
        choices.append((file['filename'], f"{published} - {file['status']}"))
    choices.reverse()
    return {'choices': choices, 'header': header, 'active': active, 'comp_header': comp_header,
            'display_comp_unpublish': display_comp_unpublish}


@blueprint.route('/_get_task_score_from_file/<taskid>/<filename>', methods=['GET'])
@login_required
def _get_task_score_from_file(taskid, filename):
    from result import pretty_format_results
    from calcUtils import c_round
    error = None
    result_file = get_task_json_by_filename(filename)
    if not result_file:
        return {'data': ''}
    taskid = int(taskid)
    rank = 1
    all_pilots = []
    timeoffset = int(result_file['info']['time_offset'])
    stats = pretty_format_results(result_file['stats'], timeoffset)
    info = result_file['info']
    for r in result_file['results']:
        track_id = r['track_id']
        name = r['name']
        status = r['result_type']
        if status not in ['dnf', 'abs']:
            pilot = {'rank': rank, 'name': f'<a href="/map/{track_id}-{taskid}">{name}</a>'}
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


@blueprint.route('/task_score_admin/<taskid>', methods=['GET'])
@login_required
def task_score_admin(taskid):
    taskid = int(taskid)
    task_in_comp = False
    for task in session['tasks']:
        if task['task_id'] == taskid:
            task_num = task['task_num']
            task_name = task['task_name']
            task_in_comp = True

    if not task_in_comp:
        return render_template('out_of_comp.html')

    fileform = TaskResultAdminForm()
    editform = EditScoreForm()
    active_file = None
    choices = [(1, 1), (2, 2)]
    fileform.result_file.choices = choices
    if active_file:
        fileform.result_file.data = active_file
    _, _, all_admin_ids = frontendUtils.get_comp_admins(taskid, task_id=True)
    if current_user.id in all_admin_ids:
        user_is_admin = True
    else:
        user_is_admin = None

    return render_template('users/task_score_admin.html', fileform=fileform, taskid=taskid,
                           active_file=active_file, user_is_admin=user_is_admin, task_name=task_name,
                           task_num=task_num, editform=editform, production=frontendUtils.production())


@blueprint.route('/_score_task/<taskid>', methods=['POST'])
@login_required
def _score_task(taskid):
    if request.method == "POST":
        from result import unpublish_result, publish_result
        """score task, request data should contain status: the score status (provisional, official etc),
        autopublish: True or False. indicates if to publish results automatically after scoring"""
        data = request.json
        taskid = int(taskid)
        task = Task.read(taskid)
        ref_id, _ = task.create_results(data['status'])
        if ref_id:
            if data['autopublish']:
                unpublish_result(taskid)
                publish_result(ref_id, ref_id=True)
                comp = Comp()
                comp.create_results(session['compid'], data['status'], name_suffix='Overview')
            return dict(redirect='/users/task_score_admin/' + str(taskid))
    return render_template('500.html')


@blueprint.route('/_full_rescore_task/<taskid>', methods=['POST'])
@login_required
def _full_rescore_task(taskid):
    taskid=int(taskid)
    data = request.json
    if frontendUtils.production():
        job = current_app.task_queue.enqueue(frontendUtils.full_rescore, taskid, background=True,
                                             user=current_user.username,  status=data['status'],
                                             autopublish=data['autopublish'], compid=session['compid'],
                                             job_timeout=2000)

        resp = jsonify(success=True, background=True)
        return resp

    else:
        frontendUtils.full_rescore(taskid, status=data['status'], autopublish=data['autopublish'],
                                   compid=session['compid'])
        resp = jsonify(success=True)
        return resp


@blueprint.route('/_unpublish_result/<taskid>', methods=['POST'])
@login_required
def _unpublish_result(taskid):
    if request.method == "POST":
        from result import unpublish_result
        unpublish_result(taskid)
        header = "No published results"
        resp = jsonify(filename='', header=header)
        comp = Comp()
        comp.create_results(session['compid'], name_suffix='Overview')
        return resp
    return render_template('500.html')


@blueprint.route('/_unpublish_comp_result/<compid>', methods=['POST'])
@login_required
def _unpublish_comp_result(compid):
    if request.method == "POST":
        from result import unpublish_result
        unpublish_result(compid, comp=True)
        comp_header = "No overall competition results published"
        resp = jsonify(filename='', comp_header=comp_header)
        return resp
    return render_template('500.html')


@blueprint.route('/_publish_result/<taskid>', methods=['POST'])
@login_required
def _publish_result(taskid):
    if request.method == "POST":
        from result import publish_result, unpublish_result
        data = request.json
        unpublish_result(taskid)
        publish_result(data['filename'])
        comp = Comp()
        comp.create_results(session['compid'])
        run_at, status = data['filetext'].split('-')
        header = f"Published result ran at:{run_at} Status:{status}"
        comp = Comp()
        comp.create_results(session['compid'], name_suffix='Overview')
        resp = jsonify(filename=data['filename'], header=header)
        return resp
    return render_template('500.html')


@blueprint.route('/_publish_comp_result/<compid>', methods=['POST'])
@login_required
def _publish_comp_result(compid):
    if request.method == "POST":
        from result import publish_result, unpublish_result
        data = request.json
        offset = (int(data['offset']) / 60 * -1) * 3600

        unpublish_result(compid, comp=True)
        comp = Comp()
        _, ref_id, filename, timestamp = comp.create_results(session['compid'])
        publish_result(ref_id, ref_id=True)
        comp_published = time.ctime(timestamp + offset)
        comp_header = f"Overall competition results published: {comp_published}"
        resp = jsonify(comp_header=comp_header)
        return resp
    return render_template('500.html')


@blueprint.route('/_change_result_status/<taskid>', methods=['POST'])
@login_required
def _change_result_status(taskid):
    if request.method == "POST":
        from result import update_result_status
        data = request.json
        update_result_status(data['filename'], data['status'])
        comp = Comp()
        comp.create_results(session['compid'], data['status'], name_suffix='Overview')
        resp = jsonify(success=True)
        return resp
    return render_template('500.html')


@blueprint.route('/_get_regions', methods=['GET'])
@login_required
def _get_regions():
    compid = session.get('compid')
    choices, details = frontendUtils.get_region_choices(compid)
    return {'choices': choices, 'details': details}


@blueprint.route('/_get_wpts/<regid>', methods=['GET'])
@login_required
def _get_wpts(regid):
    choices, details = frontendUtils.get_waypoint_choices(regid)
    return {'choices': choices, 'data': details}


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
            if not path.isdir(WAYPOINTDIR):
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
                fullpath = path.join(WAYPOINTDIR, wpt_filename)
                waypoint_file.save(fullpath)

                if airspace_file:
                    # save airspace file
                    fullpath = path.join(AIRSPACEDIR, airspace_file.filename)
                    i = 1
                    air_new_filename = airspace_file.filename
                    while path.exists(fullpath):
                        air_new_filename = f"{i}_{airspace_file.filename}"
                        fullpath = path.join(AIRSPACEDIR, air_new_filename)
                        i += 1
                    # airspace_file.save(fullpath)
                    with open(fullpath, 'w') as f:
                        f.write(airspace_file_data)
                    flash(Markup(f'Open air file added, please check it <a href="'
                                 f'{url_for("user.airspace_edit", filename=air_new_filename)}" '
                                 f'class="alert-link">here</a>'), category='info')
                else:
                    air_new_filename = None

                # write to DB
                region = Region(name=new_region.name.data, comp_id=compid, filename=wpt_filename,
                                openair=air_new_filename, turnpoints=wpts)
                region.to_db()
                flash(f"Waypoint file format: {wpt_format}, {len(wpts)} waypoints. ", category='info')
                flash(f"Region {new_region.name.data} added", category='info')

    return render_template('users/region_admin.html', region_select=region_select, new_region_form=new_region)


@blueprint.route('/_delete_region/<regid>', methods=['POST'])
@login_required
def _delete_region(regid):
    from region import delete_region
    delete_region(regid)
    # flash text goes on the second next page refresh, instead of after deleting.
    flash(f"Region deleted", category='info')
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_get_non_and_registered_pilots/<compid>', methods=['GET', 'POST'])
@login_required
def _get_non_and_registered_pilots_internal(compid):
    registered_pilots, _, _ = frontendUtils.get_participants(compid, source='internal')
    non_registered_pilots = frontendUtils.get_non_registered_pilots(compid)
    return jsonify({'non_registered_pilots': non_registered_pilots, 'registered_pilots': registered_pilots})


@blueprint.route('/_get_non_and_registered_pilots/<compid>', methods=['GET', 'POST'])
@login_required
def _get_registered_pilots_external(compid):
    registered_pilots, _ = frontendUtils.get_participants(compid, source='external')
    return {'registered_pilots': registered_pilots}


@blueprint.route('/igc_parsing_config/<filename>', methods=['GET', 'POST'])
@login_required
def igc_parsing_config(filename):
    from track import read_igc_config_yaml, save_igc_config_yaml
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


@blueprint.route('/_del_igc_config/<filename>', methods=['POST'])
@login_required
def _del_igc_config(filename):
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


@blueprint.route('/pilot_admin', methods=['GET', 'POST'])
@login_required
def pilot_admin():
    modify_participant_form = ModifyParticipantForm()
    return render_template('users/pilot_admin.html', modify_participant_form=modify_participant_form, pilotdb=PILOT_DB)


@blueprint.route('/_modify_participant_details/<parid>', methods=['POST'])
@login_required
def _modify_participant_details(parid):
    from participant import Participant
    data = request.json
    participant = Participant.read(int(parid))
    participant.ID = data.get('id_num')
    if data.get('name'):
        participant.name = data.get('name')
    if data.get('sex'):
        participant.sex = data.get('sex')
    participant.nat = data.get('nat')
    participant.glider = data.get('glider')
    participant.certification = data.get('certification')
    participant.sponsor = data.get('sponsor')
    participant.nat_team = data.get('nat_team')
    participant.team = data.get('team')
    participant.civl_id = data.get('CIVL')
    if data.get('status'):
        participant.status = data.get('status')
    if data.get('paid'):
        participant.paid = data.get('paid')
    participant.to_db()
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_add_participant/<compid>', methods=['POST'])
@login_required
def _add_participant(compid):
    from participant import Participant
    data = request.json
    participant = Participant()
    participant.comp_id = int(compid)
    participant.ID = data.get('id_num')
    if data.get('name'):
        participant.name = data.get('name')
    if data.get('sex'):
        participant.sex = data.get('sex')
    participant.nat = data.get('nat')
    participant.glider = data.get('glider')
    participant.certification = data.get('certification')
    participant.sponsor = data.get('sponsor')
    participant.nat_team = data.get('nat_team')
    participant.team = data.get('team')
    participant.civl_id = data.get('CIVL')
    if data.get('status'):
        participant.status = data.get('status')
    if data.get('paid'):
        participant.paid = data.get('paid')
    participant.to_db()
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_upload_participants_excel/<compid>', methods=['POST'])
@login_required
def _upload_participants_excel(compid):
    from participant import extract_participants_from_excel, mass_import_participants
    import tempfile
    compid = int(compid)
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


@blueprint.route('/_self_register/<compid>', methods=['POST'])
@login_required
def _self_register(compid):
    from participant import Participant
    data = request.json
    participant = Participant.from_profile(data['pil_id'], comp_id=compid)
    participant.ID = data.get('id_num')
    participant.nat = data.get('nat')
    participant.glider = data.get('glider')
    participant.certification = data.get('certification')
    participant.sponsor = data.get('sponsor')
    participant.to_db()
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_unregister_participant/<compid>', methods=['POST'])
@login_required
def _unregister_participant(compid):
    """unregister participant from a comp"""
    from participant import unregister_participant
    data = request.json
    unregister_participant(compid, data['participant'])
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_unregister_all_external_participants/<compid>', methods=['POST'])
@login_required
def _unregister_all_external_participants(compid):
    """unregister participant from a comp"""
    from participant import unregister_all_exteranl_participants
    unregister_all_exteranl_participants(compid)
    resp = jsonify(success=True)
    return resp


@blueprint.route('/_check_nat_team_size/<compid>', methods=['GET'])
@login_required
def _check_nat_team_size(compid):
    return {'message': frontendUtils.check_team_size(int(compid), nat=True)}


@blueprint.route('/_check_team_size/<compid>', methods=['GET'])
@login_required
def _check_team_size(compid):
    return {'message': frontendUtils.check_team_size(int(compid))}


@blueprint.route('/_adjust_task_result/<taskid>', methods=['POST'])
@login_required
def _adjust_task_result(taskid):
    from result import update_result_file
    taskid = int(taskid)
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


@blueprint.route('/_export_fsdb/<compid>', methods=['GET'])
@login_required
def _export_fsdb(compid):
    from fsdb import FSDB
    import tempfile
    compid = int(compid)
    comp_fsdb = FSDB.create(compid)
    filename, data = comp_fsdb.to_file()
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(data)
        resp = make_response(send_file(tmp.name, mimetype="text/xml", attachment_filename=filename, as_attachment=True))
        resp.set_cookie('ServerProcessCompleteChecker', '', expires=0)
        return resp


