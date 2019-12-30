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
from task import get_map_json, get_task_json
from trackUtils import read_track_result_file
from design_map import *
# from wtforms.widgets import ListWidget, CheckboxInput
# from wtforms.validators import Required
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField, SelectField, SelectMultipleField
from calcUtils import sec_to_time
import os
import json
import Defines as d
import mapUtils
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


@blueprint.route("/old", methods=["GET", "POST"])
def home_old():
    """Home page."""
    form = LoginForm(request.form)
    current_app.logger.info("Hello from the home page!")
    # Handle logging in
    if request.method == "POST":
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", "success")
            redirect_url = request.args.get("next") or url_for("user.members")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template("public/home.html", form=form)


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
            comp[3] = f'<img src="/static/img/{hgpg}.png" width="100%" height="100%"</img>'
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
    overall_available = False
    if result_file != 'error':
        overall_available = True
        for task in result_file['tasks']:
            task_ids.append(int(task['id']))
            wpt_coords, turnpoints, short_route, goal_line, tolerance, bbox = get_map_json(task['id'])
            layer['geojson'] = None
            layer['bbox'] = bbox
            task_map = make_map(layer_geojson=layer, points=wpt_coords, circles=turnpoints, polyline=short_route,
                                goal_line=goal_line, margin=tolerance)
            task['opt_dist'] = '{:0.2f}'.format(task['opt_dist']/1000) + ' km'
            task['tasQuality'] = '{:0.2f}'.format(task['day_quality'])
            task.update({'map': task_map._repr_html_()})
            all_tasks.append(task)

    c = aliased(tblCompetition)
    t = aliased(tblTask)

    with Database() as db:
        non_scored_tasks = (db.session.query(t.tasPk.label('id'),
                 t.tasName.label('task_name'),
                 t.tasDate.label('date'),
                 t.tasTaskType.label('task_type'),
                 t.tasShortRouteDistance,
                 t.tasComment.label('comment')).filter(t.comPk == compid, t.tasPk.notin_(task_ids))
                 .order_by(t.tasDate.desc()).all())

        competition_info = (db.session.query(
                c.comPk,
                c.comName,
                c.comLocation,
                c.comDateFrom,
                c.comDateTo).filter(c.comPk == compid).one())
    comp = competition_info._asdict()

    comp_start = comp['comDateFrom']

    if comp['comDateFrom']:
        comp['comDateFrom'] = comp['comDateFrom'].strftime("%Y-%m-%d")
    if comp['comDateTo']:
        comp['comDateTo'] = comp['comDateTo'].strftime("%Y-%m-%d")

    if comp_start > datetime.datetime.now():
        return render_template('public/future_competition.html', comp=comp)

    if non_scored_tasks:
        for t in non_scored_tasks:
            task = t._asdict()
            wpt_coords, turnpoints, short_route, goal_line, tolerance, bbox = get_map_json(task['id'])
            layer['geojson'] = None
            layer['bbox'] = bbox
            map = make_map(layer_geojson=layer, points=wpt_coords, circles=turnpoints, polyline=short_route,
                           goal_line=goal_line, margin=tolerance)
            task['opt_dist'] = '{:0.2f}'.format(task['tasShortRouteDistance']/1000) + ' km'
            task.update({'map': map._repr_html_()})
            task['tasQuality'] = "-"
            task['status'] = "Not yet scored"
            task['date'] = task['date'].strftime("%Y-%m-%d")
            all_tasks.append(task)
    all_tasks.sort(key=lambda k: k['date'], reverse=True)

    return render_template('public/comp.html', tasks=all_tasks, comp=comp, overall_available=overall_available)


@blueprint.route('/task_result/<taskid>')
def task_result(taskid):
    return render_template('public/task_result.html', taskid=taskid)


@blueprint.route('/get_task_result/<taskid>', methods=['GET', 'POST'])
def get_task_result(taskid):

    result_file = get_task_json(taskid)
    if result_file == 'error':
        return render_template('404.html')

    rank = 1
    all_pilots = []
    for r in result_file['results']:  # need sex??
        pilot = []
        track_id = r['track_id']
        name = r['name']
        pilot.append(f'<b>{rank}</b>')
        pilot.append(f'<a href="/map/{track_id}-{taskid}">{name}</a>')
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
        pilot.append(round(r['distance']/1000, 2))
        pilot.append(round(r['time_points'], 2))
        pilot.append(round(r['dep_points'], 2))
        pilot.append("")  # arrival points
        pilot.append(round(r['dist_points'], 2))
        pilot.append(round(r['penalty'], 2) if r['penalty'] else "")
        pilot.append(round(r['score'], 2))
        all_pilots.append(pilot)
        rank += 1
    result_file['data'] = all_pilots
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
    return render_template('public/comp_overall.html', compid=compid)


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
        pilot.append(r['fai_id'])
        pilot.append(r['civl_id'])
        pilot.append(r['name'])
        pilot.append(r['nat'])
        pilot.append(r['sex'])
        pilot.append(r['sponsor'])
        pilot.append(r['glider'])
        pilot.append(r['glider_cert'])
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
    result_file['data'] = all_pilots

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


class SelectAdditionalTracks(FlaskForm):
    track_pilot_list =[]
    tracks = SelectField('Add Tracks:', choices=track_pilot_list)


