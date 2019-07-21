"""
Reads a track file
should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc
Use: python3 track_reader.py [tasPk] [file] [pilPk] [opt. test]

Antonio Golfari - 2018
"""
# Use your utility module.
from compUtils import *
from trackUtils import *
from track import Track
from tempfile import TemporaryDirectory
from shutil import copyfile
from formula import get_formula_lib
from trackDB import read_formula

import io, os, sys, logger
from os import path
from os.path import isfile
from task import Task
from flight_result import Flight_result
from logger import Logger


def main(args):
    """Main module"""
    test = 0
    result = ''
    message = ''
    logfile = 'track_reader.txt'

    """check parameter is good."""
    if len(args) < 4 or not args[0].isdigit() or not args[3].isdigit():
        print('error: Use: python3 track_reader.py [tasPk] [tempfile] [filename] [pilPk] [opt. test]')
        exit()

    """Get tasPk"""
    task_id = 0 + int(args[0])
    """Get file"""
    tempfile = args[1]
    """Get filename"""
    filename = args[2]
    """get pilot"""
    pil_id = 0 + int(args[3])

    # if len(args) > 4:
    #     """Test Mode"""
    #     test = 1
    #     print('Running in TEST MODE')
    #     print('track_reader:')
    #     print('     file: {}'.format(tempfile))
    #     print('     filename: {}'.format(filename))
    #     print('     pilot: {}'.format(pil_id))
    #     print('     task: {}'.format(task_id))
    # else:
    #     '''disable output'''
    #     text_trap = io.StringIO()
    #     sys.stdout = text_trap
    #
    '''create logging and disable output'''
    Logger('ON', 'track_reader.txt')

    # with myLogger('log', logfile) as redirector:
    print('track_reader:')
    print('     file: {}'.format(tempfile))
    print('     filename: {}'.format(filename))
    print('     pilot: {}'.format(pil_id))
    print('     task: {}'.format(task_id))

    """create a temporary directory"""
    with TemporaryDirectory() as trackdir:
        file = path.join(trackdir, filename)
        copyfile(tempfile, file)

        if get_pil_track(pil_id, task_id, test):
            """pilot has already been scored"""
            result += "Pilot with ID {} has already a valid track for task with ID {} \n".format(pil_id, task_id)
        else:
            """Get Task object"""
            task = Task.read_task(task_id)
            if task.ShortRouteDistance == 0:
                message += 'task not optimised.. optimising'
                task.calculate_optimised_task_length()

            if task.comPk > 0:
                """import track"""
                #filename = os.path.basename(file)
                mytrack = Track.read_file(filename=file, pilot_id=pil_id, test=test)

                """check result"""
                if not mytrack:
                    result += ("Track {} is not a valid track file \n".format(filename))
                elif not mytrack.date == task.date:
                    message += ("dates: {}  |  {}  \n".format(task.date, mytrack.date))
                    result += ("track {} has a different date from task day \n".format(filename))
                else:
                    """pilot is registered and has no valid track yet
                    moving file to correct folder and adding to the list of valid tracks"""
                    mytrack.tasPk = task.tasPk
                    mytrack.copy_track_file(test=test)
                    message += ("pilot {} associated with track {} \n".format(mytrack.pilPk, mytrack.filename))
                    """adding track to db"""
                    import_track(mytrack, test)
                    message += ("track imported to database with ID {}\n".format(mytrack.traPk))
                    """checking track against task"""
                    formula =  read_formula(task.comPk)
                    f = get_formula_lib(formula)
                    verify_track(mytrack, task, f)
                    message += ("track {} verified with task {}\n".format(mytrack.traPk, mytrack.tasPk))
                    result += ("track correctly imported and results generated \n")
                    result += ("traPk={}".format(mytrack.traPk))

            else:
                result = ("error: task ID {} does NOT belong to any Competition \n".format(tasPk))

    print (message)

    ''' now restore stdout function '''
    # sys.stdout = sys.__stdout__
    Logger('OFF')
    print (result)

if __name__ == "__main__":
    main(sys.argv[1:])
