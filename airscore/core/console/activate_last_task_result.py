"""
Activate last task result:
- activates last created DB entry (TblResultFile)

Usage:
    python3 activate_last_task_result.py <task_id>

    task_id   - INT: task ID in TblTask

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019
"""

import time

from sqlalchemy.exc import SQLAlchemyError

from db_tables import TblResultFile as Results
from logger import Logger
from myconn import Database


def main(args):
    """create logging and disable output"""
    # Logger('ON', 'activate_last_task_result.txt')
    start = time.time()

    print("starting..")
    '''Main module. Takes task_id and status as parameters'''

    task_id = int(args[0])
    print(f"Task ID: {task_id} ")

    with Database() as db:
        try:
            results = db.session.query(Results).filter(Results.task_id == task_id).all()
            if results:
                selected = next(r for r in results if r.active == 1)
                selected.active = 0
                db.session.flush()
                new = max(results, key=lambda r: r.created)
                new.active = 1
                db.session.commit()
        except SQLAlchemyError:
            print(f'Error changing active result for task ID {task_id}')

    end = time.time()
    print(f'Process Time (mins): {(end - start) / 60}')

    ''' now restore stdout function '''
    # Logger('OFF')


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0):
        print("number of arguments != 1 and/or task_id not a number")
        print("usage: python3 activate_last_task_result.py <task_id> ")
        exit()

    main(sys.argv[1:])
