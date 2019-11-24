"""
Module for operations on tracks
Use:    import trackUtils
        pilPk = compUtils.get_track_pilot(filename)

Antonio Golfari - 2018
"""

import os
from flight_result import Flight_result
from track import Track
import formula as For
import Defines

# Use your utility module.
from myconn import Database

def extract_tracks(file, dir):
    """gets tracks from a zipfile"""
    from os.path import isfile
    from zipfile import ZipFile

    error = 0
    """Check if file exists"""
    if isfile(file):
        print('extracting: ' + file + ' in temp dir: ' + dir + ' \n')
        """Create a ZipFile Object and load file in it"""
        with ZipFile(file, 'r') as zipObj:
            """Extract all the contents of zip file in temporary directory"""
            zipObj.extractall(dir)
    else:
        print(f"reading error: {file} does not exist or is not a zip file \n")
        error = 1

    return error

def get_tracks(dir):
    """Checks files and imports what appear to be tracks"""
    files = []

    print(f"Directory: {dir} \n")
    print(f"Looking for files \n")

    """check files in temporary directory, and get only tracks"""
    for file in os.listdir(dir):
        print(f"checking: {file} \n")
        if ( (not (file.startswith(".") or file.startswith("_"))) and file.lower().endswith(".igc")):
            """file is a valid track"""
            print(f"valid filename: {file} \n")
            """add file to tracks list"""
            files.append(os.path.join(dir, file))
        else:
            print(f"NOT valid filename: {file} \n")

    print(f"files in list: {len(files)} \n")
    for f in files:
        print(f"  {f} \n")

    return files

def assign_and_import_tracks(files, task, xcontest=False):
    """Find pilots to associate with tracks"""
    from compUtils import get_registration, get_task_file_path

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
        pilot_list = get_non_scored_pilots(task_id, xcontest)

    track_path = get_task_file_path(task_id, comp_id)

    #print("found {} tracks \n".format(len(files)))
    for file in files:
        mytrack = None
        filename = os.path.basename(file)
        if registration:
            if len(pilot_list) > 0:
                print(f"checking {filename} against {len(pilot_list)} pilots... \n")
                """check filenames to find pilots"""
                pilot_id, full_name = get_pilot_from_list(filename, pilot_list)
                if pilot_id:
                    """found a pilot for the track file.
                    dropping pilot from list and creating track obj"""
                    print(f"Found a pilot to associate with file. dropping {pilot_id} from non scored list \n")
                    pilot_list[:] = [d for d in pilot_list if d.get('pilPk') != pilot_id]
                    mytrack = Track.read_file(filename=file, pilot_id=pilot_id)
        else:
            """We add track if we find a pilot in database
            that has not yet been scored"""
            mytrack = Track.read_file(filename=file)
            if get_pil_track(mytrack.pilPk, task_id):
                """pilot has already been scored"""
                print(f"Pilot with ID {mytrack.pilPk} has already a valid track for task with ID {task_id} \n")
                mytrack = None
        """check result"""
        if not mytrack:
            print(f"Track {filename} is not a valid track file \n")
        elif not mytrack.date == task_date:
            print(f"track {filename} has a different date from task \n")
        else:
            """pilot is registered and has no valid track yet
            moving file to correct folder and adding to the list of valid tracks"""
            mytrack.task_id = task_id
            mytrack.copy_track_file(task_path=track_path, pname=full_name)
            print(f"pilot {mytrack.pilPk} associated with track {mytrack.filename} \n")
            import_track(mytrack)
            verify_track(mytrack, task)

def import_track(track):
    track.add()

def verify_track(track, task):

    formula = For.Task_formula.read(task.id)
    lib = formula.get_lib()
    task_result = Flight_result.check_flight(track.flight, task, lib.parameters, 5) #check flight against task with min tolerance of 5m
    task_result.store_result(track.traPk, task.id)
    print(track.flight.notes)

