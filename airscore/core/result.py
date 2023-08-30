"""
JSON Results Creation

contains
    TaskResult class
    CompResult class

Methods:
    Contains the list of fields that should be used during JSON file creation
    Creating the result JSON files, functions get field list from this classes.
    JSON will also reflect field order inside lists.

    create_json_file:   function to create task and comp results file.
                        It also insert the entry in database.

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019
"""

import json

from db.conn import db_session
from db.tables import TblResultFile
from sqlalchemy import and_
from Defines import RESULTDIR
from calcUtils import c_round
from pathlib import Path


class TaskResult:
    """
    Task result fields lists
    """

    info_list = [
        'id',
        'comp_id',
        'comp_name',
        'comp_site',
        'comp_class',
        'date',
        'task_name',
        'task_num',
        'training',
        'time_offset',
        'comment',
        'window_open_time',
        'task_deadline',
        'window_close_time',
        'check_launch',
        'start_time',
        'start_close_time',
        'SS_interval',
        'start_iteration',
        # 'last_start_time',
        'task_type',
        'distance',
        'opt_dist',
        'SS_distance',
        'stopped_time',
        'goal_altitude',
        'locked'
    ]

    route_list = ['name', 'description', 'how', 'radius', 'shape', 'type', 'lat', 'lon', 'altitude']

    formula_list = [
        'formula_name',
        'overall_validity',  # 'ftv', 'all',
        'validity_param',
        'validity_ref',  # 'day_quality', 'max_score'
        'formula_distance',  # 'on', 'difficulty', 'off'
        'formula_arrival',  # 'position', 'time', 'off'
        'formula_departure',  # 'on', 'leadout', 'off'
        'lead_factor',  # float
        'formula_time',  # 'on', 'off'
        'arr_alt_bonus',  # float
        'arr_min_height',  # int
        'arr_max_height',  # int
        'validity_min_time',  # seconds
        'score_back_time',  # seconds
        'max_JTG',
        'JTG_penalty_per_sec',
        'nominal_goal',  # percentage / 100
        'nominal_dist',  # meters
        'nominal_time',  # seconds
        'nominal_launch',  # percentage / 100
        'min_dist',  # meters
        'score_back_time',  # seconds
        'no_goal_penalty',
        'glide_bonus',
        'tolerance',  # percentage / 100
        'scoring_altitude',  # 'GPS', 'QNH'
        'task_result_decimal',
        'team_scoring',
        'team_size',
        'max_team_size',
        'country_scoring',
        'country_size',
        'max_country_size',
    ]

    stats_list = [
        'pilots_launched',
        'pilots_present',
        'pilots_ess',
        'pilots_landed',
        'pilots_goal',
        'fastest',
        'fastest_in_goal',
        'min_dept_time',
        'max_ss_time',
        'min_ess_time',
        'max_ess_time',
        'last_landing_time',
        'max_distance',
        'tot_dist_flown',
        'tot_dist_over_min',
        'day_quality',
        'ftv_validity',
        'dist_validity',
        'time_validity',
        'launch_validity',
        'stop_validity',
        'arr_weight',
        'dep_weight',
        'time_weight',
        'dist_weight',
        'avail_dist_points',
        'avail_dep_points',
        'avail_time_points',
        'avail_arr_points',
        'min_dist_score',
        'max_score',
        'min_lead_coeff',
        'tot_flight_time',
    ]

    results_list = [
        'track_id',
        'par_id',
        'ID',
        'civl_id',
        'fai_id',
        'name',
        'birthdate',
        'sponsor',
        'nat',
        'sex',
        'glider',
        'glider_cert',
        'team',
        'nat_team',
        'distance_flown',
        'stopped_distance',
        'stopped_altitude',
        'distance',
        'ss_time',
        'speed',
        'real_start_time',
        'goal_time',
        'result_type',
        'SSS_time',
        'ESS_time',
        'ESS_rank',
        'waypoints_made',
        'waypoints_achieved',
        'distance_score',
        'time_score',
        'departure_score',
        'arrival_score',
        'before_penalty_score',
        'score',
        'penalty',
        'infringements',
        'comment',
        'lead_coeff',
        'ESS_altitude',
        'goal_altitude',
        'last_altitude',
        'max_altitude',
        'first_time',
        'last_time',
        'landing_altitude',
        'landing_time',
        'flight_time',
        'track_file',
        'pil_id',
        'custom'
    ]

    @staticmethod
    def to_html(json_file: str) -> (str, dict or list):
        """ create a HTML file from json result file"""
        import re

        from frontendUtils import get_pretty_data

        res = get_pretty_data(open_json_file(json_file), export=True)
        comp_name = res['info']['comp_name']
        task_name = res['info']['task_name']
        task_code = f"T{res['info']['task_num']}"
        rankings = res['rankings']
        if len(rankings) > 1:
            zipfile = f"{re.sub(r'[ ,.-]', '_', comp_name)}_{task_code}.zip"
        else:
            zipfile = False

        '''Task Route table'''
        right_align = [2, 3]
        thead = ['id', '', 'Radius', 'Dist.', 'Description']
        rows = []
        for wp in res['route']:
            rows.append([wp['name'], wp['type'], wp['radius'], wp['cumulative_dist'], wp['description']])
        route = dict(css_class='route', right_align=right_align, thead=thead, tbody=rows)

        ''' Times table'''
        times = []
        if not res['info']['start_iteration']:
            times.append(['Startgate:', res['info']['start_time']])
        else:
            for idx, el in enumerate(res['info']['startgates']):
                times.append(['Startgates:' if idx == 0 else ' ', el])
        if not res['info']['stopped_time']:
            times.append(['Deadline:', res['info']['task_deadline']])
        else:
            times.append(['Stopped:', res['info']['stopped_time']])
        times = dict(css_class='bold noborder', tbody=times)

        '''Main results table header'''
        thead = ['#', 'Id', 'Name', 'Nat', 'Glider', 'Sponsor']
        results_keys = []
        res_align = [0, 1]

        if len(res['info']['startgates']) > 1:
            thead.extend(['SS', 'ES'])
            results_keys.extend(['SSS_time', 'ESS_time'])
        thead.extend(['time', 'speed', 'distance'])
        results_keys.extend(['ss_time', 'speed', 'distance'])
        res_align.extend([len(thead) - 2, len(thead) - 1])
        if not res['formula']['formula_distance'] == 'off':
            thead.append('Dist. Pts')
            results_keys.append('distance_score')
            res_align.append(len(thead) - 1)
        if not res['formula']['formula_departure'] == 'off':
            dep_label = 'Lead. Pts' if res['formula']['formula_departure'] == 'leadout' else 'Dep. Pts'
            thead.append(dep_label)
            results_keys.append('departure_score')
            res_align.append(len(thead) - 1)
        if not res['formula']['formula_time'] == 'off':
            thead.append('Time Pts')
            results_keys.append('time_score')
            res_align.append(len(thead) - 1)
        if not res['formula']['formula_arrival'] == 'off':
            thead.append('Arr. Pts')
            results_keys.append('arrival_score')
            res_align.append(len(thead) - 1)
        thead.append('Total')
        results_keys.append('score')
        res_align.append(len(thead) - 1)

        response = []
        for idx, c in enumerate(rankings):
            class_name = comp_name if not c['rank_name'] else f"{comp_name} {c['rank_name']}"
            title = f"{class_name} - {task_name}"
            filename = f"{re.sub(r'[ ,.-]', '_', class_name)}_{task_code}.html"

            '''HTML headings'''
            dist = res['info']['opt_dist']
            task_type = f"{res['info']['task_type'].title()} {dist}"
            headings = [class_name, task_name, res['info']['date'], task_type, res['file_stats']['status']]

            pilots = [p for p in res['results'] if p['rankings'][c['rank_id']]]
            keys = [c['rank_id'], 'ID', 'name', 'nat', 'glider', 'sponsor']
            keys.extend(results_keys)

            '''Main results table body'''
            tbody = []
            for p in [x for x in pilots if x['result_type'] not in ['abs', 'nyp', 'dnf']]:
                tbody.append([p['rankings'][k] if i == 0 else p[k] for i, k in enumerate(keys)])
            results = dict(css_class='results', right_align=res_align, thead=thead, tbody=tbody)

            tables = [route, times, results]

            ''' Comments Table'''
            if any(p for p in pilots if p['penalty']):
                comments = []
                right_align = [0]
                for p in [x for x in pilots if x['penalty']]:
                    comments.append([p['ID'], p['name'], p['nat'], p['comment']])
                comments = dict(title='Penalties:', css_class='results', right_align=right_align, tbody=comments)
                tables.append(comments)

            ''' NYP Table'''
            if any(p for p in pilots if p['result_type'] == 'nyp'):
                nyp = []
                right_align = [0]
                for p in [x for x in pilots if x['result_type'] == 'nyp']:
                    nyp.append([p['ID'], p['name'], p['nat']])
                nyp = dict(title='Not Yet Plotted:', css_class='simple', right_align=right_align, tbody=nyp)
                tables.append(nyp)

            ''' ABS DNF Table'''
            if any(p for p in pilots if p['result_type'] in ['abs', 'dnf']):
                others = []
                right_align = [0]
                for p in [x for x in pilots if x['result_type'] in ['abs', 'dnf']]:
                    others.append([p['ID'], p['name'], p['nat'], p['result_type']])
                absdnf = dict(title='Other Pilots:', css_class='simple', right_align=right_align, tbody=others)
                tables.append(absdnf)

            ''' Stats Table'''
            stats = []
            right_align = [1]
            # adding SS_distance info as it changes based on scoring system (2023)
            key, value = next(((k, v) for k, v in res['info'].items() if k == 'SS_distance'), (None, None))
            if key:
                stats.append([key, value])

            for key, value in res['stats'].items():
                stats.append([key, value])
            stats = dict(title='Stats:', css_class='simple', right_align=right_align, tbody=stats)
            tables.append(stats)

            ''' Formula Table'''
            formula = []
            right_align = [1]
            for key, value in res['formula'].items():
                formula.append([key, value])
            formula = dict(title='Formula:', css_class='simple', right_align=right_align, tbody=formula)

            tables.append(formula)
            timestamp = res['file_stats']['timestamp']
            response.append(
                dict(
                    filename=filename, content=dict(title=title, headings=headings, tables=tables, timestamp=timestamp)
                )
            )

        if zipfile:
            return zipfile, response
        else:
            result = response.pop()
            return result['filename'], result['content']


