"""
Reads in a CSV membership list
Use: python3 bulk_pilot_import.py [csv file name]

Antonio Golfari - 2018
"""

import csv
from pathlib import Path

# Use your utility module.
from compUtils import *
from logger import Logger


def read_membership(file):
    """Read CSV File"""
    from db_tables import PilotView as P
    from db_tables import tblExtPilot as E
    from myconn import Database
    from sqlalchemy import and_, or_

    with open(file, encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        with Database() as db:
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

                cond1 = f'%{pilLName}%'
                cond2 = f'%{pilFName}%'

                """Check if pilot exists in pilots main table"""
                pil_id = 0
                result = db.session.query(P.pilPk).filter(or_(
                    and_(P.pilLastName.like(cond1), P.pilFirstName.like(cond2)),
                    and_(P.pilLastName.like(cond2), P.pilFirstName.like(cond1)),
                    and_(P.pilLastName.like(cond1), P.pilFAI == pilFAI))).all()
                if len(result) == 1:
                    '''we found the pilot'''
                    pil_id = result.pop().pilPk
                elif len(result) > 1:
                    '''try to see if we have just one pilot among the fixed database'''
                    candidate = [x.pilPk for x in result if x.pilPk < 10000]
                    if len(candidate) == 1: pil_id = candidate.pop().pilPk
                if not pil_id:
                    """Check if FAI exists"""
                    result = db.session.query(P.pilPk).filter(P.pilFAI == pilFAI).all()
                    if len(result) == 1:
                        pil_id = result.pop().pilPk
                if not pil_id:
                    """Insert new pilot"""
                    print(f'Pilot does not seem to be in database, adding to external table')
                    pilot = E(pilFirstName=pilFName, pilLastName=pilLName, pilNat=pilNat, pilSex=pilSex, pilFAI=pilFAI)
                    pil_id = db.session.add(pilot)
                    db.session.commit()
                    row.append(0)
                else:
                    print(f'Found Pilot {pilFName} {pilLName} with ID {pil_id}')
                    row.append(pil_id)


def main(args):
    """Main module"""
    comp_id = int(args[0])
    my_file = Path(str(args[1]))

    '''create logging and disable output'''
    Logger('ON', 'bulk_pilots_import.txt')

    """Check if file exists"""
    if not my_file.is_file():
        print(f"Reading error: {str(args[0])} does not exist")
        ''' restore stdout function '''
        Logger('OFF')
        print(0)
        exit()

    """Read CSV File"""
    reader = read_membership(my_file)

    ''' restore stdout function '''
    Logger('OFF')
    for p in reader:
        print(f'{p[1]} - {p[-1]}')


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1]

            and len(sys.argv) == 3):
        print("number of arguments != 2 and/or task_id not a number")
        print("Use: python3 bulk_igc_reader.py <taskPk> <csv file>")
        exit()

    main(sys.argv[1:])
