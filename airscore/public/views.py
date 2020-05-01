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
    send_file,
    session
)
from flask_login import login_required, login_user, logout_user, current_user
from airscore.extensions import login_manager
from airscore.public.forms import LoginForm, ModifyParticipantForm
from airscore.user.forms import RegisterForm
from airscore.user.models import User
from airscore.utils import flash_errors
from datetime import datetime
from task import get_map_json, get_task_json
from trackUtils import read_tracklog_map_result_file
from design_map import make_map
from flask_wtf import FlaskForm
from wtforms import SelectField
from calcUtils import sec_to_time
import mapUtils
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
            if Defines.WAYPOINT_AIRSPACE_FILE_LIBRARY:
                session['library'] = True
            else:
                session['library'] = False
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template('public/index.html', form=form)


@blueprint.route("/ladders/", methods=["GET", "POST"])
def ladders():
    return render_template('public/ladders.html')


@blueprint.route('/pilots/')
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


@blueprint.route('/competition/<int:compid>')
def competition(compid):
    from compUtils import get_comp_json
    result_file = get_comp_json(int(compid))
    all_tasks = []
    layer = {}
    country_scores = False
    task_ids = []
    overall_available = False
    if result_file != 'error':
        if result_file['formula'].get('country_scoring') == 1:
            country_scores = True
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

    comp, non_scored_tasks = frontendUtils.get_comp_info(compid, task_ids)
    comp_start = comp['date_from']
    if comp['date_from']:
        comp['date_from'] = comp['date_from'].strftime("%Y-%m-%d")
    if comp['date_to']:
        comp['date_to'] = comp['date_to'].strftime("%Y-%m-%d")
    if comp_start > datetime.now().date():
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

    return render_template('public/comp.html', tasks=all_tasks, comp=comp, overall_available=overall_available,
                           country_scores=country_scores)


# @blueprint.route('/registered_pilots/<int:compid>')
# def registered_pilots(compid):
#     """ List of registered pilots for an event.
#         Creates a Register to the event button if pilot is not yet registered"""
#     return render_template('public/registered_pilots.html', compid=compid)
#
#
# @blueprint.route('/_get_registered_pilots/<compid>', methods=['GET'])
# def _get_registered_pilots(compid):
#     comp, pilot_list, pilot = frontendUtils.get_registered_pilots(compid, current_user)
#     return jsonify(dict(info=comp, data=pilot_list, pilot=pilot))


@blueprint.route('/task_result/<int:taskid>')
def task_result(taskid):
    return render_template('public/task_result.html', taskid=taskid)


@blueprint.route('/get_task_result/<int:taskid>', methods=['GET', 'POST'])
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


@blueprint.route('/comp_result/<int:compid>')
def comp_result(compid):
    return render_template('public/comp_overall.html', compid=compid)


@blueprint.route('/_get_comp_result/<compid>', methods=['GET', 'POST'])
def _get_comp_result(compid):
    from compUtils import get_comp_json
    result_file = get_comp_json(compid)
    if result_file == 'error':
        return render_template('404.html')
    all_pilots = []
    rank = 1
    for r in result_file['results']:
        pilot = {'fai_id': r['fai_id'], 'civl_id': r['civl_id'], 'name': r['name'], 'nat': r['nat'], 'sex': r['sex'],
                 'sponsor': r['sponsor'], 'glider': r['glider'], 'glider_cert': r['glider_cert'], 'rank': rank,
                 'score': f"<b>{int(r['score'])}</b>", 'results': {}}
        # setup the 20 task placeholders
        for t in range(1, 21):
            task = 'T' + str(t)
            pilot['results'][task] = {'score': ''}
        for t, task in enumerate(r['results']):
            if r['results'][task]['pre'] == r['results'][task]['score']:
                pilot['results'][task] = {'score': r['results'][task]['score']}
            else:
                pilot['results'][task] = {'score': f"{int(r['results'][task]['score'])} <del>{int(r['results'][task]['pre'])}</del>"}

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


@blueprint.route('/country_overall/<int:compid>')
def country_overall(compid):
    return render_template('public/country_overall.html', compid=compid)


@blueprint.route('/_get_comp_country_result/<compid>', methods=['GET'])
def _get_comp_country_result(compid):
    from compUtils import get_comp_json_filename
    from result import get_comp_country_scoring
    filename = get_comp_json_filename(compid)
    if not filename:
        return render_template('404.html')
    return jsonify(get_comp_country_scoring(filename))


@blueprint.route('/country_task/<int:taskid>')
def country_task(taskid):
    return render_template('public/country_task.html', taskid=taskid)