class CompResult(object):
    """
    Comp result fields lists
    """

    info_list = [
        'id',
        'comp_name',
        'comp_class',
        'comp_type',
        'comp_site',
        'date_from',
        'date_to',
        'sanction',
        'MD_name',
        'contact',
        'comp_code',
        'restricted',
        'time_offset',
        'website',
    ]

    stats_list = [
        'winner_score',
        'valid_tasks',
        'total_validity',
        'avail_validity',
        'tot_flights',
        'tot_dist_flown',
        'tot_flight_time',
        'tot_pilots',
    ]

    formula_list = [
        'formula_name',
        'comp_class',  # 'HG', 'PG'
        'overall_validity',  # 'ftv', 'all',
        'validity_param',
        'formula_distance',  # 'on', 'difficulty', 'off'
        'formula_arrival',  # 'position', 'time', 'off'
        'formula_departure',  # 'on', 'leadout', 'off'
        'lead_factor',  # float
        'formula_time',  # 'on', 'off'
        'arr_alt_bonus',  # float
        'arr_min_height',  # int
        'arr_max_height',  # int
        'validity_min_time',  # seconds
        'score_back_time',  # seconds
        'max_JTG',  # seconds
        'JTG_penalty_per_sec',
        'nominal_goal',  # percentage / 100
        'nominal_dist',  # meters
        'nominal_time',  # seconds
        'nominal_launch',  # percentage / 100
        'min_dist',  # meters
        'score_back_time',  # seconds
        'no_goal_penalty',  # percentage / 100
        'glide_bonus',
        'tolerance',  # percentage / 100
        'scoring_altitude',  # 'GPS', 'QNH'
        'task_result_decimal',
        'comp_result_decimal',
        'team_scoring',
        'team_size',
        'max_team_size',
        'country_scoring',
        'country_size',
        'max_country_size',
    ]

    task_list = [
        'id',
        'task_name',
        'task_code',
        'date',
        'status',
        'training',
        'comment',
        'opt_dist',
        'pilots_goal',
        'day_quality',
        'ftv_validity',
        'max_score',
        'task_type',
        'locked'
    ]

    ''' result_list comes from Participant obj, and RegisteredPilotView
        available fields are: (`par_id`, `comp_id`, `civl_id`, `fai_id`, `pil_id`, `ID`, `name`, `sex`, `nat`,
                            `glider`, `class`, `sponsor`, `team`, `nat_team`, 'results')'''
    result_list = [
        'ID',
        'par_id',
        'civl_id',
        'fai_id',
        'name',
        'birthdate',
        'sex',
        'nat',
        'glider',
        'glider_cert',
        'sponsor',
        'team',
        'nat_team',
        'status',
        'pil_id',
        'score',
        'results',
        'custom'
    ]

    @staticmethod
    def to_html(json_file: str) -> (str, dict or list):
        """ create a HTML file from json result file"""
        import re

        from frontendUtils import get_pretty_data

        res = get_pretty_data(open_json_file(json_file), export=True)
        comp_name = f"{res['info']['comp_name']}"
        rankings = res['rankings']
        if len(res['rankings']) > 1:
            zipfile = f"{re.sub(r'[ ,.-]', '_', comp_name)}_after_{res['tasks'][-1]['task_code']}.zip"
        else:
            zipfile = False

        '''Tasks table'''
        tasks = []
        thead = [' ', ' ', 'Dist.', 'Validity']
        right_align = [2, 3]
        for t in res['tasks']:
            row = [
                t['task_name'],
                t['date'],
                t['opt_dist'],
                t['ftv_validity'] if res['formula']['overall_validity'] == 'ftv' else t['day_quality'],
            ]
            tasks.append(row)
        tasks = dict(title='Tasks', css_class='simple', right_align=right_align, thead=thead, tbody=tasks)

        '''Main results table'''
        thead = ['#', 'Id', 'Name', 'Nat', 'Glider', 'Sponsor', 'Total']
        right_align = [0, 1, 6]
        for t in res['tasks']:
            thead.append(t['task_code'])
            right_align.append(len(thead) - 1)

        response = []
        for idx, c in enumerate(rankings):
            title = comp_name if not c['rank_name'] else f"{comp_name} {c['rank_name']}"
            filename = f"{re.sub(r'[ ,.-]', '_', title)}_after_{res['tasks'][-1]['task_code']}.html"

            '''HTML headings'''
            headings = [
                f"{res['info']['comp_name']} - {res['info']['sanction']} Event",
                f"{c['rank_name']}",
                f"{res['info']['date_from']} to {res['info']['date_to']}",
                f"{res['info']['comp_site']}",
                f"{res['file_stats']['status']}",
            ]

            pilots = [p for p in res['results'] if p['rankings'][c['rank_id']]]
            keys = [c['rank_id'], 'ID', 'name', 'nat', 'glider', 'sponsor', 'score']

            tbody = []
            for p in pilots:
                row = [p['rankings'][k] if i == 0 else p[k] for i, k in enumerate(keys)]
                for t in res['tasks']:
                    code = t['task_code']
                    score = p['results'][code]['score']
                    row.append(score)
                tbody.append(row)
            results = dict(css_class='results', right_align=right_align, thead=thead, tbody=tbody)
            tables = [tasks, results]
            timestamp = res['file_stats']['timestamp']
            response.append(
                dict(
                    filename=filename, content=dict(title=title, headings=headings, tables=tables, timestamp=timestamp)
                )
            )

        if zipfile:
            return zipfile, response
        else:
            result = response.pop()
            return result['filename'], result['content']


