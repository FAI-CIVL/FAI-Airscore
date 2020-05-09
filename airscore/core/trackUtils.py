"""
Module for operations on tracks
Use:    import trackUtils
        pil_id = compUtils.get_track_pilot(filename)

Antonio Golfari - 2018
"""

from os import path, listdir, fsdecode

from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

from Defines import FILEDIR, MAPOBJDIR, track_sources, track_formats
from flight_result import Flight_result
from myconn import Database
import re


def extract_tracks(file, dir):
    """gets tracks from a zipfile"""
    from zipfile import ZipFile, is_zipfile

    error = 0
    """Check if file exists"""
    if is_zipfile(file):
        print(f'extracting {file} in dir: {dir}')
        """Create a ZipFile Object and load file in it"""
        try:
            with ZipFile(file, 'r') as zipObj:
                """Extract all the contents of zip file in temporary directory"""
                zipObj.extractall(dir)
        except IOError:
            print(f"Error: extracting {file} to {dir} \n")
    else:
        print(f"reading error: {file} does not exist or is not a zip file \n")
        error = 1

    return error


def get_tracks(directory):
    """Checks files and imports what appear to be tracks"""
    files = []

    print(f"Directory: {directory} \n")
    print(f"Looking for files \n")

    """check files in temporary directory, and get only tracks"""
    for file in listdir(directory):
        print(f"checking: {file} \n")
        if (not (file.startswith(".") or file.startswith("_"))) and file.lower().endswith(".igc"):
            """file is a valid track"""
            print(f"valid filename: {file} \n")
            """add file to tracks list"""
            files.append(path.join(directory, file))
        else:
            print(f"NOT valid filename: {file} \n")

    print(f"files in list: {len(files)} \n")
    for f in files:
        print(f"  {f} \n")

    return files


def assign_and_import_tracks(files, task, xcontest=False):
    """Find pilots to associate with tracks"""
    from compUtils import get_registration, get_task_path
    from track import Track
    from trackUtils import get_unscored_pilots

    pilot_list = []
    print(f"We have {len(files)} track to associate \n")
    task_id = task.id
    comp_id = task.comp_id
    task_date = task.date
    """checking if comp requires a regisration.
    Then we create a list of registered pilots to check against tracks filename.
    This should be much faster than checking against all pilots in database through a query"""
    registration = get_registration(comp_id)
    if registration:
        """We add tracks for the registered pilots not yet scored"""
        print("Comp with registration: files will be checked against registered pilots not yet scored \n")
        pilot_list = get_unscored_pilots(task_id, xcontest)

    track_path = task.file_path

    # print("found {} tracks \n".format(len(files)))
    for file in files:
        mytrack = None
        filename = path.basename(file)
        if registration:
            if len(pilot_list) > 0:
                print(f"checking {filename} against {len(pilot_list)} pilots... \n")
                """check filenames to find pilots"""
                pilot, full_name = get_pilot_from_list(filename, pilot_list)
                if pilot:
                    """found a pilot for the track file.
                    dropping pilot from list and creating track obj"""
                    print(f"Found a pilot to associate with file. dropping {pilot.name} from non scored list \n")
                    pilot_list[:] = [d for d in pilot_list if d.par_id != pilot.par_id]
                    mytrack = Track.read_file(filename=file)
        else:
            """We add track if we find a pilot in database
            that has not yet been scored"""
            mytrack = Track.read_file(filename=file)
            if get_pil_track(mytrack.par_id, task_id):
                """pilot has already been scored"""
                print(f"Pilot with ID {mytrack.par_id} has already a valid track for task with ID {task_id} \n")
                mytrack = None
        """check result"""
        if not mytrack:
            print(f"Track {filename} is not a valid track file or pilot not found in competition\n")
        elif not mytrack.date == task_date:
            print(f"track {filename} has a different date from task \n")
        else:
            """pilot is registered and has no valid track yet
            moving file to correct folder and adding to the list of valid tracks"""
            mytrack.task_id = task_id
            mytrack.copy_track_file(task_path=track_path, pname=full_name)
            print(f"pilot {mytrack.par_id} associated with track {mytrack.filename} \n")
            pilot.track = mytrack
            verify_and_import_track(pilot, task)


def import_track(pilot, task_id):
    pilot.track.to_db(task_id)
    return pilot.track.track_id


def verify_and_import_track(pilot, task):
    from airspace import AirspaceCheck

    if task.airspace_check:
        airspace = AirspaceCheck.from_task(task)
    else:
        airspace = None
    pilot.result = Flight_result.check_flight(pilot.track.flight, task, airspace_obj=airspace)  # check flight against task
    pilot.to_db()
    print(pilot.track.flight.notes)

    return pilot.result


