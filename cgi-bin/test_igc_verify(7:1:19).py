import route
from collections import namedtuple
import igc_lib
import time

waypoint = namedtuple('waypoint', 'plat plon lat lon radius type shape direction')

task_file = './test_igc/task_2018-09-16_1.xctsk'
igc_file = './test_igc/2018-09-16-Luca Fraizzoli.igc'
igc_file2 = './test_igc/poggio_not_goal.igc'
task = route.Task.create_from_xctrack_file(task_file)

st=time.time()  #time the routine
short_route=route.find_shortest_route(task.turnpoints)
print("----%.2f----"%(time.time()-st))
total_dist = 0

for waypoint in range(1,len(short_route)):
     leg_dist=route.distance(short_route[waypoint-1], short_route[waypoint])
     total_dist=total_dist+leg_dist
     print('waypoint:',waypoint )
     print('radius:', task.turnpoints[waypoint].radius)
     print(short_route[waypoint].lat, ' ' , short_route[waypoint].lon)
     print('total distance:',total_dist, '  leg_distance:',leg_dist)

flight = igc_lib.Flight.create_from_file(igc_file) #load and process igc file
flight2 = igc_lib.Flight.create_from_file(igc_file2) #load and process igc file

print(flight.notes)
print(flight.valid)

print(route.distances_to_go(short_route))

st=time.time()  #time the routine
waypoints_made, task_result = task.check_flight(flight, short_route, 0.005, 5) #check flight against task with tolerance of 0.05% or 5m
print("----%.2f----"%(time.time()-st))
for wp in waypoints_made:
    print(wp)
print(task_result.Waypoints_achieved)
print(task_result.SSS_time_str)
print(task_result.ESS_time_str)
print(task_result.total_time_str)
print(task_result.Distance_flown)
print('----second igc------')

waypoints_made, task_result = task.check_flight(flight2, short_route, 0.005, 5) #check flight against task with tolerance of 0.05% or 5m
print("----%.2f----"%(time.time()-st))
for wp in waypoints_made:
    print(wp)
print(task_result.Waypoints_achieved)
print(task_result.SSS_time_str)
print(task_result.ESS_time_str)
print(task_result.total_time_str)
print(task_result.Distance_flown)