def create_json_file(comp_id, code, elements, task_id=None, status=None, name_suffix=None):
    """
    creates the JSON file of results
    :param
    name_suffix: optional name suffix if None a timestamp will be used.
        This is so we can overwrite comp results that are only used in front end to create competition
        page not display results
    """
    from datetime import datetime
    from time import time

    timestamp = int(time())  # timestamp of generation
    dt = datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
    if name_suffix:
        filename = '_'.join([code, name_suffix]) + '.json'
    else:
        filename = '_'.join([code, dt]) + '.json'

    '''adding data section to the elements, with:
        timestamp, status'''
    result = {'file_stats': {'result_type': 'task' if task_id else 'comp', 'timestamp': timestamp, 'status': status}}
    result.update(elements)

    '''creating file'''
    write_json_file(filename, result)

    '''create or update database entry'''
    row = TblResultFile.get_one(filename=filename)
    if row:
        row.update(comp_id=comp_id, task_id=task_id, created=timestamp, filename=filename, status=status)
    else:
        row = TblResultFile(comp_id=comp_id, task_id=task_id, created=timestamp, filename=filename, status=status)
        row.save()
    return row.ref_id, filename, timestamp


def unpublish_result(taskid_or_compid, comp=False):
    """unpublish (set active to 0) all result files for a task or a comp"""
    with db_session() as db:
        if comp:
            db.query(TblResultFile).filter(
                and_(TblResultFile.comp_id == taskid_or_compid, TblResultFile.task_id.is_(None))
            ).update({'active': 0})
        else:
            db.query(TblResultFile).filter_by(task_id=taskid_or_compid).update({'active': 0})
    return 1


