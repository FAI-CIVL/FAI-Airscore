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
from map import make_map, get_map_render
from flask_wtf import FlaskForm
from wtforms import SelectField
import mapUtils
import Defines
from os import path
import frontendUtils

blueprint = Blueprint("public", __name__, static_folder="../static")


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


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


@blueprint.route('/_get_all_comps', methods=['GET', 'POST'])
def _get_all_comps():
    return frontendUtils.get_comps()


@blueprint.route('/competition/<int:compid>')
def competition(compid):
    from compUtils import get_comp_json
    # get the latest comp result file, not the active one. This is so we can display tasks that have published
    # results that are not yet official and therefore in the comp overall results
    result_file = get_comp_json(int(compid), latest=True)
    all_tasks = []
    layer = {}
    country_scores = False
    task_ids = []
    overall_available = False
    if result_file != 'error':
        if result_file['formula'].get('country_scoring') == 1:
            country_scores = True
        overall_available = True if get_comp_json(int(compid)) != 'error' else False
        for task in result_file['tasks']:
            task_ids.append(int(task['id']))
            wpt_coords, turnpoints, short_route, goal_line, tolerance, bbox, _, _ = get_map_json(task['id'])
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
                wpt_coords, turnpoints, short_route, goal_line, tolerance, bbox, _, _ = get_map_json(task['id'])
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
#     return dict(info=comp, data=pilot_list, pilot=pilot)


@blueprint.route('/task_result/<int:taskid>')
def task_result(taskid):
    return render_template('public/task_result.html', taskid=taskid)


@blueprint.route('/_get_task_result/<int:taskid>', methods=['GET', 'POST'])
def _get_task_result(taskid):
    from task import get_task_json_filename
    result_file = frontendUtils.get_pretty_data(get_task_json_filename(taskid))
    if result_file == 'error':
        return render_template('404.html')

    all_pilots = []
    results = [p for p in result_file['results'] if p['result_type'] not in ['dnf', 'abs', 'nyp']]
    for r in results:
        rt = r['result_type']
        rank = f"<b>{r['rank']}</b>"
        n = r['name']
        parid = r['par_id']
        sex = r['sex']
        if rt in ['mindist', 'nyp'] or not r['track_file']:
            name = f'<span class="sex-{sex}">{n}</span>'
        else:
            name = f'<a class="sex-{sex}" href="/map/{parid}-{taskid}">{n}</a>'
        nat = r['nat']
        sp = r['sponsor']
        gl = r['glider']
        gc = r['glider_cert']
        ss = r['SSS_time']
        es = r['ESS_time']
        goal = r['goal_time']
        t = r['ss_time']
        s = r['speed']
        if es and not goal:
            es, t, s = f'<del>{es}</del>', f'<del>{t}</del>', f'<del>{s}</del>'
        ab = ''  # alt bonus
        d = r['distance']
        ts = r['time_score']
        dep = r['departure_score']
        arr = r['arrival_score']
        dis = r['distance_score']
        pen = "" if r['penalty'] == '0.0' else r['penalty']
        score = r['score']
        pilot = [rank, name, nat, gl, gc, sp, ss, es, t, s, ab, d, ts, dep, arr, dis, pen, score]
        all_pilots.append(pilot)
        # else:
        #     '''pilot do not have result data'''
            # TODO at the moment js raises error trying to order scores, leaving non flying pilots out of datatable
            # pilot = [f'<b>{rank}</b>', f'{name}', r['nat'], r['glider'], r['glider_cert'], r['sponsor'], "", "", "", "",
            #          "", "", "", "", "", "", "", f"{r['result_type'].upper()}"]

    result_file['data'] = all_pilots
    return result_file

@blueprint.route('/ext_comp_result/<int:compid>')
def ext_comp_result(compid):
    return render_template('public/ext_comp_overall.html', compid=compid)


@blueprint.route('/comp_result/<int:compid>')
def comp_result(compid):
    return render_template('public/comp_overall.html', compid=compid)


@blueprint.route('/_get_comp_result/<compid>', methods=['GET', 'POST'])
def _get_comp_result(compid):
    from compUtils import get_comp_json_filename
    result_file = frontendUtils.get_pretty_data(get_comp_json_filename(compid))
    if result_file == 'error':
        return render_template('404.html')
    all_pilots = []
    tasks = [t['task_code'] for t in result_file['tasks']]
    for r in result_file['results']:
        pilot = {'rank': f"<b>{r['rank']}</b>",
                 'fai_id': r['fai_id'], 'civl_id': r['civl_id'],
                 'name': f"<span class='sex-{r['sex']}'><b>{r['name']}</b></span>",
                 'nat': r['nat'], 'sex': r['sex'],
                 'glider': r['glider'], 'glider_cert': r['glider_cert'], 'sponsor': r['sponsor'],
                 'score': f"<b>{r['score']}</b>", 'results': {}}
        # setup the 20 task placeholders
        for t in range(1, 21):
            task = 'T' + str(t)
            pilot['results'][task] = {'score': ''}
        for task in tasks:
            if r['results'][task]['pre'] == r['results'][task]['score']:
                pilot['results'][task] = {'score': r['results'][task]['score']}
            else:
                pilot['results'][task] = {'score': f"{int(r['results'][task]['score'])} <del>{int(r['results'][task]['pre'])}</del>"}

        all_pilots.append(pilot)
    result_file['data'] = all_pilots

    return result_file


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
    return get_comp_country_scoring(filename)


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
    return get_task_country_scoring(filename)


