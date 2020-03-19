# -*- coding: utf-8 -*-
"""User views."""
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, json, flash, redirect, url_for
from flask_login import login_required, current_user
import frontendUtils
from airscore.user.forms import NewTaskForm, CompForm, TaskForm, NewTurnpointForm, ModifyTurnpointForm, \
    TaskResultAdminForm
from comp import Comp
from formula import list_formulas, Formula
from task import Task, write_map_json
from route import save_turnpoint, Turnpoint
from flight_result import update_status, delete_result
from os import path, remove
from sys import stdout
from task import get_task_json_by_filename
from calcUtils import sec_to_time
import time

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")

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
    return jsonify(dict(redirect=newfile))


@blueprint.route('/comp_admin', methods=['GET', 'POST'])
@login_required
def comp_admin():
    return render_template('users/comp_admin.html', today=datetime.today().strftime('%d-%m-%Y'))


@blueprint.route('/create_comp', methods=['PUT'])
@login_required
def create_comp():

    data = request.json
    date_from = datetime.strptime(data['datefrom'], '%Y-%m-%d')
    date_to = datetime.strptime(data['dateto'], '%Y-%m-%d')
    new_comp = Comp(comp_name=data['name'],
                    comp_class=data['class'],
                    comp_site=data['location'],
                    comp_code=data['code'],
                    date_from=date_to,
                    date_to=date_from)
    output = new_comp.to_db()
    if type(output) == int:
        return jsonify(dict(redirect='/comp_admin'))
    else:
        return render_template('500.html')


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
    comp = Comp.read(compid)
    admins = ['joe smith', 'john wayne', 'stuartm', 'pippo', 'biuti']  # TODO

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
            comp.time_offset = compform.time_offset.data
            comp.restricted = 1 if compform.pilot_registration.data == 'registered' else None
            comp.formula = compform.formula.data
            comp.locked = compform.locked.data
            comp.to_db()

            formula = Formula.read(compid)
            formula.overall_validity = compform.overall_validity.data
            formula.validity_param = compform.validity_param.data/100
            formula.nominal_dist = compform.nom_dist.data*1000
            formula.nominal_goal = compform.nom_goal.data/100
            formula.min_dist = compform.min_dist.data*1000
            formula.nominal_launch = compform.nom_launch.data/100
            formula.nominal_time = compform.nom_time.data*60
            formula.no_goal_penalty = compform.no_goal_penalty.data
            formula.tolerance = compform.tolerance.data
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
            formula.country_scoring = compform.country_scoring.data
            formula.team_size = compform.team_size.data
            formula.team_over = compform.team_over.data

            formula.to_db()

            flash(f"{compform.comp_name.data} saved", category='info')
            return redirect(url_for('user.comp_settings_admin', compid=compid))
        else:
            flash("not valid")
            for item in compform:
                if item.errors:
                    print(f"{item} value:{item.data} error:{item.errors}")

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
        compform.time_offset.data = comp.time_offset
        compform.pilot_registration.data = comp.restricted
        compform.formula.data = formula.formula_name
        compform.overall_validity.data = formula.overall_validity
        formula.validity_param = 0 if not formula.validity_param else formula.validity_param
        formula.nominal_dist = 0 if not formula.nominal_dist else formula.nominal_dist
        formula.nominal_goal = 0 if not formula.nominal_goal else formula.nominal_goal
        formula.min_dist = 0 if not formula.min_dist else formula.min_dist
        formula.nominal_launch = 0 if not formula.nominal_launch else formula.nominal_launch
        formula.nominal_time = 0 if not formula.nominal_time else formula.nominal_time
        compform.validity_param.data = int(formula.validity_param*100)
        compform.nom_dist.data = int(formula.nominal_dist/1000)
        compform.nom_goal.data = int(formula.nominal_goal*100)
        compform.min_dist.data = int(formula.min_dist/1000)
        compform.nom_launch.data = int(formula.nominal_launch*100)
        compform.nom_time.data = int(formula.nominal_time/60)
        compform.team_scoring.data = formula.team_scoring
        compform.country_scoring.data = formula.country_scoring
        compform.team_size.data = formula.team_size
        compform.team_over.data = formula.team_over
        compform.formula_distance.data = formula.formula_distance
        compform.formula_arrival.data = formula.formula_arrival
        compform.formula_departure.data = formula.formula_departure
        compform.lead_factor.data = formula.lead_factor
        compform.formula_time.data = formula.formula_time
        compform.no_goal_penalty.data = formula.no_goal_penalty
        compform.glide_bonus.data = formula.glide_bonus
        compform.tolerance.data = formula.tolerance
        compform.min_tolerance.data = formula.min_tolerance
        compform.arr_alt_bonus.data = formula.arr_alt_bonus
        compform.arr_max_height.data = formula.arr_max_height
        compform.arr_min_height.data = formula.arr_min_height
        compform.validity_min_time.data = formula.validity_min_time
        compform.scoreback_time.data = formula.score_back_time
        compform.max_JTG.data = formula.max_JTG
        compform.JTG_penalty_per_sec.data = formula.JTG_penalty_per_sec
        compform.scoring_altitude.data = formula.scoring_altitude

        newtaskform.task_region.choices = frontendUtils.get_region_choices(compid)

        if current_user.username not in admins:
            compform.submit = None

    tasks = jsonify(frontendUtils.get_task_list(comp))

    return render_template('users/comp_settings.html', compid=compid, compform=compform, tasks=tasks,
                           taskform=newtaskform, admins=admins, error=error)


