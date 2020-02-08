# -*- coding: utf-8 -*-
"""User views."""
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import frontendUtils
from airscore.user.forms import NewTaskForm, CompForm
from comp import Comp
from formula import list_formulas, Formula
from task import Task
import json
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
        # compform.team_scoring.data = formula.
        # compform.country_scoring.data = formula.
        # compform.team_size.data = formula.
        # compform.team_over.data = formula.
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





        if current_user.username not in admins:
            compform.submit = None

    tasks = jsonify(frontendUtils.get_task_list(comp))

    return render_template('users/comp_settings.html', compid=compid, compform=compform, tasks=tasks,
                           taskform=newtaskform, admins=admins, error=error)


@blueprint.route('/task_admin/<taskid>', methods=['GET', 'POST'])
@login_required
def task_admin(taskid):
    return render_template('users/task_admin.html', taskid=taskid)


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
    task.to_db()
    comp = Comp()
    comp.comp_id = compid
    tasks = frontendUtils.get_task_list(comp)
    return jsonify(tasks)


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