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
from sqlalchemy import update

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
    return ref_id


def unpublish_result(taskid, session=None):
    """unpublish (set active to 0) all result files for a task"""
    with Database(session) as db:
        try:
            db.session.query(TblResultFile).filter(TblResultFile.task_id == taskid).update({'active': 0})
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
                db.session.query(TblResultFile).filter(TblResultFile.filename == filename_or_refid).update({'active': 1})
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