@blueprint.route('/task_admin/<taskid>', methods=['GET', 'POST'])
@login_required
def task_admin(taskid):
    from calcUtils import sec_to_time, time_to_seconds
    error = None
    taskform = TaskForm()
    turnpointform = NewTurnpointForm()
    modifyturnpointform = ModifyTurnpointForm()
    task = Task.read(int(taskid))
    waypoints = frontendUtils.get_waypoint_choices(task.reg_id)
    turnpointform.name.choices = waypoints
    modifyturnpointform.mod_name.choices = waypoints

    admins = ['john wayne', 'stuartm']  # TODO

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
            task.time_offset = taskform.time_offset.data*3600
            task.check_launch = 'on' if taskform.check_launch.data else 'off'
            task.airspace_check = taskform.airspace_check.data
            # task.openair_file = taskform.openair_file  # TODO get a list of openair files for this comp (in the case of defines.yaml airspace_file_library: off otherwise all openair files available)
            task.QNH = taskform.QNH.data
            task.formula.formula_distance = taskform.formula_distance.data
            task.formula.formula_arrival = taskform.formula_arrival.data
            task.formula.formula_departure = taskform.formula_departure.data
            task.formula.formula_time = taskform.formula_time.data
            task.formula.tolerance = taskform.tolerance.data
            task.formula.max_JTG = taskform.max_JTG.data
            task.formula.no_goal_penalty = taskform.no_goal_penalty.data
            task.formula.arr_alt_bonus = taskform.arr_alt_bonus.data
            task.to_db()

            flash("Saved", category='info')

            return redirect(url_for('user.task_admin', taskid=taskid))

        else:
            flash("not valid")
            for item in taskform:
                if item.errors:
                    print(f"{item} value:{item.data} error:{item.errors}")
                    stdout.flush()

    if request.method == 'GET':
        taskform.comp_name = task.comp_name
        taskform.task_name.data = task.task_name
        taskform.task_num.data = task.task_num
        taskform.comment.data = task.comment
        taskform.date.data = task.date
        taskform.task_type.data = task.task_type
        taskform.window_open_time.data = "" if not task.window_open_time else sec_to_time((task.window_open_time
                                                                                           + task.time_offset)%86400)
        taskform.window_close_time.data = "" if not task.window_close_time else sec_to_time((task.window_close_time
                                                                                             + task.time_offset)%86400)
        taskform.start_time.data = "" if not task.start_time else sec_to_time((task.start_time
                                                                               + task.time_offset)%86400)
        taskform.start_close_time.data = "" if not task.start_close_time else sec_to_time((task.start_close_time
                                                                                           + task.time_offset)%86400)
        taskform.stopped_time.data = "" if not task.stopped_time else sec_to_time((task.stopped_time
                                                                                   + task.time_offset)%86400)
        taskform.task_deadline.data = "" if not task.task_deadline else sec_to_time((task.task_deadline
                                                                                     + task.time_offset)%86400)
        taskform.SS_interval.data = task.SS_interval/60 # (convert from sec to min)
        taskform.start_iteration.data = task.start_iteration
        taskform.time_offset.data = task.time_offset/3600
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
        taskform.tolerance.data = task.formula.tolerance
        taskform.max_JTG.data = task.formula.max_JTG
        taskform.no_goal_penalty.data = task.formula.no_goal_penalty
        taskform.arr_alt_bonus.data = task.formula.arr_alt_bonus

        if current_user.username not in admins:
            taskform.submit = None

    return render_template('users/task_admin.html', taskid=taskid, taskform=taskform, turnpointform=turnpointform,
                           modifyturnpointform=modifyturnpointform, compid=task.comp_id, error=error)


