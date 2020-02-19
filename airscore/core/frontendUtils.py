from db_tables import tblCompetition, tblTask
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

def get_comps():
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
    c = aliased(tblCompetition)

    with Database() as db:
        comps = (db.session.query(c.comPk, c.comName, c.comLocation,
                                  c.comDateFrom,
                                  c.comDateTo, func.count(tblTask.tasPk))
                 .outerjoin(tblTask, c.comPk == tblTask.comPk)
                 .group_by(c.comPk))

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
        if int(tp['n']) > max_n:
            max_n = int(tp['n'])
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
        choices.append((region['regPk'], region['name']))
    return choices

def get_waypoint_choices(reg_id):
    import region
    wpts = region.get_region_wpts(reg_id)
    choices = []

    for wpt in wpts:
        choices.append((wpt['rwpPk'], wpt['rwpName'] + ' - ' + wpt['rwpDescription']))
    return choices