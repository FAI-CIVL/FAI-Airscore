"""
Create FSDB file:
Output: FSDB filename

Usage:
    python3 create_fsdb.py <comp_id>

    comp_id   - INT: comp ID in TblCompetition

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019
"""

import time

from fsdb import FSDB
from logger import Logger


def main(args):
    """create logging and disable output"""
    Logger('ON', 'create_fsdb.txt')
    start = time.time()

    print("starting..")
    '''Main module. Takes  comp_id as parameters'''

    comp_id = int(args[0])
    print(f"Comp ID: {comp_id}")

    fsdb = FSDB.create(comp_id)
    filename = fsdb.to_file()

    end = time.time()
    print(f'Process Time (mins): {(end - start) / 60}')

    ''' now restore stdout function '''
    Logger('OFF')

    ''' output fsdb filename to use in frontend:'''
    print(f'{filename}')


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0):
        print("number of arguments != 1 and/or task_id not a number")
        print("usage: python3 create_fsdb.py <comp_id>")
        exit()

    main(sys.argv[1:])