@blueprint.route('/get_admin_comps', methods=['GET', 'POST'])
@login_required
def get_admin_comps():
    return frontendUtils.get_admin_comps()


@blueprint.route('/airspace_admin', methods=['GET', 'POST'])
@login_required
def airspace_admin():
    return render_template('users/airspace_admin.html')


@blueprint.route('/waypoint_admin', methods=['GET', 'POST'])
@login_required
def waypoint_admin():
    return render_template('users/waypoint_admin.html')


@blueprint.route('/pilot_admin', methods=['GET', 'POST'])
@login_required
def pilot_admin():
    return render_template('users/pilot_admin.html')


@blueprint.route('/_add_task/<compid>', methods=['POST'])
@login_required
def _add_task(compid):
    data = request.json
    task = Task(comp_id=compid)
    task.task_name = data['task_name']
    task.task_num = int(data['task_num'])
    task.date = datetime.strptime(data['task_date'], '%Y-%m-%d')
    task.comment = data['task_comment']
    task.reg_id = int(data['task_region'])
    task.to_db()
    comp = Comp()
    comp.comp_id = compid
    tasks = frontendUtils.get_task_list(comp)
    return jsonify(tasks)


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
    return jsonify(tasks)


@blueprint.route('/_get_adv_settings', methods=['GET','POST'])
@login_required
def _get_adv_settings():
    data = request.json
    formula = Formula.from_preset(data['category'], data['formula'])
    settings = {'distance': formula.formula_distance, 'arrival': formula.formula_arrival,
                'departure': formula.formula_departure, 'lead_factor': formula.lead_factor,
                'time': formula.formula_time, 'no_goal_penalty': formula.no_goal_penalty,
                'glide_bonus': formula.glide_bonus, 'tolerance': formula.tolerance,
                'min_tolerance': formula.min_tolerance, 'arr_alt_bonus': formula.height_bonus,
                'arr_max_height': formula.arr_max_height, 'arr_min_height': formula.arr_min_height,
                'validity_min_time': formula.validity_min_time, 'scoreback_time': formula.score_back_time,
                'max_JTG': formula.max_JTG, 'JTG_penalty_per_sec': formula.JTG_penalty_per_sec}

    return jsonify(settings)


@blueprint.route('/_get_task_turnpoints/<taskid>', methods=['GET'])
@login_required
def _get_task_turnpoints(taskid):
    task = Task(task_id=int(taskid))
    turnpoints = frontendUtils.get_task_turnpoints(task)
    return jsonify(turnpoints)


