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

import os, sys
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
    if len(sys.argv) > 3:
        """Get tasPk"""
        tasPk = 0 + int(sys.argv[1])
        """Get file"""
        file = sys.argv[2]
        """get pilot"""
        pilPk = 0 + int(sys.argv[3])

        if len(sys.argv) > 4:
            """Test Mode"""
            print('Running in TEST MODE')
            test = 1

        if get_pil_track(mytrack.pilPk, tasPk, test):
            """pilot has already been scored"""
            message += ("Pilot with ID {} has already a valid track for task with ID {} \n".format(mytrack.pilPk, task_id))
        else:
            """Get Task object"""
            task = Task.read_task(tasPk)
            if task.ShortRouteDistance == 0:
                print('task not optimised.. optimising')
                task.calculate_optimised_task_length()

            if task.comPk > 0:
                """import track"""
                filename = os.path.basename(file)
                mytrack = Track.read_file(filename=file, pilot_id=pilPk, test=test)

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
                    mytrack.copy_track_file(test)
                    message += ("pilot {} associated with track {} \n".format(mytrack.pilPk, mytrack.filename))
                    """adding track to db"""
                    import_track(track, test)
                    message += ("track imported to database with ID {}\n".format(mytrack.traPk))
                    """checking track against task"""
                    verify_track(track, task, test)
                    message += ("track {} verified with task {}\n".format(mytrack.traPk, mytrack.tasPk))
                    result += ("track correctly imported and results generated \n".format(mytrack.traPk, mytrack.tasPk))

            else:
                result = ("error: task ID {} does NOT belong to any Competition \n".format(tasPk))

    else:
        print('error: Use: python3 track_reader.py [tasPk] [file] [pilPk] [opt. test]')

    print (result)

if __name__ == "__main__":
    main()
