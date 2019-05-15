"""
Delete Task / Comp Result JSON file and all references in result tables
Use: python3 del_result.py [refPk] [opt. test]

Antonio Golfari - 2019
"""
# Use your utility module.
from myconn import Database

import sys

def delete_result(refPk, test = 0):
    import os
    from os import path as p

    if not refPk < 1:
        message = ''
        with Database() as db:
            '''check if json file exists, and deletes it'''
            query = ("SELECT `refJSON` FROM `tblResultFile` WHERE `refPk` = {} LIMIT 1".format(refPk))
            file = db.fetchone(query)['refJSON']
            if test:
                print('json file query: ')
                print(query)
                print('result: {}'.format(file))

            if p.isfile(file):
                if test:
                    print('file {} will be deleted'.format(file))
                else:
                    os.remove(file)
                    message += 'JSON file has been deleted \n'
            else:
                message += "Couldn't find a JSON file for this result \n"

            query = ("DELETE FROM `tblResultFile` WHERE refPk = {}".format(refPk))
            if test == 1:
                message += ("Query:  {} \n".format(query))
            else:
                db.execute(query)

        message += ("Result with ID: {} succesfully deleted \n".format(refPk))
        return message
    else:
        print("Error: Parameter is not a valid Result ID \n")

def main():
    """Main module"""
    test = 0
    """check parameter is good."""
    if len(sys.argv) > 1:
        """Get refPk"""
        result = 0 + int(sys.argv[1])
        if len(sys.argv) > 2:
            """Test Mode"""
            print('Running in TEST MODE')
            test = 1

        """Delete result"""
        message = delete_result(result, test)
        print(message)

    else:
        print('error: Use: python3 del_result.py [refPk]')

if __name__ == "__main__":
    main()
