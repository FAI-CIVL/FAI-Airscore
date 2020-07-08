"""
Module for operations on tracks
Use:    import trackUtils
        pil_id = compUtils.get_track_pilot(filename)

Antonio Golfari - 2018
"""

from os import path, listdir, fsdecode

from sqlalchemy import and_
from db.conn import db_session
from Defines import TRACKDIR, MAPOBJDIR, track_sources, track_formats
from pilot.flightresult import FlightResult
import re
from pathlib import Path
import unicodedata


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


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
    from Defines import track_formats
    files = []

    print(f"Directory: {directory} \n")
    print(f"Looking for files \n")

    """check files in temporary directory, and get only tracks"""
    for file in listdir(directory):
        print(f"checking: {file} \n")
        if not Path(file).name.startswith(tuple(['_', '.'])) and Path(file).suffix.strip('.') in track_formats:
            """file is a valid track"""
            files.append(path.join(directory, file))
    return files


def assign_and_import_tracks(files, task, xcontest=False, user=None, check_g_record=False, print=print):
    """Find pilots to associate with tracks"""
    from compUtils import get_registration
    from pilot.track import Track, validate_G_record, igc_parsing_config_from_yaml
    from functools import partial
    from frontendUtils import print_to_sse
    import json
    import sources

    pilot_list = []
    task_id = task.id
    comp_id = task.comp_id
    task_date = task.date
    track_counter = 0
    """checking if comp requires a regisration.
    Then we create a list of registered pilots to check against tracks filename.
    This should be much faster than checking against all pilots in database through a query"""
    registration = get_registration(comp_id)
    if registration:
        """We add tracks for the registered pilots not yet scored"""
        print("Comp with registration: files will be checked against registered pilots not yet scored")
        pilot_list = get_unscored_pilots(task_id, xcontest)
        print(f"We have {len(pilot_list)} pilots to find tracks for")
    else:
        print(f"We have {len(files)} tracks to associate")
    track_path = task.file_path
    FlightParsingConfig = igc_parsing_config_from_yaml(task.igc_config_file)
    # print("found {} tracks \n".format(len(files)))
    for file in files:
        mytrack = None
        filename = path.basename(file)
        if registration:
            if len(pilot_list) == 0:
                break
            if len(pilot_list) > 0:
                # print(f"checking {filename} against {len(pilot_list)} pilots...")
                """check filenames to find pilots"""
                if xcontest:
                    pilot, full_name = sources.xcontest.get_pilot_from_list(filename, pilot_list)
                else:
                    pilot, full_name = get_pilot_from_list(filename, pilot_list)

                if pilot:
                    """found a pilot for the track file.
                    dropping pilot from list and creating track obj"""
                    # print(f"Found a pilot to associate with file. dropping {pilot.name} from non scored list")
                    pilot_list[:] = [d for d in pilot_list if d.par_id != pilot.par_id]
                    mytrack = Track.read_file(filename=file, config=FlightParsingConfig, print=print)
        else:
            """We add track if we find a pilot in database
            that has not yet been scored"""
            mytrack = Track.read_file(filename=file, config=FlightParsingConfig, print=print)
            if get_pil_track(mytrack.par_id, task_id):
                """pilot has already been scored"""
                print(f"Pilot with ID {mytrack.par_id} has already a valid track for task with ID {task_id}")
                mytrack = None
        """check result"""
        if not mytrack:
            print(f"Track {filename} is not a valid track file, pilot not found in competition or pilot "
                  f"already has a track")
        elif not mytrack.date == task_date:
            print(f"track {filename} has a different date from task")
        else:
            """pilot is registered and has no valid track yet
            moving file to correct folder and adding to the list of valid tracks"""
            track_counter += 1
            print(f"Track {track_counter}|counter")
            mytrack.task_id = task_id
            filename_and_path = mytrack.copy_track_file(task_path=track_path, pname=full_name)
            # print(f"pilot {mytrack.par_id} associated with track {mytrack.filename}")
            # pilot.track = mytrack
            print(f"processing {pilot.ID} {pilot.name}:")
            if user:
                new_print = partial(print_to_sse, id=mytrack.par_id, channel=user)
                print('***************START*******************')
            else:
                new_print = print
            if check_g_record:
                print('Checking G-Record...')
                validation = validate_G_record(filename_and_path)
                if validation == 'FAILED':
                    print('G-Record not valid')
                    data = {'par_id': pilot.par_id, 'track_id': pilot.track_id, 'Result': ''}
                    print(json.dumps(data) + '|g_record_fail')
                    continue
                if validation == 'ERROR':
                    print('Error trying to validate G-Record')
                    continue
                if validation == 'PASSED':
                    print('G-Record is valid')
            verify_and_import_track(pilot, mytrack, task, print=new_print)
    print("*******************processed all tracks**********************")