def publish_result(filename_or_refid, ref_id=False):
    """publish (set active to 1) a result files, by default takes filename of result to publish,
    otherwise ref_id if ref_id flag True"""

    with db_session() as db:
        if ref_id:
            db.query(TblResultFile).filter_by(ref_id=filename_or_refid).update({'active': 1})
        else:
            db.query(TblResultFile).filter_by(filename=filename_or_refid).update({'active': 1})
    return 1


def open_json_file(filename: str or Path):
    import jsonpickle

    try:
        with open(Path(RESULTDIR, filename), 'r') as f:
            return jsonpickle.decode(f.read())
    except TypeError:
        print(f"error: {filename} is not a proper filename")
    except FileNotFoundError:
        print(f"error: file {filename} does not exist")
    return None


def write_json_file(filename: str, content: dict):
    import os
    from calcUtils import CJsonEncoder
    file = Path(RESULTDIR, filename)
    '''creating json formatting'''
    content = json.dumps(content, cls=CJsonEncoder, sort_keys=True)

    '''creating file'''
    with open(file, 'w+') as f:
        f.seek(0)
        f.truncate()
        f.write(content)

    '''giving correct access permission'''
    os.chown(file, 1000, 1000)


def update_result_status(filename: str, status: str, locked: bool = None):
    import time

    '''check if json file exists, and updates it'''
    file = Path(RESULTDIR, filename)
    if not file.is_file():
        print(f'Json file {filename} does not exist')
        return None
    with open(file, 'r+') as f:
        '''update status in json file'''
        d = json.load(f)
        d['file_stats']['status'] = status
        d['file_stats']['last_update'] = int(time.time())
        if locked is not None:
            d['info']['locked'] = int(locked)
        f.seek(0)
        f.write(json.dumps(d))
        f.truncate()
        print(f'JSON file has been updated \n')
        '''update status in database'''
        with db_session() as db:
            result = db.query(TblResultFile).filter_by(filename=filename).one()
            result.status = status


def update_tasks_status_in_comp_result(comp_id: int) -> bool:
    """gets status for active tasks result files and writes them in active comp result file"""
    from compUtils import get_comp_json_filename
    from task import get_task_json
    try:
        file = Path(RESULTDIR, get_comp_json_filename(comp_id))
        with open(file, 'r+') as f:
            d = json.load(f)
            for t in d.get('tasks'):
                file = get_task_json(t['id'])
                t['status'] = file['file_stats']['status']
                t['locked'] = file['info'].get('locked') or 0
            f.seek(0)
            f.write(json.dumps(d))
            f.truncate()
        return True
    except Exception:
        return False


def update_result_file(filename: str, par_id: int, notification: dict):
    """gets result filename, pilot's par_id, and notification as dict
    notification = {'not_id': notification id if existing, can be omitted
                    'notification_type': only 'admin' can be edited / added at the moment, can be omitted
                    'flat_penalty': if we are adding just a comment without penalty / bonus, can be omitted
                    'comment': text of notification
                    }
    """
    import time
    from db.tables import TblNotification as N

    file = Path(RESULTDIR, filename)
    if not file.is_file():
        print(f'Json file {filename} does not exist')
        return None
    comment = notification['comment']
    penalty = 0 if not notification.get('flat_penalty') else float(notification['flat_penalty'])
    not_id = notification.get('not_id')
    old_penalty = 0
    with open(file, 'r+') as f:
        data = json.load(f)
        task_id = data['info']['id']
        result = next(res for res in data['results'] if res['par_id'] == par_id)
        track_id = int(result['track_id'])
        if not result:
            print(f'Result file has no pilot with ID {par_id}')
            return None
        with db_session() as db:
            if not_id:
                '''notification already existing'''
                row = db.query(N).get(not_id)
                old_penalty = row.flat_penalty
                old_comment = row.comment
                if old_penalty == penalty and row.comment == comment:
                    '''nothing changed'''
                    print(f'Result file has not changed, pilot ID {par_id}')
                    return None
                row.comment = comment
                row.flat_penalty = penalty
                db.flush()
                '''updating result file'''
                entry = next(el for el in result['notifications'] if int(el['not_id']) == not_id)
                entry['comment'] = comment
                entry['flat_penalty'] = penalty
                result['comment'].replace(' '.join(['[custom]', old_comment]), ' '.join(['[custom]', comment]))
            else:
                '''adding a new one'''
                row = N(track_id=track_id, notification_type='admin', **notification)
                db.add(row)
                db.flush()
                notification['not_id'] = row.not_id
                '''adding to result file'''
                result['notifications'].append(
                    dict(
                        not_id=row.not_id,
                        notification_type='admin',
                        percentage_penalty=0,
                        flat_penalty=penalty,
                        comment=comment,
                    )
                )
                '''update comment'''
                comment = '[custom] ' + comment
                if not result['comment']:
                    result['comment'] = comment
                else:
                    '; '.join([result['comment'], comment])
            '''penalty and score calculation'''
            if (not_id and old_penalty != penalty) or (not not_id and penalty != 0):
                '''need to recalculate scores'''
                result['penalty'] += penalty - old_penalty
                result['score'] = max(
                    0,
                    sum(
                        [
                            result['arrival_score'],
                            result['departure_score'],
                            result['time_score'],
                            result['distance_score'],
                        ]
                    )
                    - result['penalty'],
                )

                data['results'] = order_task_results(data['results'])
            data['file_stats']['last_update'] = int(time.time())
            try:
                f.seek(0)
                f.write(json.dumps(data))
                f.truncate()
            except Exception as e:
                print(f'Error updating result file for participant ID {par_id}')
                error = str(e.__dict__)
                db.rollback()
                db.close()
                return error


