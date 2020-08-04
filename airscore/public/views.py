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
    return render_template('public/index.html', form=form, now=datetime.utcnow(), ladders=Defines.LADDERS)


@blueprint.route("/ladders/", methods=["GET", "POST"])
def ladders():
    return render_template('public/ladders.html', now=datetime.utcnow())


@blueprint.route('/_get_ladders', methods=['GET', 'POST'])
def _get_ladders():
    from calcUtils import get_season_dates
    ladderlist = frontendUtils.get_ladders()
    # {'comp_id': 2, 'comp_name': 'Meeting LP 2018 - 1', 'comp_site': 'Meduno', 'comp_class': 'PG', 'sanction': 'none',
    #  'comp_type': 'RACE', 'date_from': datetime.date(2018, 4, 7), 'date_to': datetime.date(2018, 4, 8), 'external': 0}
    data = []
    now = datetime.now().date()
    '''seasons'''
    seasons = sorted(set([c['season'] for c in ladderlist]), reverse=True)
    for c in ladderlist:
        ladderid = c['ladder_id']
        name = c['ladder_name']
        season = int(c['season'])
        '''create start and end dates'''
        starts, ends = get_season_dates(ladder_id=ladderid, season=season,
                                        date_from=c['date_from'], date_to=c['date_to'])
        c['ladder_name'] = f'<a href="/ladder_result/{ladderid}/{season}">{name} {season}</a>'
        if c['ladder_class']:
            cl = c['ladder_class'].lower()
            c['ladder_class'] = f'<img src="/static/img/{cl}.png" width="100%" height="100%"</img>'
        if starts > now:
            days = (starts - now).days
            c['status'] = f"Starts in {days} days" if days > 1 else f"Starts tomorrow"
        elif ends < now:
            c['status'] = 'Finished'
        else:
            c['status'] = 'Running'
        c['date_from'] = starts.strftime('%Y-%m-%d')
        c['date_to'] = ends.strftime('%Y-%m-%d')
        data.append(c)
    return {'data': data, 'seasons': seasons}


@blueprint.route('/ladder_result/<int:ladderid>/<int:season>')
def ladder_result(ladderid: int, season: int):
    return render_template('public/ladder_overall.html', ladderid=ladderid, season=season)


