"""
Module for operations on tracks
Use:    import trackUtils
        pilPk = compUtils.get_track_pilot(filename)
        
Antonio Golfari - 2018
"""

# Use your utility module.
from myconn import Database

def main():
    """Main module"""
    message = ''
    pilPk = 66
    with Database() as db:
        query = ("""    SELECT 
                            pilFirstName,
                            pilLastName 
                        FROM 
                            PilotView 
                        WHERE 
                            pilPk = {} 
                        LIMIT 
                            1""".format(pilPk))
        if db.rows(query) > 0:
            message = 'Found Pilot ' + db.fetchone(query)['pilFirstName']
            message += ' Connection ok'
        else:
            """No result found"""
            message = ("Connection not working \n")

        print(message)


if __name__ == "__main__":
    main()
