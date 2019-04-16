"""
Delete track and all references in other tables
Use: python3 del_track.py [traPk] [opt. test]

Antonio Golfari - 2018
"""
# Use your utility module.
from myconn import Database

import sys

def delete_track(traPk, test = 0):

    if not traPk < 1:
        message = ''
        tables = ['tblTaskResult', 'tblTrack', 'tblTrackLog', 'tblWaypoint', 'tblBucket', 'tblTrackMarker', 'tblComTaskTrack']
        with Database() as db:
            for table in tables:
                query = ("DELETE FROM {} WHERE traPk = {}".format(table, traPk))
                if test == 1:
                    message += ("Query:  {} \n".format(query))
                else:
                    db.execute(query)

        message += ("track with ID: {} succesfully deleted \n".format(traPk))
        print(message)
    else:
        print("Error: Parameter is not a valid Track ID \n")

def main():
    """Main module"""
    test = 0
    """check parameter is good."""
    if len(sys.argv) > 1:
        """Get traPk"""  
        traPk = 0 + int(sys.argv[1])
        if len(sys.argv) > 2:
            """Test Mode""" 
            print('Running in TEST MODE')
            test = 1

        """Delete track"""
        delete_track(traPk, test)

    else:
        print('error: Use: python3 del_track.py [traPk] [opt. test]')

if __name__ == "__main__":
    main()
