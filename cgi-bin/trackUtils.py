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

def extract_tracks(file, dir, test = 0):
    """gets tracks from a zipfile"""
    from os.path import isfile
    from zipfile import ZipFile

    message = ''
    error = 0
    """Check if file exists"""
    if isfile(file):
        message += ('extracting: ' + file + ' in temp dir: ' + dir + ' \n')
        """Create a ZipFile Object and load file in it"""
        with ZipFile(file, 'r') as zipObj:
            """Extract all the contents of zip file in temporary directory"""
            zipObj.extractall(dir)
    else:
        message += ("reading error: {} does not exist or is not a zip file \n".format(file))
        error = 1

    if test == 1:
        """TEST MODE"""
        print (message)

    return error

def get_tracks(dir, test = 0):
    """Checks files and imports what appear to be tracks"""
    message = ''
    files = []

    message += ("Directory: {} \n".format(dir))
    message += ("Looking for files \n")

    """check files in temporary directory, and get only tracks"""
    for file in os.listdir(dir):
        message += ("checking: {} \n".format(file))
        if ( (not (file.startswith(".") or file.startswith("_"))) and file.lower().endswith(".igc")):
            """file is a valid track"""
            message += ("valid filename: {} \n".format(file))
            """add file to tracks list"""
            files.append(os.path.join(dir, file))
        else:
            message +=  ("NOT valid filename: {} \n".format(file))

    message += ("files in directory: {} \n".format(len(os.listdir(dir))))
    message += ("files in list: {} \n".format(len(files)))
    for f in files:
        message += ("  {} \n".format(f))

    if test == 1:
        """TEST MODE"""
        print (message)

    return files

def assign_and_import_tracks(files, task, xcontest=False, test = 0):
    """Find pilots to associate with tracks"""
    from compUtils import get_registration, get_task_file_path

    message = ''
    pilot_list = []
    message += ("We have {} track to associate \n".format(len(files)))
    task_id = task.id
    comp_id = task.comp_id
    task_date = task.date
    """checking if comp requires a regisration.
    Then we create a list of registered pilots to check against tracks filename.
    This should be much faster than checking against all pilots in database through a query"""
    registration = get_registration(comp_id, test)
    if registration:
        """We add tracks for the registered pilots not yet scored"""
        message += "Comp with registration: files will be checked against registered pilots not yet scored \n"
        pilot_list = get_non_scored_pilots(task_id, xcontest, test)

    track_path = get_task_file_path(task_id, comp_id)

    #print("found {} tracks \n".format(len(files)))
    for file in files:
        mytrack = None
        filename = os.path.basename(file)
        if registration:
            if len(pilot_list) > 0:
                message += ("checking {} against {} pilots... \n".format(filename, len(pilot_list)))
                """check filenames to find pilots"""
                pilot_id, full_name = get_pilot_from_list(filename, pilot_list, test)
                if pilot_id:
                    """found a pilot for the track file.
                    dropping pilot from list and creating track obj"""
                    message += ("Found a pilot to associate with file. dropping {} from non scored list \n".format(pilot_id))
                    pilot_list[:] = [d for d in pilot_list if d.get('pilPk') != pilot_id]
                    mytrack = Track.read_file(filename=file, pilot_id=pilot_id)
        else:
            """We add track if we find a pilot in database
            that has not yet been scored"""
            mytrack = Track.read_file(filename=file)
            if get_pil_track(mytrack.pilPk, task_id, test):
                """pilot has already been scored"""
                message += ("Pilot with ID {} has already a valid track for task with ID {} \n".format(mytrack.pilPk, task_id))
                mytrack = None
        """check result"""
        if not mytrack:
            message += ("Track {} is not a valid track file \n".format(filename))
        elif not mytrack.date == task_date:
            message += ("dates: {}  |  {}  \n".format(task_date, mytrack.date))
            message += ("track {} has a different date from task \n".format(filename))
        else:
            """pilot is registered and has no valid track yet
            moving file to correct folder and adding to the list of valid tracks"""
            mytrack.task_id = task_id
            mytrack.copy_track_file(task_path=track_path, pname=full_name)
            message += ("pilot {} associated with track {} \n".format(mytrack.pilPk, mytrack.filename))
            import_track(mytrack)
            verify_track(mytrack, task, test)

    if test == 1:
        """TEST MODE"""
        print (message)

