# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    jsonify
)
from flask_login import login_required, login_user, logout_user

from airscore.extensions import login_manager
from airscore.public.forms import LoginForm
from airscore.user.forms import RegisterForm
from airscore.user.models import User
from airscore.utils import flash_errors

import datetime
from task import get_map_json
from trackUtils import read_result_file
from design_map import *
# from wtforms.widgets import ListWidget, CheckboxInput
# from wtforms.validators import Required
from calcUtils import sec_to_time
import os
import json
import Defines as d
from myconn import Database
from sqlalchemy import func, not_
from sqlalchemy.orm import aliased

# from branca.element import Element, MacroElement
# from jinja2 import Template

blueprint = Blueprint("public", __name__, static_folder="../static")


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))

#
# @blueprint.route("/", methods=["GET", "POST"])
# def home():
#     """Home page."""
#     form = LoginForm(request.form)
#     current_app.logger.info("Hello from the home page!")
#     Handle logging in
#     if request.method == "POST":
#         if form.validate_on_submit():
#             login_user(form.user)
#             flash("You are logged in.", "success")
#             redirect_url = request.args.get("next") or url_for("user.members")
#             return redirect(redirect_url)
#         else:
#             flash_errors(form)
#     return render_template("public/home.html", form=form)


@blueprint.route("/", methods=["GET", "POST"])
def home():
    return render_template('public/index.html')


@blueprint.route("/logout/")
@login_required
def logout():
    """Logout."""
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            active=True,
        )
        flash("Thank you for registering. You can now log in.", "success")
        return redirect(url_for("public.home"))
    else:
        flash_errors(form)
    return render_template("public/register.html", form=form)


@blueprint.route("/about/")
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template("public/about.html", form=form)


@blueprint.route('/get_all_comps', methods=['GET', 'POST'])
def get_all_comps():
    from db_tables import tblCompetition, tblTask

    c = aliased(tblCompetition)

    with Database() as db:
        comps = (db.session.query(c.comPk, c.comName, c.comLocation,
                 c.comClass, c.comSanction, c.comType, c.comDateFrom,
                 c.comDateTo, func.count(tblTask.tasPk))
                 .outerjoin(tblTask, c.comPk == tblTask.comPk)
                 .group_by(c.comPk))

    all_comps = []
    now = datetime.datetime.now()
    for c in comps:
        comp = list(c)
        if comp[5] == 'RACE' or comp[5] == 'Route':
            compid = comp[0]
            name = comp[1]
            comp[1] = f'<a href="/competition/{compid}">{name}</a>'
        # else:
            # comp['comName'] = "<a href=\"comp_overall.html?comPk=$id\">" . $row['comName'] . '</a>';
        if comp[3] == "PG" or "HG":
            hgpg = comp[3]
            comp[3] = f'<img src="/static/build/img/{hgpg}.png" width="100%" height="100%"</img>'
        else:
            comp[3] = ''
        if comp[4] != 'none' and comp[4] != '':
            comp[5] = comp[5] + ' - ' + comp[4]
        starts = comp[6]
        ends = comp[7]
        if starts > now:
            comp.append(f"Starts in {(starts-now).days} day(s)")
        elif ends < now:
            comp.append('Finished')
        else:
            comp.append('Running')

        comp[6] = comp[6].strftime("%Y-%m-%d")
        comp[7] = comp[7].strftime("%Y-%m-%d")
        del comp[4]
        del comp[0]
        all_comps.append(comp)
    return jsonify({'data': all_comps})


@blueprint.route('/competition/<compid>')
def competition(compid):
    from db_tables import tblTask, tblCompetition, tblResultFile
    from compUtils import get_comp_json
    result_file = get_comp_json(int(compid))
    all_tasks = []
    layer = {}
    task_ids = []
    if result_file != 'error':
        for task in result_file['tasks']:
            task_ids.append(task['id'])
            wpt_coords, turnpoints, short_route, goal_line, tolerance, bbox= get_map_json(task['id'])
            layer['geojson'] = None
            layer['bbox'] = bbox
            map = make_map(layer_geojson=layer, points=wpt_coords, circles=turnpoints, polyline=short_route, goal_line=goal_line, margin=tolerance)
            task['tasDistance'] = '{:0.2f}'.format(task['opt_distance']/1000) + ' km'
            task['tasQuality'] = '{:0.2f}'.format(task['day_quality'])
            task.update({'map':map._repr_html_()})
            all_tasks.append(task)

    c = aliased(tblCompetition)
    t = aliased(tblTask)

    with Database() as db:
        non_scored_tasks = (db.session.query(t.tasPk,
                 t.tasName,
                 t.tasDate,
                 t.tasTaskType,
                 t.tasDistance,
                 t.tasComment).filter(t.comPk == compid, t.comPk.notin_(task_ids))
                 .order_by(t.tasDate.desc()).all())

        competition_info = (db.session.query(
                c.comName,
                c.comLocation,
                c.comDateFrom,
                c.comDateTo).filter(c.comPk == compid).one())
    comp = competition_info._asdict()
    if comp['comDateFrom']:
        comp['comDateFrom'] = comp['comDateFrom'].strftime("%Y-%m-%d")
    if comp['comDateTo']:
        comp['comDateTo'] = comp['comDateTo'].strftime("%Y-%m-%d")

    if non_scored_tasks:
        for t in non_scored_tasks:
            task = t._asdict()
            wpt_coords, turnpoints, short_route, goal_line, tolerance, bbox= get_map_json(task['tasPk'])
            layer['geojson'] = None
            layer['bbox'] = bbox
            map = make_map(layer_geojson=layer, points=wpt_coords, circles=turnpoints, polyline=short_route, goal_line=goal_line, margin=tolerance)
            task['tasDistance'] = '{:0.2f}'.format(task['tasDistance']/1000) + ' km'
            task.update({'map':map._repr_html_()})
            task['tasQuality'] = "-"
            task['status'] = "Not yet scored"
            all_tasks.append(task)
    return render_template('public/comp.html', tasks=all_tasks, comp=comp)