def order_task_results(results: list) -> list:
    """Orders pilots list based on result:
        - points, decr
        - NYP
        - DNF
        - ABS
    """
    pil_list = sorted(
        [p for p in results if p['result_type'] not in ['dnf', 'abs', 'nyp']],
        key=lambda k: k['score'],
        reverse=True,
    )
    pil_list += [p for p in results if p['result_type'] == 'nyp']
    pil_list += [p for p in results if p['result_type'] == 'dnf']
    pil_list += [p for p in results if p['result_type'] == 'abs']
    return pil_list


def update_results_rankings(comp_id: int, comp_class: str = None) -> bool:
    """ Updates rankings list in results json files of a comp if rankings are changed """
    from ranking import create_rankings
    from calcUtils import CJsonEncoder

    with db_session() as db:
        files = [Path(RESULTDIR, res.filename) for res in db.query(TblResultFile).filter_by(comp_id=comp_id)
                 if Path(RESULTDIR, res.filename).is_file()]
    if files:
        rankings = create_rankings(comp_id, comp_class)
        try:
            for file in files:
                with open(file, 'r+') as f:
                    data = json.load(f)
                    data['rankings'] = rankings
                    f.seek(0)
                    f.write(json.dumps(data, cls=CJsonEncoder))
                    f.truncate()
            return True
        except Exception as e:
            # raise
            print(f'Error updating result file: {str(e.__dict__)}')
            return False


def delete_result(filename: str, delete_file=False):
    if delete_file:
        Path(RESULTDIR, filename).unlink(missing_ok=True)
    row = TblResultFile.get_one(filename=filename)
    row.delete()


def get_country_list(countries: set = None, iso: int = None) -> list:
    """
    Returns a list of countries code and names.
    If a list of codes is not given, returns the whole countries set.
    Args:
        countries: set of country codes
        iso: 2 or 3 if None, return standard IOC codes; default: None
    Returns:
        a list of objects with attributes name and code
    """
    from db.tables import TblCountryCode as CC

    return CC.get_list(countries=countries, iso=iso)


def pretty_format_results(content, timeoffset=0, td=0, cd=0):
    from calcUtils import epoch_to_string, sec_to_duration, sec_to_string

    pure_time = ['ss_time', 'time_offset', 'fastest', 'fastest_in_goal']
    duration = ['tot_flight_time', 'SS_interval', 'max_JTG', 'validity_min_time', 'score_back_time']
    day_time = ('_time', '_deadline')
    validity = ('_validity', '_quality')
    weight = '_weight'
    scores = (
        '_score',
        'penalty',
        '_arr_points',
        '_dep_points',
        '_dist_points',
        '_time_points',
    )
    booleans = ['team_scoring', 'country_scoring', 'nat_team']
    percentage = ['no_goal_penalty', 'nominal_goal', 'nominal_launch', 'tolerance', 'validity_param']
    upper = ['overall_validity']
    formatted = dict()
    # content = jsonpickle.decode(content)
    # print(f'{type(content)}')
    if isinstance(content, list):
        formatted = []
        for value in content:
            if isinstance(value, (dict, list)):
                formatted.append(pretty_format_results(value))
            else:
                formatted.append(str(value))
    else:
        for key, value in content.items():
            if isinstance(value, (dict, list)):
                formatted[key] = pretty_format_results(value)
            else:
                # print(f'{key}, {type(key)}, {value}')
                try:
                    if value is None:
                        '''formatting None to empty'''
                        formatted[key] = ''
                    # Formatting Times
                    elif key in pure_time:
                        '''formatting time'''
                        formatted[key] = sec_to_string(int(value))
                    elif str(key).endswith(day_time):
                        '''formatting time with offset'''
                        formatted[key] = '' if int(value) == 0 else sec_to_string(int(value), timeoffset)
                    elif str(key) in duration:
                        '''formatting duration'''
                        formatted[key] = sec_to_duration(int(value))
                    elif 'timestamp' in str(key):
                        '''formatting timestamp'''
                        formatted[key] = epoch_to_string(int(value), timeoffset)
                    # Formatting Waypoints Table
                    elif 'cumulative_dist' in content.keys():
                        if key == 'radius':
                            '''formatting wpt radius'''
                            formatted[key] = (
                                '' if float(value) == 0
                                else f"{round(float(value) / 1000, 1):.1f} Km"
                                if float(value) > 1000
                                else f"{round(float(value))} m &nbsp;"
                            )
                        elif key == 'cumulative_dist':
                            '''formatting wpt cumulative distance'''
                            formatted[key] = '' if float(value) == 0 else f"{c_round(float(value) / 1000, 2):.2f} Km"
                        elif key == 'type':
                            '''formatting wpt type'''
                            formatted[key] = (
                                ''
                                if str(value) == 'waypoint'
                                else 'SS'
                                if str(value) == 'speed'
                                else 'ES'
                                if str(value) == 'endspeed'
                                else str(value)
                            )
                        elif key == 'shape':
                            '''formatting wpt shape'''
                            formatted[key] = '' if str(value) == 'circle' else '(line)'
                        elif key == 'shape':
                            '''formatting wpt versus'''  # Not needed anymore?
                            # formatted[key] = '' if str(value) == 'entry' else '(exit)'
                            formatted[key] = ''
                        else:
                            '''name and description'''
                            formatted[key] = str(value)
                    # Formatting Altitudes
                    elif str(key).endswith('_altitude'):
                        formatted[key] = '' if not value else int(value)
                    # Formatting Text
                    elif key in upper:
                        '''formatting uppercase text'''
                        formatted[key] = str(value).upper()
                    # Formatting Numbers
                    elif key in percentage:
                        '''formatting percentage'''
                        v = float(value if not key == 'validity_param' else 1 - value)
                        formatted[key] = f"{c_round(v * 100, 2):.2f}%"
                    elif str(key).endswith(validity):
                        '''formatting formula validity'''
                        formatted[key] = f"{c_round(float(value), 3):.3f}"
                    elif str(key).endswith(weight):
                        '''formatting formula weight'''
                        formatted[key] = f"{c_round(float(value), 3):.3f}"
                    elif str(key).endswith(scores):
                        '''formatting partial scores'''
                        formatted[key] = f"{c_round(float(value), 1):.1f}" if value else ""
                    elif key == 'speed':
                        formatted[key] = '' if float(value) == 0 else f"{c_round(float(value), 1):.1f}"
                    # Formatting Distances
                    elif key in ['distance', 'distance_flown', 'stopped_distance']:
                        '''formatting distance without unit of measure'''
                        formatted[key] = f"{c_round(float(value) / 1000, 2):.2f}"
                    elif 'dist' in str(key):
                        '''formatting distances with unit of measure'''
                        formatted[key] = f"{c_round(float(value) / 1000, 1):.1f} Km"
                    # Formatting Booleans
                    elif key in booleans:
                        '''formatting booleans'''
                        formatted[key] = value is True
                    else:
                        formatted[key] = str(value)
                except ValueError:
                    formatted[key] = str(value)
    return formatted


