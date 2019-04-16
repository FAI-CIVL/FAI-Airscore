"""
Module for operations on tracks
Use:    import trackUtils
        pilPk = compUtils.get_track_pilot(filename)

Antonio Golfari - 2018
"""

import os, sys
from shutil import copyfile
import datetime

import pwc
from track import Track
from task import Task
from flight_result import Flight_result

# Use your utility module.
from myconn import Database

def import_track(track, test = 0):
    result = ''
    result += track.add(test)
    result += ("Track {} added for Pilot with ID {} for task with ID {} \n".format(track.filename, track.pilPk, track.tasPk))

    if test:
        print (result)

def verify_track(track, task, test = 0):
    task_result = Flight_result.check_flight(track.flight, task, pwc.parameters, 5) #check flight against task with min tolerance of 5m
    task_result.store_result(track.traPk, task.tasPk)

def get_non_scored_pilots(tasPk, test=0):
    """Gets list of registered pilots that still do not have a result"""
    message = ''
    list = []
    if tasPk:
        with Database() as db:
            query = ("""    SELECT
                                R.`pilPk`,
                                P.`pilFirstName`,
                                P.`pilLastName`,
                                P.`pilFAI`,
                                P.`pilXContestUser`
                            FROM
                                `tblRegistration` R
                            JOIN `tblPilot` P USING(`pilPk`)
                            LEFT OUTER JOIN `tblResult` S ON
                                S.`pilPk` = P.`pilPk` AND S.`tasPk` = {0}
                            WHERE
                                R.`comPk` =(
                                SELECT
                                    `comPk`
                                FROM
                                    `tblTaskView`
                                WHERE
                                    `tasPk` = {0}
                                LIMIT 1
                            ) AND S.`traPk` IS NULL""".format(tasPk))
            message += ("Query: {}  \n".format(query))
            if db.rows(query) > 0:
                """create a list from results"""
                message += ("creating a list of pilots...")
                list = [{   'pilPk': row['pilPk'],
                            'pilFirstName': row['pilFirstName'],
                            'pilLastName': row['pilLastName'],
                            'pilFAI': row['pilFAI'],
                            'pilXContestUser': row['pilXContestUser']}
                        for row in db.fetchall(query)]
            else:
                message += ("No pilot found registered to the comp...")
    else:
        message += ("Registered List - Error: NOT a valid Comp ID \n")

    if test:
        """TEST MODE"""
        print (message)

    return (list)

def get_pilot_from_list(filename, list, test=0):
    """check filename against a list of pilots"""
    message = ''
    pilot_id = 0
    """Get string"""
    fields = os.path.splitext(filename)
    if fields[0].isdigit():
        """Gets pilot ID from FAI n."""
        fai = 0 + int(fields[0])
        print ("file {} contains FAI n. {} \n".format(filename, fai))
        for row in list:
            if fai == row['pilFAI']:
                print ("found a FAI number")
                pilot_id = row['pilPk']
                break
    else:
        """Gets pilot ID from XContest User or name."""
        names = fields[0].replace('.', ' ').replace('_', ' ').replace('-', ' ').split()
        if test:
            print ("filename: {} - parts: \n".format(filename))
            print (', '.join(names))
        """try to find xcontest user in filename
        otherwise try to find pilot name from filename"""
        print ("file {} contains pilot name \n".format(fields[0]))
        for row in list:
            print("XC User: {} | Name: {} {} ".format(row['pilXContestUser'], row['pilFirstName'], row['pilLastName']))
            if (row['pilXContestUser']is not None
                    and any(row['pilXContestUser'].lower() in str(name).lower() for name in names)):
                print ("found a xcontest user")
                pilot_id = row['pilPk']
                break
            elif (any(row['pilFirstName'].lower() in str(name).lower() for name in names)
                    and any(row['pilLastName'].lower() in str(name).lower() for name in names)):
                print ("found a pilot name")
                pilot_id = row['pilPk']
                break

    if test:
        print('pilot ID: {}'.format(pilot_id))

    return pilot_id


def get_pil_track(pilPk, tasPk, test=0):
    """Get pilot result in a given task"""
    message = ''
    traPk = 0

    query = ("""    SELECT
                        traPk
                    FROM
                        tblResult
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
