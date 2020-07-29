from db.tables import TblCompetition, TblTask, TblCompAuth, TblRegion, TblRegionWaypoint, TblTaskWaypoint
from route import Turnpoint
from sqlalchemy.orm import aliased
from flask import current_app, jsonify
from db.conn import db_session
import datetime
import ruamel.yaml
from sqlalchemy import func
from pathlib import Path
import jsonpickle
from Defines import MAPOBJDIR, IGCPARSINGCONFIG, track_formats
from map import make_map
from calcUtils import sec_to_time, c_round
from os import scandir, path, environ
from werkzeug.utils import secure_filename
import requests
from flask_sse import sse
from functools import partial
import json


def get_comps() -> list:
    c = aliased(TblCompetition)
    with db_session() as db:
        comps = (db.query(c.comp_id, c.comp_name, c.comp_site,
                          c.comp_class, c.sanction, c.comp_type, c.date_from,
                          c.date_to, func.count(TblTask.task_id).label('tasks'), c.external)
                 .outerjoin(TblTask, c.comp_id == TblTask.comp_id)
                 .group_by(c.comp_id))

    return [row._asdict() for row in comps]


def find_orphan_pilots(pilots_list: list, orphans: list) -> (list, list):
    """ Tries to guess participants that do not have a pil_id, and associate them to other participants or
        to a pilot in database"""
    from db.tables import PilotView as P
    from calcUtils import get_int
    pilots_found = []
    still_orphans = []
    ''' find a match among pilots already in list'''
    print(f"trying to find pilots from orphans...")
    for p in orphans:
        name, civl_id, comp_id = p['name'], p['civl_id'], p['comp_id']
        found = next((el for el in pilots_list
                      if (el['name'] == name or (civl_id and civl_id == el['civl_id']))
                      and comp_id not in el[comp_id]), None)
        if found:
            '''adding to existing pilot'''
            found['par_ids'].append(p['par_id'])
            found['comp_ids'].append(comp_id)
        else:
            still_orphans.append(p)
    ''' find a match among pilots in database if still we have orphans'''
    orphans = []
    if still_orphans:
        with db_session() as db:
            pilots = db.query(P).all()
            for p in still_orphans:
                name, civl_id, comp_id = p['name'].title(), p['civl_id'], p['comp_id']
                row = next((el for el in pilots
                            if ((el.first_name and el.last_name
                                 and el.first_name.title() in name and el.last_name.title() in name)
                                or (civl_id and el.civl_id and civl_id == get_int(el.civl_id)))), None)
                if row:
                    '''check if we already found the same pilot in orphans'''
                    found = next((el for el in pilots_found
                                  if el['pil_id'] == row.pil_id), None)
                    if found:
                        found['par_ids'].append(p['par_id'])
                        found['comp_ids'].append(comp_id)
                    else:
                        name = f"{row.first_name.title()} {row.last_name.title()}"
                        pilot = dict(comp_ids=[p['comp_id']], par_ids=[p['par_id']], pil_id=int(row.pil_id),
                                     civl_id=get_int(row.civl_id), fai_id=row.fai_id, name=name, sex=p['sex'],
                                     nat=p['nat'], glider=p['glider'], glider_cert=p['glider_cert'], results=[])
                        pilots_found.append(pilot)
                else:
                    orphans.append(p)
    pilots_list.extend(pilots_found)

    return pilots_list, orphans


def get_ladders() -> list:
    from db.tables import TblLadder as L, TblLadderSeason as LS, TblCountryCode as C
    with db_session() as db:
        ladders = db.query(L.ladder_id, L.ladder_name, L.ladder_class, L.date_from, L.date_to,
                           C.natIso3.label('nat'),
                           LS.season) \
            .join(LS, L.ladder_id == LS.ladder_id) \
            .join(C, L.nation_code == C.natId) \
            .filter(LS.active == 1) \
            .order_by(LS.season.desc())

    return [row._asdict() for row in ladders]


