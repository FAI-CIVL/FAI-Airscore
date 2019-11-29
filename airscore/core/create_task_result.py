"""
Script to create a task result JSON file, and create the row in database
usage: python3 create_task_result.py <task_id> (opt.)<'status'>

Antonio Golfari - 2019
"""

import time
from logger import Logger
from result import Task_result
from pprint import pprint

def main(args):

    """Main module. prints result from a task"""

    '''create logging and disable output'''
    Logger('ON', 'create_task_result.txt')

    task_id = int(sys.args[0])
    status  = str(sys.args[1])

    '''create result object using method 1'''
    start = time.time()
    result = Task_result.read_db(task_id=task_id)
    filename = result.to_json(status=status)
    ref_id = result.to_db()
    end = time.time()

    ''' now restore stdout function '''
    Logger('OFF')

    print(ref_id)

if __name__== "__main__":
    import sys
    if not(len(sys.argv) >= 3 and sys.argv[1].isdigit()):
        print("Error, uncorrect arguments type or number.")
        print("usage: python3 create_task_result.py task_id 'status'")
        exit()

    main(sys.argv[1:])
