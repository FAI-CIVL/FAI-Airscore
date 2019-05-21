from collections import namedtuple
import igc_lib
import time
import pwc
from task import Task


def orig_alg(f,task,param,min_tol):
    from flight_result import Flight_result
    return Flight_result.check_flight(f, task, param, min_tol)

def civl_alg(f,task,param,min_tol):
    from flight_result_new import Flight_result
    return Flight_result.check_flight(f, task, param, min_tol)

def result_report(task_result):
    report = ''
    report +=   'Waypoints achieved: {} \n'.format(task_result.Waypoints_achieved)
    report +=   'start: {} \n'.format(task_result.Start_time_str)
    report +=   'real start: {} \n'.format(task_result.Pilot_Start_time)
    report +=   'ESS: {} \n'.format(task_result.ESS_time_str)
    report +=   'Time: {} \n'.format(task_result.total_time_str)
    report +=   'Distance flown: {} ({} Km)\n'.format(task_result.Distance_flown, round(task_result.Distance_flown/1000, 2))
    report +=   'lead_coeff: {} \n'.format(task_result.Lead_coeff)
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
        task_result.Lead_coeff += pwc.coef_scaled(task_result.Lead_coeff, task.SSDistance)
        print(result_report(task_result))

        print('\n ***  Using CIVL algorithm  ***')

        task_result = civl_alg(flight, task, pwc.parameters, 5)
        task_result.Lead_coeff += pwc.coef_scaled(task_result.Lead_coeff, task.SSDistance)
        print(result_report(task_result))

if __name__== "__main__":
    main()