def get_startgates(task_info):
    """creates a list of startgates time from start_time, SS_interval, start_iteration"""
    from calcUtils import sec_to_string

    start_time = task_info['start_time'] or 0
    if start_time:
        interval = task_info['SS_interval'] or 0
        iteration = task_info['start_iteration'] or 0
        offset = task_info['time_offset'] or 0
        return [sec_to_string(start_time + i * interval, offset) for i in range(iteration + 1)]


def get_task_country_json(filename):
    """
    Get task result json file as input
    returns json formatted string
    list of nations dict with attributes:
        name: nation name
        code: nation code
        score: nation score
        pilots: list of pilots dict, as in result json file. Only pilots in National team.
    So in frontend every result after the max team size should be formatted as deleted"""
    import jsonpickle

    data = open_json_file(filename)
    formula = data['formula']
    if not formula['country_scoring']:
        print(f'Country Scoring is not available')
        return None
    countries = get_country_list(countries=set(map(lambda x: x['nat'], data['results'])))
    size = formula['team_size'] if 'country_size' not in formula.keys() else formula['country_size']
    results = []
    for nat in countries:
        nat_pilots = sorted(
            [p for p in data['results'] if p['nat'] == nat['code'] and p['nat_team']],
            key=lambda k: k['score'],
            reverse=True,
        )
        nat['pilots'] = nat_pilots
        nat['score'] = sum([p['score'] for p in nat_pilots][:size])
        results.append(nat)
    results = sorted(results, key=lambda k: k['score'], reverse=True)
    return jsonpickle.encode(results)


def get_comp_country_json(filename):
    """
    Get comp result json file as input
    returns json formatted string
    list of nations dict with attributes:
        name: nation name
        code: nation code
        score: nation score
        pilots: list of pilots dict, as in result json file, but in results attribute you have, for each task:
            pre: actual pilot result
            perf: 1 if result has been used by team, 0 otherwise
            score: actual score if used, 0 otherwise
    So in frontend every result is taken from pre, formatted as deleted if perf == 0"""
    import jsonpickle

    data = open_json_file(filename)
    formula = data['formula']
    if not formula['country_scoring']:
        print(f'Country Scoring is not available')
        return None
    '''get info: countries list, team size, task codes'''
    countries = get_country_list(countries=set(map(lambda x: x['nat'], data['results'])))
    size = formula['team_size'] if 'country_size' not in formula.keys() else formula['country_size']
    tasks = [t['task_code'] for t in data['tasks']]
    results = []
    for nat in countries:
        nat_pilots = [p for p in data['results'] if p['nat'] == nat['code'] and p['nat_team']]
        score = 0
        for t in tasks:
            '''sort pilots by task result'''
            nat_pilots = sorted(nat_pilots, key=lambda k: k['results'][t]['pre'], reverse=True)
            '''adjust values'''
            for idx, p in enumerate(nat_pilots):
                if idx < size:
                    score += p['results'][t]['pre']
                    p['results'][t]['score'] = p['results'][t]['pre']
                    p['results'][t]['perf'] = 1
                else:
                    p['results'][t]['score'] = 0
                    p['results'][t]['perf'] = 0
        '''final nation sorting'''
        for p in nat_pilots:
            p['score'] = sum(p['results'][t]['score'] for t in tasks)
        nat_pilots = sorted(nat_pilots, key=lambda k: k['score'], reverse=True)
        nat['pilots'] = nat_pilots
        nat['score'] = score
        results.append(nat)
    results = sorted(results, key=lambda k: k['score'], reverse=True)
    return jsonpickle.encode(results)


