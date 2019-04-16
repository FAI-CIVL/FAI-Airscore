"""
Test calculation of short route
Use: python3 Test_short_route.py

Stuart Mackintosh - 2018
"""

from myconn import Database
from datetime import datetime
from task import Task

query = """select tasPk, tasShortRouteDistance from tblTask where tasShortRouteDistance is not null """
with Database() as db:
    # get the tasks and optimised route.
    task_list = db.fetchall(query)

for method in ('fast_andoyer', 'vincenty','geodesic'):
    startTime = datetime.now()
    print(" *** Using {} ***".format(method))
    for db_t in task_list:
        routineTime = datetime.now()
        task=Task.read_task(db_t['tasPk'])
        task.find_shortest_route(method)

        delta = abs(task.ShortRouteDistance - db_t['tasShortRouteDistance'])
        print("Distance Delta (cm): {} ".format(delta*100))

        if delta > 1:
            print('optimised distance difference for task ', db_t['tasPk'],' over one meter' )

         print ("Routime time: {} ".format(datetime.now() - routineTime))
    print ("Total time ({}): {} ".format(method, (datetime.now() - startTime)))