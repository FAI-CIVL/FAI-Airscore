"""
Task Full rescore:
To be used on frontend.
- Calculates task Opt. Route
- checks all tracks
- calculates task scoring
- creates JSON file
- creates DB entry (tblResultFile)
- outputs result ID (refPk)

Usage:
    python3 task_full_rescore.py <tasPk>

    tasPk   - INT: task ID in tblTask

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019
"""

import time

from logger import Logger
from task import Task as T


def main(args):
    """create logging and disable output"""
    # Logger('ON', 'task_full_rescore.txt')
    start = time.time()

    print("starting..")
    '''Main module. Takes tasPk and status as parameters'''

    task_id = int(args[0])
    status = None if len(args) == 1 else str(args[1])
    print(f"Task ID: {task_id} | Status: {status}")

    '''create task obj'''
    task = T.read(task_id)

    '''create task scores obj, json file, and tblResultFile entry'''
    ref_id = task.create_results(status=status, mode='full')
    print(f'result ID: {ref_id}')

    end = time.time()
    print(f'Process Time (mins): {(end - start) / 60}')

    ''' now restore stdout function '''
    # Logger('OFF')

    ''' output ref_id to use in frontend:
        task_result.php?refPk=ref_id&tasPk=task_id&comPk=comp_id'''
    print(f'{ref_id}')


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0):
        print("number of arguments != 1 and/or task_id not a number")
        print("usage: python3 task_full_rescore.py <tasPk> (opt.)<'status'>")
        exit()

    main(sys.argv[1:])