def find_pilot(name):
    """Get pilot from name or fai
    info comes from FSDB file, as FsParticipant attributes, or from igc filename
    Not sure about best strategy to retrieve pilots ID from name and FAI n.
    """
    from db_tables import PilotView as P

    '''Gets name from string. check it is not integer'''
    if type(name) is int:
        '''name is a id number'''
        fai = name
        names = None
    else:
        fai = None
        names = name.replace("'", "''").replace('.', ' ').replace('_', ' ').replace('-', ' ').split()
        '''check if we have fai n. in names'''
        if names[0].isdigit():
            fai = names.pop(0)

    print("Trying with name... \n")
    with Database() as db:
        t = db.session.query(P.pil_id)
        if names:
            q = t.filter(P.last_name.in_(names))
            p = q.filter(P.first_name.in_(names))
        else:
            p = t.filter(P.fai_id == fai)
        pil = p.all()
        if len(pil) == 1: return pil.pop().pil_id
        '''try one more time if we have both names and fai'''
        if fai and names:
            if not pil:
                p = q  # if we have zero results, try with only lastname and fai
            pil = p.filter(P.fai_id == fai).all()
            if len(pil) == 1:
                return pil.pop().pil_id
    return None


def get_pil_track(par_id, task_id):
    """Get pilot result in a given task"""
    from db_tables import TblTaskResult as R

    with Database() as db:
        track_id = db.session.query(R.track_id).filter(
            and_(R.par_id == par_id, R.task_id == task_id)).scalar()
    if track_id == 0:
        """No result found"""
        print(f"Pilot with ID {par_id} has not been scored yet on task ID {task_id} \n")
    return track_id


def read_tracklog_map_result_file(track_id, task_id):
    """create task and track objects"""
    import jsonpickle
    from pathlib import Path

    res_path = f"{MAPOBJDIR}tracks/{task_id}/"
    filename = 'result_' + str(track_id) + '.track'
    fullname = path.join(res_path, filename)
    # if the file does not exist
    if not Path(fullname).is_file():
        create_tracklog_map_result_file(track_id, task_id)

    with open(fullname, 'r') as f:
        return jsonpickle.decode(f.read())


def create_tracklog_map_result_file(track_id, task_id):
    import flight_result
    from task import Task
    from track import Track

    task = Task.read(task_id)
    # formula = For.TaskFormula.read(task_id)
    track = Track.read_db(track_id)
    lib = task.formula.get_lib()
    result = flight_result.Flight_result.check_flight(track.flight, task)
    result.save_tracklog_map_result_file(result.to_geojson_result(track, task), str(track_id), task_id)


def get_task_fullpath(task_id):
    from db_tables import TblTask as T, TblCompetition as C

    with Database() as db:
        try:
            q = db.session.query(T.task_path, 
                                 C.comp_path).join(C, C.comp_id == T.comp_id).filter(T.task_id == task_id).one()
        except SQLAlchemyError:
            print(f'Get Task Path Query Error')
            return None
    return path.join(FILEDIR, q.comp_path, q.task_path)


def get_unscored_pilots(task_id, xcontest=False):
    """ Gets list of registered pilots that still do not have a result
        Input:  task_id INT task database ID
        Output: list of Pilot obj."""
    from pilot import Pilot
    from participant import Participant
    from db_tables import UnscoredPilotView as U
    pilot_list = []
    with Database() as db:
        try:
            results = db.session.query(U.par_id, U.comp_id, U.ID, U.name, U.nat, U.sex, U.civl_id, U.glider,
                                       U.glider_cert, U.sponsor, U.xcontest_id, U.team, U.nat_team).filter(
                U.task_id == task_id).all()
            # if xcontest:
            #     q = q.filter(U.xcontest_id != None)
            # results = q.all()
            for p in results:
                participant = Participant()
                db.populate_obj(participant, p)
                pilot = Pilot.create(task_id=task_id, info=participant)
                pilot_list.append(pilot)
        except SQLAlchemyError as e:
            error = str(e.__dict__)
            print(f"Error trying to retrieve unscored pilots from database {error}")
            db.session.rollback()
            db.session.close()
            return error
    return pilot_list