class SelectAdditionalTracks(FlaskForm):
    track_pilot_list = []
    tracks = SelectField('Add Tracks:', choices=track_pilot_list)


@blueprint.route('/map/<paridtaskid>', methods=["GET", "POST"])
def map(paridtaskid):
    from airspaceUtils import read_airspace_map_file
    from mapUtils import create_trackpoints_layer

    parid, taskid = paridtaskid.split("-")
    parid = int(parid)
    taskid = int(taskid)

    full_tracklog = bool(request.form.get('full'))
    layer = {}
    trackpoints = None
    '''task map'''
    wpt_coords, turnpoints, short_route, goal_line, tolerance, _, offset, airspace = get_map_json(taskid)

    '''tracklog'''
    layer['geojson'] = read_tracklog_map_result_file(parid, taskid)
    layer['bbox'] = layer['geojson']['bounds']
    pilot_name = layer['geojson']['info']['pilot_name']
    task_name = layer['geojson']['info']['task_name']
    '''full track log creation if requested'''
    if 'track_file' in layer['geojson']['info'] and full_tracklog:
        trackpoints = create_trackpoints_layer(layer['geojson']['info']['track_file'], offset)
    other_tracks = mapUtils.get_other_tracks(taskid, parid)

    '''airspace'''
    if airspace:
        airspace_layer = read_airspace_map_file(airspace)['spaces']
        infringements = layer['geojson']['infringements']
    else:
        airspace_layer = None
        infringements = None

    map = make_map(layer_geojson=layer, points=wpt_coords, circles=turnpoints, polyline=short_route,
                   goal_line=goal_line, margin=tolerance, thermal_layer=True, waypoint_layer=True,
                   airspace_layer=airspace_layer, infringements=infringements, trackpoints=trackpoints)
    waypoint_achieved_list = list(w for w in layer['geojson']['waypoint_achieved'])
    add_tracks = SelectAdditionalTracks()
    add_tracks.track_pilot_list = other_tracks
    return render_template('public/map.html',
                           other_tracks=other_tracks,
                           add_tracks=add_tracks,
                           map=get_map_render(map),
                           wpt_achieved=waypoint_achieved_list,
                           task={'name': task_name, 'id': taskid},
                           pilot={'name': pilot_name, 'id': parid},
                           full_tracklog=full_tracklog)


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
    if filetype == 'igc_zip':
        task_id = filename
        zip_file = frontendUtils.get_task_igc_zip(int(task_id))
        return send_file(zip_file, as_attachment=True)


@blueprint.route('/_get_participants/<compid>', methods=['GET'])
def _get_participants(compid):
    pilot_list, external, teams = frontendUtils.get_participants(compid)
    return {'data': pilot_list, 'external': external, 'teams': teams}


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
    from pilot.participant import Participant
    pilot_list, _, _ = frontendUtils.get_participants(compid)
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
    return {'data': pilot_list, 'status': status, 'pilot_details': participant_info}


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
    # if file_stats['timestamp'] == 'Cancelled':
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
                height = '[not launched yet]'
            elif el['goal_time']:
                height = ''
            elif el['landing_time']:
                height = '[landed]'
            else:
                height = f"[{el['height']} agl]"
            '''notifications'''
            if el['notifications']:
                comment = '; '.join([n['comment'].split('.')[0] for n in el['notifications']])
            else:
                comment = ''
            '''delay'''
            if not (el['landing_time'] or el['goal_time']) and el['last_time'] and rawtime - el['last_time'] > 120:  # 2 mins old
                if rawtime - el['last_time'] > 600:  # 10 minutes old
                    height = f"disconnected"
                else:
                    m, s = divmod(rawtime - el['last_time'], 60)
                    height = f"[{m:02d}:{s:02d} old]"
            time = sec_to_string(el['last_time'], info['time_offset']) if el['last_time'] else ''
            p = dict(id=el['ID'], name=el['name'], fem=1 if el['sex'] == 'F' else 0, result=res,
                     comment=comment, time=time, height=height)
            data.append(p)

    return render_template('public/live.html', file_stats=file_stats, headers=headers, data=data, info=info)
