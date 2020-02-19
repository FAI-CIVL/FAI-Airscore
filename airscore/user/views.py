# -*- coding: utf-8 -*-
"""User views."""
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import frontendUtils
from airscore.user.forms import NewTaskForm, CompForm, TaskForm, NewTurnpointForm, ModifyTurnpointForm
from comp import Comp
from formula import list_formulas, Formula
from task import Task, write_map_json
import json
from route import save_turnpoint, Turnpoint
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
    admins = ['joe smith', 'john wayne', 'stuart']  # TODO

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
            comp.update_comp_info()

            formula = Formula.read(compid)
            formula.overall_validity = compform.overall_validity.data
            formula.validity_param = compform.validity_param.data/100
            formula.nominal_dist = compform.nom_dist.data*1000
            formula.nominal_goal = compform.nom_goal.data/100
            formula.min_dist = compform.min_dist.data*1000
            formula.nominal_launch = compform.nom_launch.data/100
            formula.nominal_time = compform.nom_time.data*60
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
        compform.team_scoring.data = formula.TeamScoring
        compform.country_scoring.data = formula.CountryScoring
        compform.team_size.data = formula.TeamSize
        compform.team_over.data = formula.TeamOver
        compform.distance.data = formula.formula_distance
        compform.arrival.data = formula.formula_arrival
        compform.departure.data = formula.formula_departure
        compform.lead_factor.data = formula.lead_factor
        compform.time.data = formula.formula_time
        compform.no_goal_pen.data = formula.no_goal_penalty
        compform.glide_bonus.data = formula.glide_bonus
        compform.tolerance.data = formula.tolerance
        compform.min_tolerance.data = formula.min_tolerance
        compform.height_bonus.data = formula.height_bonus
        compform.ESS_height_upper.data = formula.arr_max_height
        compform.ESS_height_lower.data = formula.arr_min_height
        compform.min_time.data = formula.validity_min_time
        compform.scoreback_time.data = formula.score_back_time
        compform.max_JTG.data = formula.max_JTG
        compform.JTG_pen_sec.data = formula.JTG_penalty_per_sec
        compform.alt_mode.data = formula.scoring_altitude

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
    from sys import stdout
    error = None
    taskform = TaskForm()
    turnpointform = NewTurnpointForm()
    modifyturnpointform = ModifyTurnpointForm()
    task = Task.read(int(taskid))
    waypoints = frontendUtils.get_waypoint_choices(task.reg_id)
    turnpointform.name.choices = waypoints
    modifyturnpointform.mod_name.choices = waypoints

    admins = ['john wayne', 'stuart']  # TODO

    if request.method == 'POST':
        if taskform.validate_on_submit():
            task.comp_name = taskform.comp_name
            task.task_name = taskform.task_name.data
            task.task_num = taskform.task_num.data
            task.comment = taskform.comment.data
            task.date = taskform.date.data
            task.task_type = taskform.task_type.data
            task.window_open_time = time_to_seconds(taskform.window_open_time.data)
            task.window_close_time = time_to_seconds(taskform.window_close_time.data)
            task.start_time = time_to_seconds(taskform.start_time.data)
            task.start_close_time = time_to_seconds(taskform.start_close_time.data)
            task.stopped_time = None if taskform.stopped_time.data is None else time_to_seconds(taskform.stopped_time.data)
            task.task_deadline = time_to_seconds(taskform.task_deadline.data)
            task.SS_interval = taskform.SS_interval.data * 60  # (convert from min to sec)
            task.start_iteration = taskform.start_iteration.data
            task.time_offset = int(taskform.time_offset.data * 3600)  # (convert from hours to seconds)
            task.check_launch = 'on' if taskform.check_launch.data else 'off'
            task.airspace_check = taskform.airspace_check.data
            # task.openair_file = taskform.openair_file  # TODO get a list of openair files for this comp (in the case of defines.yaml airspace_file_library: off otherwise all openair files available)
            task.QNH = taskform.QNH.data
            task.update_task_info()

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
        taskform.window_open_time.data = "" if not task.window_open_time else sec_to_time(task.window_open_time)
        taskform.window_close_time.data = "" if not task.window_close_time else sec_to_time(task.window_close_time)
        taskform.start_time.data = "" if not task.start_time else sec_to_time(task.start_time)
        taskform.start_close_time.data = "" if not task.start_close_time else sec_to_time(task.start_close_time)
        taskform.stopped_time.data = "" if not task.stopped_time else sec_to_time(task.stopped_time)
        taskform.task_deadline.data = "" if not task.task_deadline else sec_to_time(task.task_deadline)
        taskform.SS_interval.data = task.SS_interval/60 # (convert from sec to min)
        taskform.start_iteration.data = task.start_iteration
        taskform.time_offset.data = task.time_offset/3600 # (convert from seconds to hours)
        taskform.check_launch.data = task.check_launch
        taskform.airspace_check.data = task.airspace_check
        # taskform.openair_file.data = task.openair_file # TODO get a list of openair files for this comp (in the case of defines.yaml airspace_file_library: off otherwise all openair files available)
        taskform.QNH.data = task.QNH
        # taskform.region.data = task.reg_id # TODO get a list of waypoint files for this comp (in the case of defines.yaml waypoint_file_library: off otherwise all regions available)
        # taskform.region.choices = frontendUtils.get_region_choices(compid)

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
    task = Task()
    task.comp_id = compid
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


@blueprint.route('/_get_adv_settings', methods=['GET'])
@login_required
def _get_adv_settings():
    data = request.json
    formula = Formula.from_preset(data['category'], data['formula'])
    settings= {}
    settings['distance'] = formula.formula_distance
    settings['arrival'] = formula.formula_arrival
    settings['departure'] = formula.formula_departure
    settings['lead_factor'] = formula.lead_factor
    settings['time'] = formula.formula_time
    settings['no_goal_pen'] = formula.no_goal_penalty
    settings['glide_bonus'] = formula.glide_bonus
    settings['tolerance'] = formula.tolerance
    settings['min_tolerance'] = formula.min_tolerance
    settings['height_bonus'] = formula.height_bonus
    settings['ESS_height_upper'] = formula.arr_max_height
    settings['ESS_height_lower'] = formula.arr_min_height
    settings['min_time'] = formula.validity_min_time
    settings['scoreback_time'] = formula.score_back_time
    settings['max_JTG'] = formula.max_JTG
    settings['JTG_pen_sec'] = formula.JTG_penalty_per_sec
    settings['alt_mode'] = formula.scoring_altitude

    return jsonify(settings)


@blueprint.route('/_get_task_turnpoints/<taskid>', methods=['GET'])
@login_required
def _get_task_turnpoints(taskid):
    task = Task()
    task.task_id = taskid
    turnpoints = frontendUtils.get_task_turnpoints(task)
    return jsonify(turnpoints)


@blueprint.route('/_add_turnpoint/<taskid>', methods=['POST'])
@login_required
def _add_turnpoint(taskid):
    """add turnpoint to the task,if rwpPk is not null then update instead of insert (add)
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
    data['rwpPk'] = int(data['rwpPk'])

    tp = Turnpoint(radius=data['radius'], how=data['direction'], shape=data['shape'], type=data['type'],
                   id=data['number'], rwpPk=data['rwpPk'])
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
    print(data)
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