@blueprint.route('/_add_turnpoint/<taskid>', methods=['POST'])
@login_required
def _add_turnpoint(taskid):
    """add turnpoint to the task,if rwp_id is not null then update instead of insert (add)
    if turnpoint is goal or we are updating and goal exists then calculate opt dist and dist."""
    data = request.json
    taskid = int(taskid)
    if data['id']:
        data['id'] = int(data['id'])
    if data['type'] != 'goal':
        data['shape'] = 'circle'
    if data['type'] != 'speed':
        data['direction'] = 'entry'
    data['radius'] = int(data['radius'])
    data['number'] = int(data['number'])
    data['rwp_id'] = int(data['rwp_id'])

    tp = Turnpoint(radius=data['radius'], how=data['direction'], shape=data['shape'], type=data['type'],
                   id=data['number'], rwp_id=data['rwp_id'])
    if save_turnpoint(int(taskid), tp, data['id']):
        task = Task()
        task.task_id = taskid
        task = Task.read(taskid)
        if task.opt_dist > 0 or data['type'] == 'goal':
            task.calculate_optimised_task_length()
            task.calculate_task_length()
            task.update_task_distance()
            write_map_json(taskid)

        turnpoints = frontendUtils.get_task_turnpoints(task)
        return jsonify(turnpoints)
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
    return jsonify({'data': frontendUtils.get_pilot_list_for_track_management(taskid)})


@blueprint.route('/_get_tracks_processed/<taskid>', methods=['GET'])
@login_required
def _get_tracks_processed(taskid):
    tracks, pilots = frontendUtils.number_of_tracks_processed(taskid)
    return jsonify({'tracks': tracks, 'pilots': pilots})


@blueprint.route('/track_admin/<taskid>', methods=['GET'])
@login_required
def track_admin(taskid):
    return render_template('users/track_admin.html', taskid=taskid)


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
    if delete_result(trackid) == 1:
        data['Result'] = "Not Yet Processed"
        resp = jsonify(data)
        return resp
    else:
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

                tracklog = request.files["tracklog"]

                if tracklog.filename == "":
                    print("No filename")
                    return redirect(request.url)

                if frontendUtils.allowed_tracklog(tracklog.filename):
                    data = frontendUtils.process_igc(taskid, parid, tracklog)
                    resp = jsonify(data)
                    # resp = jsonify({'file': 'accepted'})
                    return resp

                else:
                    print("That file extension is not allowed")
                    return redirect(request.url)
            resp = jsonify({'error': 'filesize'})
            return resp
        resp = jsonify({'error': 'request.files'})
        return resp


@blueprint.route('/_upload_XCTrack/<taskid>', methods=['GET', 'POST'])
@login_required
def _upload_XCTrack(taskid):
    taskid = int(taskid)
    if request.method == "POST":
        if request.files:
            task_file = json.load(request.files["track_file"])
            print(task_file)
            stdout.flush()
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



@blueprint.route('/_upload_track_zip/<taskid>', methods=['GET', 'POST'])
@login_required
def _upload_track_zip(taskid):
    taskid = int(taskid)
    if request.method == "POST":
        if request.files:

            if "filesize" in request.cookies:

                if not frontendUtils.allowed_tracklog_filesize(request.cookies["filesize"]):
                    print("Filesize exceeded maximum limit")
                    return redirect(request.url)

                zip_file = request.files["zip_file"]

                if zip_file.filename == "":
                    print("No filename")
                    return redirect(request.url)

                if frontendUtils.allowed_tracklog(zip_file.filename, extension=['zip']):
                    task = Task.read(taskid)
                    data = frontendUtils.process_igc_zip(task, zip_file)
                    resp = jsonify(data)
                    return resp

                else:
                    print("That file extension is not allowed")
                    return redirect(request.url)
            resp = jsonify({'error': 'filesize'})
            return resp
        resp = jsonify({'error': 'request.files'})
        return resp


@blueprint.route('/_get_task_result_files/<taskid>', methods=['GET', 'POST'])
@login_required
def _get_task_result_files(taskid):
    data = request.json
    files = frontendUtils.get_task_result_file_list(int(taskid))
    header, active = frontendUtils.get_score_header(files, data['offset'])
    choices = []
    offset = (int(data['offset'])/60*-1)*3600
    for file in files:
        published = time.ctime(file['created'] + offset)
        choices.append((file['filename'], f"{published} - {file['status']}"))
    choices.reverse()
    return jsonify({'choices': choices, 'header': header, 'active': active})


