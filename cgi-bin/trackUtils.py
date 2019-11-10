"""
Module for operations on tracks
Use:    import trackUtils
        pilPk = compUtils.get_track_pilot(filename)

Antonio Golfari - 2018
"""

import os
from flight_result import Flight_result
from track import Track
from trackDB import read_formula
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

def get_non_scored_pilots(tasPk, xcontest=False):
    """Gets list of registered pilots that still do not have a result"""
    where = ""
    pilot_list = []
    if xcontest:
        where = " AND `pilXContestUser` IS NOT NULL AND `pilXContestUser` <> ''"
    if tasPk:
        with Database() as db:
            query = """    SELECT
                                `R`.`pilPk`,
                                `P`.`pilFirstName`,
                                `P`.`pilLastName`,
                                `P`.`pilFAI`,
                                `P`.`pilXContestUser`
                            FROM
                                `tblRegistration` `R`
                            JOIN `PilotView` `P` USING(`pilPk`)
                            LEFT OUTER JOIN `ResultView` `S` ON
                                `S`.`pilPk` = `P`.`pilPk` AND `S`.`tasPk` = %s
                            WHERE
                                `R`.`comPk` =(
                                SELECT
                                    `comPk`
                                FROM
                                    `TaskView`
                                WHERE
                                    `tasPk` = %s
                                LIMIT 1
                            ) AND `S`.`traPk` IS NULL""" + where
            params = [tasPk, tasPk]
            pilot_list = db.fetchall(query, params)

            if pilot_list is None: print(f"No pilots without tracks found registered to the comp...")
    else:
        print(f"Registered List - Error: NOT a valid Comp ID \n")

    return pilot_list

def get_pilot_from_list(filename, list):
    """check filename against a list of pilots"""
    pilot_id = 0
    fullname = None
    """Get string"""
    fields = os.path.splitext(filename)
    if fields[0].isdigit():
        """Gets pilot ID from FAI n."""
        fai = fields[0]
        print(f"file {filename} contains FAI n. {fai} \n")
        for row in list:
            if fai == row['pilFAI']:
                print("found a FAI number")
                pilot_id = row['pilPk']
                fullname = row['pilFirstName'].lower() + '_' + row['pilLastName'].lower()
                break
    else:
        """Gets pilot ID from XContest User or name."""
        names = fields[0].replace('.', ' ').replace('_', ' ').replace('-', ' ').split()
        """try to find xcontest user in filename
        otherwise try to find pilot name from filename"""
        print ("file {} contains pilot name \n".format(fields[0]))
        for row in list:
            print("XC User: {} | Name: {} {} ".format(row['pilXContestUser'], row['pilFirstName'], row['pilLastName']))
            if (row['pilXContestUser']is not None
                    and any(row['pilXContestUser'].lower() in str(name).lower() for name in names)):
                print ("found a xcontest user")
                pilot_id = row['pilPk']
                fullname = row['pilFirstName'].lower() + '_' + row['pilLastName'].lower()
                break
            elif (any(row['pilFirstName'].lower() in str(name).lower() for name in names)
                    and any(row['pilLastName'].lower() in str(name).lower() for name in names)):
                print ("found a pilot name")
                pilot_id = row['pilPk']
                fullname = row['pilFirstName'].lower() + '_' + row['pilLastName'].lower()
                break

    return pilot_id, fullname


def get_pil_track(pilPk, tasPk):
    """Get pilot result in a given task"""
    traPk = 0

    query = """     SELECT
                        `traPk`
                    FROM
                        `ResultView`
                    WHERE
                        `pilPk` = %s
                        AND `tasPk` = %s
                    LIMIT 1"""
    params = [pilPk, tasPk]

    with Database() as db:
        if db.rows(query, params) > 0:
            traPk = db.fetchone(query, params)['traPk']

    if traPk == 0:
        """No result found"""
        print(f"Pilot with ID {pilPk} has not been scored yet on task ID {tasPk} \n")

    return traPk

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
    #formula = read_formula(task.comp_id)
    formula = For.Task_formula.read(task_id)
    track = Track.read_db(track_id)
    lib = For.get_formula_lib(formula.type)
    result = flight_result.Flight_result.check_flight(track.flight, task, lib.parameters, 5)
    result.save_result_file(result.to_geojson_result(track, task), str(track_id))
