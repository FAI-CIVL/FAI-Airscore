"""
Test Importing FSComp FSDB File
Use: python3 test_fsdb.py [filename] [optional test]

Antonio Golfari - 2018
"""

from fsdb import FSDB
import sys, datetime, os
import lxml.etree as ET
from datetime import date, time, datetime
from operator import itemgetter

def main():
    """Main module"""
    test = 0
    text  = dict()
    """check parameter is good."""
    if len(sys.argv) > 1:
        """Get tasPk"""  
        filename = sys.argv[1]
        if len(sys.argv) > 2:
            """Test Mode""" 
            print('Running in TEST MODE')
            test = 1
        
        myfsdb = FSDB.read(filename)
        #myfsdb.read()
        if test == 1:
            print (myfsdb.info)
            print("\n \n")
            print (myfsdb.formula)
            print("\n \n")
            print (myfsdb.pilots)
            print("\n \n")
            print (myfsdb.tasks)
            print("\n \n")
#             tasks = sorted(myfsdb.tasks, key=itemgetter('id')) 
            for task in myfsdb.tasks:
                print ("*** {} *** ".format(task.task_name))
                print ("Day: {}".format(task.task_start_time.date().isoformat()))
                for idx, item in enumerate(task.turnpoints):
                    print ("  {}  {}  {}  {}".format(item.name, item.type, item.radius, task.optimised_legs[idx]))
                print("   RESULTS")
                for res in task.results:
                    #print (res.Score)
                    print ("Result: id {} start: {} end: {} points: {} type: {}".format(res.ext_id, res.Start_time, res.ESS_time, res.Score, res.result_type))

#                 if task['state'] == 'STOPPED':
#                     print ("Task Stopped Time: {} \n".format(task['tasStoppedTime']))
#                 route = sorted(task['route'], key = lambda i: i['tawNumber']) 
#                 for row in route:
#                     print ("{}  {}  {} {} \n".format(row['rwpName'], row['tawType'], row['tawRadius'], row['ssrCumulativeDist']))
#                 if task['state'] is not 'CANCELED':
#                     print ("    RESULTS:")
#                     results = sorted(task['results'], key=itemgetter('rank')) 
#                     for row in results:
#                         if not row['abs']:
#                             print ("{}  {}  {}  {}  {} ".format(row['rank'], row['id'], row['tarES'], row['tarDistance'], row['tarScore']))
#                         else:
#                             print ("{}  {}   ".format(row['rank'], row['id']))
#         
        myfsdb.add(test)


if __name__ == "__main__":
    main()
