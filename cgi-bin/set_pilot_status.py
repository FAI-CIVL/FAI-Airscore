"""
Script to set a pilot ABS, Min.Dist.or DNF.
usage: python3 set_pilot_status.py <task_id> <pil_id> <status>

Stuart Mackintosh Antonio Golfari - 2019
"""

from task       import Task
from formula    import get_formula_lib
from trackDB    import read_formula
from myconn     import Database
from logger     import Logger
import Defines as d

def main(args):
    '''create logging and disable output'''
    Logger('ON', 'task_update.txt')
    print("starting..")
    """Main module. Takes tasPk pilPk Status as parameters"""

    '''check parameter is good'''
    if not ((args[0].isdigit() and int(args[0]) > 0) and
            (args[1].isdigit() and int(args[1]) > 0) and
            (args[2] in ('abs', 'dnf', 'mindist'))):
        print("number of arguments != 3 and/or task_id or pil_id not a number")
        exit()
    else:
        task_id = int(args[0])
        pil_id  = int(args[1])
        status  = args[2]

    print('task id: {}'.format(task_id))
    print('pil id:  {}'.format(pil_id))
    print('status:  {}'.format(status))

    '''standard values'''
    distance    = 0
    speed       = 0
    launch      = 0
    start       = 0
    ess         = 0
    goal        = 0
    lasttime    = 0
    tp          = 0
    penalty     = 0
    lastalt     = 0

    '''check what we need to do'''
    if status = 'mindist':
        task        = Task.read_task(task_id)
        formula     = read_formula(task.comPk)
        distance    = formula['forMinDistance'] * 1000
        tp          = 1
        launch      = task.task_start_time

if __name__== "__main__":
    import sys
    main(sys.argv[1:])