@blueprint.route('/_get_task_score_from_file/<taskid>/<filename>', methods=['GET'])
@login_required
def _get_task_score_from_file(taskid, filename):
    error = None
    result_file = get_task_json_by_filename(filename)
    if not result_file:
        return jsonify({'data': ''})
    taskid = int(taskid)
    rank = 1
    all_pilots = []
    for r in result_file['results']:
        track_id = r['track_id']
        name = r['name']
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
        pilot['speedP']  = round(r['time_score'], 2)
        pilot['leadP'] = round(r['departure_score'], 2)
        pilot['arrivalP'] = round(r['arrival_score'], 2) # arrival points
        pilot['distanceP'] = round(r['distance_score'], 2)
        pilot['penalty'] = round(r['penalty'], 2) if r['penalty'] else ""
        pilot['score'] = round(r['score'], 2)
        # TODO once result files have a list of comments we can activate these lines and remove the 3 dummy lines below
        # pilot['Track Comment'] = r['comment'][0]
        # pilot['Penalty Comment'] = r['comment'][1]
        # pilot['Admin Comment'] = r['comment'][2]
        pilot['Track Comment'] = 'test track comment'
        pilot['Penalty Comment'] = 'test penalt comment'
        pilot['Admin Comment'] = 'test admin comment'

        all_pilots.append(pilot)
        rank += 1

    return jsonify({'data': all_pilots})


@blueprint.route('/task_score_admin/<taskid>', methods=['GET', 'POST'])
@login_required
def task_score_admin(taskid):
    taskid = int(taskid)
    fileform = TaskResultAdminForm()
    active_file = None
    # files = frontendUtils.get_task_result_file_list(taskid)
    choices = [(1,1),(2,2)]
    # for file in files:
    #     # published = ''
    #     if file['active'] == 1:
    #         active_file = file['filename']
    #         # published = " - published"
    #     choices.append((file['filename'], f"{time.ctime(file['created'])} - {file['status']}"))
    fileform.result_file.choices = choices
    if active_file:
        fileform.result_file.data = active_file

    return render_template('users/task_score_admin.html', fileform=fileform, taskid=taskid,
                           active_file=active_file)


@blueprint.route('/_score_task/<taskid>', methods=['POST'])
@login_required
def _score_task(taskid):
    from result import unpublish_result, publish_result
    """score task, request data should contain status: the score status (provisional, official etc),
    autopublish: True or False. indicates if to publish results automatically after scoring"""
    data = request.json
    taskid = int(taskid)
    task = Task.read(taskid)
    ref_id = task.create_results(data['status'])
    if ref_id:
        if data['autopublish']:
            unpublish_result(taskid)
            publish_result(ref_id, ref_id=True)
        return jsonify(dict(redirect='/users/task_score_admin/' + str(taskid)))
    return render_template('500.html')


@blueprint.route('/_unpublish_result/<taskid>', methods=['POST'])
@login_required
def _unpublish_result(taskid):
    from result import unpublish_result
    unpublish_result(taskid)
    header = "No published results"
    resp = jsonify(filename='', header=header)
    return resp


@blueprint.route('/_publish_result/<taskid>', methods=['POST'])
@login_required
def _publish_result(taskid):
    from result import publish_result, unpublish_result
    data = request.json
    unpublish_result(taskid)
    publish_result(data['filename'])
    run_at, status = data['filetext'].split('-')
    header = f"Published result ran at:{run_at} Status:{status}"
    resp = jsonify(filename=data['filename'], header=header)
    return resp


@blueprint.route('/_change_result_status/<taskid>', methods=['POST'])
@login_required
def _change_result_status(taskid):
    from result import update_result_status
    data = request.json
    update_result_status(data['filename'], data['status'])
    resp = jsonify(success=True)
    return resp

