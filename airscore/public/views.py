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
    jsonify,
    send_file
)
from flask_login import login_required, login_user, logout_user, current_user
from airscore.extensions import login_manager
from airscore.public.forms import LoginForm
from airscore.user.forms import RegisterForm
from airscore.user.models import User
from airscore.utils import flash_errors
from datetime import datetime
from task import get_map_json, get_task_json
from trackUtils import read_track_result_file
from design_map import make_map
from flask_wtf import FlaskForm
from wtforms import SelectField
from calcUtils import sec_to_time
import mapUtils
from myconn import Database
from sqlalchemy.orm import aliased
import Defines
from os import path
import frontendUtils

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
    flash("333")
    return render_template("public/home.html", form=form)


@blueprint.route("/", methods=["GET", "POST"])
def home():
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == "POST":
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", "success")
            redirect_url = request.args.get("next") or url_for("user.members")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template('public/index.html', form=form)


@blueprint.route("/ladders/", methods=["GET", "POST"])
def ladders():
    return render_template('public/ladders.html')


@blueprint.route("/pilots/", methods=["GET", "POST"])
def pilots():
    return render_template('public/pilots.html')


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
    return frontendUtils.get_comps()


@blueprint.route('/competition/<compid>')
def competition(compid):
    from db_tables import TblTask, TblCompetition
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
            task['opt_dist'] = '{:0.2f}'.format(task['opt_dist'] / 1000) + ' km'
            task['tasQuality'] = '{:0.2f}'.format(task['day_quality'])
            task.update({'map': task_map._repr_html_()})
            all_tasks.append(task)

    c = aliased(TblCompetition)
    t = aliased(TblTask)

    with Database() as db:
        non_scored_tasks = (db.session.query(t.task_id.label('id'),
                                             t.task_name,
                                             t.date,
                                             t.task_type,
                                             t.opt_dist,
                                             t.comment).filter(t.comp_id == compid, t.task_id.notin_(task_ids))
                            .order_by(t.date.desc()).all())

        competition_info = (db.session.query(
            c.comp_id,
            c.comp_name,
            c.comp_site,
            c.date_from,
            c.date_to).filter(c.comp_id == compid).one())
    comp = competition_info._asdict()

    comp_start = comp['date_from']

    if comp['date_from']:
        comp['date_from'] = comp['date_from'].strftime("%Y-%m-%d")
    if comp['date_to']:
        comp['date_to'] = comp['date_to'].strftime("%Y-%m-%d")

    if comp_start > datetime.now():
        return render_template('public/future_competition.html', comp=comp)

    if non_scored_tasks:
        for t in non_scored_tasks:
            task = t._asdict()
            task['status'] = "Not yet scored"
            if not t.opt_dist or t.opt_dist == 0:
                task['status'] = "Task not set"
                task['opt_dist'] = '0 km'
            else:
                wpt_coords, turnpoints, short_route, goal_line, tolerance, bbox = get_map_json(task['id'])
                layer['geojson'] = None
                layer['bbox'] = bbox
                task_map = make_map(layer_geojson=layer, points=wpt_coords, circles=turnpoints, polyline=short_route,
                                    goal_line=goal_line, margin=tolerance)
                task['opt_dist'] = '{:0.2f}'.format(task['opt_dist'] / 1000) + ' km'
                task.update({'map': task_map._repr_html_()})

            task['tasQuality'] = "-"
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
        track_id = r['track_id']
        name = r['name']
        pilot = [f'<b>{rank}</b>', f'<a href="/map/{track_id}-{taskid}">{name}</a>', r['nat'], r['glider'],
                 r['glider_cert'], r['sponsor']]
        if r['SSS_time']:
            pilot.append(sec_to_time(r['SSS_time'] + result_file['info']['time_offset']).strftime("%H:%M:%S"))
        else:
            pilot.append("")
        if r['ESS_time'] == 0 or r['ESS_time'] is None:
            pilot.append("")
            pilot.append("")
        else:
            pilot.append(sec_to_time(r['ESS_time'] + result_file['info']['time_offset']).strftime("%H:%M:%S"))
            pilot.append(sec_to_time(r['ESS_time'] - r['SSS_time']).strftime("%H:%M:%S"))
        pilot.append(round(r['speed'], 2) if r['speed'] else "")
        pilot.append("")  # altitude bonus
        pilot.append(round(r['distance'] / 1000, 2))
        pilot.append(round(r['time_score'], 2))
        pilot.append(round(r['departure_score'], 2))
        pilot.append(round(r['arrival_score'], 2))  # arrival points
        pilot.append(round(r['distance_score'], 2))
        pilot.append(round(r['penalty'], 2) if r['penalty'] else "")
        pilot.append(round(r['score'], 2))
        all_pilots.append(pilot)
        rank += 1
    result_file['data'] = all_pilots
    all_classes = []
    for glider_class in result_file['rankings']:
        if glider_class[-5:].lower() == 'class':
            # if glider_class[-5:].lower() == 'class' or glider_class.lower() == 'overall':
            comp_class = {'name': glider_class, 'limit': result_file['rankings'][glider_class][-1]}
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
        pilot = [rank, r['fai_id'], r['civl_id'], r['name'], r['nat'], r['sex'], r['sponsor'], r['glider'],
                 r['glider_cert'], f"<b>{int(r['score'])}</b>"]
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
            comp_class = {'name': glider_class, 'limit': result_file['rankings'][glider_class][-1]}
            all_classes.append(comp_class)
    all_classes.reverse()
    result_file['classes'] = all_classes
    return jsonify(result_file)


class SelectAdditionalTracks(FlaskForm):
    track_pilot_list = []
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
    trackids = []
    for t in extra_trackids.split(','):
        trackids.append(t)
    # if trackids is None:
    #     map(trackid)
    layer = {}
    extra_layer = {}
    print(f"trackid={trackid} trackids={trackids}")
    wpt_coords, turnpoints, short_route, goal_line, tolerance = get_task_json(66)
    colours = ['#0000ff', '#33cc33', '#ffff00', '#9900cc', '#006600', '#3399ff', '#ff99cc', '#663300', '#99ffcc']
    # blue, green, yellow, purple, dark green,light blue, pink, brown, turquoise
    c = 0
    legend = {}
    extra_tracks = []
    for t in trackids:
        layer['geojson'] = read_track_result_file(t, 66)
        track = {'name': t, 'track': layer['geojson']['tracklog'], 'colour': colours[c]}
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


@blueprint.route('/download/<filetype>/<filename>', methods=['GET'])
def download_file(filetype, filename):
    if filetype == 'airspace':
        airspace_path = Defines.AIRSPACEDIR
        fullname = path.join(airspace_path, filename)
    return send_file(fullname, as_attachment=True)
