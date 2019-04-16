from collections import namedtuple
import igc_lib
import time
import pwc
from task import Task
from flight_result import Flight_result

waypoint = namedtuple('waypoint', 'plat plon lat lon radius type shape direction')


igc_file = './test_igc/gafforini.igc'

task = Task.read_task(59)

#task.calculate_optimised_task_length()

# total_dist = 0
# for waypoint in range(1,len(task.optimised_turnpoints)):
#     total_dist=total_dist+task.optimised_legs[waypoint-1]
#     print('waypoint:',waypoint )
#     print('radius:', task.turnpoints[waypoint].radius)
#     print(task.optimised_turnpoints[waypoint].lat, ' ' , task.optimised_turnpoints[waypoint].lon)
#     print('total distance:', total_dist, '  leg_distance:',task.optimised_legs[waypoint-1])

flight = igc_lib.Flight.create_from_file(igc_file) #load and process igc file

print(flight.notes)
print(flight.valid)

print(task.distances_to_go)

task_result= Flight_result.check_flight(flight, task, pwc.parameters, 0.005, 5) #check flight against task with tolerance of 0.05% or 5m

print(task_result.Waypoints_achieved)
print(task_result.SSS_time_str)
print(task_result.ESS_time_str)
print(task_result.total_time_str)
print(task_result.Distance_flown)
task_result.Lead_coeff = pwc.coef_scaled(task_result.Lead_coeff, task.SSDistance)
print("lead_coeff:", task_result.Lead_coeff)
