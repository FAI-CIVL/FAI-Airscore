"""
Score a task. At the moment this is only set up for PWC formula tasks.
python3 task_full_rescore_test.py <taskid>
"""

from task import Task
import importlib
from trackDB import read_formula
import logging, time
import sys
import Defines as d

def verify_tracks(task, formula):
    from myconn import Database
    from igc_lib import Flight
    from flight_result import Flight_result

    query = "SELECT `T`.`traPk` AS `id`, `P`.`pilLastName` AS `name`, `T`.`traFile` AS `file` " \
            "FROM `tblTrack` `T` JOIN `PilotView` `P` USING(`pilPk`) " \
            "WHERE `T`.`traDate` = %s"
    params = [task.date]

    with Database() as db:
        t = db.fetchall(query, params)

    if t:

        print('getting tracks...')
        # with Database() as db:
        for track in t:
            print('{} ({}) Result:'.format(track['name'], track['id']))
            igc_file = track['file']
            flight = Flight.create_from_file(igc_file)
            result = Flight_result.check_flight(flight, task, formula.parameters, 5)
            # Lead_coeff = lc_calc(result, task)
            # result.Lead_coeff = Lead_coeff
            print('   Goal: {} | part. LC: {}'.format(bool(result.goal_time),result.Fixed_LC))
            result.store_result(track['id'], task.tasPk)


def main(args):
    print("starting..")
    """Main module. Takes tasPk as parameter"""
    log_dir = d.LOGDIR
    print("log setup")
#    logging.basicConfig(filename=log_dir + 'main.log',level=logging.INFO,format='%(asctime)s %(message)s')
    task_id = 0
    #args =str(args)

    ##check parameter is good.
    if len(sys.argv)==2 and sys.argv[1].isdigit():
        task_id = int(sys.argv[1])

    #else:
       # logging.error("number of arguments != 1 and/or task_id not a number")
     #   print("number of arguments != 1 and/or task_id not a number")
      #  exit()
    print("""Task ID: {}""".format(task_id))

    task = Task.read_task(task_id)
    task.calculate_task_length()
    task.calculate_optimised_task_length()
    formula = read_formula(task.comPk)

    '''get formula library to use in scoring'''
    formula_file = 'formulas.' + formula['forClass']
    try:
        f = importlib.import_module(formula_file, package=None)
    except:
        print('formula file {} not found.'.format(formula))

    '''get all results for the task'''
    results = verify_tracks(task, f)

    totals = f.task_totals(task, formula)
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
