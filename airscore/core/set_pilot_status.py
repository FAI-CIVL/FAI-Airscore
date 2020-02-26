"""
Script to set a pilot ABS, Min.Dist. or DNF.
We need to create a fake track for each result entry.
usage: python3 set_pilot_status.py <task_id> <pil_id> <status>

Stuart Mackintosh Antonio Golfari - 2019
"""

from db_tables import TblTaskResult as R
from logger import Logger
from myconn import Database
from task import Task as T


def main(args):
    '''create logging and disable output'''
    # Logger('ON', 'pilot_status.txt')
    print("starting..")
    """Main module. Takes tasPk parPk Status as parameters"""

    task_id = int(args[0])
    par_id  = int(args[1])
    status  = args[2]

    print(f'task id: {task_id} par id: {par_id} status:  {status}')

    with Database() as db:
        result = R(tasPk=task_id, parPk=par_id, tarResultType=status)
        if status == 'mindist':
            '''we need some more info'''
            task            = T.read(task_id)
            result.tarDistance      = task.formula.min_dist
            result.tarTurnpoints    = 1
            result.tarLaunch        = task.window_open_time
        db.session.add(result)
        db.session.commit()
        result_id = result.tarPk

    ''' now restore stdout function '''
    # Logger('OFF')
    if result_id:   print(f'tarPk={result_id}')
    else:           print('We had an error creating result entry')

if __name__== "__main__":
    import sys
    if not ((sys.argv[1].isdigit() and int(sys.argv[1]) > 0) and
            (sys.argv[2].isdigit() and int(sys.argv[2]) > 0) and
            (sys.argv[3] in ('abs', 'dnf', 'mindist'))):
        print("number of arguments != 3 and/or task_id or pil_id not a number")
        exit()
    main(sys.argv[1:])
