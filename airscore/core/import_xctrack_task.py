import sys

from logger import Logger
from task import Task


def main(args):

    """Main module. Takes task_id and filename as parameters"""
    #wpNum = 0 #one or zero start???

    ##check parameter is good.
    if (len(args)==2 and args[0].isdigit() and args[1][-6:] == '.xctsk'):
        task_id = int(args[0])
        task_file = args[1]
    else:
        print('task id is not a number or File is not a .xctsk file')
        exit()

    '''create logging and disable output'''
    # Logger('ON', 'xct_task_import.txt')
    print("starting..")

    '''get task'''
    task = Task.read(task_id)
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
    # Logger('OFF')

if __name__== "__main__":
    main(sys.argv[1:])
