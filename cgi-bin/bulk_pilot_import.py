"""
Reads in a CSV membership list
Use: python3 bulk_pilot_import.py [csv file name]

Antonio Golfari - 2018
"""

# Use your utility module.
from compUtils  import *
from logger     import Logger
import csv
from pathlib    import Path


def read_membership(file):

    """Read CSV File"""
    with open(file, encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            pilFAI = row[0]
            pilFName = row[1]
            pilLName = row[2]
            pilSex = row[4]
            nat = row[3]

            """Get Nat code"""
            pilNat = get_nat_code(nat)
            if pilNat is None:
                """defaults to Italy"""
                pilNat = 380
                print(f"Pilot {pilFName} {pilLName} has a unrecognized country code, defaulting to ITA \n")

            with Database() as db:
                """Check if pilot exists in pilots main table"""
                query = """SELECT
                                `pilPK` AS `ID`
                            FROM `PilotView`
                            WHERE
                                (`pilLastName` LIKE '%%{0}%%' AND `pilFirstName` LIKE '%%{1}%%')
                            OR (`pilLastName` LIKE '%%{0}%%' AND `pilFAI` = {2})
                            LIMIT 1"""
                params = [pilLName, pilFName, pilFAI]

                try:
                    """Pilot exists already"""
                    # print ("Query: {} \n Rows: {} \n".format(query, db.rows(query)))
                    pil = 0 + db.fetchone(query, params)['ID']
                    print(f"pilot {pilLName} {pilFName} exists in pilots list: id {pil} \n")
                except:
                    """Check if FAI exists"""
                    query = """SELECT
                                    `pilPK` AS `ID`, `pilLastName` AS `Name`
                                FROM `PilotView`
                                WHERE `pilFAI` = %s LIMIT 1"""
                    try:
                        """Pilot exists already"""
                        row = db.fetchone(query, [pilFAI])
                        print(f"FAI n. {pilFAI} already associated to pilot {row['Name']}: id {row['ID']} \n")
                    except:
                        """Insert new pilot"""
                        query = """ INSERT INTO `tblExtPilot`
                                        (`pilFirstName`,
                                        `pilLastName`,
                                        `pilNat`,
                                        `pilSex`,
                                        `pilFAI`)
                                    VALUES
                                        (%s,%s,%s,%s,%s)"""
                        params = [pilFName, pilLName, pilNat, pilSex, pilFAI]

                        """Normal Mode"""
                        pil_id = db.execute(query, params)
                        print(f"PILOT {pilLName} {pilFName} ADDED with id {pil_id}\n")

def main(args):
    """Main module"""
    my_file = Path(str(args[0]))

    '''create logging and disable output'''
    Logger('ON', 'bulk_pilots_import.txt')

    """Check if file exists"""
    if not my_file.is_file():
        print (f"Reading error: {str(args[0])} does not exist")
        ''' restore stdout function '''
        Logger('OFF')
        print(0)
        exit()

    """Read CSV File"""
    read_membership(file)

    ''' restore stdout function '''
    Logger('OFF')
    print(1)

if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1]

            and len(sys.argv) == 3):
        print("number of arguments != 2 and/or task_id not a number")
        print("Use: python3 bulk_igc_reader.py <taskPk> <zipfile>")
        exit()

    main(sys.argv[1:])
