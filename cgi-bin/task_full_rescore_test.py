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

def lc_calc(res, t):
    leading     = 0
    trailing    = 0
    my_start    = res.Pilot_Start_time
    first_start = t.stats['tasFirstDepTime']
    ss_start    = t.start_time
    SS_Distance = t.SSDistance
    '''add the leading part, from start time of first pilot to start, to my start time'''
    if my_start > first_start:
        leading = coef_landout((my_start - first_start), SS_Distance/1000)
        leading = coef_scaled(leading, SS_Distance)
    if not any(e[0] == 'ESS' for e in res.Waypoints_achieved):
        '''pilot did not make ESS'''
        best_dist_to_ess    = (t.EndSSDistance - res.Distance_flown)/1000
        my_last_time        = res.Stopped_time
        last_ess            = t.stats['tasLastArrTime']
        task_time           = (max(my_last_time,last_ess) - my_start)
        trailing            = coef_landout(task_time, best_dist_to_ess)
        trailing            = coef_scaled(trailing, SS_Distance)

    print('*************')
    print('last time: {}'.format(res.Stopped_time))
    print('LC from result: {}'.format(res.Lead_coeff))
    print('Start Time: {}'.format(ss_start))
    print('First Start Time: {}'.format(first_start))
    print('My Start Time: {}'.format(my_start))
    print('leading part: {}'.format(leading))
    print('landed early: {}'.format(bool(not any(e[0] == 'ESS' for e in res.Waypoints_achieved))))
    print('trailing part: {}'.format(trailing))
    return leading + res.Lead_coeff + trailing

def get_results(task):
    from flight_result_new import Flight_result
    query = "SELECT `R`.`tarPk` AS `id`, `R`.`pilName` AS `name`, `T`.`traFile` AS `file` " \
            "FROM `tblTrack` `T` RIGHT OUTER JOIN `tblResultView` `R` USING(`traPk`) " \
            "WHERE `R`.`tasPk` = %s"
    params = [task.tasPk]

    with Database() as db:
        t = db.fetchall(query, params)

    if t:
        results = []
        taskt = dict()
        min_dist = task.min_dist
        pilots = 81
        totdist = 0
        totdistovermin = 0
        maxdist = 0
        launched = 0
        ess = 0
        goal = 0
        fastest = 0
        tqtime = 0
        mindept = 0
        lastdept = 0
        minarr = 0
        maxarr = 0
        mincoeff2 = 0

        print('getting tracks...')
        for track in t:
            print('{} ({}) Result:'.format(t['name'], t['id']))
            igc_file = track['file']
            flight = igc_lib.Flight.create_from_file(igc_file)
            result = Flight_result.check_flight(flight, task, pwc.parameters, 5)
            Lead_coeff = lc_calc(result, task)
            result.Lead_coeff = Lead_coeff
            results.append(result)

            query = "UPDATE `tblTaskResult` " \
                    "SET `tarDistance`=%s,`tarSpeed`=%s,`tarStart`=%s,`tarGoal`=%s, " \
                    "`tarResultType`=%s,`tarSS`=%s,`tarES`=%s,`tarLeadingCoeff2`=%s, " \
                    "`tarLastAltitude`=%s,`tarLastTime`=%s " \
                    "WHERE `tarPk`=%s"

            params = [result.Distance_flown, result.speed, tresult.pilot_start_time, result.goal_time,
                         'lo', result.SS_time, result.ESS_time, result.Lead_coeff,
                         result.Stopped_altitude, result.Stopped_time, 
                         t['id']]

            with Database() as db:
                db.execute(query, params)

            if result.Distance_flown:
                launched += 1
                totdist += result.Distance_flown
                totDistOverMin += 0 if result.Distance_flown < min_dist else result.Distance_flown - min_dist
                if result.Distance_flown > maxdist: maxdist = result.Distance_flown
                if not mindept or result.pilot_start_time < mindept: mindept = result.pilot_start_time
                if result.pilot_start_time > maxdept: maxdept = result.pilot_start_time
                if result.ESS_time:
                    ess += 1
                    if result.goal_time:
                        goal += 1
                        if not fastest:
                            fastest = result.ESS_time
                            tqtime = fastest
                        elif result.ESS_time < fastest:
                            tqtime = fastest
                            fastest = result.ESS_time
                        if not minarr or result.ESS_time < minarr: minarr = result.ESS_time
                        if result.ESS_time > maxarr: maxarr = result.ESS_time
                if not mincoeff2 or result.Lead_coeff < mincoeff2: mincoeff2 = result.Lead_coeff

        taskt['pilots'] = pilots
        taskt['maxdist'] = maxdist
        taskt['distance'] = totdist
        taskt['distovermin'] = totdistovermin
        #taskt['median'] = median
        #taskt['stddev'] = stddev
        taskt['landed'] = landed
        taskt['launched'] = launched
        taskt['launchvalid'] = 1
        taskt['goal'] = goal
        taskt['ess'] = ess
        taskt['fastest'] = fastest
        taskt['tqtime'] = tqtime
        taskt['firstdepart'] = mindept
        taskt['lastdepart'] = lastdept
        taskt['firstarrival'] = minarr
        taskt['lastarrival'] = maxarr
        #taskt['mincoeff'] = mincoeff
        taskt['mincoeff2'] = mincoeff2
        #taskt['distspread'] = distspread
        #taskt['kmmarker'] = kmmarker
        taskt['endssdistance'] = task.EndSSDistance
        taskt['quality'] = None
        #
        # return results, taskt



        return results
    else:
        print('No results found')
        exit()

