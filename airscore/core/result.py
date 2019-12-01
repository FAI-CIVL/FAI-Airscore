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

from myconn import Database


class Task_result:
    """
        Task result fields lists
    """

    info_list =[    'comp_name',
                    'comp_site',
                    'comp_class',
                    'date',
                    'task_name',
                    'time_offset',
                    'comment',
                    'window_open_time',
                    'task_deadline',
                    'window_close_time',
                    'check_launch',
                    'start_time',
                    'start_close_time',
                    'SS_interval',
                    'last_start_time',
                    'task_type',
                    'distance',
                    'opt_dist',
                    'SS_distance',
                    'stopped_time',
                    'goal_altitude']

    route_list   = ['name',
                    'description',
                    'how',
                    'radius',
                    'shape',
                    'type',
                    'lat',
                    'lon',
                    'altitude']

    formula_list = ['formula_name',
                    'nominal_dist',
                    'nominal_time',
                    'nominal_goal',
                    'nominal_launch',
                    'min_dist',
                    'departure',
                    'arrival',
                    'no_goal_penalty',
                    'score_back_time',
                    'stopped_time_calc',
                    'glide_bonus',
                    'arr_alt_bonus',
                    'tolerance']

    stats_list = [  'pilots_launched',
                    'pilots_present',
                    'pilots_ess',
                    'pilots_landed',
                    'pilots_goal',
                    'fastest',
                    'fastest_in_goal',
                    'min_dept_time',
                    'min_ess_time',
                    'max_distance',
                    'tot_dist_flown',
                    'tot_dist_over_min',
                    'day_quality',
                    'dist_validity',
                    'time_validity',
                    'launch_validity',
                    'stop_validity',
                    'avail_dist_points',
                    'avail_dep_points',
                    'avail_time_points',
                    'avail_arr_points',
                    'max_score',
                    'min_lead_coeff']

    results_list = ['track_id',
                    'par_id',
                    'ID',
                    'name',
                    'sponsor',
                    'nat',
                    'sex',
                    'glider',
                    'class',
                    'distance',
                    'speed',
                    'real_start_time',
                    'goal_time',
                    'result',
                    'SS_time',
                    'ES_time',
                    'turnpoints_made',
                    'dist_points',
                    'time_points',
                    'dep_points',
                    'arr_points',
                    'score',
                    'penalty',
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
                    'track_file',
                    'pil_id']


class Comp_result(object):
    """
        Comp result fields lists
    """

    info_list =    ['id',
                    'comp_name',
                    'comp_class',
                    'type',
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

    tasks_list =   ['task_name',
                    'date',
                    'comment',
                    'opt_dist',
                    'pilots_goal',
                    'day_quality',
                    'max_score']


def create_json_file(comp_id, code, elements, task_id=None, status=None):
    """
    creates the JSON file of results
    """
    import  os
    import  json
    from    time        import time
    from    datetime    import datetime
    import  Defines  as d
    from    db_tables   import tblResultFile as R
    from    calcUtils   import CJsonEncoder

    timestamp   = int(time())       # timestamp of generation
    dt          = datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
    filename    = '_'.join([code,dt]) + '.json'

    '''adding data section to the elements, with:
        timestamp, status'''
    result = {'file_stats': {'timestamp': timestamp, 'status': status}}
    result.update(elements)

    '''creating json formatting'''
    content = json.dumps(result, cls=CJsonEncoder)

    '''creating file'''
    with open(d.RESULTDIR + filename, 'w') as f:
        f.write(content)
    os.chown(d.RESULTDIR + filename, 1000, 1000)

    # with open(filename, 'w') as f:
    #     json.dump(value, f)
    # os.chown(filename, 1000, 1000)
    #
    '''create database entry'''
    with Database() as db:
        result = R(comPk=comp_id, tasPk=task_id, refTimestamp=timestamp, refJSON=filename, refStatus=status)
        db.session.add(result)
        db.session.commit()
        ref_id = result.refPk
    return ref_id
    # return value
