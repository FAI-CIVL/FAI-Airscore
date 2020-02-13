from db_tables import tblCompetition, tblTask
from sqlalchemy.orm import aliased
from flask import jsonify
from myconn import Database
import datetime
from sqlalchemy import func, not_

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
    for tp in turnpoints:
        tp['partial_distance'] = '' if not tp['partial_distance']  else round(tp['partial_distance'] /1000, 2)
        if tp['type'] == 'speed':
            tp['type'] = 'SSS'
        elif tp['type'] == 'endspeed':
            tp['type'] = 'ESS'
        else:
            tp['type'] = tp['type'].capitalize()

    return {'turnpoints': turnpoints}


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
        choices.append((wpt['regPk'], wpt['rwpName'] + ' - ' + wpt['rwpDescription']))
    return choices