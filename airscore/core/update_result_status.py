"""
Update Task / Comp Result status in JSON file and in database
Use: python3 update_result_status.py [refPk] [status]

Antonio Golfari - 2019
"""
from db_tables import TblResultFile as R
# Use your utility module.
from myconn import Database


def update_result(ref_id, status):
    from os import path as p
    import json

    with Database() as db:
        result  = db.session.query(R).get(ref_id)
        file    = result.refJSON
        '''check if json file exists, and updates it'''
        if p.isfile(file):
            '''update status in json file'''
            with open(file, 'r+') as f:
                d = json.load(f)
                d['data']['status'] = status
                f.seek(0)
                f.write(json.dumps(d))
                f.truncate()
                print(f'JSON file has been updated \n')
            '''update status in database'''
            result.refStatus = status
            db.session.commit()
            return 1
        else:
            print(f"Couldn't find a JSON file for this result \n")
            return 0

def main(args):
    from logger import Logger
    """Main module"""
    '''create logging and disable output'''
    Logger('ON', 'update_result.txt')

    print("starting..")
    '''Main module. Takes refPk and status as parameters'''
    ref_id = 0 + int(args[0])
    status = str(args[1])

    """Update result"""
    out = update_result(ref_id, status)
    print(f"out = {out}")

    ''' now restore stdout function '''
    Logger('OFF')

    print(f"{out}")

if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0):
        print("number of arguments != 1 and/or task_id not a number")
        print("usage: python3 update_result.py [refPk] [status]'")
        exit()

    main(sys.argv[1:])
