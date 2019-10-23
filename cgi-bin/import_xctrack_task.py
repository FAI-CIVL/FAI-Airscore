import json, sys
from logger import Logger
from myconn import Database
from task import Task
from compUtils import get_wpts

# def update_times(task_id, startzulu, deadlinezulu):
#     """update the database with the start time and endtime. considers time offset of comp and date of task"""
#
#     with Database() as db:
#         # get the comp id to use to get time offset.
#         query = ("""SELECT comPk FROM `tblTask`
#                   WHERE tasPk = '{}' LIMIT 1""".format(task_id))
#         comp = 0 + int(db.fetchone(query)['comPk'])
#
#         #get the time offset
#         query = ("""SELECT comTimeOffset FROM `tblCompetition`
#                   WHERE comPk = '{}' LIMIT 1""".format(comp))
#         offset = 0 + int(db.fetchone(query)['comTimeOffset'])
#
#     startzulu_split = startzulu.split(":")  #separate hours, minutes and seconds.
#     deadlinezulu_split = deadlinezulu.split(":")    #separate hours, minutes and seconds.
#
#     startHHMM = (str(int(startzulu_split[0])+ offset) + ":" + startzulu_split[1])
#     deadlineHHMM = (str(int(deadlinezulu_split[0])+ offset) + ":" + deadlinezulu_split[1])
#     windowopenHHMM = (str(int(startzulu_split[0])+ offset -2) + ":" + startzulu_split[1])  #not in xctrack spec default to 2 hrs before start
#     windowcloseHHMM = (str(int(startzulu_split[0])+ offset + 2) + ":" + startzulu_split[1]) #not in xctrack spec default to 2 hrs after start
#
#     with Database() as db:
#         sql = ("""   UPDATE
#                         tblTask
#                     SET
#                         tasStartTime = DATE_ADD(
#                             tasDate,
#                             INTERVAL '{}' HOUR_MINUTE
#                         ),
#                         tasFinishTime = DATE_ADD(
#                             tasDate,
#                             INTERVAL '{}' HOUR_MINUTE
#                         ),
#                         tasTaskStart = DATE_ADD(
#                             tasDate,
#                             INTERVAL '{}' HOUR_MINUTE
#                         ),
#                         tasStartCloseTime = DATE_ADD(
#                             tasDate,
#                             INTERVAL '{}' HOUR_MINUTE
#                         )
#                     WHERE
#                         tasPk = {} """.format(startHHMM, deadlineHHMM, windowopenHHMM, windowcloseHHMM, task_id))
#         #update start and deadline
#         db.execute(sql)

def main(args):

    """Main module. Takes tasPk and filename as parameters"""
    #wpNum = 0 #one or zero start???

    ##check parameter is good.
    if (len(args)==2 and args[0].isdigit() and args[1][-6:] == '.xctsk'):
        task_id = int(args[0])
        task_file = args[1]
    else:
        print('task id is not a number or File is not a .xctsk file')
        exit()

    '''create logging and disable output'''
    Logger('ON', 'xct_task_import.txt')
    print("starting..")

    '''get task'''
    task = Task.read_task(task_id)
    print('Task read from DB:')
    print('start:       {} '.format(task.start_time))
    print('start close: {} '.format(task.start_close_time))
    print('deadline:    {} '.format(task.task_deadline))
    print('window open: {} '.format(task.window_open_time))

    '''delete old waypoints in database'''
    task.clear_waypoints()
    # print('Waypoints after clear:')
    # for wp in task.turnpoints:
    #     print('{} - {}'.format(wp.id, wp.name))

    '''get new task definition from xctrack file'''
    task.update_from_xctrack_file(task_file)
    # print('Waypoints after reading xct file:')
    # for wp in task.turnpoints:
    #     print('{} - {}'.format(wp.rwpPk, wp.name))
    task.update_task_info()
    task.update_waypoints()
    task.calculate_task_length()
    task.calculate_optimised_task_length()
    task.update_task_distance()

    ''' now restore stdout function '''
    Logger('OFF')

if __name__== "__main__":
    main(sys.argv[1:])