def get_ladder_results(ladder_id: int, season: int,
                       nat: str = None, starts: datetime.date = None, ends: datetime.date = None) -> json:
    """creates result json using comp results from all events in ladder"""
    from db.tables import TblParticipant as P, TblLadder as L, TblLadderComp as LC, TblLadderSeason as LS, \
        TblCompetition as C, TblTask as T, TblResultFile as R
    from calcUtils import get_season_dates
    from compUtils import get_nat, create_classifications
    from result import open_json_file

    if not (nat and starts and ends):
        lad = L.get_by_id(ladder_id)
        nat_code, date_from, date_to = lad.nation_code, lad.date_from, lad.date_to
        nat = get_nat(nat_code)
        '''get season start and end day'''
        starts, ends = get_season_dates(ladder_id=ladder_id, season=season, date_from=date_from, date_to=date_to)
    with db_session() as db:
        '''get ladder info'''
        # probably we could keep this from ladder list page?
        row = db.query(L.ladder_id, L.ladder_name, L.ladder_class,
                       LS.season, LS.cat_id, LS.overall_validity, LS.validity_param) \
            .join(LS) \
            .filter(L.ladder_id == ladder_id, LS.season == season).one()
        rankings = create_classifications(row.cat_id)
        info = {'ladder_name': row.ladder_name,
                'season': row.season,
                'ladder_class': row.ladder_class,
                'id': row.ladder_id}
        formula = {'overall_validity': row.overall_validity,
                   'validity_param': row.validity_param}

        '''get comps and files'''
        results = db.query(C.comp_id, R.filename) \
                    .join(LC) \
                    .join(R, (R.comp_id == C.comp_id) & (R.task_id.is_(None)) & (R.active == 1)) \
                    .filter(C.date_to > starts, C.date_to < ends, LC.c.ladder_id == ladder_id)
        comps_ids = [row.comp_id for row in results]
        files = [row.filename for row in results]
        print(comps_ids, files)

        '''create Participants list'''
        results = db.query(P) \
            .filter(P.comp_id.in_(comps_ids), P.nat == nat) \
            .order_by(P.pil_id, P.comp_id).all()
        pilots_list = []
        orphans = []
        for row in results:
            if row.pil_id:
                p = next((el for el in pilots_list if el['pil_id'] == row.pil_id), None)
                if p:
                    '''add par_id'''
                    p['par_ids'].append(row.par_id)
                    p['comp_ids'].append(row.comp_id)
                else:
                    '''insert a new pilot'''
                    p = dict(comp_ids=[row.comp_id], par_ids=[row.par_id], pil_id=row.pil_id, civl_id=row.civl_id,
                             fai_id=row.fai_id, name=row.name, sex=row.sex, nat=row.nat,
                             glider=row.glider, glider_cert=row.glider_cert, results=[])
                    pilots_list.append(p)
            else:
                p = dict(comp_id=row.comp_id, pil_id=row.pil_id, par_id=row.par_id, civl_id=row.civl_id,
                         fai_id=row.fai_id, name=row.name, sex=row.sex, nat=row.nat,
                         glider=row.glider, glider_cert=row.glider_cert)
                orphans.append(p)
    '''try to guess orphans'''
    if orphans:
        pilots_list, orphans = find_orphan_pilots(pilots_list, orphans)
    print(pilots_list)

    '''get results'''
    stats = {'tot_pilots': len(pilots_list)}
    comps = []
    tasks = []
    for file in files:
        f = open_json_file(file)
        '''get comp info'''
        i = f['info']
        comp_code = i['comp_code']
        results = f['results']
        comps.append(dict(id=i['id'], comp_code=i['comp_code'], comp_name=i['comp_name']))
        tasks.extend([dict(id=t['id'], ftv_validity=t['ftv_validity'], task_code=f"{i['comp_code']}_{t['task_code']}")
                      for t in f['tasks']])
        for r in results:
            p = next((el for el in pilots_list if r['par_id'] in el['par_ids']), None)
            if p:
                scores = r['results']
                for i, s in scores.items():
                    idx, code = next((t['id'], t['task_code']) for t in tasks if f"{comp_code}_{i}" == t['task_code'])
                    p['results'].append({'task_id': idx, 'task_code': code, **s})

    '''get params'''
    val = formula['overall_validity']
    param = formula['validity_param']
    stats['valid_tasks'] = len(tasks)
    stats['total_validity'] = c_round(sum([t['ftv_validity'] for t in tasks]), 4)
    stats['avail_validity'] = (0 if len(tasks) == 0
                               else c_round(stats['total_validity'] * param, 4) if val == 'ftv'
                               else stats['total_validity'])

    '''calculate scores'''
    for pil in pilots_list:
        dropped = 0 if not (val == 'round' and param) else int(len(pil['results']) / param)
        pil['score'] = 0

        '''reset scores in list'''
        for res in pil['results']:
            res['score'] = res['pre']

        ''' if we score all tasks, or tasks are not enough to have discards,
            or event has just one valid task regardless method,
            we can simply sum all score values
        '''
        if not ((val == 'all')
                or (val == 'round' and dropped == 0)
                or (len(tasks) < 2)
                or len(pil['results']) < 2):
            '''create a ordered list of results, score desc (perf desc if ftv)'''
            sorted_results = sorted(pil['results'],
                                    key=lambda x: (x['perf'], x['pre'] if val == 'ftv' else x['pre']), reverse=True)
            if val == 'round' and dropped:
                for i in range(1, dropped + 1):
                    sorted_results[-i]['score'] = 0  # getting id of worst result task
            elif val == 'ftv':
                '''ftv calculation'''
                pval = stats['avail_validity']
                for res in sorted_results:
                    if not (pval > 0):
                        res['score'] = 0
                    else:
                        '''get ftv_validity of corresponding task'''
                        tval = next(t['ftv_validity'] for t in tasks if t['task_code'] == res['task_code'])
                        if pval > tval:
                            '''we can use the whole score'''
                            pval -= tval
                        else:
                            '''we need to calculate proportion'''
                            res['score'] = c_round(res['score'] * (pval / tval))
                            pval = 0

            '''calculates final pilot score'''
            pil['results'] = sorted_results
            pil['score'] = sum(r['score'] for r in sorted_results)

    '''order results'''
    pilots_list = sorted(pilots_list, key=lambda x: x['score'], reverse=True)
    stats['winner_score'] = 0 if not pilots_list else pilots_list[0]['score']
    '''create json'''
    output = {'info': info,
              'comps': comps,
              'formula': formula,
              'stats': stats,
              'results': pilots_list,
              'rankings': rankings}
    return output


