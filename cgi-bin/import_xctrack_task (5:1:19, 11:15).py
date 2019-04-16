import json, sys

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

def get_area_wps(task_id, DB_User, DB_Password, DB):
    """query db get all wpts names and pks for region of task and put into dictionary"""
    db = pymysql.connect(user=DB_User, passwd=DB_Password, db=DB, autocommit=True)
    c = db.cursor()
    c.execute("SELECT regPk FROM tblTask "
              "WHERE tasPk = %s", (int(task_id),))
    region = c.fetchone()[0]
    
    c.execute("SELECT rwpName, rwpPk FROM `tblRegionWaypoint` "
              "WHERE regPk = %s", (int(region),))
        
    wps = dict((rwpName, rwpPk)
                      for rwpName, rwpPk in c.fetchall())
    
    return wps  

def update_times(task_id, startzulu, deadlinezulu, DB_User, DB_Password, DB):
    """update the database with the start time and endtime. considers time offset of comp and date of task"""
    db =   pymysql.connect(user=DB_User, passwd=DB_Password, db=DB, autocommit=True)
    c = db.cursor()
    
    # get the comp id to use to get time offset.
    c.execute("SELECT comPk FROM `tblTask` "
              "WHERE tasPk = %s", (task_id,))
    comp = int(c.fetchone()[0])

    #get the time offset    
    c.execute("SELECT comTimeOffset FROM `tblCompetition` "    ###check the query!!!!!!!
              "WHERE comPk = %s", (comp,))
    offset = int(c.fetchone()[0])

    startzulu_split = startzulu.split(":")  #separate hours, minutes and seconds.
    deadlinezulu_split = deadlinezulu.split(":")    #separate hours, minutes and seconds.

    startHHMM = (str(int(startzulu_split[0])+ offset) + ":" + startzulu_split[1])
    deadlineHHMM = (str(int(deadlinezulu_split[0])+ offset) + ":" + deadlinezulu_split[1])
    windowopenHHMM = (str(int(startzulu_split[0])+ offset -2) + ":" + startzulu_split[1])  #not in xctrack spec default to 2 hrs before start
    windowcloseHHMM = (str(int(startzulu_split[0])+ offset + 2) + ":" + startzulu_split[1]) #not in xctrack spec default to 2 hrs after start

    sql = "update tblTask set  tasStartTime=DATE_ADD( tasDate , INTERVAL '%s' HOUR_MINUTE),  tasFinishTime=DATE_ADD( tasDate , INTERVAL '%s' HOUR_MINUTE), tasTaskStart=DATE_ADD( tasDate , INTERVAL '%s' HOUR_MINUTE), tasStartCloseTime=DATE_ADD( tasDate , INTERVAL '%s' HOUR_MINUTE) where tasPk=%s;" % (startHHMM, deadlineHHMM, windowopenHHMM, windowcloseHHMM, task_id )
    #update start and deadline
    c.execute(sql)

def delete_task_waypoints(task_id, DB_User, DB_Password, DB):
    db =   pymysql.connect(user=DB_User, passwd=DB_Password, db=DB, autocommit=True)
    c = db.cursor()
    c.execute("delete FROM `tblTaskWaypoint` "
              "WHERE tasPk = %s;", (task_id,))

def main():
    print("starting..")
    """Main module. Takes tasPk and filename as parameters"""
    # DB_User = 'phpmyadmin'
    # DB_Password = 'airscore'
    # DB = 'xcdb'
    DB_User = 'airscore_db'  # mysql db user
    DB_Password = 'Tantobuchi01'  # mysql db password
    DB = 'airscore'  # mysql db name
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
    waypoint_list = get_area_wps(task_id, DB_User, DB_Password, DB) 
    startopen = t['sss']['timeGates'][0]
    deadline = t['goal']['deadline']

    update_times(task_id, startopen, deadline, DB_User, DB_Password, DB)
    delete_task_waypoints(task_id, DB_User, DB_Password, DB)

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
            if tp['type'] == 'SSS':
                waytype = "speed"
                if t['sss']['direction'] == "EXIT":  #get the direction form the SSS section
                    how = "exit"
            if tp['type'] == 'ESS':
                waytype = "endspeed"

        #print("insert into tblTaskWaypoint (tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius) values (",task_id,", ",wpID,", ",wpNum,", ",waytype,", ",how,", ",shape ," , 0 , ",tp["radius"],")")
        
        db = pymysql.connect(user = DB_User, passwd = DB_Password, db = DB, autocommit=True)
        c = db.cursor()
        sql = "insert into tblTaskWaypoint (tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius) values (%d, %d, %d, '%s', '%s', '%s' , 0 , %d);" % (task_id, wpID, wpNum, waytype, how, shape, tp["radius"])
        c.execute(sql)
        wpNum += 1
    
    #goal - last turnpoint
    goal = t['turnpoints'][-1]
    waytype = "goal"
    if t['goal']['type'] == 'LINE':
        shape = "line"
    #print("insert into tblTaskWaypoint (tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius) values (",task_id,", ",wpID,", ",wpNum,", ",waytype,", 'entry', ",shape ," , 0 , ",tp["radius"],")")
    sql = "insert into tblTaskWaypoint (tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius) values (%d, %d, %d, '%s', 'entry', '%s' , 0 , %d);" % (task_id, wpID, wpNum, waytype, shape, goal["radius"])
    c.execute(sql)

if __name__== "__main__":
  main()