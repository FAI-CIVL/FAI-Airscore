"""
Score a task. At the moment this is only set up for PWC formula tasks.
python3 task_full_rescore_test.py <taskid>
"""

from task import Task
import importlib
from trackDB import read_formula
import logging
import sys
import Defines as d

# def lc_calc(res, t):
#     leading     = 0
#     trailing    = 0
#     my_start    = res.Pilot_Start_time
#     first_start = t.stats['firstdepart']
#     ss_start    = t.start_time
#     SS_Distance = t.SSDistance
#     '''add the leading part, from start time of first pilot to start, to my start time'''
#     if my_start > first_start:
#         leading = coef_landout((my_start - first_start), SS_Distance)
#         leading = coef_scaled(leading, SS_Distance)
#     if not any(e[0] == 'ESS' for e in res.Waypoints_achieved):
#         '''pilot did not make ESS'''
#         best_dist_to_ess    = (t.EndSSDistance - res.Distance_flown)
#         my_last_time        = res.Stopped_time
#         last_ess            = t.stats['lastarrival']
#         task_time           = (max(my_last_time,last_ess) - my_start)
#         trailing            = coef_landout(task_time, best_dist_to_ess)
#         trailing            = coef_scaled(trailing, SS_Distance)
#
#     print('*************')
#     print('last time: {}'.format(res.Stopped_time))
#     print('LC from result: {}'.format(res.Fixed_LC))
#     print('Start Time: {}'.format(ss_start))
#     print('First Start Time: {}'.format(first_start))
#     print('My Start Time: {}'.format(my_start))
#     print('leading part: {}'.format(leading))
#     print('landed early: {}'.format(bool(not any(e[0] == 'ESS' for e in res.Waypoints_achieved))))
#     print('trailing part: {}'.format(trailing))
#     return leading + res.Fixed_LC + trailing

# def rescore(task, formula):
#     from myconn import Database
#     from igc_lib import Flight
#     from flight_result import Flight_result
#     import pwc
#     from statistics import pstdev
#
#     query = "SELECT `T`.`traPk` AS `id`, `P`.`pilLastName` AS `name`, `T`.`traFile` AS `file` " \
#             "FROM `tblTrack` `T` JOIN `PilotView` `P` USING(`pilPk`) " \
#             "WHERE `T`.`traDate` = %s"
#     params = [task.date]
#
#     with Database() as db:
#         t = db.fetchall(query, params)
#
#     if t:
#         results = []
#         index = []
#         std = []
#         #taskt = dict()
#         min_dist = formula['forMinDistance']
#         pilots = 81
#         totdist = 0
#         totdistovermin = 0
#         maxdist = 0
#         launched = 0
#         ess = 0
#         goal = 0
#         fastest = 0
#         tqtime = 0
#         mindept = 0
#         lastdept = 0
#         minarr = 0
#         maxarr = 0
#         LCmin = 0
#         stddev = 0
#
#         print('getting tracks...')
#         # with Database() as db:
#         for track in t:
#             print('{} ({}) Result:'.format(track['name'], track['id']))
#             igc_file = track['file']
#             flight = Flight.create_from_file(igc_file)
#             result = Flight_result.check_flight(flight, task, pwc.parameters, 5)
#             # Lead_coeff = lc_calc(result, task)
#             # result.Lead_coeff = Lead_coeff
#             print('   Goal: {} | part. LC: {}'.format(bool(result.goal_time),result.Lead_coeff))
#             results.append(result)
#             index.append(track['id'])
#
#             '''calculate task totals'''
#             if result.Distance_flown:
#                 launched += 1
#                 totdist += result.Distance_flown
#                 std.append((min_dist if result.Distance_flown < min_dist else result.Distance_flown))
#                 totdistovermin += 0 if result.Distance_flown < min_dist else result.Distance_flown - min_dist
#                 if result.Distance_flown > maxdist: maxdist = result.Distance_flown
#                 if not mindept or result.Pilot_Start_time < mindept: mindept = result.Pilot_Start_time
#                 if result.Pilot_Start_time > lastdept: lastdept = result.Pilot_Start_time
#                 if result.ESS_time:
#                     ess += 1
#                     if result.goal_time:
#                         goal += 1
#                         if not fastest:
#                             fastest = result.ESS_time - result.SSS_time
#                             tqtime = fastest
#                         elif (result.ESS_time - result.SSS_time) < fastest:
#                             tqtime = fastest
#                             fastest = result.ESS_time - result.SSS_time
#                         if not minarr or result.ESS_time < minarr: minarr = result.ESS_time
#                         if result.ESS_time > maxarr: maxarr = result.ESS_time
#
#         '''Update task totals'''
#         task.stats['pilots'] = pilots
#         task.stats['maxdist'] = maxdist
#         task.stats['distance'] = totdist
#         task.stats['distovermin'] = totdistovermin
#         #taskt['median'] = median
#         #taskt['stddev'] = stddev
#         #taskt['landed'] = landed
#         task.stats['launched'] = launched
#         task.stats['launchvalid'] = 1
#         task.stats['goal'] = goal
#         task.stats['ess'] = ess
#         task.stats['fastest'] = fastest
#         task.stats['tqtime'] = tqtime
#         task.stats['firstdepart'] = mindept
#         task.stats['lastdepart'] = lastdept
#         task.stats['minarr'] = minarr
#         task.stats['lastarrival'] = maxarr
#         #taskt['mincoeff'] = mincoeff
#         #task.stats['distspread'] = distspread
#         #taskt['kmmarker'] = kmmarker
#         task.stats['endssdistance'] = task.EndSSDistance
#         task.stats['stddev'] = pstdev(std)
#         task.stats['quality'] = None
#
#         task.update_totals()
#
#         '''update LC with final part
#             which need all tracks to be processed and totals to be calculated'''
#         for result in results:
#             result.Lead_coeff = lc_calc(result, task)
#             #result.Lead_coeff = Lead_coeff
#             print('({}) Result:'.format(index[0]))
#             print('   * Goal: {} | Final LC: {}'.format(bool(result.goal_time),result.Lead_coeff))
#
#             if not LCmin or result.Lead_coeff < LCmin: LCmin = result.Lead_coeff
#
#             '''store new result'''
#             result.store_result(index[0],task.tasPk)
#             print('* Result stored in DB \n\n')
#             index.pop(0)
#
#         task.stats['LCmin'] = LCmin
#
#         print('\n *** Totals:')
#         print('Tot. Dist: {} | Tot. Dist. over Min.: {}'.format(totdist,totdistovermin))
#         print('Max Dist: {} | Fastest time: {}'.format(maxdist,fastest))
#         print('Goal: {} | Min. LC: {}'.format(goal,mincoeff2))
#
#         #return taskt
#     else:
#         print('No results found')
#         exit()
#
#     return results

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
    print(task_id)

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