def verify_and_import_track(result: FlightResult, track, task, print=print):
    from airspace import AirspaceCheck
    from pilot.flightresult import save_track

    if task.airspace_check:
        airspace = AirspaceCheck.from_task(task)
    else:
        airspace = None
    '''check flight against task'''
    result.check_flight(track.flight, task, airspace_obj=airspace, print=print)
    '''create map file'''
    result.save_tracklog_map_file(task, track.flight)
    '''save to database'''
    save_track(result, task.id)
    if result.notifications:
        print(str(result.notifications))
    print('***************END****************')
    return result


def find_pilot(name):
    """Get pilot from name or fai
    info comes from FSDB file, as FsParticipant attributes, or from igc filename
    Not sure about best strategy to retrieve pilots ID from name and FAI n.
    """
    from db.tables import PilotView as P

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
    with db_session() as db:
        t = db.query(P.pil_id)
        if names:
            q = t.filter(P.last_name.in_(names))
            p = q.filter(P.first_name.in_(names))
        else:
            p = t.filter_by(fai_id=fai)
        pil = p.all()
        if len(pil) == 1:
            return pil.pop().pil_id
        '''try one more time if we have both names and fai'''
        if fai and names:
            if not pil:
                p = q  # if we have zero results, try with only lastname and fai
            pil = p.filter(P.fai_id == fai).all()
            if len(pil) == 1:
                return pil.pop().pil_id
    return None


def get_pil_track(par_id: int, task_id: int):
    """Get pilot result in a given task"""
    from db.tables import TblTaskResult as R
    with db_session() as db:
        track_id = db.query(R.track_id).filter(
            and_(R.par_id == par_id, R.task_id == task_id)).scalar()
    if track_id == 0:
        """No result found"""
        print(f"Pilot with ID {par_id} has not been scored yet on task ID {task_id} \n")
    return track_id


def read_tracklog_map_result_file(par_id: int, task_id: int):
    """create task and track objects"""
    import jsonpickle
    from pathlib import Path
    res_path = Path(MAPOBJDIR, 'tracks', str(task_id))
    filename = f'{par_id}.track'
    fullname = Path(res_path, filename)
    # if the file does not exist
    if not Path(fullname).is_file():
        create_tracklog_map_result_file(par_id, task_id)
    with open(fullname, 'r') as f:
        return jsonpickle.decode(f.read())


def create_tracklog_map_result_file(par_id: int, task_id: int):
    from pilot import flightresult
    from task import Task
    from igc_lib import Flight
    from airspace import AirspaceCheck
    task = Task.read(task_id)
    airspace = None if not task.airspace_check else AirspaceCheck.from_task(task)
    pilot = flightresult.FlightResult.read(par_id, task_id)
    file = path.join(task.file_path, pilot.track_file)
    '''load track file'''
    flight = Flight.create_from_file(file)
    pilot.check_flight(flight, task, airspace)
    pilot.save_tracklog_map_file(task, flight)


