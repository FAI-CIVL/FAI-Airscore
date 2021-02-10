"""
Ranking Library

contains
    CompRanking class
    CompAttribute class
    read        - reads ranking from database by id
    read_all    - reads all rankings from database by comp_id
    from_excel  - create CompAttribute from excel column
    from_fsdb   - create CompAttribute from fsdb custom attribute

Use: from ranking import CompAttribute

Stuart Mackintosh, Antonio Golfari - 2021
"""

from datetime import datetime
from dataclasses import dataclass
from db.tables import TblCompAttribute as CA, TblCompRanking as CR, TblCertification as Cert, TblCompetition as C
from db.conn import db_session


@dataclass
class CompAttribute:
    attr_id: int = None  # database id
    comp_id: int = None
    attr_key: str = None
    attr_value: str = None

    def as_dict(self):
        return self.__dict__

    @staticmethod
    def read(attr_id: int):
        try:
            return CompAttribute(**CA.get_by_id(attr_id).as_dict())
        except (TypeError, Exception):
            return None

    @staticmethod
    def read_all(comp_id: int) -> list:
        try:
            return [CompAttribute(**el.as_dict()) for el in CA.get_all(comp_id=comp_id)]
        except (TypeError, Exception):
            return []

    @staticmethod
    def read_meta(comp_id: int) -> list:
        try:
            return [CompAttribute(**el.as_dict()) for el in CA.get_all(comp_id=comp_id, attr_key='meta')]
        except (TypeError, Exception):
            return []

    def to_db(self):
        row = CA.from_obj(self)
        row.save_or_update()
        self.attr_id = row.attr_id


@dataclass
class CompRanking:
    rank_id: int = None  # database id
    comp_id: int = None  # comp_id
    rank_name: str = None
    rank_type: str = None  # cert, birthdate, female, nat, custom
    cert_id: int = None
    min_date: datetime.date = None
    max_date: datetime.date = None
    attr_id: int = None
    rank_value: str = None

    @property
    def description(self):
        """ text description of ranking"""
        if self.rank_type == 'overall':
            return f'All participants'
        elif self.rank_type == 'cert':
            cert = Cert.get_by_id(self.cert_id).cert_name
            return f'Gliders certification up to {cert}'
        elif self.rank_type == 'birthdate':
            if self.max_date is None:
                return f'Pilots born after {self.min_date.strftime("%d.%m.%Y")}'
            if self.min_date is None:
                return f'Pilots born before {self.max_date.strftime("%d.%m.%Y")}'
            else:
                return f'Pilots born between {self.min_date.strftime("%d.%m.%Y")} ' \
                       f'and {self.max_date.strftime("%d.%m.%Y")}'
        elif self.rank_type == 'female':
            if self.rank_value is None:
                return f'Female Pilots'
            else:
                return f'Female Pilots (calculated if at least {self.rank_value} attend)'
        elif self.rank_type == 'nat':
            return f'Pilots with nationality: {self.rank_value}'
        elif self.rank_type == 'custom':
            name = CA.get_by_id(self.attr_id).attr_value
            return f'Pilots with {name}: {self.rank_value}'

    def as_dict(self):
        return self.__dict__

    @staticmethod
    def read(rank_id: int):
        try:
            return CompRanking(**CR.get_by_id(rank_id).as_dict())
        except (TypeError, Exception):
            return None

    @staticmethod
    def read_all(comp_id: int) -> list:
        """returns a list of CompRanking objects of comp_id event, ordered by type"""
        try:
            results = [CompRanking(**el.as_dict()) for el in CR.get_all(comp_id=comp_id)]
            splitted = {el: [] for el in ('overall', 'cert', 'female', 'nat', 'birthdate', 'custom')}
            ordered = []
            for el in results:
                splitted[el.rank_type].append(el)

            ordered.extend(splitted['overall'])
            if splitted['cert']:
                certs = sorted(Cert.get_all(), key=lambda x: x.cert_order)
                cert_ranks = sorted(splitted['cert'],
                                    key=lambda x: certs.index(next(el for el in certs if el.cert_id == x.cert_id)),
                                    reverse=True)
                ordered.extend(cert_ranks)
            for key in ('female', 'nat', 'birthdate', 'custom'):
                ordered.extend(sorted(splitted[key], key=lambda x: x.rank_name))
            return ordered
        except (TypeError, Exception):
            print(f'Error trying to retrieve comp rankings')
            return []

    def to_db(self):
        row = CR.from_obj(self)
        row.save_or_update()
        self.rank_id = row.rank_id


def delete_ranking(comp_id: int, rank_id: int) -> bool:
    row = CR.get_one(rank_id=rank_id, comp_id=comp_id)
    if row:
        row.delete()
        return True
    else:
        return False


def create_rankings(comp_id: int, comp_class: str = None) -> list:
    from db.tables import TblCompetition as C

    ordered = CompRanking.read_all(comp_id)
    if not ordered:
        '''creating overall ranking'''
        print('creating overall ranking')
        create_overall_ranking(comp_id)
        ordered = CompRanking.read_all(comp_id)

    rankings = []
    ''' get certifications if needed '''
    if any(el for el in ordered if el.rank_type == 'cert'):
        if not comp_class:
            comp_class = C.get_by_id(comp_id).comp_class
        certs = sorted(Cert.get_all(comp_class=comp_class), key=lambda x: x.cert_order)
    for idx, el in enumerate(ordered, 1):
        rank = dict(rank_id=idx, rank_name=el.rank_name, rank_type=el.rank_type, description=el.description)
        if el.rank_type == 'cert':
            limit = (next(x for x in certs if x.cert_id == el.cert_id)).cert_order
            rank['certs'] = [x.cert_name for x in certs if x.cert_order <= limit]
        elif el.rank_type == 'nat':
            rank['nat'] = el.rank_value
        elif el.rank_type == 'birthdate':
            rank['min_date'] = el.min_date
            rank['max_date'] = el.max_date
        elif el.rank_type == 'female':
            rank['min_num'] = int(el.rank_value)
        elif el.rank_type == 'custom':
            rank['attr_id'] = el.attr_id
            rank['rank_value'] = el.rank_value
        rankings.append(rank)
    return rankings


def create_overall_ranking(comp_id: int):
    row = CompRanking(comp_id=comp_id, rank_name='Overall', rank_type='overall')
    row.to_db()


def get_fsdb_custom_attributes(tree) -> list:
    custom_attributes = []
    p = tree.find('FsParticipant').find('FsCustomAttributes')
    if p is not None:
        for el in p.iter('FsCustomAttribute'):
            if not el.get('name').lower() in ('live', 'team', 'fai_id', 'fai_licence'):
                custom_attributes.append(CompAttribute(attr_key='meta', attr_value=el.get('name')))
    return custom_attributes


def delete_meta(comp_id: int):
    with db_session() as db:
        try:
            db.query(CA).filter_by(comp_id=comp_id, attr_key='meta').delete(synchronize_session=False)
        except Exception:
            return False
