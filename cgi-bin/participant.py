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

class Partecipant(object):
    """Partecipant definition, DB operations
    """

    def __init__(self, par_id=None, comp_id=None, pilot_ID=None, civl_id=None, name=None, sex=None, birthdate=None,
                nat=None, glider=None, glider_cert=None, sponsor=None, fai_id=None, fai_valid=1, xcontest_id=None,
                team=None, paid=None, status=None):

        self.par_id                     = par_id            # parPk
        self.comp_id                    = comp_id           # comPk
        self.ID                         = pilot_ID          # int
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

        pilot = Partecipant(par_id=par_id)

        with Database() as db:
            # get pilot details.
            q   = db.session.query(R).get(par_id)
            db.populate_obj(pilot, q)
        return pilot