def get_admin_comps(current_userid):
    """get a list of all competitions in the DB and flag ones where owner is current user"""
    c = aliased(TblCompetition)
    ca = aliased(TblCompAuth)
    with db_session() as db:
        comps = (db.query(c.comp_id, c.comp_name, c.comp_site,
                          c.date_from,
                          c.date_to, func.count(TblTask.task_id), ca.user_id)
                 .outerjoin(TblTask, c.comp_id == TblTask.comp_id).outerjoin(ca)
                 .filter(ca.user_auth == 'owner')
                 .group_by(c.comp_id))
    all_comps = []
    for c in comps:
        comp = list(c)
        comp[1] = f'<a href="/users/comp_settings_admin/{comp[0]}">{comp[1]}</a>'
        comp[3] = comp[3].strftime("%Y-%m-%d")
        comp[4] = comp[4].strftime("%Y-%m-%d")
        if int(comp[6]) == current_userid:
            comp[6] = 'delete'
        else:
            comp[6] = ''
        all_comps.append(comp)
    return jsonify({'data': all_comps})


def get_task_list(comp):
    tasks = comp.get_tasks_details()
    max_task_num = 0
    last_region = 0
    for task in tasks:
        tasknum = task['task_num']
        if int(tasknum) > max_task_num:
            max_task_num = int(tasknum)
            last_region = task['reg_id']
        task['num'] = f"Task {tasknum}"
        # check if we have all we need to be able to accept tracks and score:
        task['ready_to_score'] = (task['opt_dist'] and task['window_open_time'] and task['window_close_time']
                                  and task['start_time'] and task['start_close_time']
                                  and task['task_deadline']) is not None

        task['opt_dist'] = 0 if not task['opt_dist'] else c_round(task['opt_dist'] / 1000, 2)
        task['opt_dist'] = f"{task['opt_dist']} km"
        if task['comment'] is None:
            task['comment'] = ''
        if not task['track_source']:
            task['track_source'] = ''
        task['date'] = task['date'].strftime('%d/%m/%y')
    return {'next_task': max_task_num + 1, 'last_region': last_region, 'tasks': tasks}


def get_task_turnpoints(task):
    turnpoints = task.read_turnpoints()
    max_n = 0
    total_dist = ''
    for tp in turnpoints:
        tp['original_type'] = tp['type']
        tp['partial_distance'] = '' if not tp['partial_distance'] else c_round(tp['partial_distance'] / 1000, 2)
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
    if task.opt_dist is None or total_dist == '':
        total_dist = 'Distance not yet calculated'
    else:
        total_dist = str(total_dist) + "km"
    # max_n = int(math.ceil(max_n / 10.0)) * 10
    max_n += 1

    task_file = Path(MAPOBJDIR, 'tasks', str(task.task_id) + '.task')
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


def get_comp_regions(compid: int):
    """Gets a list of dicts of: if defines.yaml waypoint library function is on - all regions
    otherwise only the regions with their comp_id field set the the compid parameter"""
    import Defines
    import region
    if Defines.WAYPOINT_AIRSPACE_FILE_LIBRARY:
        return region.get_all_regions()
    else:
        return region.get_comp_regions_and_wpts(compid)


def get_region_choices(compid: int):
    """gets a list of regions to be used in frontend select field (choices) and details of each region (details)"""
    regions = get_comp_regions(compid)
    choices = []
    details = {}
    for region in regions['regions']:
        choices.append((region['reg_id'], region['name']))
        details[region['reg_id']] = region
    return choices, details


def get_waypoint_choices(reg_id: int):
    import region
    wpts = region.get_region_wpts(reg_id)
    choices = []
    details = []

    for wpt in wpts:
        choices.append((wpt['rwp_id'], wpt['name'] + ' - ' + wpt['description']))
        wpt['Class'] = wpt['name'][0]
        details.append(wpt)

    return choices, details


