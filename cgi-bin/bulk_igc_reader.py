"""
Reads in a zip file full of .igc files
should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc
Use: python3 bulk_igc_reader.py [taskPk] [zipfile] [opt. test]

Antonio Golfari - 2018
"""
# Use your utility module.
from compUtils import *
from trackUtils import *
from track import Track

import os, sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from os.path import isfile
import pwc
from task import Task
from flight_result import Flight_result

def printf(format, *args):
    sys.stdout.write(format % args)

def extract_tracks(file, dir, test = 0):
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
        if ( (not (file.startswith(".") or file.startswith("_"))) and file.endswith(".igc") ):
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

def assign_tracks(files, task, test = 0):
    """Find pilots to associate with tracks"""
    from datetime import datetime

    message = ''
    mytracks = []
    list = []
    message += ("We have {} track to associate \n".format(len(files)))
    task_id = task.tasPk
    comp_id = task.comPk
    task_date = task.date
    """checking if comp requires a regisration.
    Then we create a list of registered pilots to check against tracks filename.
    This should be much faster than checking against all pilots in database through a query"""
    registration = get_registration(comp_id, test)
    if registration:
        """We add tracks for the registered pilots not yet scored"""
        message += "Comp with registration: files will be checked against registered pilots not yet scored \n"
        list = get_non_scored_pilots(task_id, test)
    for file in files:
        mytrack = None
        filename = os.path.basename(file)
        if registration:
            if len(list) > 0:
                message += ("checking {} against {} pilots... \n".format(filename, len(list)))
                """check filenames to find pilots"""
                pilot_id = get_pilot_from_list(filename, list, test)
                if pilot_id:
                    """found a pilot for the track file.
                    dropping pilot from list and creating track obj"""
                    message += ("Found a pilot to associate with file. dropping {} from non scored list \n".format(pilot_id))
                    list[:] = [d for d in list if d.get('pilPk') != pilot_id]
                    mytrack = Track.read_file(filename=file, pilot_id=pilot_id, test=test)
        else:
            """We add track if we find a pilot in database
            that has not yet been scored"""
            mytrack = Track.read_file(filename=file, test=test)
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
            mytrack.tasPk = task_id
            mytrack.copy_track_file(test)
            mytracks.append(mytrack)
            message += ("pilot {} associated with track {} \n".format(mytrack.pilPk, mytrack.filename))

    if test == 1:
        """TEST MODE"""
        print (message)

    return mytracks

def import_tracks(mytracks, task, test = 0):
    """Import tracks in db"""
    message = ''
    result = ''
    for track in mytracks:
        """adding track to db"""
        import_track(track, test)
        """checking track against task"""
        verify_track(track, task, test)

    if test == 1:
        """TEST MODE"""
        print (message)

    return result

def main():
    """Main module"""
    test = 0
    result = ''
    """check parameter is good."""
    if len(sys.argv) > 2:
        """Get tasPk"""
        tasPk = 0 + int(sys.argv[1])
        """Get zip filename"""
        zipfile = sys.argv[2]
        if len(sys.argv) > 3:
            """Test Mode"""
            print('Running in TEST MODE')
            test = 1

        """Get Task object"""
        task = Task.read_task(tasPk)
        if task.ShortRouteDistance == 0:
            print('task not optimised.. optimising')
            task.calculate_optimised_task_length()

        if task.comPk > 0:
            """create a temporary directory"""
            with TemporaryDirectory() as tracksdir:
                error = extract_tracks(zipfile, tracksdir, test)
                if not error:
                    """find valid tracks"""
                    tracks = get_tracks(tracksdir, test)
                    if tracks is not None:
                        """associate tracks to pilots"""
                        mytracks = assign_tracks(tracks, task, test)
                        """import tracks"""
                        result = import_tracks(mytracks, task, test)
                    else:
                        result = ("There is no valid track in zipfile {} \n".format(zipfile))
                else:
                    result = ("An error occured while dealing with file {} \n".format(zipfile))
        else:
            result = ("error: task ID {} does NOT belong to any Competition \n".format(tasPk))

    else:
        print('error: Use: python3 dbulk_igc_reader.py [taskPk] [zipfile] [opt. test]')

    print (result)

if __name__ == "__main__":
    main()