@blueprint.route('/_get_ladder_result/<int:ladderid>/<int:season>', methods=['GET', 'POST'])
def _get_ladder_result(ladderid: int, season: int):

    result_file = frontendUtils.get_pretty_data(frontendUtils.get_ladder_results(ladderid, season))
    if result_file == 'error':
        return render_template('404.html')

    for t in result_file['comps']:
        link, code = f"/competition/{t['id']}", t['comp_name']
        t['link'] = f"<a href='{link}' target='_blank'>{code}</a>"

    all_pilots = []
    columns = 0
    for r in result_file['results']:
        pilot = {'fai_id': r['fai_id'], 'civl_id': r['civl_id'],
                 'name': f"<span class='sex-{r['sex']}'><b>{r['name']}</b></span>", 'nat': r['nat'], 'sex': r['sex'],
                 'score': f"<b>{r['score']}</b>", 'ranks': {'rank': f"<b>{r['rank']}</b>"}}
        for i, c in enumerate(result_file['classes'][1:], 1):
            pilot['ranks']['class' + str(i)] = f"{r[c['limit']]}"
        pilot['results'] = []
        for idx, res in enumerate(r['results'], 1):
            score = f"{res['score']}" if res['score'] == res['pre'] else f"{res['score']} <del>{res['pre']}</del>"
            link = f"<a href=/task_result/{res['task_id']} target='_blank'>{res['task_code']}</a>"
            html = f"<span class='task_score'>{score}</span><span class='task_code'>({link})</span>"
            pilot['results'].append(html)
        if len(pilot['results']) > columns:
            columns = len(pilot['results'])
        all_pilots.append(pilot)
    result_file['data'] = all_pilots
    result_file['columns'] = columns

    return result_file


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
    comps = frontendUtils.get_comps()
    # {'comp_id': 2, 'comp_name': 'Meeting LP 2018 - 1', 'comp_site': 'Meduno', 'comp_class': 'PG', 'sanction': 'none',
    #  'comp_type': 'RACE', 'date_from': datetime.date(2018, 4, 7), 'date_to': datetime.date(2018, 4, 8), 'external': 0}
    data = []
    now = datetime.now().date()
    '''seasons'''
    seasons = sorted(set([c['date_from'].year for c in comps]), reverse=True)
    for c in comps:
        compid = c['comp_id']
        starts = c['date_from']
        ends = c['date_to']
        if c['comp_type'] in ('RACE', 'Route'):
            name = c['comp_name']
            if c['external']:
                c['tasks'] = 'external'
                c['comp_name'] = f'<a href="/ext_comp_result/{compid}">{name}</a>'
            else:
                c['comp_name'] = f'<a href="/competition/{compid}">{name}</a>'
            if c['sanction'] and not c['sanction'] == 'none':
                c['comp_type'] = ' - '.join([c['comp_type'], c['sanction']])
            if c['comp_class']:
                c['comp_class'] = f'<img src="/static/img/{c["comp_class"]}.png" width="100%" height="100%"</img>'
            if starts > now:
                days = (starts - now).days
                c['status'] = f"Starts in {days} days" if days > 1 else f"Starts tomorrow"
            elif ends < now:
                c['status'] = 'Finished'
            else:
                c['status'] = 'Running'
            c['date_from'] = c['date_from'].strftime('%Y-%m-%d')
            c['date_to'] = c['date_to'].strftime('%Y-%m-%d')
            data.append(c)
    return {'data': data, 'seasons': seasons}


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
    from task import get_task_json
    result_file = frontendUtils.get_pretty_data(get_task_json(taskid))
    if result_file == 'error':
        return render_template('404.html')

    all_pilots = []
    results = [p for p in result_file['results'] if p['result_type'] not in ['dnf', 'abs', 'nyp']]
    for r in results:
        pilot = {'fai_id': r['fai_id'], 'civl_id': r['civl_id'], 'nat': r['nat'], 'sex': r['sex'],
                 'glider': r['glider'], 'glider_cert': r['glider_cert'], 'sponsor': r['sponsor'],
                 'SSS_time': r['SSS_time'], 'distance': r['distance'], 'time_score': r['time_score'],
                 'departure_score': r['departure_score'], 'arrival_score': r['arrival_score'],
                 'distance_score': r['distance_score'], 'score': f"<b>{r['score']}</b>",
                 'ranks': {'rank': f"<b>{r['rank']}</b>"}}
        n = r['name']
        parid = r['par_id']
        sex = r['sex']
        if r['result_type'] in ['mindist', 'nyp'] or not r['track_file']:
            pilot['name'] = f'<span class="sex-{sex}">{n}</span>'
        else:
            pilot['name'] = f'<a class="sex-{sex}" href="/map/{parid}-{taskid}">{n}</a>'
        goal = r['goal_time']
        pilot['ESS_time'] = r['ESS_time'] if goal else f"<del>{r['ESS_time']}</del>"
        pilot['speed'] = r['speed'] if goal else f"<del>{r['speed']}</del>"
        pilot['ss_time'] = r['ss_time'] if goal else f"<del>{r['ss_time']}</del>"
        pilot['goal_time'] = goal
        # ab = ''  # alt bonus
        pilot['penalty'] = "" if r['penalty'] == '0.0' else r['penalty']
        # setup 4 sub-rankings placeholders
        for i, c in enumerate(result_file['classes'][1:], 1):
            pilot['ranks']['class' + str(i)] = f"{r[c['limit']]}"
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
    from compUtils import get_comp_json
    result_file = frontendUtils.get_pretty_data(get_comp_json(compid))
    if result_file == 'error':
        return render_template('404.html')

    for t in result_file['tasks']:
        link, code = f"/task_result/{t['id']}", t['task_code']
        t['link'] = f"<a href='{link}' target='_blank'>{code}</a>"

    all_pilots = []
    for r in result_file['results']:
        pilot = {'fai_id': r['fai_id'], 'civl_id': r['civl_id'],
                 'name': f"<span class='sex-{r['sex']}'><b>{r['name']}</b></span>", 'nat': r['nat'], 'sex': r['sex'],
                 'glider': r['glider'], 'glider_cert': r['glider_cert'], 'sponsor': r['sponsor'],
                 'score': f"<b>{r['score']}</b>", 'ranks': {'rank': f"<b>{r['rank']}</b>"}}
        for i, c in enumerate(result_file['classes'][1:], 1):
            pilot['ranks']['class' + str(i)] = f"{r[c['limit']]}"
        pilot['results'] = []
        for k, v in r['results'].items():
            score = f"{v['score']}" if v['score'] == v['pre'] else f"{v['score']} <del>{v['pre']}</del>"
            html = f"<span class='task_score'>{score}</span>"
            pilot['results'].append(html)
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
    from calcUtils import sec_to_string, time_to_seconds, c_round
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
            status = ''
            res = ''
            '''status, time or distance'''
            if el['first_time'] is None:
                '''not launched'''
                status = '[not launched yet]'
            elif el['ESS_time']:
                val = sec_to_string(el['ss_time'])
                res = f"<del>{val}</del>" if not el['goal_time'] else f"<b>{val}</b>"
            else:
                res = str(c_round(el['distance'] / 1000, 2)) + ' Km' if el['distance'] > 500 else ''
                status = '[landed]' if el['landing_time'] else f"[{el['height']} agl]"

            '''notifications'''
            if el['notifications']:
                comment = '; '.join([n['comment'].split('.')[0] for n in el['notifications']])
            else:
                comment = ''
            '''delay'''
            if not (el['landing_time'] or el['goal_time']) and el['last_time'] and rawtime - el['last_time'] > 120:  # 2 mins old
                if rawtime - el['last_time'] > 600:  # 10 minutes old
                    status = f"disconnected"
                else:
                    m, s = divmod(rawtime - el['last_time'], 60)
                    status = f"[{m:02d}:{s:02d} old]"
            time = sec_to_string(el['last_time'], info['time_offset']) if el['last_time'] else ''
            p = dict(id=el['ID'], name=el['name'], fem=1 if el['sex'] == 'F' else 0, result=res,
                     comment=comment, time=time, status=status)
            data.append(p)

    return render_template('public/live.html', file_stats=file_stats, headers=headers, data=data, info=info)
