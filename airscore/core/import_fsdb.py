"""
Import FSDB:

Usage:
    python3 import_fsdb.py <filename> (opt.)<'short_name'> (opt. keep_task_path)<0/1> (opt. from_CIVL)<0/1>

    filename       - STR: FSDB file
    short_name     - 0 or STR: Comp Code (if 0 will be automatically calculated from Comp Name ad Date)
    keep_task_path - 0/1: Keep tracks folder name found in FSDB (0 will calculate standard names from Task number and Date)
    from_CIVL      - 0/1: Get pilots information from CIVL database using pilots CIVL ID (default False)

Ex:
    python import_fsdb.py 'test.fsdb' 0 1         imports test.fsdb, calculates comp_code, keeps track folder names
    python import_fsdb.py 'test.fsdb' 'test' 0    imports test.fsdb, comp_code='test', standard track folder names
    python import_fsdb.py 'test.fsdb' 'test' 0 1  imports test.fsdb, comp_code='test', standard track folder names, get pilots name, nat and sex from CIVL database

- AirScore -
Stuart Mackintosh - Antonio Golfari
2020
"""

import time

from fsdb import FSDB
from logger import Logger


def main(args):
    """create logging and disable output"""
    Logger('ON', 'import_fsdb.txt')
    start = time.time()

    print("starting..")
    '''Main module. Takes fsdb and switches as parameters'''

    file = str(args[0])
    print(f"FSDB file: {file} ")

    print(f"{'None' if len(args) == 1 else args[1]} | {'None' if len(args) < 3 else args[2]} | {'None' if len(args) < 4 else args[3]}")
    short_name = None if (len(args) <= 1 or args[1] == '0') else str(args[1])
    keep_task_path = (len(args) > 2 and int(args[2]) == 1)
    from_CIVL = (len(args) > 3 and int(args[3]) == 1)
    print(f"short_name: {short_name} | keep_task_path: {keep_task_path} | from_CIVL: {from_CIVL}")

    '''read FSDB file'''
    fsdb = FSDB.read(file, short_name=short_name, keep_task_path=keep_task_path, from_CIVL=from_CIVL)

    if fsdb:
        print(f"Comp Name: {fsdb.comp.comp_name} | code: {fsdb.comp.comp_code} | path: {fsdb.comp.file_path}")
        for t in fsdb.tasks:
            print(f"{t.task_code} | path: {t.task_path}")

        '''store to database'''
        fsdb.add_all()

    end = time.time()
    print(f'Process Time (mins): {(end - start) / 60}')

    ''' now restore stdout function '''
    Logger('OFF')
    print(f'FSDB Processed correctly: {fsdb is not None} | Imported to database: {fsdb.comp.comp_id is not None}')
    if fsdb:
        print(f'path to comp folder: {fsdb.comp.file_path}')


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not sys.argv[1]:
        print("number of arguments less than minimum")
        print(
            "usage: python3 import_fsdb.py <filename> (opt.)<'short_name'> (opt. keep_task_path)<0/1> (opt. from_CIVL)<0/1>")
        exit()

    main(sys.argv[1:])
