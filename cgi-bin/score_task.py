"""
Script to score a task.
usage: python3 score_task.py <taskid>

Stuart Mackintosh Antonio Golfari - 2019
"""

from task       import Task
from formula    import get_formula_lib
from trackDB    import read_formula
from myconn     import Database
import logging
import Defines as d

def main(args):
    print("starting..")
    """Main module. Takes tasPk as parameter"""
    # log_dir = d.LOGDIR
    # print("log setup")
    # logging.basicConfig(filename=log_dir + 'main.log',level=logging.INFO,format='%(asctime)s %(message)s')

    '''check parameter is good'''
    if not (args[0].isdigit() and int(args[0]) > 0):
        print("number of arguments != 1 and/or task_id not a number")
        exit()
    else:
        task_id = int(args[0])

    '''
    new logic:
    totals are already available in TaskTotalsView
    create task.stats from taskTotalsView
    create pilots array
    we calculate total LC for each pilot
    update LCmin in task.stats
    calculate Validities and Points
    Score
    '''

    print('task id: {}'.format(task_id))
    task    = Task.read_task(task_id)
    formula = read_formula(task.comPk)
    f       = get_formula_lib(formula)


    totals = f.task_totals(task, formula)
    if totals:
        task.stats.update(totals)   #have to check that all keys are the same
        task.update_totals()        #with new logic (totals in a view calculated from mysql) this should no longer be needed

        dist, time, launch, stop = f.day_quality(task, formula)

        task.stats['distval']   = dist
        task.stats['timeval']   = time
        task.stats['launchval'] = launch
        task.stats['stopval']   = stop

        if task.stopped_time:
            quality = dist * time * launch * stop
        else:
            quality = dist * time * launch

        print("-- TASK_SCORE -- distQ = {} | timeQ = {} | launchQ = {} | stopQ = {}".format(dist, time, launch, stop))
        print("-- TASK_SCORE -- Day Quality = ", quality)
        if quality > 1.0:
            quality = 1.0

        task.stats['quality']   = quality

        task.update_quality()   #with new logic (multiple JSON result files for every task) this should no longer be needed

        if totals['pilots'] > 0:
            f.points_allocation(task, formula)    #with new logic (totals in task.stats) totals parameter should no longer be needed

if __name__== "__main__":
    import sys
    main(sys.argv[1:])
