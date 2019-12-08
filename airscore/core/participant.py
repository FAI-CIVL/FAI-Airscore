"""
Competition Library

contains
    Partecipant class
    function to write comp result json file
    function to write comp result fsdb file

Use: from participant import Partecipant

Stuart Mackintosh Antonio Golfari - 2019
"""

from myconn     import Database
from calcUtils  import json, get_datetime, decimal_to_seconds, time_difference
import jsonpickle
import Defines

class Participant(object):
    """Partecipant definition, DB operations
    """

    def __init__(self, par_id=None, comp_id=None, ID=None, civl_id=None, name=None, sex=None, birthdate=None,
                nat=None, glider=None, glider_cert=None, sponsor=None, fai_id=None, fai_valid=1, xcontest_id=None,
                team=None, nat_team=1, paid=None, status=None):

        self.par_id                     = par_id            # parPk
        self.comp_id                    = comp_id           # comPk
        self.ID                         = ID                # int
        self.civl_id                    = civl_id           # int
        self.name                       = name              # str
        self.sex                        = sex               # 'M', 'F'
        self.birthdate                  = birthdate         # in datetime.date (Y-m-d) format
        self.nat                        = nat               # str
        self.glider                     = glider            # str
        self.glider_cert                = glider_cert       # str
        self.sponsor                    = sponsor           # str
        self.fai_id                     = fai_id            # str
        self.fai_valid                  = fai_valid         # bool
        self.xcontest_id                = xcontest_id       # str
        self.team                       = team              # ?
        self.nat_team                   = nat_team          # default 1
        self.paid                       = paid              # bool
        self.status                     = status            # 'confirmed', 'waiting list', 'wild card', ?
        self.pil_id                     = None              # PilotView id
        self.results                    = dict()

    def __setattr__(self, attr, value):
        if attr in ('name', 'glider') and type(value) is str:
            value = value.title()
        elif attr in ('nat', 'sex') and type(value) is str:
            value = value.upper()
        self.__dict__[attr] = value

    @property
    def pilot_birthdate_str(self):
        from datetime import datetime
        return self.birthdate.strftime("%Y-%m-%d")

    def as_dict(self):
        return self.__dict__

    def __str__(self):
        out = ''
        out += 'Pilot:'
        out += f'{self.name} - CIVL_ID {self.civl_id} \n'
        out += f'{self.glider}  | {self.sponsor}\n'
        return out

    @staticmethod
    def read(par_id):
        """Reads pilot registration from database
        takes parPk as argument"""
        from db_tables import RegistrationView as R

        if not (type(par_id) is int and par_id > 0):
            print(f"par_id needs to be int > 0, {par_id} was given")
            return None

        pilot = Participant(par_id=par_id)

        with Database() as db:
            # get pilot details.
            q   = db.session.query(R).get(par_id)
            db.populate_obj(pilot, q)
        return pilot

def import_participants_from_excel(comp_id, filename):
    '''Gets participants from external file;
    Returns a list of Participant objects
    - read Airtribune XSLX file

    excel file format:
    column name on row 1
    columns:
    id,	name,	nat,	female,	birthday,	glider,	color,	sponsor,	fai_licence,	CIVILID,	club,	team,	class
    '''
    from logger         import Logger
    from openpyxl       import load_workbook

    '''create logging and disable output'''
    Logger('ON', 'import_participants.txt')

    print(f"Comp ID: {comp_id} | filename: {filename}")

    '''load excel file'''
    try:
        workbook = load_workbook(filename=filename)
    except:
        print('excel file importing error')
        return

    '''active sheet'''
    sheet = workbook.active

    '''check validity'''
    if not (sheet['A1'].value == 'id'):
        exit()

    pilots = []
    for row in sheet.iter_rows(min_row=2,
                               min_col=1,
                               max_col=13,
                               values_only=True):
        if not row[0]:
            break
        pil = Participant(ID=row[0], comp_id=comp_id, civl_id=row[9], name=row[1], nat=row[2],
                sex='F' if row[3]==1 else 'M', glider=row[5], sponsor=row[7],
                team=row[11], fai_id=row[8], fai_valid=0 if row[8] is None else 1)
        pilots.append(pil)

    ''' now restore stdout function '''
    Logger('OFF')

    return pilots
