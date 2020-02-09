"""
Participant Library

contains
    Partecipant class
    function to import participants from excel file

Use: from participant import Participant

Stuart Mackintosh Antonio Golfari - 2019
"""

from logger import Logger
from openpyxl import load_workbook
from civlrankings import create_participant_from_CIVLID, create_participant_from_name
from calcUtils import get_date
from myconn import Database
from db_tables import tblParticipant
from sqlalchemy.exc import SQLAlchemyError


class Participant(object):
    """Participant definition, DB operations
    """

    def __init__(self, par_id=None, comp_id=None, ID=None, civl_id=None, name=None, sex=None, birthdate=None,
                 nat=None, glider=None, glider_cert=None, sponsor=None, fai_id=None, fai_valid=1, xcontest_id=None,
                 team=None, nat_team=1, status=None, ranking=None, paid=None):

        self.par_id = par_id  # parPk
        self.comp_id = comp_id  # comPk
        self.ID = ID  # int
        self.civl_id = civl_id  # int
        self.name = name  # str
        self.sex = sex  # 'M', 'F'
        self.birthdate = birthdate  # in datetime.date (Y-m-d) format
        self.nat = nat  # str
        self.glider = glider  # str
        self.glider_cert = glider_cert  # str
        self.sponsor = sponsor  # str
        self.fai_id = fai_id  # str
        self.fai_valid = fai_valid  # bool
        self.xcontest_id = xcontest_id  # str
        self.team = team  # ?
        self.nat_team = nat_team  # default 1
        self.paid = paid  # bool
        self.status = status  # 'confirmed', 'waiting list', 'wild card', 'cancelled', ?
        self.ranking = ranking  # WPRS Ranking?
        self.live_id = None     # int
        self.pil_id = None  # PilotView id

    def __setattr__(self, attr, value):
        if attr in ('name', 'glider') and type(value) is str:
            value = value.title()
        elif attr in ('nat', 'sex') and type(value) is str:
            value = value.upper()
        self.__dict__[attr] = value

    @property
    def pilot_birthdate_str(self):
        return self.birthdate.strftime("%Y-%m-%d")

    @property
    def female(self):
        return 1 if self.sex == 'F' else 0

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
            q = db.session.query(R).get(par_id)
            db.populate_obj(pilot, q)
        return pilot

    @staticmethod
    def from_dict(d):
        par = Participant()
        for key, value in d.items():
            if hasattr(par, key):
                setattr(par, key, value)
        return par

    def to_db(self, session=None):
        """stores Participant to AirScore database"""

        with Database(session) as db:
            try:
                if not self.par_id:
                    pil = tblParticipant()
                else:
                    pil = db.session.query(tblParticipant).get(self.par_id)
                pil.comPk = self.comp_id
                pil.CIVLID = self.civl_id
                pil.parID = self.ID
                pil.parName = self.name
                pil.parBirthdate = self.birthdate
                pil.parSex = self.sex
                pil.parNat = self.nat
                pil.parGlider = self.glider
                pil.parCert = self.glider_cert
                pil.parSponsor = self.sponsor
                pil.parValidFAI = self.fai_valid
                pil.parFAI = self.fai_id,
                pil.parXC = self.xcontest_id
                pil.LiveID = self.live_id
                pil.parTeam = self.team
                pil.parNatTeam = self.nat_team
                pil.parStatus = self.status
                pil.parRanking = self.ranking
                pil.parPaid = self.paid
                pil.parHours = None
                pil.pilPk = self.pil_id

                if not self.par_id:
                    db.session.add(pil)
                db.session.flush()

            except SQLAlchemyError:
                print('Participant storing error')
                db.session.rollback()
                return None

            self.par_id = pil.parPk
        return self.par_id

    @staticmethod
    def from_fsdb(pil, from_CIVL=0):
        """gets pilot obj. from FSDB file
            Input:
                - pil:          lxml.etree: FsParticipant section
                - from_CIVL:    BOOL: look for pilot on CIVL database"""

        CIVLID = None if not pil.get('CIVLID') else int(pil.get('CIVLID'))
        name = pil.get('name')
        # print(CIVLID, name)
        pilot = None
        if from_CIVL:
            '''check CIVL database'''
            if CIVLID:
                pilot = create_participant_from_CIVLID(CIVLID)
            else:
                pilot = create_participant_from_name(name)
        '''check if we have a result and name is similar'''
        if not (pilot and any(n in pilot.name for n in name)):
            '''get all pilot info from fsdb file'''
            if from_CIVL:
                print('*** no result in CIVL database, getting data from FSDB file')
            pilot = Participant(name=name, civl_id=CIVLID)
            pilot.sex = 'F' if int(pil.get('female') if pil.get('female') else 0) > 0 else 'M'
            pilot.nat = pil.get('nat_code_3166_a3')

        pilot.birthdate = get_date(pil.get('birthday'))
        pilot.ID = int(pil.get('id'))
        pilot.glider = pil.get('glider')
        pilot.sponsor = pil.get('sponsor')
        """check fai is int"""
        pilot.fai_valid = int(pil.get('fai_licence') if pil.get('fai_licence') else 0)

        return pilot


