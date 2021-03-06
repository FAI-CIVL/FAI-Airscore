"""
Score Competition:
To be used on frontend.
- calculates competition results from tasks active JSON files.
- creates JSON file
- creates DB entry (TblResultFile)
- outputs result ID (ref_id)

Usage:
    python3 create_comp_results.py [comp_id] (opt.)['status']

    comp_id   - INT: comp ID in TblCompetition
    status  - STR: provisional, official, test...

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019

"""

from logger import Logger
from result import CompResult as C


def main(args):
    """create logging and disable output"""
    # Logger('ON', 'comp_results.txt')

    print("starting..")
    '''Main module. Takes task_id as parameter'''

    comp_id = int(args[0])
    status = None if len(args) == 1 else str(args[1])
    print(f"Task ID: {comp_id}")

    '''create comp result obj, json file, db entry'''
    ref_id = C.create_from_json(comp_id, status)

    print(f'Comp result ID: {ref_id}')

    ''' now restore stdout function '''
    # Logger('OFF')

    print(f'{ref_id}')


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0):
        print("number of arguments != 1 and/or comp_id not a number")
        print("usage: python3 create_comp_results.py [comp_id] (opt.)['status']")
        exit()

    main(sys.argv[1:])
