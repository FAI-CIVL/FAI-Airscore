"""
Reads in a zip file full of .igc files
should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc
Use: python3 bulk_igc_reader.py <task_id> <zipfile>

Antonio Golfari - 2018
"""
from tempfile import TemporaryDirectory

# Use your utility module.
from logger import Logger
from task import Task
from trackUtils import *


def printf(format, *args):
    sys.stdout.write(format % args)


def main(args):
    """create logging and disable output"""
    # Logger('ON', 'bulk_igc_reader.txt')

    print("starting..")
    '''Main module. Takes task_id as parameter'''

    task_id = 0 + int(args[0])
    """Get zip filename"""
    zipfile = str(args[1])

    """Get Task object"""
    task = Task.read(task_id)

    if task.opt_dist == 0:
        print('task not optimised.. optimising')
        task.calculate_optimised_task_length()

    if not (task.comp_id > 0):
        print(f"error: task with ID {task_id} does NOT belong to any Competition")
        ''' restore stdout function '''
        Logger('OFF')
        print(0)
        exit()

    """create a temporary directory"""
    with TemporaryDirectory() as tracksdir:
        error = extract_tracks(zipfile, tracksdir)
        if error:
            print(f"An error occured while dealing with file {zipfile} \n")
            ''' restore stdout function '''
            # Logger('OFF')
            print(0)
            exit()
        """find valid tracks"""
        tracks = get_tracks(tracksdir)
        if tracks is None:
            print(f"There is no valid track in zipfile {zipfile} \n")
            ''' restore stdout function '''
            # Logger('OFF')
            print(0)
            exit()
        """associate tracks to pilots and import"""
        assign_and_import_tracks(tracks, task)

    ''' now restore stdout function '''
    # Logger('OFF')
    print(1)


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0 and len(sys.argv) == 3):
        print("number of arguments != 2 and/or task_id not a number")
        print("Use: python3 bulk_igc_reader.py <task_id> <zipfile>")
        exit()

    main(sys.argv[1:])
