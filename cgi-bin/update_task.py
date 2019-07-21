"""script to calculate tassk distances, optimised and non optimised and write to the DB
python3 update_task.py <taskid>
this is to used in current front end. eventually will be deprecated when we go to flask app

Stuart Mackintosh - 2019
"""

from task import Task
from logger import Logger
import sys
import Defines as d


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
    print('{} - ID {}'.format(task.task_name, task.tasPk))
    task.calculate_optimised_task_length()
    task.calculate_task_length()
    task.update_task_distance()

    opt_dist = task.ShortRouteDistance
    print('task distance:   {}'.format(task.Distance))
    print('task Opt. dist.: {}'.format(opt_dist))

    ''' now restore stdout function '''
    Logger('OFF')
    if opt_dist:
        print('Opt. Dist. = {}'.format(opt_dist))

if __name__== "__main__":
    main(sys.argv[1:])
