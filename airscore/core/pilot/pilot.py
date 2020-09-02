"""
Pilot Library

contains Pilot class and methods

Methods:
    read    - reads from database
    to_db   - write result to DB (TblTaskResult) store_result_test - write result to DB in test mode(TblTaskResult_test)

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019

"""


class Pilot(object):
    """Container class
    Attributes:
        info:           Participant Obj.
        result:         TaskResult Obj.
        track:          Track Obj.
    """

    def __init__(self, civl_id=None, name=None, sex=None, birthdate=None, nat=None, fai_id=None, fai_valid=1,
                 xcontest_id=None, pil_id=None, ranking=None, hours=None):

        self.civl_id = civl_id  # int
        self.name = name  # str
        self.sex = sex  # 'M', 'F'
        self.birthdate = birthdate  # in datetime.date (Y-m-d) format
        self.nat = nat  # str
        self.fai_id = fai_id  # str
        self.fai_valid = fai_valid  # bool
        self.xcontest_id = xcontest_id  # str
        self.pil_id = pil_id  # PilotView id
        self.ranking = ranking  # WPRS Ranking?
        self.hours = hours  # flying hours last year?

    def __setattr__(self, attr, value):
        property_names = [p for p in dir(Pilot) if isinstance(getattr(Pilot, p), property)]
        if attr in ('nat', 'sex') and type(value) is str:
            self.__dict__[attr] = value.upper()
        elif attr not in property_names:
            self.__dict__[attr] = value

    @property
    def pilot_birthdate_str(self):
        return '' if not self.birthdate else self.birthdate.strftime("%Y-%m-%d")

    @property
    def female(self):
        return 1 if self.sex == 'F' else 0

    def as_dict(self):
        return self.__dict__

    def __str__(self):
        out = ''
        out += 'Pilot:'
        out += f'{self.name} - CIVL_ID {self.civl_id} \n'
        return out