@blueprint.route('/map/<trackidtaskid>')
def map(trackidtaskid):
    trackid, taskid = trackidtaskid.split("-")
    trackid = int(trackid)
    taskid = int(taskid)
    layer = {}
    wpt_coords, turnpoints, short_route, goal_line, tolerance, _ = get_map_json(taskid)
    layer['geojson'] = read_track_result_file(trackid, taskid)
    layer['bbox'] = layer['geojson']['bounds']
    pilot = layer['geojson']['info']['pilot_name']
    task_name = layer['geojson']['info']['task_name']
    parid = layer['geojson']['info']['pilot_parid']
    other_tracks = mapUtils.get_other_tracks(taskid, parid)

    map = make_map(layer_geojson=layer, points=wpt_coords, circles=turnpoints, polyline=short_route,
                   goal_line=goal_line, margin=tolerance, thermal_layer=True, waypoint_layer=True)
    waypoint_achieved_list = list(w for w in layer['geojson']['waypoint_achieved'])
    add_tracks = SelectAdditionalTracks()
    add_tracks.track_pilot_list = other_tracks
    return render_template('public/map.html', other_tracks=other_tracks, add_tracks=add_tracks, map=map._repr_html_(),
                           wpt_achieved=waypoint_achieved_list, task=task_name, pilot=pilot)

@blueprint.route('/_map/<trackid>/<extra_trackids>')
def multimap(trackid, extra_trackids):
    trackids=[]
    for t in extra_trackids.split(','):
        trackids.append(t)
    # if trackids is None:
    #     map(trackid)
    layer={}
    extra_layer={}
    print(f"trackid={trackid} trackids={trackids}")
    wpt_coords, turnpoints, short_route, goal_line, tolerance = get_task_json(66)
    colours = ['#0000ff', '#33cc33', '#ffff00', '#9900cc', '#006600', '#3399ff', '#ff99cc', '#663300', '#99ffcc']
    #blue, green, yellow, purple, dark green,light blue, pink, brown, turquoise
    c = 0
    legend = {}
    extra_tracks = []
    for t in trackids:
        layer['geojson'] = read_track_result_file(t, 66)
        track = {}
        track['name'] = t
        track['track'] = layer['geojson']['tracklog']
        track['colour'] = colours[c]
        extra_tracks.append(track)
        legend[t] = colours[c]
        c += 1

    layer['geojson'] = read_track_result_file(trackid, 66)
    layer['bbox'] = layer['geojson']['bounds']
    map = make_map(layer_geojson=layer, points=wpt_coords, circles=turnpoints, polyline=short_route,
                   goal_line=goal_line, margin=tolerance, thermal_layer=False, waypoint_layer=False,
                   extra_tracks=extra_tracks)
    waypoint_achieved_list = list(list(w for w in layer['geojson']['waypoint_achieved']))
    pilot_name = trackids
    c = 0

    map_id = map.get_name()

    macro = mapUtils.map_legend(legend)
    map.get_root().add_child(macro)
    map = map._repr_html_()
    return map


@blueprint.route('/airspace_map')
def airspace_edit():
    from aerofiles import openair
    import jsonpickle
    import airspace
    import design_map
    from itertools import tee
    from mapUtils import get_airspace_bbox

    filename = '/app/airscore/data/test/test_openair.txt'
    message = ''
    spaces = []
    unknown_flag = False
    FL_detail = None

    with open(filename) as fp:
        reader = openair.Reader(fp)
        reader, reader_2 = tee(reader)
        bbox = get_airspace_bbox(reader_2)
        airspace_list = []
        for record, error in reader:
            if error:
                raise error  # or handle it otherwise
            if record['type'] == 'airspace':
                airspace_list.append(airspace.airspace_info(record))
                polygon = airspace.polygon_map(record)
                if polygon:
                    spaces.append(polygon)
                for element in record['elements']:
                    if element['type'] == 'circle':
                        spaces.append(airspace.circle_map(element, record))

    for space in airspace_list:
        if space["floor unit"] == "FL":
            FL_detail = f"{space['floor description']} is {int(space['floor'])*100} ft or {int(space['floor'])*100*0.3048} m"
            space['floor'] = None

        if space["ceiling unit"] == "FL":
            FL_detail = f"{space['ceiling description']} is {int(space['ceiling']) * 100} ft or {int(space['ceiling']) * 100 * 0.3048} m"
            space['ceiling'] = None
            
        if space["floor unit"] == "Unknown height unit" or space["ceiling unit"] == "Unknown height unit":
            unknown_flag = True

    if FL_detail:
        message = 'Attention: There is FL units in the file. You should adjust to meters or feet above sea level'
        FL_detail +=" assuming an International Standard Atmosphere pressure of 1013.25. " \
                    "You should round down to be conservative"
    if unknown_flag:
        message += 'Attention: There is unknown height units in the file. You should adjust to meters or ' \
                   'feet above sea level'
    data = jsonpickle.encode(spaces)
    fullname: str = 'test_airspace'

    map = design_map.make_map(airspace_layer=spaces, bbox=bbox)
    # map.save('map.html')
    return render_template('users/airspace_admin_map.html', airspace_list=airspace_list, file=filename,
                           map=map._repr_html_(), message = message, FL_message = FL_detail)