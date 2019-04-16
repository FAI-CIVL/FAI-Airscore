"""
Test calculation of short route
Use: python3 Test_short_route.py

Stuart Mackintosh - 2018
"""

import route
from myconn import  Database


query = """select tasPk, tasShortRouteDistance from tblTask where tasShortRouteDistance is not null """
with Database() as db:
    # get the tasks and optimised route.
    task_list = db.fetchall(query)

for db_t in task_list:
    task=route.Task.read_task(db_t['tasPk'])
    short=task.find_shortest_route()
    total_dist = 0
    for wp in range(1, len(short)):
        leg_dist = route.distance(short[wp - 1], short[wp])
        total_dist += leg_dist
    delta = abs(total_dist - db_t['tasShortRouteDistance'])
    print(delta)
    if delta > 1:
        print('optimised distance difference for task ', db_t['tasPk'],' over one meter' )
