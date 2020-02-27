"""
Score Task:
To be used on frontend.
- calculates task scoring
- creates JSON file
- creates DB entry (TblResultFile)
- outputs result ID (ref_id)

Usage:
    python3 score_comp.py <comp_id> (opt.)<'status'>

    comp_id   - INT: comp ID in TblCompetition
    status  - STR: 'provisional', 'official', 'test', ...

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019

"""

from comp import Comp as C
from logger import Logger


def main(args):
    """create logging and disable output"""
    # Logger('ON', 'score_comp.txt')

    print("starting..")
    '''Main module. Takes comp_id and status as parameters'''

    comp_id = int(args[0])
    status = None if len(args) == 1 else str(args[1])
    print(f"Comp ID: {comp_id} | Status: {status}")

    '''create comp obj, scores, json file, and TblResultFile entry'''
    ref_id = C.create_results(comp_id, status)
    print(f'result ID: {ref_id}')

    ''' now restore stdout function '''
    # Logger('OFF')


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0):
        print("number of arguments != 1 and/or task_id not a number")
        print("usage: python3 score_comp.py <comp_id> (opt.)<'status'>")
        exit()

    main(sys.argv[1:])
