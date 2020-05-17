"""
JSON Results Creation

contains
    Task_result class
    Comp_result class

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

from db_tables import TblResultFile
from myconn import Database
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update, and_


class Task_result:
    """
        Task result fields lists
    """

    info_list = ['id',
                 'comp_name',
                 'comp_site',
                 'comp_class',
                 'date',
                 'task_name',
                 'task_num',
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
                 'last_start_time',
                 'task_type',
                 'distance',
                 'opt_dist',
                 'SS_distance',
                 'stopped_time',
                 'goal_altitude']

    route_list = ['name',
                  'description',
                  'how',
                  'radius',
                  'shape',
                  'type',
                  'lat',
                  'lon',
                  'altitude']

    formula_list = ['formula_name',
                    'formula_type',
                    'formula_version',
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
                    'max_country_size'
                    ]

    stats_list = ['pilots_launched',
                  'pilots_present',
                  'pilots_ess',
                  'pilots_landed',
                  'pilots_goal',
                  'fastest',
                  'fastest_in_goal',
                  'min_dept_time',
                  'max_ss_time'
                  'min_ess_time',
                  'max_ess_time',
                  'last_landing_time'
                  'max_distance',
                  'tot_distance_flown',
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
                  'max_score',
                  'min_lead_coeff',
                  'tot_flight_time']

    results_list = ['track_id',
                    'par_id',
                    'ID',
                    'civl_id',
                    'fai_id',
                    'name',
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
                    'turnpoints_made',
                    'waypoints_achieved',
                    'distance_score',
                    'time_score',
                    'departure_score',
                    'arrival_score',
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
                    'pil_id']


class Comp_result(object):
    """
        Comp result fields lists
    """

    info_list = ['id',
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
                 'website']

    stats_list = ['winner_score',
                  'valid_tasks',
                  'tot_validity',
                  'avail_validity',
                  'tot_flights',
                  'tot_distance_flown',
                  'tot_flight_time',
                  'tot_pilots']

    formula_list = ['formula_name',
                    'formula_type',
                    'formula_version',
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
                    'comp_result_decimal',
                    'team_scoring',
                    'team_size',
                    'max_team_size',
                    'country_scoring',
                    'country_size',
                    'max_country_size'
                    ]

    task_list = ['id',
                 'task_name',
                 'task_code',
                 'date',
                 'comment',
                 'opt_dist',
                 'pilots_goal',
                 'day_quality',
                 'ftv_validity',
                 'max_score',
                 'task_type']

    ''' result_list comes from Participant obj, and RegisteredPilotView
        available fields are: (`par_id`, `comp_id`, `civl_id`, `fai_id`, `pil_id`, `ID`, `name`, `sex`, `nat`,
                            `glider`, `class`, `sponsor`, `team`, `nat_team`, 'results')'''
    result_list = ['ID',
                   'par_id',
                   'civl_id',
                   'fai_id',
                   'name',
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
                   'results']


def create_json_file(comp_id, code, elements, task_id=None, status=None):
    """
    creates the JSON file of results
    """
    import os
    import json
    from time import time
    from datetime import datetime
    from Defines import RESULTDIR
    from calcUtils import CJsonEncoder

    timestamp = int(time())  # timestamp of generation
    dt = datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
    filename = '_'.join([code, dt]) + '.json'

    '''adding data section to the elements, with:
        timestamp, status'''
    result = {'file_stats': {'timestamp': timestamp, 'status': status}}
    result.update(elements)

    '''creating json formatting'''
    content = json.dumps(result, cls=CJsonEncoder)

    '''creating file'''
    with open(RESULTDIR + filename, 'w') as f:
        f.write(content)
    os.chown(RESULTDIR + filename, 1000, 1000)

    '''create database entry'''
    with Database() as db:
        result = TblResultFile(comp_id=comp_id, task_id=task_id, created=timestamp, filename=filename, status=status)
        db.session.add(result)
        db.session.commit()
        ref_id = result.ref_id
    return ref_id, filename, timestamp


def unpublish_result(taskid_or_compid, comp=False, session=None):
    """unpublish (set active to 0) all result files for a task or a comp"""
    with Database(session) as db:
        try:
            if comp:
                db.session.query(TblResultFile).filter(and_(TblResultFile.comp_id == taskid_or_compid,
                                                            TblResultFile.task_id.is_(None))).update({'active': 0})
            else:
                db.session.query(TblResultFile).filter(TblResultFile.task_id == taskid_or_compid).update({'active': 0})
            db.session.commit()
            if not session:
                db.session.close()
        except SQLAlchemyError as e:
            error = str(e.__dict__)
            print(f"Error unpublishing result in database: {error}")
            db.session.rollback()
            db.session.close()
            return error
        return 1


def publish_result(filename_or_refid, ref_id=False, session=None):
    """publish (set active to 1) a result files, by default takes filename of result to publish,
    otherwise ref_id if ref_id flag True"""

    with Database(session) as db:
        try:
            if ref_id:
                db.session.query(TblResultFile).filter(TblResultFile.ref_id == filename_or_refid).update({'active': 1})
            else:
                db.session.query(TblResultFile).filter(TblResultFile.filename == filename_or_refid).update(
                    {'active': 1})
            db.session.commit()
            if not session:
                db.session.close()
        except SQLAlchemyError as e:
            error = str(e.__dict__)
            print(f"Error publishing result in database: {error}")
            db.session.rollback()
            db.session.close()
            return error
        return 1


def update_result_status(filename, status):
    from Defines import RESULTDIR
    from os import path
    from pathlib import Path
    import json
    '''check if json file exists, and updates it'''
    file = path.join(RESULTDIR, filename)
    if not Path(file).is_file():
        print(f'Json file {filename} does not exist')
        return None
    with open(file, 'r+') as f:
        '''update status in json file'''
        d = json.load(f)
        d['file_stats']['status'] = status
        f.seek(0)
        f.write(json.dumps(d))
        f.truncate()
        print(f'JSON file has been updated \n')
        '''update status in database'''
        with Database() as db:
            try:
                result = db.session.query(TblResultFile).filter(TblResultFile.filename == filename).one()
                result.status = status
                db.session.flush()
            except SQLAlchemyError as e:
                print(f'Error updating result file {filename}')
                error = str(e.__dict__)
                db.session.rollback()
                db.session.close()
                return error


def update_result_file(filename, par_id, comment=None, penalty=None):
    """gets result file id and info to update from frontend"""
    from db_tables import TblTaskResult
    from sqlalchemy import and_
    from Defines import RESULTDIR
    from os import path
    from pathlib import Path
    import json
    file = path.join(RESULTDIR, filename)
    if not Path(file).is_file():
        print(f'Json file {filename} does not exist')
        return None
    with open(file, 'r+') as f:
        data = json.load(f)
        task_id = data['info']['id']
        result = next(res for res in data['results'] if res['par_id'] == par_id)
        if not result:
            print(f'Result file has no pilot with ID {par_id}')
            return None
        with Database() as db:
            try:
                pilot = db.session.query(TblTaskResult).filter(and_(TblTaskResult.par_id == par_id,
                                                                    TblTaskResult.task_id == task_id)).one()
                if comment:
                    comment = '[admin] ' + str(comment)
                    result['comment'].append(comment)
                    pilot.comment = comment if not pilot.comment else pilot.comment + '; ' + comment
                if penalty is not None:
                    result['penalty'] = penalty
                    result['score'] = max(0, sum([result['arrival_score'], result['departure_score'],
                                                  result['time_score'], result['distance_score']]) - penalty)
                    pilot.penalty = result['penalty']
                    pil_list = sorted([p for p in data['results'] if p['result_type'] not in ['dnf', 'abs']],
                                      key=lambda k: k['score'], reverse=True)
                    pil_list += [p for p in data['results'] if p['result_type'] == 'dnf']
                    pil_list += [p for p in data['results'] if p['result_type'] == 'abs']
                    data['results'] = pil_list
                db.session.flush()
            except SQLAlchemyError as e:
                print(f'Error updating result entry for participant ID {par_id}')
                error = str(e.__dict__)
                db.session.rollback()
                db.session.close()
                return error
        f.seek(0)
        f.write(json.dumps(data))
        f.truncate()


def delete_result(ref_id, filename=None, session=None):
    from Defines import RESULTDIR
    import os
    with Database(session) as db:
        try:
            if not filename:
                filename = db.session.query(TblResultFile).get(ref_id).filename
            file = os.path.join(RESULTDIR, filename)
            if os.path.exists(file):
                os.remove(file)
            db.session.query(TblResultFile).filter(TblResultFile.ref_id == ref_id).delete(synchronize_session=False)
            db.session.commit()
        except SQLAlchemyError as e:
            error = str(e)
            print(f"Error deleting result from database: {error}")
            db.session.rollback()
            db.session.close()
            return error


def get_country_list(countries=None, iso=3):
    """
    Returns a list of countries code and names.
    If a list of codes is not given, returns the whole countries set.
    Args:
        countries: list of country codes
        iso: 2 or 3
    Returns:
        a list of objects with attributes name and code
    """
    from db_tables import TblCountryCode as CC
    from myconn import Database
    from sqlalchemy.exc import SQLAlchemyError
    column = getattr(CC, 'natIso' + str(iso))
    with Database() as db:
        try:
            query = db.session.query(CC.natName.label('name'), column.label('code'))
            if countries:
                return sorted(query.filter(column.in_(countries)).all(), key=lambda k: k.name)
            return query.all()
        except SQLAlchemyError as e:
            error = str(e)
            print(f"Error getting countries list from database: {error}")
            db.session.rollback()
            db.session.close()
            return error


def open_json_file(filename):
    from pathlib import Path
    from os import path
    import jsonpickle
    from Defines import RESULTDIR
    file = path.join(RESULTDIR, filename)
    if not Path(file).is_file():
        print(f"error: file {filename} does not exist")
        return None
    with open(file, 'r') as f:
        return jsonpickle.decode(f.read())


def pretty_format_results(content, timeoffset=0, td=0, cd=0):
    import jsonpickle
    from calcUtils import sec_to_string, sec_to_duration, epoch_to_datetime, c_round
    pure_time = ['ss_time', 'time_offset', 'fastest', 'fastest_in_goal']
    duration = ['tot_flight_time', 'SS_interval', 'max_JTG', 'validity_min_time', 'score_back_time']
    day_time = ('_time', '_deadline')
    validity = ('_validity', '_quality')
    weight = '_weight'
    scores = ('_score', 'penalty', '_arr_points', '_dep_points', '_dist_points', '_time_points',)
    booleans = ['team_scoring', 'country_scoring', 'nat_team']
    percentage = ['no_goal_penalty', 'nominal_goal', 'nominal_launch', 'tolerance', 'validity_param']
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
                    elif 'timestamp' in key:
                        '''formatting timestamp'''
                        formatted[key] = epoch_to_datetime(int(value), timeoffset)
                    # Formatting Waypoints Table
                    elif 'cumulative_dist' in content.keys():
                        if key == 'radius':
                            '''formatting wpt radius'''
                            formatted[key] = (f"{round(float(value) / 1000, 1):.1f} Km" if float(value) > 1000
                                              else f"{round(float(value))} m &nbsp;")
                        elif key == 'cumulative_dist':
                            '''formatting wpt cumulative distance'''
                            formatted[key] = '' if float(value) == 0 else f"{round(float(value) / 1000, 2):.2f} Km"
                        elif key == 'type':
                            '''formatting wpt type'''
                            formatted[key] = ('' if str(value) == 'waypoint'
                                              else 'SS' if str(value) == 'speed'
                                              else 'ES' if str(value) == 'endspeed'
                                              else str(value))
                        elif key == 'shape':
                            '''formatting wpt shape'''
                            formatted[key] = '' if str(value) == 'circle' else '(line)'
                        elif key == 'shape':
                            '''formatting wpt versus'''  # Not needed anymore?
                            formatted[key] = '' if str(value) == 'entry' else '(exit)'
                        else:
                            '''name and description'''
                            formatted[key] = str(value)
                    # Formatting Numbers
                    elif key in percentage:
                        '''formatting percentage'''
                        formatted[key] = f"{c_round(float(value) * 100, 2):.2f}%"
                    elif str(key).endswith(validity):
                        '''formatting formula validity'''
                        formatted[key] = f"{c_round(float(value), 3):.3f}"
                    elif str(key).endswith(weight):
                        '''formatting formula weight'''
                        formatted[key] = f"{c_round(float(value), 3):.3f}"
                    elif str(key).endswith(scores):
                        '''formatting scores'''
                        formatted[key] = f"{c_round(float(value), 1):.1f}"
                    elif key == 'score':
                        formatted[key] = f"{c_round(float(value), 1):.{td}f}"
                    elif key == 'speed':
                        formatted[key] = f"{c_round(float(value), 1):.2f}"
                    # Formatting Distances
                    elif key in ['distance', 'distance_flown', 'stopped_distance']:
                        '''formatting distance without unit of measure'''
                        formatted[key] = f"{round(float(value) / 1000, 2):.2f}"
                    elif 'dist' in key:
                        '''formatting distances with unit of measure'''
                        formatted[key] = f"{round(float(value) / 1000, 1):.1f} Km"
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
        print(f'Team Scoring is not available')
        return None
    countries = get_country_list(countries=set(map(lambda x: x['nat'], data['results'])))
    size = formula['team_size'] if 'country_size' not in formula.keys() else formula['country_size']
    results = []
    for nat in countries:
        nation = dict(code=nat.code, name=nat.name)
        nat_pilots = sorted([p for p in data['results'] if p['nat'] == nation['code']
                             and p['nat_team']], key=lambda k: k['score'], reverse=True)
        nation['pilots'] = nat_pilots
        nation['score'] = sum([p['score'] for p in nat_pilots][:size])
        results.append(nation)
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
        print(f'Team Scoring is not available')
        return None
    '''get info: countries list, team size, task codes'''
    countries = get_country_list(countries=set(map(lambda x: x['nat'], data['results'])))
    size = formula['team_size'] if 'country_size' not in formula.keys() else formula['country_size']
    tasks = [t['task_code'] for t in data['tasks']]
    results = []
    for nat in countries:
        nation = dict(code=nat.code, name=nat.name)
        nat_pilots = [p for p in data['results'] if p['nat'] == nation['code'] and p['nat_team']]
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
        nation['pilots'] = nat_pilots
        nation['score'] = score
        results.append(nation)
    results = sorted(results, key=lambda k: k['score'], reverse=True)
    return jsonpickle.encode(results)
    # for idx, nat in enumerate(results, 1):
    #     print(f"{idx}. - {nat['name']}: {nat['score']}")
    #     for p in nat['pilots']:
    #         print(f" - {p['name']}: {[(t, p['results'][t]['score']) for t in tasks]} - {p['score']}")


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
    # for idx, team in enumerate(results, 1):
    #     print(f"{idx}. - {team['name']}: {team['score']}")
    #     for p in team['pilots']:
    #         print(f" - {p['name']}: {[(t, p['results'][t]['score']) for t in tasks]} - {p['score']}")


def get_task_team_json(filename):
    """
    Get task result json file as input
    returns json formatted string
    list of teams dict with attributes:
        name: team name
        score: team score
        pilots: list of team pilots dict, as in result json file.
    So in frontend every result after the max team size should be formatted as deleted.
    Only pilots with team different from None or '' """
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
        team_pilots = sorted([p for p in pilots if p['team'].strip().title() == team['name']],
                             key=lambda k: k['score'], reverse=True)
        team['pilots'] = team_pilots
        team['score'] = sum([p['score'] for p in team_pilots][:size])
        results.append(team)
    results = sorted(results, key=lambda k: k['score'], reverse=True)
    return jsonpickle.encode(results)
    # for idx, team in enumerate(results, 1):
    #     print(f"{idx}. - {team['name']}: {team['score']}")
    #     for p in team['pilots']:
    #         print(f" - {p['name']}: {p['score']}")


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
        print(f'Team Scoring is not available')
        return None
    countries = get_country_list(countries=set(map(lambda x: x['nat'], data['results'])))
    size = formula['team_size'] if 'country_size' not in formula.keys() else formula['country_size']
    for nat in countries:
        nation = dict(code=nat.code, name=nat.name)
        nat_pilots = sorted([p for p in data['results'] if p['nat'] == nation['code']
                             and p['nat_team']], key=lambda k: k['score'], reverse=True)
        nation['score'] = sum([p['score'] for p in nat_pilots][:size])
        for rank, p in enumerate(nat_pilots):
            p['group'] = f". {nat.name} - {nation['score']:.0f} points"
            p['nation_score'] = nation['score']
            if rank >= size:
                p['score'] = f"<del>{p['score']:.2f}</del>"
            else:
                p['score'] = f"{p['score']:.2f}"
        teams.append(nation)
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
        print(f'Team Scoring is not available')
        return None
    '''get info: countries list, team size, task codes'''
    countries = get_country_list(countries=set(map(lambda x: x['nat'], data['results'])))
    size = formula['team_size'] if 'country_size' not in formula.keys() else formula['country_size']
    tasks = [t['task_code'] for t in data['tasks']]
    teams = []
    pilots = []
    all_scores = []
    all_possible_tasks = []

    # setup the 20 task placeholders
    for t in range(1, 21):
        all_possible_tasks.append('T' + str(t))

    for nat in countries:
        nation = dict(code=nat.code, name=nat.name)
        nat_pilots = [p for p in data['results'] if p['nat'] == nation['code'] and p['nat_team']]
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
                    p['results'][t]['score'] = f"<del>{int(p['results'][t]['pre'])}</del>"
                    p['results'][t]['perf'] = 0
        for t in list(set(all_possible_tasks) - set(tasks)):
            for idx, p in enumerate(nat_pilots):
                p['results'][t] = {'score': ''}
        '''final nation sorting'''
        for p in nat_pilots:
            p['score'] = sum(p['results'][t]['score'] for t in tasks if not isinstance(p['results'][t]['score'], str))
            p['group'] = f". {nat.name} - {score:.0f} points"
            p['nation_score'] = score
        nat_pilots = sorted(nat_pilots, key=lambda k: k['score'], reverse=True)
        pilots.extend(nat_pilots)
        nation['score'] = score
        teams.append(nation)
    # get rank after sort
    for t in teams:
        all_scores.append(t['score'])
    for row in pilots:
        row['group'] = str(sum(map(lambda x: x > row['nation_score'], all_scores)) + 1) + row['group']

    return {'teams': teams, 'data': pilots, 'info': data['info'], 'formula': data['formula']}


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
    if not formula['country_scoring']:
        print(f'Team Scoring is not available')
        return None
    pilots_list = [p for p in data['results'] if not p['team'] in [None, '']]
    teams_list = set(map(lambda x: x['team'].strip().title(), pilots_list))
    size = formula['team_size']
    for el in teams_list:
        team = dict(name=el)
        team_pilots = sorted([p for p in pilots_list if p['team'].strip().title() == team['name']],
                             key=lambda k: k['score'], reverse=True)
        team['pilots'] = team_pilots
        team['score'] = sum([p['score'] for p in team_pilots][:size])
        for rank, p in enumerate(team_pilots):
            p['group'] = f". {team['name']} - {team['score']:.0f} points"
            p['team_score'] = team['score']
            if rank >= size:
                p['score'] = f"<del>{p['score']:.2f}</del>"
            else:
                p['score'] = f"{p['score']:.2f}"
        teams.append(team)
        pilots.extend(team_pilots)
    # get rank after sort
    for t in teams:
        all_scores.append(t['score'])
    for row in pilots:
        row['group'] = str(sum(map(lambda x: x > row['team_score'], all_scores)) + 1) + row['group']
    return {'teams': teams, 'data': pilots, 'info': data['info'], 'formula': data['formula']}


def get_comp_team_scoring(filename):
    """takes a competition result filename and outputs a nested dict ready to be jsonified for the front end
        each pilot has attributes for their nation and nation score to allow grouping in datatables js.
        Scores are given html strikethough <del> if they do not count towards nation total
    """
    data = open_json_file(filename)
    formula = data['formula']
    if not formula['country_scoring']:
        print(f'Team Scoring is not available')
        return None
    '''get info: teams list, team size, task codes'''
    pilots_list = [p for p in data['results'] if not p['team'] in [None, '']]
    teams_list = set(map(lambda x: x['team'].strip().title(), pilots_list))
    size = formula['team_size']
    tasks = [t['task_code'] for t in data['tasks']]
    teams = []
    pilots = []
    all_scores = []
    all_possible_tasks = []

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
            p['group'] = f". {team['name']} - {score:.0f} points"
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

    return {'teams': teams, 'data': pilots, 'info': data['info'], 'formula': data['formula']}
