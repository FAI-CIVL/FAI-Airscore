"""
Reads in a CSV membership list
Use: python3 bulk_pilot_import.py [csv file name]

Antonio Golfari - 2018
"""

import csv
from pathlib import Path

# Use your utility module.
from compUtils import *


def read_membership(file):
    """Read CSV File"""
    from db.tables import PilotView as P
    from db.conn import db_session
    from sqlalchemy import and_, or_

    with open(file, encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        with db_session() as db:
            for row in csv_reader:
                fai_id = row[0]
                first_name = row[1]
                last_name = row[2]
                sex = row[4]
                nat = row[3]

                """Get Nat code"""
                nat = get_nat_code(nat)
                if nat is None:
                    """defaults to Italy"""
                    nat = 380
                    print(f"Pilot {first_name} {last_name} has a unrecognized country code, defaulting to ITA \n")

                cond1 = f'%{last_name}%'
                cond2 = f'%{first_name}%'

                """Check if pilot exists in pilots main table"""
                pil_id = 0
                result = db.query(P.pil_id).filter(or_(
                    and_(P.last_name.like(cond1), P.first_name.like(cond2)),
                    and_(P.last_name.like(cond2), P.first_name.like(cond1)),
                    and_(P.last_name.like(cond1), P.fai_id == fai_id))).all()
                if len(result) == 1:
                    '''we found the pilot'''
                    pil_id = result.pop().pil_id
                elif len(result) > 1:
                    '''try to see if we have just one pilot among the fixed database'''
                    candidate = [x.pil_id for x in result if x.pil_id < 10000]
                    if len(candidate) == 1:
                        pil_id = candidate.pop().pil_id
                if not pil_id:
                    """Check if FAI exists"""
                    result = db.query(P.pil_id).filter(P.fai_id == fai_id).all()
                    if len(result) == 1:
                        pil_id = result.pop().pil_id
                if not pil_id:
                    """Insert new pilot"""
                    print(f'Pilot does not seem to be in database')
                else:
                    print(f'Found Pilot {first_name} {last_name} with ID {pil_id}')
                    row.append(pil_id)


def main(args):
    """Main module"""
    comp_id = int(args[0])
    my_file = Path(str(args[1]))

    '''create logging and disable output'''
    # Logger('ON', 'bulk_pilots_import.txt')

    """Check if file exists"""
    if not my_file.is_file():
        print(f"Reading error: {str(args[0])} does not exist")
        ''' restore stdout function '''
        # Logger('OFF')
        print(0)
        exit()

    """Read CSV File"""
    reader = read_membership(my_file)

    ''' restore stdout function '''
    # Logger('OFF')
    for p in reader:
        print(f'{p[1]} - {p[-1]}')


if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1]

            and len(sys.argv) == 3):
        print("number of arguments != 2 and/or task_id not a number")
        print("Use: python3 bulk_igc_reader.py <task_id> <csv file>")
        exit()

    main(sys.argv[1:])