def get_comp_team_json(filename):
    """
    Get comp result json file as input
    returns json formatted string
    list of teams dict with attributes:
        name: team name
        score: team score
        pilots: list of pilots dict, as in result json file, but in results attribute you have, for each task:
            pre: actual pilot result
            perf: 1 if result has been used by team, 0 otherwise
            score: actual score if used, 0 otherwise
    So in frontend every result is taken from pre, formatted as deleted if perf == 0"""
    import jsonpickle

    data = open_json_file(filename)
    formula = data['formula']
    if not formula['team_scoring']:
        print(f'Team Scoring is not available')
        return None
    '''get info: teams list, team size, task codes'''
    pilots = [p for p in data['results'] if not p['team'] in [None, '']]
    teams = set(map(lambda x: x['team'].strip().title(), pilots))
    size = formula['team_size']
    tasks = [t['task_code'] for t in data['tasks']]
    results = []
    for el in teams:
        team = dict(name=el)
        team_pilots = [p for p in pilots if p['team'].strip().title() == team['name']]
        score = 0
        for t in tasks:
            '''sort pilots by task result'''
            team_pilots = sorted(team_pilots, key=lambda k: k['results'][t]['pre'], reverse=True)
            '''adjust values'''
            for idx, p in enumerate(team_pilots):
                if idx < size:
                    score += p['results'][t]['pre']
                    p['results'][t]['score'] = p['results'][t]['pre']
                    p['results'][t]['perf'] = 1
                else:
                    p['results'][t]['score'] = 0
                    p['results'][t]['perf'] = 0
        '''final nation sorting'''
        for p in team_pilots:
            p['score'] = sum(p['results'][t]['score'] for t in tasks)
        nat_pilots = sorted(team_pilots, key=lambda k: k['score'], reverse=True)
        team['pilots'] = nat_pilots
        team['score'] = score
        results.append(team)
    results = sorted(results, key=lambda k: k['score'], reverse=True)
    return jsonpickle.encode(results)


def get_task_team_json(filename):
    """
    Get task result json file as input
    returns json formatted string
    list of teams dict with attributes:
        name: team name
        score: team score
        pilots: list of team pilots dict, as in result json file.
    So in frontend every result after the max team size should be formatted as deleted.
    Only pilots with team different from None or ''"""
    import jsonpickle

    data = open_json_file(filename)
    formula = data['formula']
    if not formula['team_scoring']:
        print(f'Team Scoring is not available')
        return None
    pilots = [p for p in data['results'] if not p['team'] in [None, '']]
    teams = set(map(lambda x: x['team'].strip().title(), pilots))
    size = formula['team_size']
    results = []
    for el in teams:
        team = dict(name=el)
        team_pilots = sorted(
            [p for p in pilots if p['team'].strip().title() == team['name']], key=lambda k: k['score'], reverse=True
        )
        team['pilots'] = team_pilots
        team['score'] = sum([p['score'] for p in team_pilots][:size])
        results.append(team)
    results = sorted(results, key=lambda k: k['score'], reverse=True)
    return jsonpickle.encode(results)


def get_task_country_scoring(filename):
    """takes a task result filename and outputs a nested dict ready to be jsonified for the front end
    each pilot has attributes for their nation and nation score to allow grouping in datatables js.
    Scores are given html strikethough <del> if they do not count towards nation total
    """
    data = open_json_file(filename)
    formula = data['formula']
    pilots = []
    teams = []
    all_scores = []
    if not formula['country_scoring']:
        print(f'Country Scoring is not available')
        return {'error': 'Country Scoring is not available'}

    '''score decimals'''
    td = 0 if 'task_result_decimal' not in formula.keys() else int(data['formula']['task_result_decimal'])

    countries = get_country_list(countries=set(map(lambda x: x['nat'], data['results'])))
    size = formula['team_size'] if 'country_size' not in formula.keys() else formula['country_size']
    for nat in countries:
        nat_pilots = sorted(
            [p for p in data['results'] if p['nat'] == nat['code'] and p['nat_team']],
            key=lambda k: k['score'],
            reverse=True,
        )
        nat['score'] = sum([p['score'] for p in nat_pilots][:size])
        for rank, p in enumerate(nat_pilots):
            p['group'] = f". {nat['name']} - {c_round(nat['score'], td)} points"
            p['nation_score'] = nat['score']
            if rank >= size:
                p['score'] = f"<del>{c_round(p['score'], td)}</del>"
            else:
                p['score'] = f"{c_round(p['score'], td)}"
        teams.append(nat)
        pilots.extend(nat_pilots)
    # get rank after sort
    for t in teams:
        all_scores.append(t['score'])
    for row in pilots:
        row['group'] = str(sum(map(lambda x: x > row['nation_score'], all_scores)) + 1) + row['group']
    return {'teams': teams, 'data': pilots, 'info': data['info'], 'formula': data['formula']}


def get_comp_country_scoring(filename):
    """takes a competition result filename and outputs a nested dict ready to be jsonified for the front end
    each pilot has attributes for their nation and nation score to allow grouping in datatables js.
    Scores are given html strikethough <del> if they do not count towards nation total
    """
    data = open_json_file(filename)
    formula = data['formula']
    if not formula['country_scoring']:
        print(f'Country Scoring is not available')
        return None

    '''score decimals'''
    td = 0 if 'task_result_decimal' not in formula.keys() else int(data['formula']['task_result_decimal'])
    cd = 0 if 'comp_result_decimal' not in formula.keys() else int(data['formula']['comp_result_decimal'])

    '''get info: countries list, team size, task codes'''
    countries = get_country_list(countries=set(map(lambda x: x['nat'], data['results'])))
    '''rankings'''
    rankings = [dict(rank=1, counter=0, prev=None, **rank) for rank in data['rankings']
                if rank['rank_type'] in ('overall', 'country')]
    size = formula['team_size'] if 'country_size' not in formula.keys() else formula['country_size']
    tasks = [t['task_code'] for t in data['tasks'] if not t['training']]
    teams = []
    pilots = []
    all_scores = []

    rank = 0
    prev = None
    for nat in countries:
        nat_pilots = [p for p in data['results'] if p['nat'] == nat['code'] and p['nat_team'] == 1]
        score = 0
        for t in tasks:
            '''sort pilots by task result'''
            nat_pilots = sorted(nat_pilots, key=lambda k: k['results'][t]['pre'], reverse=True)
            '''adjust values'''
            for idx, p in enumerate(nat_pilots):
                pre = c_round(p['results'][t]['pre'] or 0, td)
                if idx < size:
                    score += pre
                    p['results'][t]['score'] = pre
                    p['results'][t]['perf'] = 1
                else:
                    p['results'][t]['score'] = f"<del>{pre}</del>"
                    p['results'][t]['perf'] = 0
        '''final nation sorting'''
        for p in nat_pilots:
            p['score'] = sum(p['results'][t]['score'] for t in tasks if not isinstance(p['results'][t]['score'], str))
            p['group'] = f". {nat['name']} - {c_round(score, cd)} points"
            p['nation_score'] = score
        nat_pilots = sorted(nat_pilots, key=lambda k: k['score'], reverse=True)
        pilots.extend(nat_pilots)
        nat['score'] = score
        teams.append(nat)

    # get rank after sort
    for t in teams:
        all_scores.append(t['score'])
    for row in pilots:
        row['group'] = str(sum(map(lambda x: x > row['nation_score'], all_scores)) + 1) + row['group']

    # '''manage rankings'''

    return {'data': pilots, 'info': data['info'], 'tasks': data['tasks'],
            'formula': data['formula'], 'stats': data['stats'], 'rankings': rankings}


