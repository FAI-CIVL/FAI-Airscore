"""
Script to set a pilot ABS, Min.Dist. or DNF.
We need to create a fake track for each result entry.
usage: python3 set_pilot_status.py <task_id> <pil_id> <status>

Stuart Mackintosh Antonio Golfari - 2019
"""

from task       import Task
from myconn     import Database
from logger     import Logger
from compUtils  import get_glider, get_offset
from datetime   import datetime
from calcUtils  import sec_to_time
import Defines as d

def main(args):
    '''create logging and disable output'''
    Logger('ON', 'pilot_status.txt')
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

    task        = Task.read(task_id)

    '''standard values'''
    distance    = 0
    speed       = 0
    launch      = 0
    start       = 0
    trastart    = None
    ess         = 0
    goal        = 0
    lasttime    = 0
    tp          = 0
    penalty     = 0
    lastalt     = 0
    duration    = 0
    track_class = task.comp_class
    track_date  = task.date
    glider      = []

    '''check what we need to do'''
    if status == 'mindist':
        distance    = task.formula.min_dist
        tp          = 1
        launch      = task.window_open_time
        glider      = get_glider(pil_id)
        stime       = sec_to_time(launch + get_offset(task_id)*3600)

    '''create result entry'''
    query = """ INSERT INTO `tblTaskResult`(
                    `tasPk`,
                    `pilPk`,
                    `traGlider`,
                    `traDHV`,
                    `tarDistance`,
                    `tarResultType`,
                    `tarTurnpoints`
                )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s)"""

    params = [  task_id,
                pil_id,
                glider['name'] if glider else None,
                glider['cert'] if glider else None,
                distance,
                status,
                tp
            ]

    with Database() as db:
        result_id = db.execute(query, params)

    ''' now restore stdout function '''
    Logger('OFF')
    if result_id:   print(f'tarPk={result_id}')
    else:           print('We had an error creating result entry')

if __name__== "__main__":
    import sys
    main(sys.argv[1:])
