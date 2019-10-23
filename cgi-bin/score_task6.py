"""
Score a task. At the moment this is only set up for PWC formula tasks.
python3 score_task.py <taskid>
"""

from task import Task
from pwc import *
from trackDB import read_formula
from myconn import Database
import logging
import sys
import Defines as d

def main():
    print("starting..")
    """Main module. Takes tasPk as parameter"""
    log_dir = d.LOGDIR
    print("log setup")
    #logging.basicConfig(filename=log_dir + 'main.log',level=logging.INFO,format='%(asctime)s %(message)s')
    task_id = 0

    ##check parameter is good.
    if len(sys.argv)==2 and sys.argv[1].isdigit():
        task_id = int(sys.argv[1])

    else:
        logging.error("number of arguments != 1 and/or task_id not a number")
        print("number of arguments != 1 and/or task_id not a number")
        exit()

    task = Task.read_task(task_id)
    formula = read_formula(task.comp_id)
    if formula['forClass'] == 'pwc':
        totals = task_totals(task, formula)
        # query = "update tblTask set tasTotalDistanceFlown=%s, " \
        #         "tasTotDistOverMin= %s, tasPilotsTotal=%s, " \
        #         "tasPilotsLaunched=%s, tasPilotsGoal=%s, " \
        #         "tasFastestTime=%s, tasMaxDistance=%s " \
        #         "where tasPk=%s"
        #
        # params = [totals['tot_dist_flown'], totals['tot_dist_over_min'], totals['pilots_present'], totals['pilots_launched'],
        #              totals['pilots_goal'], totals['fastest'], totals['max_distance'], task.task_id]
        #
        # with Database() as db:
        #     db.execute(query, params)

        dist, time, launch, stop = day_quality(totals, formula)

        if task.stopped_time:
            quality = dist * time * launch * stop
        else:
            quality = dist * time * launch

        print("-- TASK_SCORE -- distQ = {} | timeQ = {} | launchQ = {} | stopQ = {}".format(dist, time, launch, stop))
        print("-- TASK_SCORE -- Day Quality = ", quality)
        if quality > 1.0:
            quality = 1.0
        #
        # query = "UPDATE tblTask " \
        #         "SET tasQuality = %s, " \
        #         "tasDistQuality = %s, " \
        #         "tasTimeQuality = %s, " \
        #         "tasLaunchQuality = %s, " \
        #         "tasStopQuality = %s " \
        #         "WHERE tasPk = %s"
        # params = [quality, dist, time, launch, stop, task.task_id]
        #
        # with Database() as db:
        #     db.execute(query, params)

        totals['day_quality'] = quality

        if totals['pilots_present'] > 0:
            points_allocation(task, totals, formula)


if __name__== "__main__":
    main()
