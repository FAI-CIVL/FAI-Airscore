from db_tables import TblCompetition, TblTask
from sqlalchemy.orm import aliased
from flask import jsonify
from myconn import Database
import datetime
from sqlalchemy import func, not_
import math
from pathlib import Path
import jsonpickle
from Defines import MAPOBJDIR
from design_map import make_map
from sqlalchemy.exc import SQLAlchemyError
from calcUtils import sec_to_time
from os import path
from werkzeug.utils import secure_filename

def get_comps():
    c = aliased(TblCompetition)

    with Database() as db:
        comps = (db.session.query(c.comp_id, c.comp_name, c.comp_site,
                                  c.comp_class, c.sanction, c.comp_type, c.date_from,
                                  c.date_to, func.count(TblTask.task_id))
                 .outerjoin(TblTask, c.comp_id == TblTask.comp_id)
                 .group_by(c.comp_id))

    all_comps = []
    now = datetime.datetime.now().date()
    for c in comps:
        comp = list(c)
        if comp[5] == 'RACE' or comp[5] == 'Route':
            compid = comp[0]
            name = comp[1]
            comp[1] = f'<a href="/competition/{compid}">{name}</a>'
        # else:
        # comp['comp_name'] = "<a href=\"comp_overall.html?comp_id=$id\">" . $row['comp_name'] . '</a>';
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
            comp.append(f"Starts in {(starts - now).days} day(s)")
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


def get_admin_comps():
    c = aliased(TblCompetition)

    with Database() as db:
        comps = (db.session.query(c.comp_id, c.comp_name, c.comp_site,
                                  c.date_from,
                                  c.date_to, func.count(TblTask.task_id))
                 .outerjoin(TblTask, c.comp_id == TblTask.comp_id)
                 .group_by(c.comp_id))

    all_comps = []
    for c in comps:
        comp = list(c)
        comp[1] = f'<a href="/users/comp_settings_admin/{comp[0]}">{comp[1]}</a>'
        comp[3] = comp[3].strftime("%Y-%m-%d")
        comp[4] = comp[4].strftime("%Y-%m-%d")
        all_comps.append(comp)
    return jsonify({'data': all_comps})


def get_task_list(comp):
    tasks = comp.get_tasks_details()
    max_task_num = 0
    last_region = 0
    for task in tasks:
        taskid = task['task_id']
        tasknum = task['task_num']
        if int(tasknum) > max_task_num:
            max_task_num = int(tasknum)
            last_region = task['reg_id']
        # if task['task_name'] is None or task['task_name'] == '':
        #     task['task_name'] = f'Task {tasknum}'
        task['link'] = f'<a href="/users/task_admin/{taskid}">Task {tasknum}</a>'
        task['opt_dist'] = 0 if not task['opt_dist'] else round(task['opt_dist']/1000, 2)
        task['opt_dist'] = f"{task['opt_dist']} km"
        if task['comment'] is None:
            task['comment'] = ''
        task['date'] = task['date'].strftime('%d/%m/%y')
    return {'next_task': max_task_num + 1, 'last_region': last_region, 'tasks': tasks}


def get_task_turnpoints(task):
    turnpoints = task.read_turnpoints()
    max_n = 0
    total_dist = 0
    for tp in turnpoints:
        tp['original_type'] = tp['type']
        tp['partial_distance'] = '' if not tp['partial_distance'] else round(tp['partial_distance'] / 1000, 2)
        if int(tp['num']) > max_n:
            max_n = int(tp['num'])
            total_dist = tp['partial_distance']
        if tp['type'] == 'speed':
            if tp['how'] == 'entry':
                tp['type'] = 'SSS - Out/Enter'
            else:
                tp['type'] = 'SSS - In/Exit'
        elif tp['type'] == 'endspeed':
            tp['type'] = 'ESS'
        elif tp['type'] == 'goal':
            if tp['shape'] == 'circle':
                tp['type'] = 'Goal Cylinder'
            else:
                tp['type'] = 'Goal Line'

        else:
            tp['type'] = tp['type'].capitalize()
    if total_dist == '':
        total_dist = 'Distance not yet calculated'
    else:
        total_dist = str(total_dist) + "km"
    # max_n = int(math.ceil(max_n / 10.0)) * 10
    max_n += 1

    task_file = Path(MAPOBJDIR + 'tasks/' + str(task.task_id) + '.task')
    if task_file.is_file():
        with open(task_file, 'r') as f:
            data = jsonpickle.decode(f.read())
            task_coords = data['task_coords']
            map_turnpoints = data['turnpoints']
            short_route = data['short_route']
            goal_line = data['goal_line']
            tolerance = data['tolerance']
            bbox = data['bbox']
            layer = {'geojson': None, 'bbox': bbox}
            task_map = make_map(layer_geojson=layer, points=task_coords, circles=map_turnpoints, polyline=short_route,
                                goal_line=goal_line, margin=tolerance)
            task_map = task_map._repr_html_()

    else:
        task_map = None

    return {'turnpoints': turnpoints, 'next_number': max_n, 'distance': total_dist, 'map': task_map}


def get_comp_regions(compid):
    import Defines
    import region
    if Defines.WAYPOINT_FILE_LIBRARY:
        return region.get_all_regions()
    else:
        return region.get_comp_regions_and_wpts(compid)


def get_region_choices(compid):
    regions = get_comp_regions(compid)
    choices = []
    for region in regions['regions']:
        choices.append((region['reg_id'], region['name']))
    return choices


