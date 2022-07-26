"""
Module for operations on tracks
Use:    import trackUtils
        pil_id = compUtils.get_track_pilot(filename)

Antonio Golfari - 2018
"""

import re
import unicodedata
from os import fsdecode, listdir
from pathlib import Path
from airspace import AirspaceCheck
from db.conn import db_session
from Defines import MAPOBJDIR, TRACKDIR, track_formats, track_sources, IGCPARSINGCONFIG
from pilot.track import Track, FlightParsingConfig
from pilot.flightresult import FlightResult, save_track
from sqlalchemy import and_


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def extract_tracks(file, folder):
    """gets tracks from a zipfile"""
    from zipfile import ZipFile, is_zipfile

    error = 0
    """Check if file exists"""
    if is_zipfile(file):
        print(f'extracting {file} in dir: {folder}')
        """Create a ZipFile Object and load file in it"""
        try:
            with ZipFile(file, 'r') as zipObj:
                """Extract all the contents of zip file in temporary directory"""
                zipObj.extractall(folder)
        except IOError:
            print(f"Error: extracting {file} to {folder} \n")
            error = 1
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
    for el in listdir(directory):
        print(f"checking: {el}")

        file = Path(directory, el)
        if not file.name.startswith(tuple(['_', '.'])) and file.suffix.strip('.').lower() in track_formats:
            """file is a valid track"""
            print(f"{file} is a valid track")
            files.append(file)
        else:
            print(f"{file} is NOT a valid track")
    return files


def assign_and_import_tracks(files, task, track_source=None, user=None, check_g_record=False, print=print):
    """Find pilots to associate with tracks"""
    import importlib
    from functools import partial
    from frontendUtils import print_to_sse, track_result_output
    from pilot.flightresult import update_all_results
    import json

    task_id = task.id
    """checking if comp requires a registration.
    Then we create a list of registered pilots to check against tracks filename.
    This should be much faster than checking against all pilots in database through a query"""
    # TODO: at the moment we need to cover only events where participants are registered
    #  this part will be adjusted as soon as we want to accept open events.

    """We add tracks for the registered pilots not yet scored"""
    pilot_list = get_unscored_pilots(task_id, track_source)
    if len(pilot_list) == 0:
        print(f"Pilot list is empty")
        return

    pilots_to_save = []
    if track_source:
        ''' Use Live server filename format to get pilot '''
        lib = importlib.import_module('.'.join(['sources', track_source]))
    else:
        lib = importlib.import_module('trackUtils')

    tracks_processed = 0
    number_of_tracks = len(files)
    number_of_pilots = len(pilot_list)

    print(f"We have {number_of_pilots} pilots to find tracks for, and {number_of_tracks} tracks")

    FlightParsingConfig = igc_parsing_config_from_yaml(task.igc_config_file)
    airspace = None if not task.airspace_check else AirspaceCheck.from_task(task)

    for file in files:
        filename = file.name

        '''check igc file is correct'''
        mytrack, error = import_igc_file(file, task, parsing_config=FlightParsingConfig, check_g_record=check_g_record)
        if error:
            '''error importing igc file'''
            print(f'Error: {filename} - {error}')
            continue

        print(f'filename {filename}, {type(filename)}')
        """check filenames to find pilots"""
        pilot = lib.get_pilot_from_list(filename, pilot_list)
        if not pilot:
            print(f'No pilot to associate with {filename}, or pilot already has a track.')
            continue

        """found a pilot for the track file. dropping pilot from list and creating track obj"""
        pilot_list[:] = [d for d in pilot_list if d.par_id != pilot.par_id]

        """pilot is registered and has no valid track yet
        moving file to correct folder and adding to the list of valid tracks"""
        tracks_processed += 1
        print(f"Track {tracks_processed}|counter")
        pilot.track_file = save_igc_file(file, task.file_path, task.date, pilot.name, pilot.ID)

        print(f"processing {pilot.ID} {pilot.name}:")
        if user:
            pilot_print = partial(print_to_sse, id=pilot.par_id, channel=user)
            print('***************START*******************')
        else:
            pilot_print = print
        check_flight(pilot, mytrack, task, airspace, print=pilot_print)
        if pilot.notifications:
            print(f"NOTES:<br /> {'<br />'.join(n.comment for n in pilot.notifications)}")

        pilots_to_save.append(pilot)
        data = track_result_output(pilot, task.task_id)
        pilot_print(f'{json.dumps(data)}|result')
        print(f"{tracks_processed}/{number_of_tracks}|track_counter")
        print('***************END****************')
        if tracks_processed > number_of_pilots:
            '''all pilots have a track'''
            break
    print("*******************processed all tracks**********************")

    '''save all successfully processed pilots to database'''
    update_all_results([p for p in pilots_to_save], task_id)


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
        track_id = db.query(R.track_id).filter(and_(R.par_id == par_id, R.task_id == task_id)).scalar()
    if track_id == 0:
        """No result found"""
        print(f"Pilot with ID {par_id} has not been scored yet on task ID {task_id} \n")
    return track_id