def get_pilot_from_list(filename, pilots):
    """ check filename against a list of Pilot Obj.
        Looks for different information in filename

        filename:   STR file name
        pilots:     LIST Participants Obj.
    """
    # TODO define different acceptable filename formats

    '''Get string'''
    string = path.splitext(filename)[0]

    """Try to get pilot from filename, using ID, CIVLID or name."""
    fields = string.replace('.', ' ').replace('_', ' ').replace('-', ' ').lower().split()
    # strip out all numbers and other non letters. So we can process igc files like the ones airscore saves.
    string_alpha_only = re.sub("[^a-zA-Z']+", ' ', string)
    fields_alpha_only = string_alpha_only.replace('.', ' ').replace('_', ' ').replace('-', ' ').lower().split()
    for idx, pilot in enumerate(pilots):
        civl_id = pilot.info.civl_id
        fullname = pilot.info.name.replace('_', ' ').lower().split()
        ID = pilot.info.ID
        if all(n in fields_alpha_only for n in fullname):
            '''found a pilot'''
            pilot.track.track_file = filename
            return pilot, '_'.join(fullname)

        elif any(f == str(ID) for f in fields) and any(n in fields for n in fullname):
            '''found a pilot'''
            pilot.track.track_file = filename
            pilot.track.comment = f'Pilot found using name {pilot.name.lower()} and ID {ID}'
            return pilot, '_'.join(fullname)

        elif any(f == str(civl_id) for f in fields) and any(n in fields for n in fullname):
            '''found a pilot'''
            pilot.track.track_file = filename
            pilot.track.comment = f'Pilot found using name {pilot.name.lower()} and CIVLID {civl_id}'
            return pilot, '_'.join(fullname)
    return None, None


def assign_tracks(task, file_dir, pilots_list, source):
    """ This function will look for tracks in giver dir or in task_path, and tries to associate tracks to participants.
        For the moment we give for granted pilots need to register, as for this stage only event with registration
        are possible.

        AirScore will permit to retrieve tracks from different sources and repositories. We need to be able
        to recognise pilot from filename.
    """
    from pathlib import Path
    from igc_lib import Flight
    import shutil

    # if not file_dir:
    #     file_dir = task.file_path
    if len(listdir(file_dir)) == 0:
        ''' directory is empty'''
        print(f'directory {file_dir} is empty')
        return None

    for file in listdir(file_dir):
        filename = fsdecode(file)  # filename is without path
        file_ext = Path(filename).suffix[1:].lower()
        if filename.startswith((".", "_")) or file_ext not in track_formats:
            """file is not a valid track"""
            print(f"Not a valid filename: {filename}")
            pass

        # TODO manage track file source (comp attr?)
        if source:
            pilot, idx = source.get_pilot_from_list(filename, pilots_list)
        else:
            pilot, idx = get_pilot_from_list(filename, pilots_list)

        if pilot:
            try:
                '''move track to task folder'''
                file_path = task.file_path
                full_path = path.join(file_path, filename)
                shutil.move(filename, full_path)
                '''add flight'''
                pilot.track.flight = Flight.create_from_file(full_path)
                '''check flight'''
                pilot.result = verify_track(pilot.track, task)
                '''remove pilot from list'''
                pilots_list.pop(idx)
            except IOError:
                print(f"Error assigning track {filename} to pilot \n")


def get_tracks_from_source(task, source=None):
    """ Accept tracks for unscored pilots of the task
        - Gets unscored pilots list and, if is not null:
        - Gets tracks from server source to a temporary folder
        - assigns tracks to pilots
        - imports assigned track to correct task folder and, if needed, changes filename"""
    # TODO function that loads existing results before, so we can score directly after?
    from tempfile import TemporaryDirectory
    import importlib

    ''' Get unscored pilots list'''
    pilots_list = get_unscored_pilots(task.task_id)
    if len(pilots_list) == 0:
        print(f"No pilots without tracks found registered to the comp...")
        return

    ''' load source lib'''
    if source is None:
        if task.track_source not in track_sources:
            print(f"We do not have any zipfile source.")
            return
        else:
            source = importlib.import_module('tracksources.' + task.track_source)

    '''get zipfile'''
    with TemporaryDirectory() as archive_dir:
        zipfile = source.get_zipfile(task, archive_dir)

        ''' Get tracks from zipfile to a temporary folder'''
        with TemporaryDirectory() as temp_dir:
            extract_tracks(zipfile, temp_dir)
            assign_tracks(task, temp_dir, pilots_list, source)


def get_tracks_from_zipfile(task, zipfile):
    """ Accept tracks for unscored pilots of the task
        - Gets unscored pilots list and, if is not null:
        - Gets tracks from zipfile to a temporary folder
        - assigns tracks to pilots
        - imports assigned track to correct task folder and, if needed, changes filename"""
    # TODO function that loads existing results before, so we can score directly after?
    from tempfile import TemporaryDirectory

    ''' Get unscored pilots list'''
    pilots_list = get_unscored_pilots(task.task_id)
    if len(pilots_list) == 0:
        print(f"No pilots without tracks found registered to the comp...")
        return

    ''' Get tracks from zipfile to a temporary folder'''
    with TemporaryDirectory() as temp_dir:
        extract_tracks(zipfile, temp_dir)
        assign_tracks(task, temp_dir, pilots_list, task.track_source)