def import_participants_from_excel(comp_id, filename, from_CIVL=False):
    """Gets participants from external file (Airtribune Participants list in Excel format;
    Returns a list of Participant objects
    Input:
        comp_id:    INT comPk
        filename:   STR filename
        from_CIVL:  BOOL retrieve data from CIVL database using CIVLID
    - read Airtribune XSLX file

    excel file format:
    column name on row 1
    columns:
    id,name,nat,female,birthday,glider,color,sponsor,fai_licence,CIVILID,club,team,class,Live(optional)
    """

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
                               max_col=14,
                               values_only=True):
        if not row[0]:
            'EOF'
            break

        ''' Check CIVL database if active'''
        pil = None
        if from_CIVL and row[9]:
            pil = create_participant_from_CIVLID(row[9])
        if pil is None:
            pil = Participant(civl_id=row[9], name=row[1], nat=row[2], sex='F' if row[3] == 1 else 'M')
        pil.ID = row[0]
        pil.comp_id = comp_id
        pil.birthdate = None if row[4] is None else row[4].date()   # row[4] should be datetime
        pil.glider = row[5]
        pil.sponsor = row[7]
        pil.team = row[11]
        pil.fai_id = row[8]
        pil.fai_valid = 0 if row[8] is None else 1
        pil.Live = row[13]
        pilots.append(pil)

    ''' now restore stdout function '''
    Logger('OFF')

    return pilots


def mass_import_participants(comp_id, pilots):
    """get participants to update from the list"""
    # TODO check if we already have participants for the comp before inserting, and manage update instead

    insert_mappings = []
    update_mappings = []
    for pil in pilots:
        mapping = {'parPk': pil.par_id,
                   'comPk': comp_id,
                   'CIVLID': pil.civl_id,
                   'parID': pil.ID,
                   'parName': pil.name,
                   'parBirthdate': pil.birthdate,
                   'parSex': pil.sex,
                   'parNat': pil.nat,
                   'parGlider': pil.glider,
                   'parCert': pil.glider_cert,
                   'parSponsor': pil.sponsor,
                   'parValidFAI': pil.fai_valid,
                   'parFAI': pil.fai_id,
                   'parXC': pil.xcontest_id,
                   'parLive': pil.live_id,
                   'parTeam': pil.team,
                   'parNatTeam': pil.nat_team,
                   'parStatus': pil.status,
                   'parRanking': pil.ranking,
                   'parPaid': pil.paid,
                   'parHours': None,
                   'pilPk': pil.pil_id}
        if mapping['parPk']:
            update_mappings.append(mapping)
        else:
            insert_mappings.append(mapping)

    '''update database'''
    with Database() as db:
        try:
            if len(insert_mappings) > 0:
                db.session.bulk_insert_mappings(tblParticipant, insert_mappings)
            if len(update_mappings) > 0:
                db.session.bulk_update_mappings(tblParticipant, update_mappings)
            db.session.commit()
        except SQLAlchemyError:
            print(f'update all participants on database gave an error')
            db.session.rollback()
            return False

    return True