def read_tracklog_map_result_file(par_id: int, task_id: int):
    """create task and track objects"""
    from pathlib import Path
    import jsonpickle

    res_path = Path(MAPOBJDIR, 'tracks', str(task_id))
    filename = f'{par_id}.track'
    fullname = Path(res_path, filename)
    # if the file does not exist
    if not Path(fullname).is_file():
        create_tracklog_map_result_file(par_id, task_id)
    with open(fullname, 'r') as f:
        return jsonpickle.decode(f.read())


def create_tracklog_map_result_file(par_id: int, task_id: int):
    from airspace import AirspaceCheck
    from pilot import flightresult
    from task import Task

    task = Task.read(task_id)
    airspace = None if not task.airspace_check else AirspaceCheck.from_task(task)
    pilot = flightresult.FlightResult.read(par_id, task_id)
    file = Path(task.file_path, pilot.track_file)
    '''load track file'''
    flight = Track.process(file, task)
    if flight:
        check_flight(pilot, flight, task, airspace)


def get_task_fullpath(task_id: int):
    from pathlib import Path

    from db.tables import TblCompetition as C
    from db.tables import TblTask as T

    with db_session() as db:
        q = db.query(T.task_path, C.comp_path).join(C, C.comp_id == T.comp_id).filter(T.task_id == task_id).one()
    return Path(TRACKDIR, q.comp_path, q.task_path)


def get_unscored_pilots(task_id: int, track_source=None):
    """Gets list of registered pilots that still do not have a result
    Input:  task_id INT task database ID
    Output: list of Pilot obj."""
    from db.tables import UnscoredPilotView as U
    from pilot.flightresult import FlightResult

    pilot_list = []
    with db_session() as db:
        results = db.query(U).filter_by(task_id=task_id)
        if track_source == 'xcontest':
            results = results.filter(U.xcontest_id.isnot(None))
        elif track_source == 'flymaster':
            results = results.filter(U.live_id.isnot(None))
        results = results.all()
        for p in results:
            pilot = FlightResult()
            p.populate(pilot)
            pilot_list.append(pilot)
    return pilot_list


