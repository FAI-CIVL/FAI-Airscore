import json, sys
from myconn import Database

def get_area_wps(task_id):
    """query db get all wpts names and pks for region of task and put into dictionary"""
    with Database() as db:
        query = ("""SELECT regPk FROM `tblTask` 
                  WHERE tasPk = '{}' LIMIT 1""".format(task_id))
        region = 0 + db.fetchone(query)['regPk']
        print ('region: {}'.format(region))
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
        sql = "update tblTask set  tasStartTime=DATE_ADD( tasDate , INTERVAL '%s' HOUR_MINUTE),  tasFinishTime=DATE_ADD( tasDate , INTERVAL '%s' HOUR_MINUTE), tasTaskStart=DATE_ADD( tasDate , INTERVAL '%s' HOUR_MINUTE), tasStartCloseTime=DATE_ADD( tasDate , INTERVAL '%s' HOUR_MINUTE) where tasPk=%s;" % (startHHMM, deadlineHHMM, windowopenHHMM, windowcloseHHMM, task_id )
        #update start and deadline
        db.execute(sql)

def delete_task_waypoints(task_id):
    with Database() as db:
        query = ("delete FROM `tblTaskWaypoint` "
                 "WHERE tasPk = %s;", (task_id,))
        db.execute(query)

def main():
    print("starting..")
    """Main module. Takes tasPk and filename as parameters"""
    task_id = 0
    wpNum = 1 #one or zero start??? 

    ##check parameter is good.
    if len(sys.argv)==2 and sys.argv[1].isdigit():
        task_id = 0 + int(sys.argv[1])

    #query db get all wpts for region of comp name and pk put into dictionary
    waypoint_list = get_area_wps(task_id)
    print (waypoint_list)
    wpID = waypoint_list['B44']
    print ("""Takeoff ID: {}""".format(wpID))


if __name__== "__main__":
    main()