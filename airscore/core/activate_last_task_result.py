"""
Activate last task result:
- activates last created DB entry (tblResultFile)

Usage:
    python3 activate_last_task_result.py <tasPk>

    tasPk   - INT: task ID in tblTask

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019
"""

from task import Task as T
from result import Task_result as R
from logger import Logger
import time
from myconn import Database
from db_tables import tblResultFile as Results
from sqlalchemy.exc import SQLAlchemyError


def main(args):
    """create logging and disable output"""
    Logger('ON', 'activate_last_task_result.txt')
    start = time.time()

    print("starting..")
    '''Main module. Takes tasPk and status as parameters'''

    task_id = int(args[0])
    print(f"Task ID: {task_id} ")

    with Database() as db:
        try:
            results = db.session.query(Results).filter(Results.tasPk == task_id).all()
            if results:
                selected = next(r for r in results if r.refVisible == 1)
                selected.refVisible = 0
                db.session.flush()
                new = max(results, key=lambda r: r.refTimestamp)
                new.refVisible = 1
                db.session.commit()
        except SQLAlchemyError:
            print(f'Error changing active result for task ID {task_id}')

    end = time.time()
    print(f'Process Time (mins): {(end - start) / 60}')

    ''' now restore stdout function '''
    Logger('OFF')


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0):
        print("number of arguments != 1 and/or task_id not a number")
        print("usage: python3 activate_last_task_result.py <tasPk> ")
        exit()

    main(sys.argv[1:])
