"""
Update Task / Comp Result status in JSON file and in database
Use: python3 update_result_status.py [refPk] [status] [opt. test]

Antonio Golfari - 2019
"""
# Use your utility module.
from myconn import Database

import sys

def update_result(refPk, status, test = 0):
    import os
    from os import path as p
    import json

    if not refPk < 1:
        message = ''
        with Database() as db:
            '''check if json file exists, and updates it'''
            query = ("SELECT `refJSON` FROM `tblResultFile` WHERE `refPk` = {} LIMIT 1".format(refPk))
            file = db.fetchone(query)['refJSON']
            if test:
                print('json file query: ')
                print(query)
                print('result: {}'.format(file))

            if p.isfile(file):
                '''update status in json file'''
                with open(file, 'r+') as f:
                    d = json.load(f)
                    if test:
                        print('old status: {}'.format(d['data']['status']))
                        print('will be updated to {}'.format(status))
                    else:
                        d['data']['status'] = status
                        f.seek(0)
                        f.write(json.dumps(d))
                        f.truncate()
                        message += 'JSON file has been updated \n'
            else:
                message += "Couldn't find a JSON file for this result \n"

            '''update status in database'''
            query = ("UPDATE `tblResultFile` SET `refStatus` = '{}' WHERE refPk = {}".format(status, refPk))
            if test == 1:
                print("Query:  {} \n".format(query))
            else:
                db.execute(query)
                message += ("Result with ID: {} succesfully updated \n".format(refPk))
        return message
    else:
        print("Error: Parameter is not a valid Result ID \n")

def main():
    """Main module"""
    test = 0
    """check parameter is good."""
    if len(sys.argv) >= 3:
        """Get refPk"""
        ref_id = 0 + int(sys.argv[1])
        status = str(sys.argv[2])
        if len(sys.argv) > 3:
            """Test Mode"""
            print('Running in TEST MODE')
            test = 1

        """Delete result"""
        message = update_result(ref_id, status, test)
        print(message)

    else:
        print('error: Use: python3 update_result.py [refPk] [status]')

if __name__ == "__main__":
    main()
