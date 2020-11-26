"""
Delete Task / Comp Result JSON file and all references in result tables
Use: python3 del_result.py [ref_id]

Antonio Golfari - 2019
"""
# Use your utility module.
from db.conn import db_session


def delete_result(ref_id):
    import os
    from os import path as p

    from db.tables import TblResultFile as R

    if type(ref_id) is int and ref_id > 0:
        with db_session() as db:
            '''check if json file exists, and deletes it'''
            q = db.query(R)
            result = q.get(ref_id).delete()
            file = result.filename
            db.delete(result)
            db.commit()

        if p.isfile(file):
            os.remove(file)
            print(f'JSON file has been deleted \n')
        else:
            print("Couldn't find a JSON file for this result \n")

        if result > 1:
            print(f"Result with ID: {ref_id} succesfully deleted \n")
            return 1
    return 0


def main(args):
    from logger import Logger

    '''create logging and disable output'''
    Logger('ON', 'del_result.txt')

    print("starting..")
    '''Main module. Takes ref_id as parameter'''
    """Get ref_id"""
    result = 0 + int(args[0])

    """Delete result"""
    out = delete_result(result)

    ''' now restore stdout function '''
    Logger('OFF')

    ''' output out to use in frontend'''
    print(f'{out}')


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0):
        print("number of arguments != 1 and/or task_id not a number")
        print("Use: python3 del_result.py [ref_id] ")
        exit()

    main(sys.argv[1:])
