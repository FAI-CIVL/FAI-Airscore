"""script to calculate tassk distances, optimised and non optimised and write to the DB
python3 update_task.py <taskid>
this is to used in current front end. eventually will be deprecated when we go to flask app

Stuart Mackintosh - 2019
"""

from task import Task, write_task_json
from logger import Logger
import sys
import Defines
import os


def main(args):
    '''create logging and disable output'''
    Logger('ON', 'task_update.txt')
    print("starting..")
    task_id = 0

    ##check parameter is good.
    if args[0].isdigit():
        task_id = int(args[0])

    else:
        print("number of arguments != 1 and/or task_id not a number")
        exit()

    task = Task.read_task(task_id)
    print('{} - ID {}'.format(task.task_name, task.task_id))
    task.calculate_optimised_task_length()
    task.calculate_task_length()
    task.update_task_distance()
    # delete and recreate and task json file for maps
    try:
        os.remove(Defines.MAPOBJDIR+str(task.task_id) + '.task')
    except OSError:
        pass
    write_task_json(task_id)

    opt_dist = task.opt_dist
    print('task distance:   {}'.format(task.distance))
    print('task Opt. dist.: {}'.format(opt_dist))

    ''' now restore stdout function '''
    Logger('OFF')
    if opt_dist:
        print('Opt. Dist. = {}'.format(opt_dist))

if __name__== "__main__":
    main(sys.argv[1:])
