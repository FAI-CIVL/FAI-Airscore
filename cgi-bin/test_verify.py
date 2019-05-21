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
    report +=   'ESS: {} \n'.format(task_result.ESS_time_str)
    report +=   'Time: {} \n'.format(task_result.total_time_str)
    report +=   'Distance flown: {} Km\n'.format(task_result.Distance_flown)
    report +=   'lead_coeff: {} \n'.format(task_result.Lead_coeff)
    return report

def main():

    waypoint = namedtuple('waypoint', 'plat plon lat lon radius type shape direction')
    igc_file = './tests/test_igc/0215.igc'
    task = Task.read_task(64)

    #task.calculate_optimised_task_length()

    # total_dist = 0
    # for waypoint in range(1,len(task.optimised_turnpoints)):
    #     total_dist=total_dist+task.optimised_legs[waypoint-1]
    #     print('waypoint:',waypoint )
    #     print('radius:', task.turnpoints[waypoint].radius)
    #     print(task.optimised_turnpoints[waypoint].lat, ' ' , task.optimised_turnpoints[waypoint].lon)
    #     print('total distance:', total_dist, '  leg_distance:',task.optimised_legs[waypoint-1])

    print("starting..")
    print('using task {} and track file {}'.format(task.tasPk, igc_file))

    flight = igc_lib.Flight.create_from_file(igc_file) #load and process igc file

    print('flight notes: {}'.format(flight.notes))
    print('flight valid: {}'.format(flight.valid))
    print('partial distances:')
    print(task.distances_to_go)

    print('\n ***  Using Original algorithm  ***')

    task_result = orig_alg(flight, task, pwc.parameters, 5)
    task_result.Lead_coeff = pwc.coef_scaled(task_result.Lead_coeff, task.SSDistance)
    print(result_report(task_result))

    print('\n ***  Using CIVL algorithm  ***')

    task_result = civl_alg(flight, task, pwc.parameters, 5)
    task_result.Lead_coeff = pwc.coef_scaled(task_result.Lead_coeff, task.SSDistance)
    print(result_report(task_result))

    # task_result= Flight_result.check_flight(flight, task, pwc.parameters, 5) #check flight against task with tolerance of 0.05% or 5m

    # print('Waypoints achieved: {}'.format(task_result.Waypoints_achieved))
    # print('start: {}'.format(task_result.SSS_time_str))
    # print('ESS: {}'.format(task_result.ESS_time_str))
    # print('Time: {}'.format(task_result.total_time_str))
    # print('Distance flown: {}'.format(task_result.Distance_flown))
    # task_result.Lead_coeff = pwc.coef_scaled(task_result.Lead_coeff, task.SSDistance)
    # print("lead_coeff:", task_result.Lead_coeff)

if __name__== "__main__":
    main()