def get_non_scored_pilots(task_id, xcontest=False):
    """Gets list of registered pilots that still do not have a result"""
    from db_tables import tblRegistration as R, tblTaskResult as S, tblTask as T
    from sqlalchemy import func, and_, or_

    with Database() as db:

        comp_id = db.session.query(T).get(task_id).comPk
        q       = (db.session.query(R.pilPk.label('pil_id'),
                                    func.lower(R.regName).label('name'), R.regFAI.label('fai'),
                                    R.regXC.label('xcontest')).outerjoin(
                                    S, and_(R.pilPk==S.pilPk, S.tasPk==task_id))).filter(and_(R.comPk==comp_id, S.tarPk==None))
        if xcontest:
            q = q.filter(R.regXC!=None)
        pilot_list = q.all()
    if pilot_list is None: print(f"No pilots without tracks found registered to the comp...")

    return pilot_list

def get_pilot_from_list(filename, pilots):
    """check filename against a list of pilots"""
    pilot_id = 0
    fullname = None
    """Get string"""
    fields = os.path.splitext(filename)
    if fields[0].isdigit():
        """Gets pilot ID from FAI n."""
        fai = fields[0]
        print(f"file {filename} contains FAI n. {fai} \n")
        for p in pilots:
            if fai == p.fai:
                print("found a FAI number")
                pilot_id = p.pil_id
                fullname = p.name.replace(' ', '_')
                break
    else:
        """Gets pilot ID from XContest User or name."""
        names = fields[0].replace('.', ' ').replace('_', ' ').replace('-', ' ').lower().split()
        """try to find xcontest user in filename
        otherwise try to find pilot name from filename"""
        print ("file {} contains pilot name \n".format(fields[0]))
        for p in pilots:
            print(f"XC User: {p.xcontest} | Name: {p.name}")
            if (p.xcontest is not None
                    and any(p.xcontest.lower() in str(name).lower() for name in names)):
                print ("found a xcontest user")
                pilot_id = p.pil_id
                fullname = p.name.replace(' ', '_')
                break
            elif all(n in names for n in p.name.split()):
                print ("found a pilot name")
                pilot_id = p.pil_id
                fullname = p.name.replace(' ', '_')
                break

    return pilot_id, fullname

def find_pilot(name):
    """Get pilot from name or fai
    info comes from FSDB file, as FsParticipant attributes, or from igc filename
    Not sure about best strategy to retrieve pilots ID from name and FAI n.
    """
    from db_tables import PilotView as P
    from sqlalchemy import and_, or_

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
        # q   = db.session.query(P.pilPk).filter(and_(P.pilLastName==func.any(names), P.pilFirstName==func.any(names)))
        t   = db.session.query(P.pilPk)
        if names:
            q = t.filter(P.pilLastName.in_(names))
            p = q.filter(P.pilFirstName.in_(names))
        else:
            p = t.filter(P.pilFAI==fai)
        pil = p.all()
        if len(pil) == 1: return pil.pop().pilPk
        '''try one more time if we have both names and fai'''
        if fai and names:
            if pil == []: p = q         # if we have zero results, try with only lastname and fai
            pil = p.filter(P.pilFAI==fai).all()
            if len(pil) == 1: return pil.pop().pilPk
    return None

def get_pil_track(pil_id, task_id):
    """Get pilot result in a given task"""
    from db_tables import tblTaskResult as R
    from sqlalchemy import func, and_, or_
    track_id = 0

    with Database() as db:
        track_id = db.session.query(R.tarPk).filter(
                                and_(R.pilPk==pil_id, R.tasPk==task_id)).scalar()

    if track_id == 0:
        """No result found"""
        print(f"Pilot with ID {pil_id} has not been scored yet on task ID {task_id} \n")

    return track_id

def read_result_file(track_id, task_id):
    """create task and track objects"""
    import jsonpickle
    from pathlib import Path

    res_path = Defines.MAPOBJDIR + 'tracks/'
    filename = 'result_' + str(track_id) + '.json'
    fullname = os.path.join(res_path, filename)
    # if the file exists
    if not Path(fullname).is_file():
        create_result_file(track_id, task_id)

    with open(fullname, 'r') as f:
        return jsonpickle.decode(f.read())

def create_result_file(track_id, task_id):
    import flight_result
    from task import Task

    task = Task.read(task_id)
    formula = For.Task_formula.read(task_id)
    track = Track.read_db(track_id)
    lib = For.get_formula_lib(formula.type)
    result = flight_result.Flight_result.check_flight(track.flight, task, lib.parameters, 5)
    result.save_result_file(result.to_geojson_result(track, task), str(track_id))