def get_pilot_list_for_track_management(taskid: int):
    from db.tables import TblTaskResult as R, TblParticipant as P, TblTask as T
    with db_session() as db:
        results = db.query(R.goal_time, R.track_file, R.track_id, R.result_type, R.distance_flown,
                           R.ESS_time, R.SSS_time, R.par_id).filter(
            R.task_id == taskid).subquery()
        pilots = db.query(T.task_id, P.name, P.ID, P.par_id, results.c.track_id, results.c.SSS_time,
                          results.c.ESS_time,
                          results.c.distance_flown, results.c.track_file, results.c.result_type) \
            .outerjoin(P, T.comp_id == P.comp_id).filter(T.task_id == taskid) \
            .outerjoin(results, results.c.par_id == P.par_id).all()

        if pilots:
            pilots = [row._asdict() for row in pilots]

    all_data = []
    for pilot in pilots:
        data = {'ID': pilot['ID'], 'name': pilot['name'], 'par_id': pilot['par_id'], 'track_id': pilot['track_id']}
        if pilot['track_file']:
            parid = data['par_id']
            if pilot['ESS_time']:
                time = sec_to_time(pilot['ESS_time'] - pilot['SSS_time'])
                if pilot['result_type'] == 'goal':
                    result = f'Goal {time}'
                else:
                    result = f"ESS {round(pilot['distance_flown'] / 1000, 2)} Km (<del>{time}</del>)"
            else:
                result = f"LO {round(pilot['distance_flown'] / 1000, 2)} Km"
            data['Result'] = f'<a href="/map/{parid}-{taskid}">{result}</a>'
        elif pilot['result_type'] == "mindist":
            data['Result'] = "Min Dist"
        else:
            data['Result'] = "Not Yet Processed" if not pilot['track_id'] else pilot['result_type'].upper()
        all_data.append(data)
    return all_data


def get_waypoint(wpt_id: int = None, rwp_id: int = None):
    """reads waypoint from tblTaskWaypoint or tblRegionWaypoint depending on input and returns Turnpoint object"""
    if not (wpt_id or rwp_id):
        return None
    with db_session() as db:
        if wpt_id:
            result = db.query(TblTaskWaypoint).get(wpt_id)
        else:
            result = db.query(TblRegionWaypoint).get(rwp_id)
        tp = Turnpoint()
        result.populate(tp)
    return tp


def save_turnpoint(task_id: int, turnpoint: Turnpoint):
    """save turnpoint in a task- for frontend"""
    if not (type(task_id) is int and task_id > 0):
        print("task not present in database ", task_id)
        return None
    with db_session() as db:
        if not turnpoint.wpt_id:
            '''add new taskWaypoint'''
            # tp = TblTaskWaypoint(**turnpoint.as_dict())
            tp = TblTaskWaypoint.from_obj(turnpoint)
            db.add(tp)
            db.flush()
        else:
            '''update taskWaypoint'''
            tp = db.query(TblTaskWaypoint).get(turnpoint.wpt_id)
            if tp:
                for k, v in turnpoint.as_dict().items():
                    if hasattr(tp, k):
                        setattr(tp, k, v)
            db.flush()
        return 1


def allowed_tracklog(filename, extension=track_formats):
    ext = Path(filename).suffix
    if not ext:
        return False
    # Check if the extension is allowed (make everything uppercase)
    if ext.strip('.').lower() in [e.lower() for e in extension]:
        return True
    else:
        return False


def allowed_tracklog_filesize(filesize, size=5):
    """check if tracklog exceeds maximum file size for tracklog (5mb)"""
    if int(filesize) <= size * 1024 * 1024:
        return True
    else:
        return False


def process_igc(task_id: int, par_id: int, tracklog):
    from pilot.track import create_igc_filename, igc_parsing_config_from_yaml
    from calcUtils import epoch_to_date
    from airspace import AirspaceCheck
    from igc_lib import Flight
    from task import Task
    from pilot.flightresult import FlightResult, save_track

    pilot = FlightResult.read(par_id, task_id)
    if pilot.name:
        task = Task.read(task_id)
        fullname = create_igc_filename(task.file_path, task.date, pilot.name)
        tracklog.save(fullname)
        pilot.track_file = Path(fullname).name
    else:
        return None, None

    """import track"""
    # track = Track(track_file=fullname, par_id=pilot.par_id)
    FlightParsingConfig = igc_parsing_config_from_yaml(task.igc_config_file)
    flight = Flight.create_from_file(fullname, config_class=FlightParsingConfig)
    """check result"""
    if not flight:
        error = f"for {pilot.name} - Track is not a valid track file"
        return None, error
    elif not epoch_to_date(flight.date_timestamp) == task.date:
        error = f"for {pilot.name} - Track has a different date from task date"
        return None, error
    else:
        print(f"pilot {pilot.par_id} associated with track {pilot.track_file} \n")

        """checking track against task"""
        if task.airspace_check:
            airspace = AirspaceCheck.from_task(task)
        else:
            airspace = None
        pilot.check_flight(flight, task, airspace_obj=airspace)
        print(f"track verified with task {task.task_id}\n")
        '''create map file'''
        pilot.save_tracklog_map_file(task, flight)
        """adding track to db"""
        # pilot.to_db()
        save_track(pilot, task.id)
        time = ''
        data = {'par_id': pilot.par_id, 'track_id': pilot.track_id}
        if pilot.goal_time:
            time = sec_to_time(pilot.ss_time)
        if pilot.result_type == 'goal':
            data['Result'] = f'Goal {time}'
        elif pilot.result_type == 'lo':
            data['Result'] = f"LO {round(pilot.distance / 1000, 2)}"
        if pilot.track_id:  # if there is a track, make the result a link to the map
            # trackid = data['track_id']
            parid = data['par_id']
            result = data['Result']
            data['Result'] = f'<a href="/map/{parid}-{task.task_id}">{result}</a>'
    return data, None