def get_task_team_scoring(filename):
    """takes a task result filename and outputs a nested dict ready to be jsonified for the front end
    each pilot has attributes for their nation and nation score to allow grouping in datatables js.
    Scores are given html strikethough <del> if they do not count towards nation total
    """
    data = open_json_file(filename)
    formula = data['formula']
    pilots = []
    teams = []
    all_scores = []
    if not formula['team_scoring']:
        print(f'Team Scoring is not available')
        return None

    '''score decimals'''
    td = 0 if 'task_result_decimal' not in formula.keys() else int(data['formula']['task_result_decimal'])

    pilots_list = [p for p in data['results'] if not p['team'] in [None, '']]
    teams_list = set(map(lambda x: x['team'].strip().title(), pilots_list))
    size = formula['team_size']
    for el in teams_list:
        team = dict(name=el)
        team_pilots = sorted(
            [p for p in pilots_list if p['team'].strip().title() == team['name']],
            key=lambda k: k['score'],
            reverse=True,
        )
        team['pilots'] = team_pilots
        team['score'] = sum([p['score'] for p in team_pilots][:size])
        for rank, p in enumerate(team_pilots):
            p['group'] = f". {team['name']} - {c_round(team['score'], td)} points"
            p['team_score'] = team['score']
            if rank >= size:
                p['score'] = f"<del>{c_round(p['score'], td)}</del>"
            else:
                p['score'] = f"{c_round(p['score'], td)}"
        teams.append(team)
        pilots.extend(team_pilots)
    # get rank after sort
    for t in teams:
        all_scores.append(t['score'])
    for row in pilots:
        row['group'] = str(sum(map(lambda x: x > row['team_score'], all_scores)) + 1) + row['group']
    return {'teams': teams, 'data': pilots, 'info': data['info'], 'formula': data['formula'], 'stats': data['stats']}


def get_comp_team_scoring(filename):
    """takes a competition result filename and outputs a nested dict ready to be jsonified for the front end
    each pilot has attributes for their nation and nation score to allow grouping in datatables js.
    Scores are given html strikethough <del> if they do not count towards nation total
    """
    data = open_json_file(filename)
    formula = data['formula']
    if not formula['team_scoring']:
        print(f'Team Scoring is not available')
        return None
    '''get info: teams list, team size, task codes'''
    pilots_list = [p for p in data['results'] if not p['team'] in [None, '']]
    teams_list = set(map(lambda x: x['team'].strip().title(), pilots_list))
    size = formula['team_size']
    tasks = [t['task_code'] for t in data['tasks'] if not t.get('training')]
    teams = []
    pilots = []
    all_scores = []
    all_possible_tasks = []

    '''score decimals'''
    td = 0 if 'task_result_decimal' not in formula.keys() else int(data['formula']['task_result_decimal'])
    cd = 0 if 'comp_result_decimal' not in formula.keys() else int(data['formula']['comp_result_decimal'])

    # setup the 20 task placeholders
    for t in range(1, 21):
        all_possible_tasks.append('T' + str(t))

    for el in teams_list:
        team = dict(name=el)
        team_pilots = [p for p in pilots_list if p['team'].strip().title() == team['name']]
        score = 0
        for t in tasks:
            '''sort pilots by task result'''
            team_pilots = sorted(team_pilots, key=lambda k: k['results'][t]['pre'], reverse=True)
            '''adjust values'''
            for idx, p in enumerate(team_pilots):
                if idx < size:
                    score += p['results'][t]['pre']
                    p['results'][t]['score'] = p['results'][t]['pre']
                    p['results'][t]['perf'] = 1
                else:
                    p['results'][t]['score'] = f"<del>{int(p['results'][t]['pre'])}</del>"
                    p['results'][t]['perf'] = 0
        for t in list(set(all_possible_tasks) - set(tasks)):
            for idx, p in enumerate(team_pilots):
                p['results'][t] = {'score': ''}
        '''final team sorting'''
        for p in team_pilots:
            p['score'] = sum(p['results'][t]['score'] for t in tasks if not isinstance(p['results'][t]['score'], str))
            p['group'] = f". {team['name']} - {c_round(score, cd)} points"
            p['team_score'] = score
        team_pilots = sorted(team_pilots, key=lambda k: k['score'], reverse=True)
        pilots.extend(team_pilots)
        team['score'] = score
        teams.append(team)
    # get rank after sort
    for t in teams:
        all_scores.append(t['score'])
    for row in pilots:
        row['group'] = str(sum(map(lambda x: x > row['team_score'], all_scores)) + 1) + row['group']

    return {'teams': teams, 'data': pilots, 'info': data['info'], 'tasks': data['tasks'], 'formula': data['formula'], 'stats': data['stats']}
