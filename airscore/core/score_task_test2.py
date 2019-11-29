"""
Score a task. At the moment this is only set up for PWC formula tasks.
python3 score_task.py <taskid>
"""

from task import Task
import importlib
from trackDB import read_formula
from myconn import Database
import logging
import sys
import Defines as d

def main(args):
    print("starting..")
    """Main module. Takes tasPk as parameter"""
    log_dir = d.LOGDIR
    print("log setup")
#    logging.basicConfig(filename=log_dir + 'main.log',level=logging.INFO,format='%(asctime)s %(message)s')
    task_id = 0
    #args =str(args)

    ##check parameter is good.
    #if len(args)==2 and args[0].isdigit():
    task_id = args

    #else:
       # logging.error("number of arguments != 1 and/or task_id not a number")
     #   print("number of arguments != 1 and/or task_id not a number")
      #  exit()

    '''
    new logic:
    totals are already available in taskTotalsView
    create task.stats from taskTotalsView
    create pilots array
    we calculate total LC for each pilot
    update minLC in task.stats
    calculate Validities and Points
    Score
    '''

    print(task_id)
    task = Task.read_task(task_id)
    formula = 'formulas.' + read_formula(task.comPk)[0]
    #task = Task.read_task(int(task_id[0]))
    try:
        f = importlib.import_module(formula, package=None)
    except:
        print('formula file {} not found.'.format(formula))
        break

    totals = f.task_totals(task, formula)
    task.stats.update(totals)   #have to check that all keys are the same
    task.update_totals()        #with new logic (totals in a view calculated from mysql) this should no longer be needed
    # query = "update tblTask_test set tasTotalDistanceFlown=%s, " \
    #         "tasTotDistOverMin= %s, tasPilotsTotal=%s, " \
    #         "tasPilotsLaunched=%s, tasPilotsGoal=%s, " \
    #         "tasFastestTime=%s, tasMaxDistance=%s " \
    #         "where tasPk=%s"
    #
    # params = [totals['distance'], totals['distovermin'], totals['pilots'], totals['launched'],
    #              totals['goal'], totals['fastest'], totals['maxdist'], task.tasPk]
    #
    # with Database() as db:
    #     db.execute(query, params)

    dist, time, launch, stop = f.day_quality(totals, formula)


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

    # query = "UPDATE tblTask_test " \
    #         "SET tasQuality = %s, " \
    #         "tasDistQuality = %s, " \
    #         "tasTimeQuality = %s, " \
    #         "tasLaunchQuality = %s, " \
    #         "tasStopQuality = %s " \
    #         "WHERE tasPk = %s"
    # params = [quality, dist, time, launch, stop, task.tasPk]
    #
    # with Database() as db:
    #     db.execute(query, params)

    totals['quality'] = quality

    if totals['pilots'] > 0:
        f.points_allocation(task, totals, formula)    #with new logic (totals in task.stats) totals parameter should no longer be needed


if __name__== "__main__":
    import sys
    main(sys.argv[1:])