def get_waypoint_choices(reg_id):
    import region
    wpts = region.get_region_wpts(reg_id)
    choices = []

    for wpt in wpts:
        choices.append((wpt['rwp_id'], wpt['name'] + ' - ' + wpt['description']))
    return choices


def get_pilot_list_for_track_management(taskid):
    from db_tables import TblTaskResult as R, TblParticipant as P, TblTask as T
    with Database() as db:
        try:
            results = db.session.query(R.goal_time, R.track_file, R.track_id, R.result_type, R.distance_flown, R.ESS_time, R.SSS_time, R.par_id).filter(
                                               R.task_id == taskid).subquery()
            pilots = db.session.query(T.task_id, P.name, P.par_id, results.c.track_id, results.c.SSS_time, results.c.ESS_time,
                                      results.c.distance_flown, results.c.track_file, results.c.result_type)\
                .outerjoin(P, T.comp_id == P.comp_id).filter(T.task_id == taskid)\
                .outerjoin(results, results.c.par_id == P.par_id).all()

            if pilots:
                pilots = [row._asdict() for row in pilots]

        except SQLAlchemyError:
            print("there was a problem with getting the pilot list")
            return None
    all_data = []
    for pilot in pilots:
        time = ''
        data = {}
        data['name'] = pilot['name']
        data['par_id'] = pilot['par_id']
        data['track_id'] = pilot['track_id']
        if pilot['ESS_time']:
            time = sec_to_time(pilot['ESS_time'] - pilot['SSS_time'])
        if pilot['result_type'] == 'goal':
            data['Result'] = f'Goal {time}'
        elif pilot['result_type'] == 'lo':
            data['Result'] = f"LO {round(pilot['distance_flown']/1000,2)}"
        elif pilot['result_type'] is None:
            data['Result'] = "Not Yet Processed"
        elif pilot['result_type'] == "mindist":
            data['Result'] = "Min Dist"
        else:
            data['Result'] = pilot['result_type'].upper()
        if pilot['track_file']:   # if there is a track, make the result a link to the map
            trackid = data['track_id']
            result = data['Result']
            data['Result']  = f'<a href="/map/{trackid}-{taskid}">{result}</a>'
        all_data.append(data)
    return all_data


def allowed_tracklog(filename, extension=['IGC']):

    if "." not in filename:
        return False

    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]

    # Check if the extension is allowed (make everything uppercase)
    if ext.upper() in [e.upper() for e in extension]:
        return True
    else:
        return False


def allowed_tracklog_filesize(filesize):

    if int(filesize) <= 5*1024*1024:
        return True
    else:
        return False


def process_igc(task_id, par_id, tracklog):
    from task import Task
    from track import Track
    from pilot import Pilot
    from flight_result import Flight_result
    from airspace import AirspaceCheck
    from igc_lib import Flight

    pilot = Pilot.read(par_id, task_id)
    if pilot.name:
        filename = pilot.name.replace(' ', '_').lower() + '.IGC'
        filename = secure_filename(filename)
    else:
        return None

    task = Task.read(task_id)
    track_path = task.file_path
    print(task_id)
    print(filename)

    full_file_name = path.join(track_path, filename)
    tracklog.save(full_file_name)
    print("Tracklog saved")

    """import track"""
    pilot.track = Track(track_file=filename, par_id=par_id)
    pilot.track.flight = Flight.create_from_file(full_file_name)
    """check result"""
    if not pilot.track:
        print(f"Track {filename} is not a valid track file \n")
    elif not pilot.track.date == task.date:
        print(f"track {filename} has a different date from task day \n")
    else:

        print(f"pilot {pilot.track.par_id} associated with track {pilot.track.filename} \n")

        """checking track against task"""

        if task.airspace_check:
            airspace = AirspaceCheck.from_task(task)
        else:
            airspace = None
        pilot.result = Flight_result.check_flight(pilot.track.flight, task, airspace_obj=airspace)
        print(f"track verified with task {task.task_id}\n")
        """adding track to db"""

        pilot.to_db()

        time = ''
        data = {'par_id': pilot.par_id, 'track_id': pilot.track_id}
        if pilot.result.goal_time:
            time = sec_to_time(pilot.result.ESS_time - pilot.result.SSS_time)
        if pilot.result.result_type == 'goal':
            data['Result'] = f'Goal {time}'
        elif pilot.result.result_type == 'lo':
            data['Result'] = f"LO {round(pilot.result.distance / 1000, 2)}"
        if pilot.track_id:   # if there is a track, make the result a link to the map
            trackid = data['track_id']
            result = data['Result']
            data['Result']  = f'<a href="/map/{trackid}-{task_id}">{result}</a>'
    return data


def process_igc_zip(task, zipfile):
    from trackUtils import extract_tracks, get_tracks, assign_and_import_tracks
    from tempfile import TemporaryDirectory

    if task.opt_dist == 0:
        print('task not optimised.. optimising')
        task.calculate_optimised_task_length()

    """create a temporary directory"""
    with TemporaryDirectory() as tracksdir:
        error = extract_tracks(zipfile, tracksdir)
        if error:
            print(f"An error occurred while dealing with file {zipfile} \n")
            return None
        """find valid tracks"""
        tracks = get_tracks(tracksdir)
        if tracks is None:
            print(f"There are no valid tracks in zipfile {zipfile} \n")
            return None

        """associate tracks to pilots and import"""
        assign_and_import_tracks(tracks, task)
        return 'Success'