@blueprint.route('/_get_task_country_result/<taskid>', methods=['GET'])
def _get_task_country_result(taskid):
    from task import get_task_json_filename
    from result import get_task_country_scoring
    filename = get_task_json_filename(taskid)
    if not filename:
        return render_template('404.html')
    return jsonify(get_task_country_scoring(filename))


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
    layer['geojson'] = read_tracklog_map_result_file(trackid, taskid)
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
        layer['geojson'] = read_tracklog_map_result_file(t, 66)
        track = {'name': t, 'track': layer['geojson']['tracklog'], 'colour': colours[c]}
        extra_tracks.append(track)
        legend[t] = colours[c]
        c += 1

    layer['geojson'] = read_tracklog_map_result_file(trackid, 66)
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


@blueprint.route('/_get_participants/<compid>', methods=['GET'])
def _get_participants(compid):
    pilot_list, external = frontendUtils.get_participants(compid)
    return jsonify({'data': pilot_list, 'external': external})


@blueprint.route('/registered_pilots/<int:compid>')
def registered_pilots(compid):
    """ List of registered pilots for an event.
        Creates a Register to the event button if pilot is not yet registered"""
    modify_participant_form = ModifyParticipantForm()
    comp, _ = frontendUtils.get_comp_info(compid)
    if comp['date_from']:
        comp['date_from'] = comp['date_from'].strftime("%Y-%m-%d")
    if comp['date_to']:
        comp['date_to'] = comp['date_to'].strftime("%Y-%m-%d")
    return render_template('public/registered_pilots.html', modify_participant_form=modify_participant_form,
                           compid=compid, comp=comp)


@blueprint.route('/_get_participants_and_status/<compid>', methods=['GET'])
def _get_participants_and_status(compid):
    from participant import Participant
    pilot_list, _ = frontendUtils.get_participants(compid)
    status = None
    participant_info = None
    if current_user:
        if not current_user.is_authenticated:
            status = None
        elif any(p for p in pilot_list if p['pil_id'] == current_user.id):
            participant_info = next(p for p in pilot_list if p['pil_id'] == current_user.id)
            status = 'registered'
        else:
            participant = Participant.from_profile(current_user.id)
            participant_info = participant.as_dict()
            status = 'not_registered'
    return jsonify({'data': pilot_list, 'status': status, 'pilot_details': participant_info})

@blueprint.route('/live/<int:taskid>')
def livetracking(taskid):
    from livetracking import get_live_json
    from calcUtils import sec_to_string, time_to_seconds
    from datetime import datetime
    result_file = get_live_json(int(taskid))
    file_stats = result_file['file_stats']
    headers = result_file['headers']
    data = result_file['data']
    info = result_file['info']
    if info['time_offset']:
        file_stats['last_update'] = datetime.fromtimestamp(file_stats['timestamp'] + info['time_offset']).isoformat()
    if result_file['data']:
        rawtime = time_to_seconds(datetime.fromtimestamp(file_stats['timestamp']).time())
        task_distance = info['opt_dist']
        results = []
        goal = [p for p in result_file['data'] if p['ESS_time'] and (p['distance'] - task_distance) <= 5]
        results.extend(sorted(goal, key=lambda k: k['ss_time']))
        ess = [p for p in result_file['data'] if p['ESS_time'] and (p['distance'] - task_distance) > 5]
        results.extend(sorted(ess, key=lambda k: k['ss_time']))
        others = [p for p in result_file['data'] if p['ESS_time'] is None]
        results.extend(sorted(others, key=lambda k: k['distance'], reverse=True))
        data = []
        for el in results:
            '''result, time or distance'''
            if el['ESS_time'] and (el['distance'] - task_distance) <= 5:
                res = sec_to_string(el['ss_time'])
            elif el['ESS_time'] and (el['distance'] - task_distance) > 5:
                res = f"[{sec_to_string(el['ss_time'])}]"
            else:
                res = str(round(el['distance'] / 1000, 2)) + ' Km' if el['distance'] > 500 else ''
            '''height'''
            if not ('height' in el) or not el['first_time']:
                height = 'not launched yet'
            elif el['landing_time']:
                height = 'landed'
            else:
                height = f"{el['height']} agl"
            '''notifications'''
            if el['notifications']:
                comment = '; '.join([n['comment'].split('.')[0] for n in el['notifications']])
            else:
                comment = ''
            '''delay'''
            if not el['landing_time'] and el['last_time'] and rawtime - el['last_time'] > 60:  # 1 minutes old
                m, s = divmod(rawtime - el['last_time'], 60)
                delay = f"{m:02d} min {s:02d} sec"
            else:
                delay = ''
            time = sec_to_string(el['last_time'], info['time_offset']) if el['last_time'] else ''
            p = dict(id=el['ID'], name=el['name'], fem=1 if el['sex'] == 'F' else 0, result=res,
                     comment=comment, delay=delay, time=time, height=height)
            data.append(p)

    return render_template('public/live.html', file_stats=file_stats, headers=headers, data=data, info=info)