def get_task_fullpath(task_id: int):
    from db.tables import TblTask as T, TblCompetition as C
    with db_session() as db:
        q = db.query(T.task_path, C.comp_path).join(C, C.comp_id == T.comp_id).filter_by(task_id=task_id).one()
    return path.join(TRACKDIR, q.comp_path, q.task_path)


def get_unscored_pilots(task_id: int, xcontest=False):
    """ Gets list of registered pilots that still do not have a result
        Input:  task_id INT task database ID
        Output: list of Pilot obj."""
    from pilot.flightresult import FlightResult
    from db.tables import UnscoredPilotView as U
    pilot_list = []
    with db_session() as db:
        results = db.query(U.par_id, U.comp_id, U.ID, U.name, U.nat, U.sex, U.civl_id,
                           U.live_id, U.glider, U.glider_cert, U.sponsor, U.xcontest_id,
                           U.team, U.nat_team).filter_by(task_id=task_id)
        if xcontest:
            results = results.filter(U.xcontest_id != None)
        results = results.all()
        for p in results:
            pilot = FlightResult()
            p.populate(pilot)
            pilot_list.append(pilot)
    return pilot_list


def get_pilot_from_list(filename, pilots: list):
    """ check filename against a list of Pilot Obj.
        Looks for different information in filename

        filename:   STR file name
        pilots:     LIST Participants Obj.
    """
    from Defines import filename_formats
    '''prepare filename formats'''
    # name = r'[a-zA-Z]+'
    # id = r'[\d]+'
    # fai = r'[\da-zA-Z]+'
    # civl = r'[0-9]+'
    # live = r'[\d]+'
    # other = r'[\da-zA-Z]+'
    filename_check = dict(name=r"[a-zA-Z']+", id=r'[\d]+', fai=r'[\da-zA-Z]+', civl=r'[\d]+', live=r'[\da-zA-Z]+',
                          other=r"[a-zA-Z0-9']+")
    format_list = [re.findall(r'[\da-zA-Z]+', el) for el in filename_formats]

    '''Get string'''
    string = Path(filename).stem
    elements = re.findall(r"[\d]+|[a-zA-Z']+", string)
    num_of_el = len(elements)
    pilot = None
    if any(el for el in format_list if len(el) == num_of_el):
        '''we have a match in number of elements between filename and accepted formats'''
        for f in [el for el in format_list if len(el) == num_of_el]:
            if all(re.match(filename_check[val], elements[idx]) for idx, val in enumerate(f)):
                '''we have a match between filename and accepted formats'''
                print(f'{f}')
                print(f'{elements}')
                if any(k for k in f if k in ['id', 'live', 'civl', 'fai']):
                    '''unique id, each should find the exact pilot'''
                    for idx, val in enumerate(f):
                        print(f'{val}, {elements[idx]}')
                        if val in ['other', 'name']:
                            continue
                        elif val == 'id':
                            v = int(elements[idx])
                            a = 'ID'
                        elif val == 'civl':
                            v = int(elements[idx])
                            a = 'civl_id'
                        elif val == 'live':
                            v = elements[idx]
                            a = 'live_id'
                        elif val == 'fai':
                            v = elements[idx]
                            a = 'fai_id'
                        else:
                            continue
                        pilot = next((p for p in pilots if getattr(p.info, a) == v), None)
                        if pilot:
                            print(f'{a}, found {pilot.name}')
                            filename = remove_accents('_'.join(pilot.name.replace('_', ' ')
                                                               .replace("'", ' ').lower().split()))
                            return pilot, filename
                else:
                    '''no unique id in filename, using name'''
                    names = [str(elements[idx]).lower() for idx, val in enumerate(f) if val == 'name']
                    pilot = next((p for p in pilots if all(n in p.name.lower().split() for n in names)), None)
                    if pilot:
                        print(f'using name, found {pilot.name}')
                        '''we found a pilot'''
                        filename = remove_accents('_'.join(pilot.name.replace('_', ' ')
                                                           .replace("'", ' ').lower().split()))
                        return pilot, filename
    return None, None
