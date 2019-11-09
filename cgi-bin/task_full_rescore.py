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
    python3 task_full_rescore_test.py <tasPk>

    tasPk   - INT: task ID in tblTask

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019
"""

from    task        import Task as T
from    result      import Task_result as R
from    logger      import Logger
import  importlib
import  sys
import  Defines as d

def main(args):
    '''create logging and disable output'''
    Logger('ON', 'task_full_rescore.txt')

    print("starting..")
    """Main module. Takes tasPk as parameter"""
    task_id = 0

    #check parameter is good.
    if len(sys.argv)==2 and sys.argv[1].isdigit():
        task_id = int(sys.argv[1])

    else:
        print("number of arguments != 1 and/or task_id not a number")
        exit()

    print(f"Task ID: {task_id}")

    task = T.read(task_id)

    '''create task scores obj, json file, and tblResultFile entry'''
    ref_id = task.create_scoring(status=status, mode='full')
    print(f'result ID: {ref_id}')

    ''' now restore stdout function '''
    Logger('OFF')

    ''' output ref_id to use in frontend:
        task_result.php?refPk=ref_id&tasPk=task_id&comPk=comp_id'''
    print(f'{ref_id}')

if __name__== "__main__":
    import sys
    main(sys.argv[1:])
