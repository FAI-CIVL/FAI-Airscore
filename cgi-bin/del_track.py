"""
Delete track and all references in other tables
Use: python3 del_track.py [traPk]

Antonio Golfari - 2019
"""
# Use your utility module.
from myconn import Database

def delete_track(traPk):

    # pretty sure we are not using all those tables anylonger
    tables = ['tblTaskResult', 'tblTrack', 'tblTrackMarker', 'tblComTaskTrack']
    with Database() as db:
        for table in tables:
            query = "DELETE FROM %s WHERE `traPk` = %s"
            params = [table, traPk]
            try:
                db.execute(query, params)
                print(f"track with ID: {traPk} succesfully deleted from {table}\n")
            except:
                print(f"Error with track with ID: {traPk} and table {table} \n")
                error = True

    return 0 if error else 1

def main(args):
    from logger import Logger
    '''create logging and disable output'''
    Logger('ON', 'task_full_rescore.txt')

    print("starting..")
    '''Main module. Takes traPk as parameter'''
    track_id = 0 + int(args[0])

    """Delete track"""
    out = delete_track(track_id)

    ''' now restore stdout function '''
    Logger('OFF')

    ''' output ref_id to use in frontend:
        task_result.php?refPk=ref_id&tasPk=task_id&comPk=comp_id'''
    print(f'{out}')

if __name__ == "__main__":
    import sys
    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0):
        print("number of arguments != 1 and/or track_id not a number")
        print("usage: python3 del_track.py <traPk>")
        exit()

    main(sys.argv[1:])
