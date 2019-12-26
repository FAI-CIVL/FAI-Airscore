"""
Reads a track file
should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc
Use: python3 track_reader.py [tasPk] [file] [parPk]

Antonio Golfari - 2018
"""
# Use your utility module.
from compUtils import *
from trackUtils import *
from track import Track
from tempfile import TemporaryDirectory
from shutil import copyfile
from formula import Task_formula, get_formula_lib

import io, os, sys
from os import path
from os.path import isfile
from task import Task
from flight_result import Flight_result
from logger import Logger


def main(args):
    """Main module"""
    '''create logging and disable output'''
    Logger('ON', 'track_reader.txt')

    print("starting..")
    '''Main module. Takes tasPk, tempfile, filename and pil_id as parameters'''

    out = 0
    """Get tasPk"""
    task_id = 0 + int(args[0])
    """Get file"""
    tempfile = str(args[1])
    """Get filename"""
    filename = str(args[2])
    """get pilot"""
    par_id = 0 + int(args[3])

    '''create logging and disable output'''
    Logger('ON', 'track_reader.txt')

    print(f'track_reader:')
    print(f'     file: {tempfile}')
    print(f'     filename: {filename}')
    print(f'     pilot: {par_id}')
    print(f'     task: {task_id}')

    """create a temporary directory"""
    with TemporaryDirectory() as trackdir:
        file = path.join(trackdir, filename)
        copyfile(tempfile, file)

        if get_pil_track(par_id, task_id):
            """pilot has already been scored"""
            print(f"Pilot with ID {par_id} has already a valid track for task with ID {task_id} \n")
        else:
            """Get Task object"""
            task = Task.read(task_id)
            if task.opt_dist == 0:
                print('task not optimised.. optimising')
                task.calculate_optimised_task_length()

            if task.comp_id > 0:
                """import track"""
                mytrack = Track.read_file(filename=file, pilot_id=par_id)
                """check result"""
                if not mytrack:
                    print(f"Track {filename} is not a valid track file \n")
                elif not mytrack.date == task.date:
                    print(f"track {filename} has a different date from task day \n")
                else:
                    """pilot is registered and has no valid track yet
                    moving file to correct folder and adding to the list of valid tracks"""
                    mytrack.task_id = task.id
                    mytrack.copy_track_file()
                    print(f"pilot {mytrack.par_id} associated with track {mytrack.filename} \n")
                    """adding track to db"""
                    import_track(mytrack)
                    print(f"track imported to database with ID {mytrack.traPk}\n")
                    """checking track against task"""
                    formula = Task_formula.read(task_id)
                    lib = get_formula_lib(formula.type)
                    verify_track(mytrack, task, lib)
                    print(f"track {mytrack.traPk} verified with task {mytrack.task_id}\n")
                    print("track correctly imported and results generated \n")
                    out = (f"traPk={mytrack.traPk}")

            else:
                print(f"error: task ID {task_id} does NOT belong to any Competition \n")

    ''' now restore stdout function '''
    Logger('OFF')

    print(f"{out}")


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1]
            and sys.argv[1].isdigit()
            and int(sys.argv[1]) > 0
            and len(sys.argv) > 4):
        print("number of arguments != 1 and/or task_id not a number")
        print("usage: track_reader.py [tasPk] [tempfile] [filename] [parPk]")
        exit()

    main(sys.argv[1:])
