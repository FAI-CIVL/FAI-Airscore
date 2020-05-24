"""
Score Task:
To be used on frontend.
- calculates task scoring
- creates JSON file
- creates DB entry (TblResultFile)
- outputs result ID (ref_id)

Usage:
    python3 score_task.py <task_id> (opt.)<'status'>

    task_id   - INT: task ID in TblTask
    status  - STR: 'provisional', 'official', 'test', ...

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019

"""

from logger import Logger
from task import Task as T


def main(args):
    """create logging and disable output"""
    # Logger('ON', 'score_task.txt')

    print("starting..")
    '''Main module. Takes task_id as parameter'''

    task_id = int(args[0])
    status = None if len(args) == 1 else str(args[1])
    print(f"Task ID: {task_id} | Status: {status}")

    '''create task obj'''
    task = T.read(task_id)

    '''create task scores obj, json file, and TblResultFile entry'''
    ref_id, _ = task.create_results(status)
    print(f'result ID: {ref_id}')

    ''' now restore stdout function '''
    # Logger('OFF')

    print(f'{ref_id}')


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0):
        print("number of arguments != 1 and/or task_id not a number")
        print("usage: python3 score_task.py <task_id> (opt.)<'status'>")
        exit()

    main(sys.argv[1:])