def save_igc_background(task_id: int, par_id: int, tracklog, user, check_g_record=False):
    from task import Task
    from pilot.track import create_igc_filename, validate_G_record
    from pilot.flightresult import FlightResult

    pilot = FlightResult.read(par_id, task_id)
    print = partial(print_to_sse, id=par_id, channel=user)
    if pilot.name:
        task = Task.read(task_id)
        fullname = create_igc_filename(task.file_path, task.date, pilot.name)
        tracklog.save(fullname)
        print('|open_modal')
        print('***************START*******************')
        if check_g_record:
            print('Checking G-Record...')
            validation = validate_G_record(fullname)
            if validation == 'FAILED':
                print('G-Record not valid')
                data = {'par_id': pilot.par_id, 'track_id': pilot.track_id, 'Result': ''}
                print(json.dumps(data) + '|g_record_fail')
                return None, None
            if validation == 'ERROR':
                print('Error trying to validate G-Record')
                return None, None
            if validation == 'PASSED':
                print('G-Record is valid')
        print(f'IGC file saved: {fullname.name}')
    else:
        return None, None
    return fullname


def process_igc_background(task_id: int, par_id: int, file: Path, user: str):
    from pilot.track import igc_parsing_config_from_yaml
    from calcUtils import epoch_to_date
    from pilot.flightresult import FlightResult, save_track
    from airspace import AirspaceCheck
    from igc_lib import Flight
    from task import Task
    import json
    pilot = FlightResult.read(par_id, task_id)
    task = Task.read(task_id)
    print = partial(print_to_sse, id=par_id, channel=user)

    """import track"""
    # pilot.track = Track(track_file=filename, par_id=pilot.par_id)
    FlightParsingConfig = igc_parsing_config_from_yaml(task.igc_config_file)
    flight = Flight.create_from_file(file, config_class=FlightParsingConfig)
    data = {'par_id': pilot.par_id, 'track_id': pilot.track_id, 'Result': 'Not Yet Processed'}
    """check result"""
    if not flight:
        print(f"for {pilot.name} - Track is not a valid track file")
        print(json.dumps(data) + '|result')
        return None
    if not flight.valid:
        print(f'IGC does not meet quality standard set by igc parsing config. Notes:{pilot.flight.notes}')
        print(json.dumps(data) + '|result')
        return None
    elif not epoch_to_date(flight.date_timestamp) == task.date:
        print(f"for {pilot.name} - Track has a different date from task date")
        print(json.dumps(data) + '|result')
        return None
    else:
        print(f"pilot {pilot.par_id} associated with track {file.name} \n")
        pilot.track_file = file.name
        """checking track against task"""
        if task.airspace_check:
            airspace = AirspaceCheck.from_task(task)
        else:
            airspace = None
        pilot.check_flight(flight, task, airspace_obj=airspace, print=print)
        print(f"track verified with task {task.task_id}\n")
        '''create map file'''
        pilot.save_tracklog_map_file(task, flight)
        """adding track to db"""
        # pilot.to_db()
        save_track(pilot, task.id)
        data['track_id'] = pilot.track_id
        time = ''

        if pilot.goal_time:
            time = sec_to_time(pilot.ESS_time - pilot.SSS_time)
        if pilot.result_type == 'goal':
            data['Result'] = f'Goal {time}'
        elif pilot.result_type == 'lo':
            data['Result'] = f"LO {c_round(pilot.distance / 1000, 2)}"
        if pilot.track_id:  # if there is a track, make the result a link to the map
            # trackid = data['track_id']
            parid = data['par_id']
            result = data['Result']
            data['Result'] = f'<a href="/map/{parid}-{task.task_id}">{result}</a>'
        print(data['Result'])
        print(json.dumps(data) + '|result')
        print('***************END****************')
    return None


def unzip_igc(zipfile):
    """split function for background in production"""
    from trackUtils import extract_tracks
    from tempfile import mkdtemp
    from os import chmod
    from Defines import TEMPFILES

    """create a temporary directory"""
    # with TemporaryDirectory() as tracksdir:
    tracksdir = mkdtemp(dir=TEMPFILES)
    # make readable and writable by other users as background runs in another container
    chmod(tracksdir, 0o775)

    error = extract_tracks(zipfile, tracksdir)
    if error:
        print(f"An error occurred while dealing with file {zipfile}")
        return None
    return tracksdir


def process_archive_background(taskid: int, tracksdir, user, check_g_record=False, track_source=None):
    """function split for background use.
    tracksdir is a temp dir that will be deleted at the end of the function"""
    from task import Task
    from trackUtils import get_tracks, assign_and_import_tracks
    from shutil import rmtree
    print = partial(print_to_sse, id=None, channel=user)
    print('|open_modal')
    task = Task.read(taskid)
    if task.opt_dist == 0:
        print('task not optimised.. optimising')
        task.calculate_optimised_task_length()
    tracks = get_tracks(tracksdir)
    """find valid tracks"""
    if tracks is None:
        print(f"There are no valid tracks in zipfile")
        return None
    """associate tracks to pilots and import"""
    assign_and_import_tracks(tracks, task, track_source, user=user, check_g_record=check_g_record, print=print)
    rmtree(tracksdir)
    print('|reload')
    return 'Success'


