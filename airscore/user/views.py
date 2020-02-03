# -*- coding: utf-8 -*-
"""User views."""
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
import frontendUtils
from airscore.user.forms import NewTaskForm, CompForm
from comp import Comp
from formula import list_formulas, Formula

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
    comp = Comp.read(compid)
    formula = Formula.read(compid)
    compform = CompForm()
    newtaskform = NewTaskForm()

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
    compform.validity_param.data = formula.validity_param*100
    compform.nom_dist.data = formula.nominal_dist/1000
    compform.nom_goal.data = formula.nominal_goal*100
    compform.min_dist.data = formula.min_dist/1000
    compform.nom_launch.data = formula.nominal_launch*100
    compform.nom_time.data = formula.nominal_time/60
    # compform.team_scoring = formula. TODO
    compform.formula.choices = [(1, '1'), (2, '2')]

    admins = ['joe smith', 'john wayne', 'astuart']  # TODO

    if current_user.username not in admins:
        compform.submit = None

    if compform.validate_on_submit():
        return f'Start Date is : {compform.date_from} End Date is : {compform.date_to}'
    else:
        error = flash("Start date is greater than End date")


    tasks = frontendUtils.get_task_list(comp)



    # if request.method == 'GET':
    return render_template('users/comp_settings.html', compid=compid , compform=compform, tasks=tasks, taskform=newtaskform, admins=admins, error=error)


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