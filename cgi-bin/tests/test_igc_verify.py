from collections import namedtuple
import igc_lib
import time
import pwc
from task import Task, distances_to_go

waypoint = namedtuple('waypoint', 'plat plon lat lon radius type shape direction')

task_file = './test_igc/task_2018-09-16_1.xctsk'
igc_file = './test_igc/2018-09-16-Luca Fraizzoli.igc'
igc_file2 = './test_igc/poggio_not_goal.igc'
task = Task.create_from_xctrack_file(task_file)

st=time.time()  #time the routine
task.calculate_optimised_task_length()
print("----%.2f----"%(time.time()-st))

total_dist = 0
for waypoint in range(1,len(task.optimised_turnpoints)):
    total_dist=total_dist+task.optimised_legs[waypoint-1]
    print('waypoint:',waypoint )
    print('radius:', task.turnpoints[waypoint].radius)
    print(task.optimised_turnpoints[waypoint].lat, ' ' , task.optimised_turnpoints[waypoint].lon)
    print('total distance:', total_dist, '  leg_distance:',task.optimised_legs[waypoint-1])

flight = igc_lib.Flight.create_from_file(igc_file) #load and process igc file
flight2 = igc_lib.Flight.create_from_file(igc_file2) #load and process igc file

print(flight.notes)
print(flight.valid)

print(distances_to_go(task.optimised_turnpoints))

st=time.time()  # time the routine
waypoints_made, task_result = task.check_flight(flight, pwc.parameters, 0.005, 5) #check flight against task with tolerance of 0.05% or 5m
print("----%.2f----"%(time.time()-st))
for wp in waypoints_made:
    print(wp)
print(task_result.Waypoints_achieved)
print(task_result.SSS_time_str)
print(task_result.ESS_time_str)
print(task_result.total_time_str)
print(task_result.Distance_flown)
task_result.Lead_coeff = pwc.coef_scaled(task_result.Lead_coeff, task.SSDistance)
print("lead_coeff:", task_result.Lead_coeff)
print('----second igc------')

waypoints_made, task_result = task.check_flight(flight2, pwc.parameters, 0.005, 5) #check flight against task with tolerance of 0.05% or 5m
print("----%.2f----"%(time.time()-st))
for wp in waypoints_made:
    print(wp)
print(task_result.Waypoints_achieved)
print(task_result.SSS_time_str)
print(task_result.ESS_time_str)
print(task_result.total_time_str)
print(task_result.Distance_flown)