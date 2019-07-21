"""
Reads in a CSV membership list
Use: python3 bulk_pilot_import.py [csv file name] [opt. test]

Antonio Golfari - 2018
"""

# Use your utility module.
from compUtils import *
import sys, csv
from pathlib import Path


def read_membership(file, test):

    message = ''
    """Check if file exists"""
    my_file = Path(file)
    if not my_file.is_file():
        print ("Reading error: {} does not exist".format(file))
    else:
        if test == 1:
            message += ("Reading: {} \n".format(file))
        """Read CSV File"""
        with open(file, encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                pilFAI = row[0]
                pilFName = row[1]
                pilLName = row[2]
                pilSex = row[4]
                nat = row[3]
                if test == 1:
                    message += '-- new line -- \n'
                    message += ("Pilot {} {}, from {}, sex {}, FAI n. {} \n".format(pilLName, pilFName, nat, pilSex, pilFAI))

                """Get Nat code"""
                pilNat = get_nat_code(nat)
                if pilNat is None:
                    """defaults to Italy"""
                    pilNat = 380
                    message += ("Pilot {} {} has a unrecognized country code, defaulting to ITA \n".format(pilFName, pilLName))                 

                with Database() as db:
                    """Check if pilot exists in pilots main table"""
                    query = ("""SELECT 
                                    pilPK AS ID 
                                FROM PilotView 
                                WHERE 
                                    (pilLastName LIKE '%%{0}%%' AND pilFirstName LIKE '%%{1}%%') 
                                OR (pilLastName LIKE '%%{0}%%' AND pilFAI = {2}) 
                                LIMIT 1""".format(pilLName, pilFName, pilFAI))

                    try:
                        """Pilot exists already"""
                        # print ("Query: {} \n Rows: {} \n".format(query, db.rows(query)))
                        pil = 0 + db.fetchone(query)['ID']
                        message += ("pilot {} {} exists in pilots list: id {} \n".format(pilLName, pilFName, pil))
                    except:
                        """Check if FAI exists"""
                        query = ("""SELECT 
                                        pilPK AS ID, pilLastName AS Name 
                                    FROM PilotView 
                                    WHERE pilFAI = '{}' LIMIT 1""".format(pilFAI))
                        try:
                            """Pilot exists already"""
                            row = db.fetchone(query)
                            message += ("FAI n. {} already associated to pilot {}: id {} \n".format(pilFAI, row['Name'], row['ID']))
                        except:
                            """Insert new pilot"""
                            query = ("""INSERT INTO 
                                            `tblExtPilot`(`pilFirstName`, `pilLastName`, `pilNat`, `pilSex`, `pilFAI`) 
                                        VALUES ('{}','{}',{},'{}',{})""".format(pilFName, pilLName, pilNat, pilSex, pilFAI))
                            if not test == 1:
                                """Normal Mode"""
                                db.execute(query)
                                message += ("PILOT {} {} ADDED \n".format(pilLName, pilFName))
                            else:
                                message += ("pilot {} {} doesn't exist so we need to add \n".format(pilLName, pilFName))
                                message += ('Query: ' + query + ' \n')

        """Print messages"""
        print(message)


def main():
    """Main module"""
    test = 0
    """check parameter is good."""
    if len(sys.argv) > 1:
        file = sys.argv[1]
        if len(sys.argv) > 2:
            print('Running in TEST MODE')
            test = 1

        """Read CSV File"""
        read_membership(file, test)

    else:
        print('error: no filename found')


if __name__ == "__main__":
    main()