def import_track(track, test = 0):
    result = ''
    result += track.add(test)
    result += ("Track {} added for Pilot with ID {} for task with ID {} \n".format(track.filename, track.pilPk, track.task_id))

    if test:
        print (result)

def verify_track(track, task, test):

    #formula = read_formula(task.comp_id)
    formula = For.Task_formula.read(task.id)

    lib = For.get_formula_lib(formula.type)
    task_result = Flight_result.check_flight(track.flight, task, lib.parameters, 5) #check flight against task with min tolerance of 5m
    task_result.store_result(track.traPk, task.id)
    print(track.flight.notes)

def get_non_scored_pilots(tasPk, xcontest=False, test=0):
    """Gets list of registered pilots that still do not have a result"""
    message = ''
    where = ""
    pilot_list = []
    if xcontest:
        where = " AND pilXContestUser is not null AND pilXContestUser <> ''"
    if tasPk:
        with Database() as db:
            query = """    SELECT
                                R.`pilPk`,
                                P.`pilFirstName`,
                                P.`pilLastName`,
                                P.`pilFAI`,
                                P.`pilXContestUser`
                            FROM
                                `tblRegistration` R
                            JOIN `PilotView` P USING(`pilPk`)
                            LEFT OUTER JOIN `ResultView` S ON
                                S.`pilPk` = P.`pilPk` AND S.`tasPk` = %s
                            WHERE
                                R.`comPk` =(
                                SELECT
                                    `comPk`
                                FROM
                                    `TaskView`
                                WHERE
                                    `tasPk` = %s
                                LIMIT 1
                            ) AND S.`traPk` IS NULL""" + where
            params = [tasPk, tasPk]
            message += ("Query: {}  \n".format(query))
            pilot_list = db.fetchall(query, params)

            if pilot_list is None: message += ("No pilots without tracks found registered to the comp...")
    else:
        message += ("Registered List - Error: NOT a valid Comp ID \n")

    if test:
        """TEST MODE"""
        print(message)

    return pilot_list

def get_pilot_from_list(filename, list, test=0):
    """check filename against a list of pilots"""
    pilot_id = 0
    fullname = None
    """Get string"""
    fields = os.path.splitext(filename)
    if fields[0].isdigit():
        """Gets pilot ID from FAI n."""
        fai = fields[0]
        print("file {} contains FAI n. {} \n".format(filename, fai))
        for row in list:
            if fai == row['pilFAI']:
                print ("found a FAI number")
                pilot_id = row['pilPk']
                fullname = row['pilFirstName'].lower() + '_' + row['pilLastName'].lower()
                break
    else:
        """Gets pilot ID from XContest User or name."""
        names = fields[0].replace('.', ' ').replace('_', ' ').replace('-', ' ').split()
        if test:
            print("filename: {} - parts: \n".format(filename))
            print(', '.join(names))
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

    if test:
        print('pilot ID: {}'.format(pilot_id))

    return pilot_id, fullname


def get_pil_track(pilPk, tasPk, test=0):
    """Get pilot result in a given task"""
    message = ''
    traPk = 0

    query = ("""    SELECT
                        traPk
                    FROM
                        ResultView
                    WHERE
                        pilPk = {}
                        AND tasPk = {}
                    LIMIT
                        1""".format(pilPk, tasPk))

    message += ("Query: {}  \n".format(query))
    with Database() as db:
        if db.rows(query) > 0:
            traPk = db.fetchone(query)['traPk']

    if traPk == 0:
        """No result found"""
        message += ("Pilot with ID {} has not been scored yet on task ID {} \n".format(pilPk, tasPk))

    if test == 1:
        """TEST MODE"""
        message += ("traPk: {}  \n".format(traPk))
        print (message)

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