def main(args):
    print("starting..")
    """Main module. Takes tasPk as parameter"""
    log_dir = d.LOGDIR
    print("log setup")
#    logging.basicConfig(filename=log_dir + 'main.log',level=logging.INFO,format='%(asctime)s %(message)s')
    task_id = 0
    #args =str(args)

    ##check parameter is good.
    if len(args)==2 and args[0].isdigit():
        task_id = int(args[0])

    #else:
       # logging.error("number of arguments != 1 and/or task_id not a number")
     #   print("number of arguments != 1 and/or task_id not a number")
      #  exit()
    print(task_id)

    task = Task.read_task(task_id)

    '''get all results for the task'''
    results, totals = get_results(task)

    formula = read_formula(task.comPk)

    if formula['forClass'] == 'pwc':
        #totals = task_totals(task, formula)
        query = "update tblTask_test set tasTotalDistanceFlown=%s, " \
                "tasTotDistOverMin= %s, tasPilotsTotal=%s, " \
                "tasPilotsLaunched=%s, tasPilotsGoal=%s, " \
                "tasFastestTime=%s, tasMaxDistance=%s " \
                "where tasPk=%s"

        params = [totals['distance'], totals['distovermin'], totals['pilots'], totals['launched'],
                     totals['goal'], totals['fastest'], totals['maxdist'], task.tasPk]

        with Database() as db:
            db.execute(query, params)

        dist, time, launch, stop = day_quality(totals, formula)

        if task.stopped_time:
            quality = dist * time * launch * stop
        else:
            quality = dist * time * launch

        print("-- TASK_SCORE -- distQ = {} | timeQ = {} | launchQ = {} | stopQ = {}".format(dist, time, launch, stop))
        print("-- TASK_SCORE -- Day Quality = ", quality)
        if quality > 1.0:
            quality = 1.0

        query = "UPDATE tblTask_test " \
                "SET tasQuality = %s, " \
                "tasDistQuality = %s, " \
                "tasTimeQuality = %s, " \
                "tasLaunchQuality = %s, " \
                "tasStopQuality = %s " \
                "WHERE tasPk = %s"
        params = [quality, dist, time, launch, stop, task.tasPk]

        with Database() as db:
            db.execute(query, params)

        totals['quality'] = quality

        if totals['pilots'] > 0:
            pwc_points_allocation(task, totals, formula)


if __name__== "__main__":
    import sys
    main(sys.argv[1:])
