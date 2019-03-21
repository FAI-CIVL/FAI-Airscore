import json, sys
from myconn import Database

def get_area_wps(task_id):
    """query db get all wpts names and pks for region of task and put into dictionary"""
    with Database() as db:
        query = ("""SELECT regPk FROM `tblTask` 
                  WHERE tasPk = '{}' LIMIT 1""".format(task_id))
        region = 0 + db.fetchone(query)['regPk']
        query = """ SELECT rwpName, rwpPk FROM `tblRegionWaypoint` 
                    WHERE regPk = '{}' AND rwpOld = '0' ORDER BY rwpName""".format(region)
        wps = dict()
        for row in db.fetchall(query):
            wps[row['rwpName']] = row['rwpPk'] 
#         wps = dict((rwpName, rwpPk)
#                           for rwpName, rwpPk in db.fetchall(query))
    return wps  

def update_times(task_id, startzulu, deadlinezulu):
    """update the database with the start time and endtime. considers time offset of comp and date of task"""

    with Database() as db:
        # get the comp id to use to get time offset.
        query = ("""SELECT comPk FROM `tblTask`
                  WHERE tasPk = '{}' LIMIT 1""".format(task_id))
        comp = 0 + int(db.fetchone(query)['comPk'])

        #get the time offset    
        query = ("""SELECT comTimeOffset FROM `tblCompetition` 
                  WHERE comPk = '{}' LIMIT 1""".format(comp))
        offset = 0 + int(db.fetchone(query)['comTimeOffset'])

    startzulu_split = startzulu.split(":")  #separate hours, minutes and seconds.
    deadlinezulu_split = deadlinezulu.split(":")    #separate hours, minutes and seconds.

    startHHMM = (str(int(startzulu_split[0])+ offset) + ":" + startzulu_split[1])
    deadlineHHMM = (str(int(deadlinezulu_split[0])+ offset) + ":" + deadlinezulu_split[1])
    windowopenHHMM = (str(int(startzulu_split[0])+ offset -2) + ":" + startzulu_split[1])  #not in xctrack spec default to 2 hrs before start
    windowcloseHHMM = (str(int(startzulu_split[0])+ offset + 2) + ":" + startzulu_split[1]) #not in xctrack spec default to 2 hrs after start

    with Database() as db:
        sql = ("""   UPDATE
                        tblTask
                    SET
                        tasStartTime = DATE_ADD(
                            tasDate,
                            INTERVAL '{}' HOUR_MINUTE
                        ),
                        tasFinishTime = DATE_ADD(
                            tasDate,
                            INTERVAL '{}' HOUR_MINUTE
                        ),
                        tasTaskStart = DATE_ADD(
                            tasDate,
                            INTERVAL '{}' HOUR_MINUTE
                        ),
                        tasStartCloseTime = DATE_ADD(
                            tasDate,
                            INTERVAL '{}' HOUR_MINUTE
                        )
                    WHERE
                        tasPk = {} """.format(startHHMM, deadlineHHMM, windowopenHHMM, windowcloseHHMM, task_id))
        #update start and deadline
        db.execute(sql)

def delete_task_waypoints(task_id):
    with Database() as db:
        query = ("""DELETE FROM `tblTaskWaypoint` 
                    WHERE tasPk = {}""".format(task_id))
        db.execute(query)

def main():
    print("starting..")
    """Main module. Takes tasPk and filename as parameters"""
    task_id = 0
    wpNum = 1 #one or zero start??? 

    ##check parameter is good.
    if len(sys.argv)==3 and sys.argv[1].isdigit():
        task_id = sys.argv[1]
        task_file = sys.argv[2]
    task_id = int(task_id)
    #a little bit of checking
    if task_file[-6:] != '.xctsk':
        print('File is not a .xctsk file')
        exit()

    #'/home/stu/Documents/xcontest_lega/task/saved_task_2018-05-05.xctsk'
    with open(task_file, encoding='utf-8') as json_data:
        #a bit more checking..
        print("file: ", task_file)
        try:
            t = json.load(json_data)
        except:
            Print("file is not a valid JSON object")
            exit()

    #query db get all wpts for region of comp name and pk put into dictionary
    waypoint_list = get_area_wps(task_id) 
    startopen = t['sss']['timeGates'][0]
    deadline = t['goal']['deadline']

    update_times(task_id, startopen, deadline)
    delete_task_waypoints(task_id)

    for tp in t['turnpoints'][:-1]:  #loop through all waypoints except last one which is always goal
        waytype = "waypoint"
        shape = "circle"
        how = "entry"  #default entry .. looks like xctrack doesn't support exit cylinders apart from SSS
        wpID = waypoint_list[tp["waypoint"]["name"]]

        if 'type' in tp :
            if tp['type'] == 'TAKEOFF':
                waytype = "launch"  #live
                #waytype = "start"  #aws
                how = "exit"
            elif tp['type'] == 'SSS':
                waytype = "speed"
                if t['sss']['direction'] == "EXIT":  #get the direction form the SSS section
                    how = "exit"
            elif tp['type'] == 'ESS':
                waytype = "endspeed"

        #print("insert into tblTaskWaypoint (tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius) values (",task_id,", ",wpID,", ",wpNum,", ",waytype,", ",how,", ",shape ," , 0 , ",tp["radius"],")")
        with Database() as db:
            sql = ("""   INSERT INTO tblTaskWaypoint(
                        tasPk,
                        rwpPk,
                        tawNumber,
                        tawType,
                        tawHow,
                        tawShape,
                        tawTime,
                        tawRadius
                    )
                    VALUES({},{},{},'{}','{}','{}','0',{})""".format(task_id, wpID, wpNum, waytype, how, shape, tp["radius"]))
#             sql = "insert into tblTaskWaypoint (tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius) values (%d, %d, %d, '%s', '%s', '%s' , 0 , %d);" % (task_id, wpID, wpNum, waytype, how, shape, tp["radius"])
            db.execute(sql)
        wpNum += 1

    #goal - last turnpoint
    goal = t['turnpoints'][-1]
    waytype = "goal"
    if t['goal']['type'] == 'LINE':
        shape = "line"
    #print("insert into tblTaskWaypoint (tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius) values (",task_id,", ",wpID,", ",wpNum,", ",waytype,", 'entry', ",shape ," , 0 , ",tp["radius"],")")
    with Database() as db:
        sql = ("""   INSERT INTO tblTaskWaypoint(
                        tasPk,
                        rwpPk,
                        tawNumber,
                        tawType,
                        tawHow,
                        tawShape,
                        tawTime,
                        tawRadius
                    )
                    VALUES({},{},{},'{}','entry','{}','0',{})""".format(task_id, wpID, wpNum, waytype, shape, goal["radius"]))
      
#         insert into tblTaskWaypoint (tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius) values (%d, %d, %d, '%s', 'entry', '%s' , 0 , %d);" % (task_id, wpID, wpNum, waytype, shape, goal["radius"])
        db.execute(sql)

if __name__== "__main__":
    main()