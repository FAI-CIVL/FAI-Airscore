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
from task import Task


def printf(format, *args):
    sys.stdout.write(format % args)

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