def process_archive(task, zipfile, check_g_record=False, track_source=None):
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
        if not tracks:
            print(f"There are no valid tracks in zipfile {zipfile}, or all pilots are already been scored \n")
            return None

        """associate tracks to pilots and import"""
        assign_and_import_tracks(tracks, task, track_source, check_g_record=check_g_record)
        return 'Success'


def process_zip_file(zip_file: Path, taskid: int, username: str, grecord: bool, track_source: str = None):
    from task import Task
    if production():
        tracksdir = unzip_igc(zip_file)
        job = current_app.task_queue.enqueue(process_archive_background,
                                             taskid=taskid,
                                             tracksdir=tracksdir,
                                             user=username,
                                             check_g_record=grecord,
                                             track_source=track_source,
                                             job_timeout=2000)
        resp = jsonify(success=True)
        return resp
    else:
        task = Task.read(taskid)
        data = process_archive(task, zip_file, check_g_record=grecord, track_source=track_source)
        resp = jsonify(success=True) if data == 'Success' else None
        return resp


def get_task_result_file_list(taskid: int):
    from db.tables import TblResultFile as R
    files = []
    with db_session() as db:
        rows = db.query(R.created, R.filename, R.status, R.active, R.ref_id).filter_by(task_id=taskid).all()
        if rows:
            files = [row._asdict() for row in rows]
        return files


def number_of_tracks_processed(taskid: int):
    from db.tables import TblTaskResult as R, TblParticipant as P, TblTask as T
    from sqlalchemy import func
    with db_session() as db:
        results = db.query(func.count()).filter(R.task_id == taskid).scalar()
        pilots = db.query(func.count(P.par_id)).outerjoin(T, P.comp_id == T.comp_id).filter(
            T.task_id == taskid).scalar()
    return results, pilots


def get_score_header(files, offset):
    import time
    active_published = None
    active_status = None
    active = None
    header = "This task has not been scored"
    offset = (int(offset) / 60 * -1) * 3600
    for file in files:
        published = time.ctime(file['created'] + offset)
        if int(file['active']) == 1:
            active_published = published
            active_status = file['status']
            active = file['filename']
    if active_published:
        header = f"Published result ran: {active_published} Status: {active_status}"
    elif len(files) > 0:
        header = "No published results"
    return header, active


def get_comp_admins(compid_or_taskid: int, task_id=False):
    """returns owner and list of admins takes compid by default or taskid if taskid is True"""
    from db.tables import TblCompAuth as CA
    from airscore.user.models import User
    with db_session() as db:
        if task_id:
            taskid = compid_or_taskid
            all_admins = db.query(User.id, User.username, User.first_name, User.last_name, CA.user_auth) \
                .join(CA, User.id == CA.user_id).join(TblTask, CA.comp_id == TblTask.comp_id).filter(
                TblTask.task_id == taskid,
                CA.user_auth.in_(('owner', 'admin'))).all()
        else:
            compid = compid_or_taskid
            all_admins = db.query(User.id, User.username, User.first_name, User.last_name, CA.user_auth) \
                .join(CA, User.id == CA.user_id).filter(CA.comp_id == compid,
                                                        CA.user_auth.in_(('owner', 'admin'))).all()
        if all_admins:
            all_admins = [row._asdict() for row in all_admins]
        admins = []
        all_ids = []
        owner = None
        for admin in all_admins:
            all_ids.append(admin['id'])
            if admin['user_auth'] == 'owner':
                del admin['user_auth']
                owner = admin
            else:
                del admin['user_auth']
                admins.append(admin)
    return owner, admins, all_ids


def set_comp_admin(compid: int, userid, owner=False):
    from db.tables import TblCompAuth as CA
    auth = 'owner' if owner else 'admin'
    with db_session() as db:
        admin = CA(user_id=userid, comp_id=compid, user_auth=auth)
        db.add(admin)
        db.flush()
    return True


def get_all_admins():
    """returns a list of all admins in the system"""
    from airscore.user.models import User
    with db_session() as db:
        all_admins = db.query(User.id, User.username, User.first_name, User.last_name) \
            .filter(User.is_admin == 1).all()
        if all_admins:
            all_admins = [row._asdict() for row in all_admins]
        return all_admins


def update_airspace_file(old_filename, new_filename):
    """change the name of the openair file in all regions it is used."""
    R = aliased(TblRegion)
    with db_session() as db:
        db.query(R).filter(R.openair_file == old_filename).update({R.openair_file: new_filename},
                                                                  synchronize_session=False)
        db.commit()
    return True


# def save_waypoint_file(file):
#     from Defines import WAYPOINTDIR, AIRSPACEDIR
#     full_file_name = path.join(WAYPOINTDIR, filename)


