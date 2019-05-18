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

import os, sys
from os import path
from os.path import isfile
import pwc
from task import Task
from flight_result import Flight_result


def main():
    """Main module"""
    test = 0
    result = ''
    message = ''

    """check parameter is good."""
    if len(sys.argv) < 5 or not sys.argv[1].isdigit() or not sys.argv[4].isdigit():
        print('error: Use: python3 track_reader.py [tasPk] [tempfile] [filename] [pilPk] [opt. test]')
        exit()

    """Get tasPk"""
    task_id = 0 + int(sys.argv[1])
    """Get file"""
    tempfile = sys.argv[2]
    """Get filename"""
    filename = sys.argv[3]
    """get pilot"""
    pil_id = 0 + int(sys.argv[4])

    if len(sys.argv) > 5:
        """Test Mode"""
        print('Running in TEST MODE')
        test = 1

    if test:
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
            print ("Pilot with ID {} has already a valid track for task with ID {} \n".format(pil_id, task_id))
        else:

                """Get Task object"""
                task = Task.read_task(task_id)
                if task.ShortRouteDistance == 0:
                    print('task not optimised.. optimising')
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
                        verify_track(mytrack, task, test)
                        message += ("track {} verified with task {}\n".format(mytrack.traPk, mytrack.tasPk))
                        result += ("track correctly imported and results generated \n")
                        result += ("traPk={}".format(mytrack.traPk))

                else:
                    result = ("error: task ID {} does NOT belong to any Competition \n".format(tasPk))

    print (result)

if __name__ == "__main__":
    main()