def get_pilot_from_list(filename: str, pilots: list):
    """check filename against a list of Pilot Obj.
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
    filename_check = dict(
        name=r"[a-zA-Z']+", id=r'[\d]+', fai=r'[\da-zA-Z]+', civl=r'[\d]+', live=r'[\da-zA-Z]+', other=r"[a-zA-Z0-9']+"
    )
    format_list = [re.findall(r'[\da-zA-Z]+', el) for el in filename_formats]

    string = Path(filename).stem
    '''testing before against preferred format: Pilot ID as last element, string.ID.igc'''
    if string.split('.')[-1].isdigit():
        pilot = next((p for p in pilots if p.ID == int(string.split('.')[-1])), None)
        if pilot:
            print(f'found {pilot.ID} {pilot.name} using ID in filename')
            return pilot
    '''Get string'''
    elements = re.findall(r"[\d]+|[a-zA-Z']+", string)
    num_of_el = len(elements)
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
                        pilot = next((p for p in pilots if getattr(p, a) == v), None)
                        if pilot:
                            print(f'{a}, found {pilot.name}')
                            return pilot
                else:
                    '''no unique id in filename, using name'''
                    names = [str(elements[idx]).lower() for idx, val in enumerate(f) if val == 'name']
                    pilot = next((p for p in pilots if all(n in p.name.lower().split() for n in names)), None)
                    if pilot:
                        print(f'using name, found {pilot.name}')
                        '''we found a pilot'''
                        return pilot
    return None


def validate_G_record(igc_filename):
    """validates g record by passing the file to a validation server.
    Assumption is that the protocol is the same as the FAI server (POST)
    :argument igc_filename (full path and filename of igc_file)
    :returns PASSED, FAILED or ERROR"""
    from Defines import G_Record_validation_Server
    from requests import post

    try:
        with open(igc_filename, 'rb') as igc:
            file = {'igcfile': igc}
            r = post(G_Record_validation_Server, files=file)
            if r.json()['result'] in ('PASSED', 'FAILED'):
                return r.json()['result']
            else:
                return 'ERROR'
    except IOError:
        print(f"Could not read file:{igc_filename}")
        return 'ERROR'


def igc_parsing_config_from_yaml(yaml_filename):
    """reads the settings from a YAML file and creates a
    new FlightParsingConfig object for use when processing track files"""

    if yaml_filename[:-5].lower != '.yaml':
        yaml_filename = yaml_filename + '.yaml'
    yaml_config = read_igc_config_yaml(yaml_filename)
    if yaml_config is None:
        return None

    config = FlightParsingConfig()
    yaml_config.pop('editable', None)
    yaml_config.pop('description', None)
    yaml_config.pop('owner', None)
    for setting in yaml_config:
        setattr(config, setting, yaml_config[setting])
    return config


def read_igc_config_yaml(yaml_filename):
    import ruamel.yaml

    yaml = ruamel.yaml.YAML()
    full_filename = Path(IGCPARSINGCONFIG, yaml_filename)
    try:
        with open(full_filename) as fp:
            return yaml.load(fp)
    except IOError:
        return None


def save_igc_config_yaml(yaml_filename, yaml_data):
    import ruamel.yaml

    yaml = ruamel.yaml.YAML()
    full_filename = Path(IGCPARSINGCONFIG, yaml_filename)
    try:
        with open(full_filename, 'w') as fp:
            yaml.dump(yaml_data, fp)
    except IOError:
        return None
    return True


def create_igc_filename(file_path: str, date, pilot_name: str, pilot_id: int = None) -> Path:
    """creates a name for the track
    name_surname_date_time_index.igc
    if we use flight date then we need an index for multiple tracks"""
    import glob

    if not Path(file_path).is_dir():
        Path(file_path).mkdir(mode=0o755)
    pname = remove_accents('_'.join(pilot_name.replace('_', ' ').replace("'", ' ').lower().split()))
    index = str(len(glob.glob(file_path + '/' + pname + '*.igc')) + 1).zfill(2)
    if pilot_id:
        filename = '_'.join([pname, str(date), index]) + f'.{pilot_id}.igc'
    else:
        filename = '_'.join([pname, str(date), index]) + '.igc'
    fullname = Path(file_path, filename)
    return fullname


def import_igc_file(file, task, parsing_config, check_g_record=False) -> Track or str:
    from calcUtils import epoch_to_date
    if check_g_record:
        print('Checking G-Record...')
        validation = validate_G_record(file)
        if validation == 'FAILED':
            return False, {'code': 'g_record_fail', 'text': f'G-Record not valid'}
        elif validation == 'ERROR':
            return False, {'code': 'g_record_error', 'text': f'Error trying to validate G-Record'}

    flight = Track.process(filename=file, task=task, config=parsing_config)

    '''check flight'''
    if not flight:
        return (False,
                {'code': 'track_error',
                 'text': f"Track is not a valid track file, pilot not found in competition "
                         f"or pilot already has a track"})
    elif not flight.valid:
        return (False,
                {'code': 'valid_fail',
                 'text': f"IGC does not meet quality standard set by igc parsing config. "
                         f"Notes: {'; '.join(flight.notes)}"})

    elif not epoch_to_date(flight.date_timestamp) == task.date:
        return False, {'code': 'track_error', 'text': f"track has a different date from task"}

    return flight, None


def check_flight(result: FlightResult, track: Track, task, airspace=None, print=print):
    if task.airspace_check and not airspace:
        print(f'should not be here')
        airspace = AirspaceCheck.from_task(task)
    '''check flight against task'''
    result.check_flight(track, task, airspace_obj=airspace, print=print)
    '''create map file'''
    result.save_tracklog_map_file(task, track)
    # '''save to database'''
    # save_track(result, task.id)


def save_igc_file(file, task_path: str, task_date, pilot_name, pid: int = None) -> str:
    from shutil import copyfile
    fullname = create_igc_filename(task_path, task_date, pilot_name, pid)
    if isinstance(file, (Path, str)):
        copyfile(file, fullname)
    else:
        file.save(fullname)
    return Path(fullname).name