def get_non_registered_pilots(compid: int):
    from db.tables import TblParticipant, PilotView

    p = aliased(TblParticipant)
    pv = aliased(PilotView)

    with db_session() as db:
        '''get registered pilots'''
        reg = db.query(p.pil_id).filter(p.comp_id == compid).subquery()
        non_reg = db.query(pv.pil_id, pv.civl_id, pv.first_name, pv.last_name). \
            filter(reg.c.pil_id == None). \
            outerjoin(reg, reg.c.pil_id == pv.pil_id). \
            order_by(pv.first_name, pv.last_name).all()

        non_registered = [row._asdict() for row in non_reg]
    return non_registered


def get_igc_parsing_config_file_list():
    yaml = ruamel.yaml.YAML()
    configs = []
    choices = []
    for file in scandir(IGCPARSINGCONFIG):
        if file.name.endswith(".yaml"):
            with open(file.path) as fp:
                config = yaml.load(fp)
            configs.append({'file': file.name, 'name': file.name[:-5], 'description': config['description'],
                            'editable': config['editable']})
            choices.append((file.name[:-5], file.name[:-5]))
    return choices, configs


def get_comps_with_igc_parsing(igc_config):
    from db.tables import TblCompetition

    c = aliased(TblCompetition)
    with db_session() as db:
        return db.query(c.comp_id).filter(c.igc_config_file == igc_config).all()


def get_comp_info(compid: int, task_ids=None):
    if task_ids is None:
        task_ids = []
    c = aliased(TblCompetition)
    t = aliased(TblTask)

    with db_session() as db:
        non_scored_tasks = (db.query(t.task_id.label('id'),
                                     t.task_name,
                                     t.date,
                                     t.task_type,
                                     t.opt_dist,
                                     t.comment).filter(t.comp_id == compid, t.task_id.notin_(task_ids))
                            .order_by(t.date.desc()).all())

        competition_info = (db.query(
            c.comp_id,
            c.comp_name,
            c.comp_site,
            c.date_from,
            c.date_to,
            c.self_register,
            c.website).filter(c.comp_id == compid).one())
    comp = competition_info._asdict()

    return comp, non_scored_tasks


def get_participants(compid: int, source='all'):
    """get all registered pilots for a comp.
    Compid: comp_id
    source: all: all participants
            internal: only participants from pilot table (with pil_id)
            external: only participants not in pilot table (without pil_id)"""
    from compUtils import get_participants
    from formula import Formula
    pilots = get_participants(compid)
    pilot_list = []
    external = 0
    for pilot in pilots:
        if pilot.nat_team == 1:
            pilot.nat_team = '✓'
        else:
            pilot.nat_team = None
        if pilot.paid == 1:
            pilot.paid = 'Y'
        else:
            pilot.paid = 'N'
        if source == 'all' or source == 'internal':
            if pilot.pil_id:
                pilot_list.append(pilot.as_dict())
        if source == 'all' or source == 'external':
            if not pilot.pil_id:
                external += 1
                pilot_list.append(pilot.as_dict())
    formula = Formula.read(compid)
    teams = {'country_scoring': formula.country_scoring, 'max_country_size': formula.max_country_size,
             'country_size': formula.country_size, 'team_scoring': formula.team_scoring, 'team_size': formula.team_size,
             'max_team_size': formula.max_team_size}
    return pilot_list, external, teams


def check_team_size(compid: int, nat=False):
    """Checks that the number of pilots in a team don't exceed the allowed number"""
    from formula import Formula
    from db.tables import TblParticipant as P
    formula = Formula.read(compid)
    message = ''
    if nat:
        max_team_size = formula.max_country_size or 0
    else:
        max_team_size = formula.max_team_size or 0

    with db_session() as db:
        if nat:
            q = db.query(P.nat, func.sum(P.nat_team)).filter(P.comp_id == compid).group_by(P.nat)
        else:
            q = db.query(P.team, func.count(P.team)).filter(P.comp_id == compid).group_by(P.team)
        result = q.all()
        for team in result:
            if team[1] > max_team_size:
                message += f"<p>Team {team[0]} has {team[1]} members - only {max_team_size} allowed.</p>"
    return message


def print_to_sse(text, id, channel):
    """Background jobs can send SSE by using this function which takes a string and sends to webserver
    as an HTML post request (via push_sse).
    A message type can be specified by including it in the string after a pipe "|" otherwise the default message
    type is 'info'
    Args:
        :param text: a string
        :param id: int/string to identify what the message relates to (par_id etc.)
        :param channel: string to identify destination of message (not access control) such as username etc
    """
    message = text.split('|')[0]
    if len(text.split('|')) > 1:
        message_type = text.split('|')[1]
    else:
        message_type = 'info'
    body = {'message': message, 'id': id}
    push_sse(body, message_type, channel=channel)


def push_sse(body, message_type, channel):
    """send a post request to webserver with contents of SSE to be sent"""
    from Defines import FLASKCONTAINER, FLASKPORT
    data = {'body': body, 'type': message_type, 'channel': channel}
    requests.post(f'http://{FLASKCONTAINER}:{FLASKPORT}/internal/see_message', json=data)


def production():
    """Checks if we are running production or dev via environment variable."""
    return not environ['FLASK_DEBUG'] == '1'