@blueprint.route('/task_result/<taskid>')
def task_result(taskid):
    return render_template('public/task_result.html')


@blueprint.route('/get_task_result/<taskid>', methods=['GET', 'POST'])
def get_task_result(taskid):
    filename = 'LEGA19_2_T1_20191116_154121.json'
    with open(d.RESULTDIR+filename, 'r') as myfile:
        data=myfile.read()
    if not data:
        return "error"

    result_file = json.loads(data)
    del result_file['data']
    rank=1
    all_pilots = []
    for r in result_file['results']:  #need sex??
        pilot = []
        track_id = r['track_id']
        name = r['name']
        pilot.append(f'<b>{rank}</b>')
        pilot.append(f'<a href="/map/{track_id}">{name}</a>')
        pilot.append(r['nat'])
        pilot.append(r['glider'])
        pilot.append(r['class'])
        pilot.append(r['sponsor'])
        if r['SS_time']:
            pilot.append(sec_to_time(r['SS_time']+result_file['info']['time_offset']).strftime("%H:%M:%S"))
        else:
            pilot.append("")
        if r['ES_time'] == 0 or r['ES_time'] is None :
            pilot.append("")
            pilot.append("")
        else:
            pilot.append(sec_to_time(r['ES_time']+result_file['info']['time_offset']).strftime("%H:%M:%S"))
            pilot.append(sec_to_time(r['ES_time']-r['SS_time']).strftime("%H:%M:%S"))
        pilot.append(round(r['speed'],2) if r['speed'] else "")
        pilot.append("")  # altitude bonus
        pilot.append(round(r['distance']/1000,2))
        pilot.append(round(r['time_points'],2))
        pilot.append(round(r['dep_points'],2))
        pilot.append("")  # arrival points
        pilot.append(round(r['dist_points'],2))
        pilot.append(round(r['penalty'],2) if r['penalty'] else "")
        pilot.append(round(r['score'], 2))
        all_pilots.append(pilot)
        rank += 1
    result_file['data']= all_pilots
    all_classes = []
    for glider_class in result_file['rankings']:
        if glider_class[-5:].lower() == 'class':
            comp_class = {}
            comp_class['name'] = glider_class
            comp_class['limit'] = result_file['rankings'][glider_class][-1]
            all_classes.append(comp_class)
    all_classes.reverse()
    result_file['classes'] = all_classes
    return jsonify(result_file)


@blueprint.route('/comp_result/<compid>')
def comp_result(compid):
    return render_template('public/comp_overall.html')


@blueprint.route('/get_comp_result/<compid>', methods=['GET', 'POST'])
def get_comp_result(compid):
    from compUtils import get_comp_json
    result_file = get_comp_json(compid)
    if result_file == 'error':
        return render_template('404.html')
    all_pilots = []
    rank = 1
    for r in result_file['results']:
        pilot = []
        pilot.append(rank)
        pilot.append(r['fai'])
        pilot.append(r['civl'])
        pilot.append(r['name'])
        pilot.append(r['nat'])
        pilot.append(r['sex'])
        pilot.append(r['sponsor'])
        pilot.append(r['glider'])
        pilot.append(r['class'])
        pilot.append(f"<b>{int(r['score'])}</b>")
        for task in r['results']:
            if r['results'][task]['pre'] == r['results'][task]['score']:
                pilot.append(r['results'][task]['score'])
            else:
                pilot.append(f"{int(r['results'][task]['score'])} <del>{int(r['results'][task]['pre'])}</del>")
        # add blanks to get to a total of 16 tasks
        for t in range(len(r['results']), 16):
            pilot.append("")

        rank += 1
        all_pilots.append(pilot)
    result_file['data']= all_pilots

    total_validity = 0
    for task in result_file['tasks']:
        total_validity += task['ftv_validity']

    result_file['stats']['tot_validity'] = total_validity
    all_classes = []
    for glider_class in result_file['rankings']:
        if glider_class[-5:].lower() == 'class':
            comp_class = {}
            comp_class['name'] = glider_class
            comp_class['limit'] = result_file['rankings'][glider_class][-1]
            all_classes.append(comp_class)
    all_classes.reverse()
    result_file['classes'] = all_classes
    return jsonify(result_file)
