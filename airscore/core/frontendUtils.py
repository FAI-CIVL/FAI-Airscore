from db_tables import TblCompetition, TblTask, TblCompAuth, TblRegion, TblRegionWaypoint, TblTaskWaypoint
from route import Turnpoint
from sqlalchemy.orm import aliased
from flask import jsonify
from myconn import Database
import datetime
import ruamel.yaml
from sqlalchemy import func
from pathlib import Path
import jsonpickle
from Defines import MAPOBJDIR, IGCPARSINGCONFIG, track_formats
from design_map import make_map
from sqlalchemy.exc import SQLAlchemyError
from calcUtils import sec_to_time
from os import scandir, path, environ
from werkzeug.utils import secure_filename
import requests
from flask_sse import sse
from functools import partial


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


def get_admin_comps(current_userid):
    """get a list of all competitions in the DB and flag ones where owner is current user"""
    c = aliased(TblCompetition)
    ca = aliased(TblCompAuth)
    with Database() as db:
        comps = (db.session.query(c.comp_id, c.comp_name, c.comp_site,
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
        taskid = task['task_id']
        tasknum = task['task_num']
        if int(tasknum) > max_task_num:
            max_task_num = int(tasknum)
            last_region = task['reg_id']
        # if task['task_name'] is None or task['task_name'] == '':
        #     task['task_name'] = f'Task {tasknum}'
        task['num'] = f"Task {tasknum}"
        # task['link'] = f'<a href="/users/task_admin/{taskid}">Task {tasknum}</a>'
        task['opt_dist'] = 0 if not task['opt_dist'] else round(task['opt_dist'] / 1000, 2)
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
    """Gets a list of dicts of: if defines.yaml waypoint library function is on - all regions
    otherwise only the regions with their comp_id field set the the compid parameter"""
    import Defines
    import region
    if Defines.WAYPOINT_AIRSPACE_FILE_LIBRARY:
        return region.get_all_regions()
    else:
        return region.get_comp_regions_and_wpts(compid)


def get_region_choices(compid):
    """gets a list of regions to be used in frontend select field (choices) and details of each region (details)"""
    regions = get_comp_regions(compid)
    choices = []
    details = {}
    for region in regions['regions']:
        choices.append((region['reg_id'], region['name']))
        details[region['reg_id']] = region
    return choices, details


def get_waypoint_choices(reg_id):
    import region
    wpts = region.get_region_wpts(reg_id)
    choices = []
    details = []

    for wpt in wpts:
        choices.append((wpt['rwp_id'], wpt['name'] + ' - ' + wpt['description']))
        wpt['Class'] = wpt['name'][0]
        details.append(wpt)

    return choices, details


def get_pilot_list_for_track_management(taskid):
    from db_tables import TblTaskResult as R, TblParticipant as P, TblTask as T
    with Database() as db:
        try:
            results = db.session.query(R.goal_time, R.track_file, R.track_id, R.result_type, R.distance_flown,
                                       R.ESS_time, R.SSS_time, R.par_id).filter(
                R.task_id == taskid).subquery()
            pilots = db.session.query(T.task_id, P.name, P.ID, P.par_id, results.c.track_id, results.c.SSS_time,
                                      results.c.ESS_time,
                                      results.c.distance_flown, results.c.track_file, results.c.result_type) \
                .outerjoin(P, T.comp_id == P.comp_id).filter(T.task_id == taskid) \
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
        data['ID'] = pilot['ID']
        data['name'] = pilot['name']
        data['par_id'] = pilot['par_id']
        data['track_id'] = pilot['track_id']
        if pilot['ESS_time']:
            time = sec_to_time(pilot['ESS_time'] - pilot['SSS_time'])
        if pilot['result_type'] == 'goal':
            data['Result'] = f'Goal {time}'
        elif pilot['result_type'] == 'lo':
            data['Result'] = f"LO {round(pilot['distance_flown'] / 1000, 2)}"
        elif pilot['result_type'] is None:
            data['Result'] = "Not Yet Processed"
        elif pilot['result_type'] == "mindist":
            data['Result'] = "Min Dist"
        else:
            data['Result'] = pilot['result_type'].upper()
        if pilot['track_file']:  # if there is a track, make the result a link to the map
            trackid = data['track_id']
            result = data['Result']
            data['Result'] = f'<a href="/map/{trackid}-{taskid}">{result}</a>'
        all_data.append(data)
    return all_data


def get_waypoint(wpt_id=None, rwp_id=None):
    """reads waypoint from tblTaskWaypoint or tblRegionWaypoint depending on input and returns Turnpoint object"""
    if not (wpt_id or rwp_id):
        return None
    with Database() as db:
        try:
            if wpt_id:
                result = db.session.query(TblTaskWaypoint).get(wpt_id)
            else:
                result = db.session.query(TblRegionWaypoint).get(rwp_id)
            tp = Turnpoint()
            db.populate_obj(tp, result)
        except SQLAlchemyError as e:
            error = str(e)
            print(f"error creating Turnpoint obj. error{error}")
            db.session.rollback()
            db.session.close()
            return None
        return tp


def save_turnpoint(task_id, turnpoint: Turnpoint):
    """save turnpoint in a task- for frontend"""
    if not (type(task_id) is int and task_id > 0):
        print("task not present in database ", task_id)
        return None
    with Database() as db:
        try:
            if not turnpoint.wpt_id:
                '''add new taskWaypoint'''
                # tp = TblTaskWaypoint(**turnpoint.as_dict())
                tp = TblTaskWaypoint()
                db.populate_row(tp, turnpoint)
                db.session.add(tp)
                db.session.flush()
            else:
                '''update taskWaypoint'''
                tp = db.session.query(TblTaskWaypoint).get(turnpoint.wpt_id)
                if tp:
                    for k, v in turnpoint.as_dict().items():
                        if hasattr(tp, k):
                            setattr(tp, k, v)
                db.session.flush()
        except SQLAlchemyError:
            print('error saving turnpoint')
            db.session.rollback()
            return None
        return 1


def allowed_tracklog(filename, extension=track_formats):
    if "." not in filename:
        return False

    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]

    # Check if the extension is allowed (make everything uppercase)
    if ext.upper() in [e.upper() for e in extension]:
        return True
    else:
        return False


def allowed_tracklog_filesize(filesize, size=5):
    """check if tracklog exceeds maximum file size for tracklog (5mb)"""
    if int(filesize) <= size * 1024 * 1024:
        return True
    else:
        return False


def process_igc(task_id, par_id, tracklog):
    from track import Track, create_igc_filename
    from flightresult import FlightResult
    from airspace import AirspaceCheck
    from igc_lib import Flight
    from task import Task
    from pilot import Pilot

    pilot = Pilot.read(par_id, task_id)
    if pilot.name:
        task = Task.read(task_id)
        fullname = create_igc_filename(task.file_path, task.date, pilot.name)
        tracklog.save(fullname)
    else:
        return None, None

    """import track"""
    pilot.track = Track(track_file=fullname, par_id=pilot.par_id)
    pilot.track.flight = Flight.create_from_file(fullname)
    """check result"""
    if not pilot.track:
        error = f"for {pilot.name} - Track is not a valid track file"
        return None, error
    elif not pilot.track.date == task.date:
        error = f"for {pilot.name} - Track has a different date from task date"
        return None, error
    else:
        print(f"pilot {pilot.track.par_id} associated with track {pilot.track.filename} \n")

        """checking track against task"""
        if task.airspace_check:
            airspace = AirspaceCheck.from_task(task)
        else:
            airspace = None
        pilot.result = FlightResult.check_flight(pilot.track.flight, task, airspace_obj=airspace)
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
        if pilot.track_id:  # if there is a track, make the result a link to the map
            trackid = data['track_id']
            result = data['Result']
            data['Result'] = f'<a href="/map/{trackid}-{task.task_id}">{result}</a>'
    return data, None


def save_igc_background(task_id, par_id, tracklog, user):
    from task import Task
    from track import create_igc_filename
    from pilot import Pilot

    pilot = Pilot.read(par_id, task_id)
    if pilot.name:
        task = Task.read(task_id)
        fullname = create_igc_filename(task.file_path, task.date, pilot.name)
        tracklog.save(fullname)
        sse.publish({'message': f'IGC file saved: {fullname.split("/")[-1]}', 'id': par_id}, channel=user, type='info',
                    retry=30)
    else:
        return None, None

    return fullname.split("/")[-1], fullname


def process_igc_background(task_id, par_id, filename, full_file_name, user):
    from track import Track
    from flightresult import FlightResult
    from airspace import AirspaceCheck
    from igc_lib import Flight
    from task import Task
    from pilot import Pilot
    import json
    pilot = Pilot.read(par_id, task_id)
    task = Task.read(task_id)
    print = partial(print_to_sse, id=par_id, channel=user)
    print('|open_modal')
    print('***************START*******************')
    """import track"""
    pilot.track = Track(track_file=filename, par_id=pilot.par_id)
    pilot.track.flight = Flight.create_from_file(full_file_name)
    """check result"""
    if not pilot.track:
        print(f"for {pilot.name} - Track is not a valid track file")
        return None
    elif not pilot.track.date == task.date:
        print(f"for {pilot.name} - Track has a different date from task date")
        return None
    else:
        print(f"pilot {pilot.track.par_id} associated with track {pilot.track.filename} \n")

        """checking track against task"""
        if task.airspace_check:
            airspace = AirspaceCheck.from_task(task)
        else:
            airspace = None
        pilot.result = FlightResult.check_flight(pilot.track.flight, task, airspace_obj=airspace, print=print)
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
        if pilot.track_id:  # if there is a track, make the result a link to the map
            trackid = data['track_id']
            result = data['Result']
            data['Result'] = f'<a href="/map/{trackid}-{task.task_id}">{result}</a>'
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


def process_igc_from_zip(taskid, tracksdir, user):
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
    assign_and_import_tracks(tracks, task, user=user, print=print)
    rmtree(tracksdir)
    print('|reload')
    return 'Success'


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
            print(f"There are no valid tracks in zipfile {zipfile}, or all pilots are already been scored \n")
            return None

        """associate tracks to pilots and import"""
        assign_and_import_tracks(tracks, task)
        return 'Success'


def get_task_result_file_list(taskid):
    from db_tables import TblResultFile as R
    with Database() as db:
        try:
            files = db.session.query(R.created, R.filename, R.status, R.active, R.ref_id).filter(
                R.task_id == taskid).all()
            if files:
                files = [row._asdict() for row in files]

        except SQLAlchemyError:
            print("there was a problem with getting the result list")
            return None

        return files


def number_of_tracks_processed(taskid):
    from db_tables import TblTaskResult as R, TblParticipant as P, TblTask as T
    from sqlalchemy import func
    with Database() as db:
        try:
            results = db.session.query(func.count()).filter(R.task_id == taskid).scalar()
            pilots = db.session.query(func.count(P.par_id)).outerjoin(T, P.comp_id == T.comp_id).filter(
                T.task_id == taskid).scalar()

        except SQLAlchemyError:
            print("there was a problem with getting the pilot/result list")
            return None
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


def get_comp_admins(compid_or_taskid, task_id=False):
    """returns owner and list of admins takes compid by default or taskid if taskid is True"""
    from db_tables import TblCompAuth as CA
    from airscore.user.models import User
    if task_id:
        taskid = compid_or_taskid
    else:
        compid = compid_or_taskid
    with Database() as db:
        try:
            if task_id:
                all_admins = db.session.query(User.id, User.username, User.first_name, User.last_name, CA.user_auth) \
                    .join(CA, User.id == CA.user_id).join(TblTask, CA.comp_id == TblTask.comp_id).filter(
                    TblTask.task_id == taskid,
                    CA.user_auth.in_(('owner', 'admin'))).all()
            else:
                all_admins = db.session.query(User.id, User.username, User.first_name, User.last_name, CA.user_auth) \
                    .join(CA, User.id == CA.user_id).filter(CA.comp_id == compid,
                                                            CA.user_auth.in_(('owner', 'admin'))).all()
            if all_admins:
                all_admins = [row._asdict() for row in all_admins]
        except SQLAlchemyError as e:
            error = str(e)
            print(f"there was a problem with getting the admin list for comp id{compid_or_taskid} error{error}")
            db.session.rollback()
            db.session.close()
            return None, None
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


def set_comp_admin(compid, userid, owner=False):
    from db_tables import TblCompAuth as CA
    auth = 'owner' if owner else 'admin'
    with Database() as db:
        try:
            admin = CA(user_id=userid, comp_id=compid, user_auth=auth)
            db.session.add(admin)
            db.session.flush()
        except SQLAlchemyError as e:
            error = str(e)
            print(f"there was a problem with setting the admin for comp id{compid} error{error}")
            db.session.rollback()
            db.session.close()
            return None
    return True


def get_all_admins():
    """returns a list of all admins in the system"""
    from airscore.user.models import User
    with Database() as db:
        try:
            all_admins = db.session.query(User.id, User.username, User.first_name, User.last_name) \
                .filter(User.is_admin == 1).all()
            if all_admins:
                all_admins = [row._asdict() for row in all_admins]
        except SQLAlchemyError as e:
            error = str(e)
            print(f"there was a problem with getting the admin list. error{error}")
            db.session.rollback()
            db.session.close()
            return None
        return all_admins


def update_airspace_file(old_filename, new_filename):
    """change the name of the openair file in all regions it is used."""
    R = aliased(TblRegion)
    with Database() as db:
        try:

            db.session.query(R).filter(R.openair_file == old_filename).update({R.openair_file: new_filename},
                                                                              synchronize_session=False)
            db.session.commit()

        except SQLAlchemyError as e:
            error = str(e)
            print(f"error trying to update openair_file file in DB. error{error}")
            db.session.rollback()
            db.session.close()
            return None
    return True


# def save_waypoint_file(file):
#     from Defines import WAYPOINTDIR, AIRSPACEDIR
#     full_file_name = path.join(WAYPOINTDIR, filename)


def get_non_registered_pilots(compid):
    from db_tables import TblParticipant, PilotView

    p = aliased(TblParticipant)
    pv = aliased(PilotView)

    with Database() as db:
        '''get registered pilots'''
        reg = db.session.query(p.pil_id).filter(p.comp_id == compid).subquery()
        non_reg = db.session.query(pv.pil_id, pv.civl_id, pv.first_name, pv.last_name). \
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
    from db_tables import TblCompetition

    c = aliased(TblCompetition)
    with Database() as db:
        try:
            comps = db.session.query(c.comp_id).filter(c.igc_config_file == igc_config).all()
        except SQLAlchemyError as e:
            error = str(e)
            print(f"error trying to update openair_file file in DB. error{error}")
            db.session.rollback()
            db.session.close()
            return None
        return comps


def get_comp_info(compid, task_ids=None):
    if task_ids is None:
        task_ids = []
    c = aliased(TblCompetition)
    t = aliased(TblTask)

    with Database() as db:
        non_scored_tasks = (db.session.query(t.task_id.label('id'),
                                             t.task_name,
                                             t.date,
                                             t.task_type,
                                             t.opt_dist,
                                             t.comment).filter(t.comp_id == compid, t.task_id.notin_(task_ids))
                            .order_by(t.date.desc()).all())

        competition_info = (db.session.query(
            c.comp_id,
            c.comp_name,
            c.comp_site,
            c.date_from,
            c.date_to,
            c.self_register,
            c.website).filter(c.comp_id == compid).one())
    comp = competition_info._asdict()

    return comp, non_scored_tasks


def get_participants(compid, source='all'):
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


def check_team_size(compid, nat=False):
    """Checks that the number of pilots in a team don't exceed the allowed number"""
    from formula import Formula
    from db_tables import TblParticipant as P
    formula = Formula.read(compid)
    message = ''
    if nat:
        max_team_size = formula.max_country_size or 0
    else:
        max_team_size = formula.max_team_size or 0

    with Database() as db:
        if nat:
            q = db.session.query(P.nat, func.sum(P.nat_team)).filter(P.comp_id == compid).group_by(P.nat)
        else:
            q = db.session.query(P.team, func.count(P.team)).filter(P.comp_id == compid).group_by(P.team)
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
    # from sys import stdout
    message = text.split('|')[0]
    if len(text.split('|')) > 1:
        message_type = text.split('|')[1]
    else:
        message_type = 'info'
    body = {'message': message, 'id': id}
    push_sse(body, message_type, channel=channel)
    # print(f"pushed {body=} {message_type=} {channel=}")
    # stdout.flush()


def push_sse(body, message_type, channel):
    """send a post request to webserver with contents of SSE to be sent"""
    from Defines import FLASKCONTAINER, FLASKPORT
    data = {'body': body, 'type': message_type, 'channel': channel}
    requests.post(f'http://{FLASKCONTAINER}:{FLASKPORT}/internal/see_message', json=data)


def production():
    """Checks if we are running production or dev via environment variable."""
    if environ['FLASK_DEBUG'] == '1':
        return False
    else:
        return True


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


def get_pretty_data(filename):
    """transforms result json file in human readable data"""
    from result import open_json_file, pretty_format_results, get_startgates
    try:
        content = open_json_file(filename)
        '''time offset'''
        timeoffset = int(content['info']['time_offset'])
        '''score decimals'''
        td = 0 if 'task_result_decimal' not in content['formula'].keys() else int(content['formula']['task_result_decimal'])
        cd = 0 if 'task_result_decimal' not in content['formula'].keys() else int(content['formula']['task_result_decimal'])
        pretty_content = dict()
        pretty_content['file_stats'] = pretty_format_results(content['file_stats'], timeoffset)
        pretty_content['info'] = pretty_format_results(content['info'], timeoffset)
        pretty_content['info'].update(startgates=get_startgates(content['info']))
        if 'tasks' in content.keys():
            pretty_content['tasks'] = pretty_format_results(content['tasks'], timeoffset, td)
        elif 'route' in content.keys():
            pretty_content['route'] = pretty_format_results(content['route'], timeoffset)
        pretty_content['stats'] = pretty_format_results(content['stats'], timeoffset)
        pretty_content['formula'] = pretty_format_results(content['formula'])
        results = []
        rank = 1
        for r in content['results']:
            p = pretty_format_results(r, timeoffset, td, cd)
            p['rank'] = str(rank)
            results.append(p)
            rank += 1
        pretty_content['results'] = results
        all_classes = []
        for glider_class in content['rankings']:
            if glider_class[-5:].lower() == 'class':
                comp_class = {'name': glider_class, 'limit': content['rankings'][glider_class][-1]}
                all_classes.append(comp_class)
        all_classes.reverse()
        pretty_content['classes'] = all_classes
        return pretty_content
    except:
        return 'error'


def full_rescore(taskid, background=False, status=None, autopublish=None, compid=None, user=None):
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


def get_task_igc_zip(task_id):
    from trackUtils import get_task_fullpath
    import shutil
    import glob
    from Defines import TEMPFILES

    task_path = get_task_fullpath(task_id)
    task_folder = task_path.split('/')[-1]
    comp_folder = '/'.join(task_path.split('/')[:-1])
    zip_filename = task_folder + '.zip'
    zip_full_filename = path.join(comp_folder, zip_filename)
    # check if there is a zip already there and is the youngest file for the task,
    # if not delete (if there) and (re)create
    if path.isfile(zip_full_filename):
        zip_time = path.getctime(zip_full_filename)
        list_of_files = glob.glob(task_path + '/*')
        latest_file = max(list_of_files, key=path.getctime)
        latest_file_modified = path.getctime(latest_file)
        if latest_file_modified > zip_time:
            Path(zip_full_filename).unlink(missing_ok=True)
        else:
            return zip_full_filename
    shutil.make_archive(comp_folder + '/' + task_folder, 'zip', task_path)
    return zip_full_filename


def check_short_code(comp_short_code):
    with Database() as db:
        code = db.session.query(TblCompetition.comp_code).filter(TblCompetition.comp_code == comp_short_code).first()
        if code:
            return False
        else:
            return True
