"""
Score Task:
To be used on frontend.
- calculates task scoring
- creates JSON file
- creates DB entry (tblResultFile)
- outputs result ID (refPk)

Usage:
    python3 score_task.py <tasPk> (opt.)<'status'>

    tasPk   - INT: task ID in tblTask
    status  - STR: 'provisional', 'official', 'test', ...

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019

"""

from logger import Logger
from task import Task as T
from pprint import pprint


def main(args):
    '''create logging and disable output'''
    # Logger('ON', 'score_task.txt')

    print("starting..")
    '''Main module. Takes tasPk as parameter'''

    task_id = int(args[0])
    status = None if len(args) == 1 else str(args[1])
    print(f"Task ID: {task_id} | Status: {status}")

    '''create task obj'''
    task = T.read(task_id)

    '''create task scores obj, json file, and tblResultFile entry'''
    ref_id = task.create_results(status)
    print(f'result ID: {ref_id}')

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
        print("usage: python3 score_task.py <tasPk> (opt.)<'status'>")
        exit()

    main(sys.argv[1:])
