from collections import namedtuple
import igc_lib
import time
import pwc
from task import Task


def orig_alg(f,task,param,min_tol):
    from flight_result_old import Flight_result
    return Flight_result.check_flight(f, task, param, min_tol)

def civl_alg(f,task,param,min_tol):
    from flight_result import Flight_result
    return Flight_result.check_flight(f, task, param, min_tol)

def lc_calc(res, t):
    LC          = 0
    leading     = 0
    trailing    = 0
    my_start    = res['start']
    first_start = t.stats['firstdepart']
    ss_start    = t.start_time
    SS_Distance = t.SSDistance
    '''add the leading part, from start time of first pilot to start, to my start time'''
    if not my_start:
        my_start = 0  # this is to avoid my_start being none if pilot didn't make start and causing error below
    if my_start > first_start:
        leading = parameters.coef_landout((my_start - first_start), SS_Distance)
        leading = parameters.coef_func_scaled(leading, SS_Distance)
    if not res['endSS']:
        '''pilot did not make ESS'''
        best_dist_to_ess    = (t.EndSSDistance - res['distance'])
        my_last_time        = res['last_time']          # should not need to check if < task deadline as we stop in Flight_result.check_flight()
        last_ess            = t.stats['maxarr']
        task_time           = (max(my_last_time,last_ess) - my_start)
        trailing            = parameters.coef_landout(task_time, best_dist_to_ess)
        trailing            = parameters.coef_func_scaled(trailing, SS_Distance)

    LC = leading + res['fixed_LC'] + trailing

    print('*************')
    print('last time: {}'.format(res.Stopped_time))
    print('LC from result: {}'.format(res.Fixed_LC))
    print('Start Time: {}'.format(ss_start))
    print('First Start Time: {}'.format(first_start))
    print('My Start Time: {}'.format(my_start))
    print('leading part: {}'.format(leading))
    print('landed early: {}'.format(bool(not any(e[0] == 'ESS' for e in res.Waypoints_achieved))))
    print('trailing part: {}'.format(trailing))
    return LC


def result_report(task_result):
    report = ''
    report +=   'Waypoints achieved: {} \n'.format(task_result.Waypoints_achieved)
    report +=   'start: {} \n'.format(task_result.Start_time_str)
    report +=   'real start: {} \n'.format(task_result.Pilot_Start_time)
    report +=   'ESS: {} \n'.format(task_result.ESS_time_str)
    report +=   'Time: {} \n'.format(task_result.total_time_str)
    report +=   'Distance flown: {} ({} Km)\n'.format(task_result.Distance_flown, round(task_result.Distance_flown/1000, 2))
    report +=   'partial lead_coeff: {}'.format(task_result.Lead_coeff)
    return report

def main():

    waypoint = namedtuple('waypoint', 'plat plon lat lon radius type shape direction')
    tracks = ['0215', '0941', '0407']
    #igc_file = './tests/test_igc/0941.igc'
    task = Task.read_task(64)

    print("starting..")
    print('using task {}'.format(task.tasPk))
    print('partial distances:')
    print(task.distances_to_go)

    for track in tracks:
        igc_file = './tests/test_igc/'+track+'.igc'
        flight = igc_lib.Flight.create_from_file(igc_file) #load and process igc file

        print('***')
        print('Pilot {}:'.format(track))
        print('flight notes: {}'.format(flight.notes))
        print('flight valid: {}'.format(flight.valid))

        print('\n ***  Using Original algorithm  ***')

        task_result = orig_alg(flight, task, pwc.parameters, 5)
        print(result_report(task_result))

        print('\n ***  Using CIVL algorithm  ***')

        task_result = civl_alg(flight, task, pwc.parameters, 5)
        Lead_coeff = lc_calc(task_result, task)
        print(result_report(task_result))
        print('calculated Final LC: {} \n'.format(Lead_coeff))

if __name__== "__main__":
    main()