def unique_filename(filename, filepath):
    """checks file does not already exist and creates a unique and secure filename"""
    from pathlib import Path
    from os.path import join
    import glob
    from werkzeug.utils import secure_filename
    fullpath = join(filepath, filename)
    if Path(fullpath).is_file():
        index = str(len(glob.glob(fullpath)) + 1).zfill(2)
        name, suffix = filename.rsplit(".", 1)
        filename = '_'.join([name, index]) + '.' + suffix
    return secure_filename(filename)


def get_pretty_data(content: dict) -> dict:
    """transforms result json file in human readable data"""
    from result import pretty_format_results, get_startgates
    try:
        '''time offset'''
        timeoffset = 0 if 'time_offset' not in content['info'].keys() else int(content['info']['time_offset'])
        '''score decimals'''
        td = (0 if 'task_result_decimal' not in content['formula'].keys()
              else int(content['formula']['task_result_decimal']))
        cd = (0 if 'task_result_decimal' not in content['formula'].keys()
              else int(content['formula']['task_result_decimal']))
        pretty_content = dict()
        if 'file_stats' in content.keys():
            pretty_content['file_stats'] = pretty_format_results(content['file_stats'], timeoffset)
        pretty_content['info'] = pretty_format_results(content['info'], timeoffset)
        if 'tasks' in content.keys():
            pretty_content['tasks'] = pretty_format_results(content['tasks'], timeoffset, td)
        elif 'route' in content.keys():
            pretty_content['info'].update(startgates=get_startgates(content['info']))
            pretty_content['route'] = pretty_format_results(content['route'], timeoffset)
        if 'stats' in content.keys():
            pretty_content['stats'] = pretty_format_results(content['stats'], timeoffset)
        pretty_content['formula'] = pretty_format_results(content['formula'])
        results = []
        '''rankings'''
        sub_classes = sorted([dict(name=c, cert=v, limit=v[-1], prev=None, rank=1, counter=0)
                              for c, v in content['rankings'].items() if isinstance(v, list)],
                             key=lambda x: len(x['cert']), reverse=True)
        rank = 0
        prev = None
        for idx, r in enumerate(content['results'], 1):
            p = pretty_format_results(r, timeoffset, td, cd)
            if not prev == p['score']:
                rank, prev = idx, p['score']
            p['rank'] = str(rank)
            '''sub-classes'''
            for s in sub_classes:
                if p['glider_cert'] and p['glider_cert'] in s['cert']:
                    s['counter'] += 1
                    if not s['prev'] == p['score']:
                        s['rank'], s['prev'] = s['counter'], p['score']
                    p[s['limit']] = f"{s['rank']} ({p['rank']})"
                else:
                    p[s['limit']] = ''
            results.append(p)
        pretty_content['results'] = results
        pretty_content['classes'] = [{k: c[k] for k in ('name', 'limit', 'cert', 'counter')} for c in sub_classes]
        return pretty_content
    except:
        return 'error'


def full_rescore(taskid: int, background=False, status=None, autopublish=None, compid=None, user=None):
    from task import Task
    from comp import Comp
    from result import unpublish_result, publish_result
    task = Task.read(taskid)
    if background:
        print = partial(print_to_sse, id=None, channel=user)
        print('|open_modal')
        print('***************START*******************')
        refid, filename = task.create_results(mode='full', status=status, print=print)
        if autopublish:
            unpublish_result(taskid)
            publish_result(refid, ref_id=True)
            if compid:
                comp = Comp()
                comp.create_results(compid, name_suffix='Overview')
        print('****************END********************')
        print(f'{filename}|reload_select_latest')
        return None
    else:
        refid, filename = task.create_results(mode='full', status=status)
        if autopublish:
            unpublish_result(taskid)
            publish_result(refid, ref_id=True)
            if compid:
                comp = Comp()
                comp.create_results(compid, name_suffix='Overview')
        return refid


def get_task_igc_zip(task_id: int):
    from trackUtils import get_task_fullpath
    import shutil
    from Defines import track_formats

    task_path = get_task_fullpath(task_id)
    task_folder = task_path.parts[-1]
    comp_folder = task_path.parent
    zip_filename = task_folder + '.zip'
    zip_full_filename = Path(comp_folder, zip_filename)
    # check if there is a zip already there and is the youngest file for the task,
    # if not delete (if there) and (re)create
    if zip_full_filename.is_file():
        zip_time = zip_full_filename.stat().st_mtime
        list_of_files = [e for e in task_path.iterdir() if e.is_file() and e.suffix.strip('.').lower() in track_formats]
        latest_file = max(file.stat().st_mtime for file in list_of_files)
        if latest_file > zip_time:
            zip_full_filename.unlink(missing_ok=True)
        else:
            return zip_full_filename
    shutil.make_archive(comp_folder / task_folder, 'zip', task_path)
    return zip_full_filename


def check_short_code(comp_short_code):
    with db_session() as db:
        code = db.query(TblCompetition.comp_code).filter(TblCompetition.comp_code == comp_short_code).first()
        if code:
            return False
        else:
            return True
