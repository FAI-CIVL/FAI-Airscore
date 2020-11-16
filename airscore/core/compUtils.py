"""
Module for operations on comp / task / formulas
Use:    import compUtils
        com_id = compUtils.get_comp(tas_id)
Antonio Golfari - 2019
"""

import json
import datetime
import Defines
from db.conn import db_session


def get_comp(task_id: int):
    """Get com_id from task_id"""
    from db.tables import TblTask as T
    with db_session() as db:
        comp_id = db.query(T.comp_id).filter_by(task_id=task_id).scalar()
        return comp_id


def get_class(task_id: int):
    """Get comp_class ('PG', 'HG', 'BOTH') from task_id"""
    from db.tables import TaskObjectView as T
    with db_session() as db:
        comp_class = db.query(T.comp_class).filter_by(task_id=task_id).scalar()
        return comp_class


def get_task_date(task_id: int):
    """Get date from task_id in datetime.date format"""
    from db.tables import TblTask as T
    with db_session() as db:
        return db.query(T.date).filter_by(task_id=task_id).scalar()


def get_registration(comp_id: int):
    """Check if comp has mandatory registration"""
    from db.tables import TblCompetition as C
    with db_session() as db:
        restricted = db.query(C.restricted).filter_by(comp_id=comp_id).scalar()
        return bool(restricted)


def get_offset(task_id: int):
    from db.tables import TblTask as T
    with db_session() as db:
        return db.query(T.time_offset).filter_by(task_id=task_id).scalar()


def is_registered(civl_id: int, comp_id: int):
    """Check if pilot is registered to the comp"""
    from db.tables import TblParticipant as R
    with db_session() as db:
        return db.query(R.par_id).filter_by(comp_id=comp_id, civl_id=civl_id).scalar()


def is_ext(comp_id: int):
    """True if competition is external"""
    from db.tables import TblCompetition as C
    with db_session() as db:
        # comps = db.query(C)
        ext = db.query(C.external).filter_by(comp_id=comp_id).scalar()
        return bool(ext)


def get_comp_json_filename(comp_id: int, latest=False):
    """returns active json results filename, or latest if latest is True"""
    from db.tables import TblResultFile as R
    with db_session() as db:
        results = db.query(R.filename).filter_by(comp_id=comp_id, task_id=None)
        if latest:
            filename = results.order_by(R.ref_id.desc()).limit(1).scalar()
        else:
            filename = results.filter_by(active=1).scalar()
        return filename


def get_comp_json(comp_id: int, latest=False):
    """returns json data from comp result file, default the active one or latest if latest is True"""
    from result import open_json_file
    filename = get_comp_json_filename(comp_id, latest)
    return open_json_file(filename) if filename else 'error'


def get_nat_code(iso: str):
    """Get Country Code from ISO2 or ISO3"""
    from db.tables import TblCountryCode as CC
    if not (isinstance(iso, str) and len(iso) in (2, 3)):
        return None
    column = getattr(CC, 'natIoc') if len(iso) == 3 else getattr(CC, 'natIso' + str(len(iso)))
    with db_session() as db:
        return db.query(CC.natId).filter(column == iso).limit(1).scalar()


def get_nat_name(iso: str):
    """Get Country name from ISO2 or ISO3"""
    from db.tables import TblCountryCode as CC
    if not (type(iso) is str and len(iso) in (2, 3)):
        return None
    column = getattr(CC, 'natIoc') if len(iso) == 3 else getattr(CC, 'natIso' + str(len(iso)))
    with db_session() as db:
        return db.query(CC.natName).filter(column == iso).limit(1).scalar()


def get_nat(nat_code: int, iso: int = 3) -> str:
    from db.tables import TblCountryCode as CC
    return CC.get_by_id(nat_code).natIoc if iso == 3 else CC.get_by_id(nat_code).natIso2


def get_task_path(task_id: int):
    """ returns task folder name"""
    from db.tables import TblTask as T
    if type(task_id) is int and task_id > 0:
        with db_session() as db:
            return db.query(T.task_path).filter_by(task_id=task_id).limit(1).scalar()


def get_comp_path(comp_id: int):
    """ returns comp folder name"""
    from db.tables import TblCompetition as C
    if type(comp_id) is int and comp_id > 0:
        with db_session() as db:
            return db.query(C.comp_path).filter_by(comp_id=comp_id).limit(1).scalar()


def create_comp_path(date: datetime.date, code: str):
    """ creates comp path from input:
        - comp date
        - comp_code"""
    from pathlib import Path
    return Path(str(date.year), str(code).lower()).as_posix()


def get_task_region(task_id: int):
    """returns task region id from task_id"""
    from db.tables import TblTask as T
    with db_session() as db:
        return db.query(T.reg_id).filter_by(task_id=task_id).limit(1).scalar()


def get_area_wps(region_id: int):
    """query db get all wpts names and pks for region and put into dictionary"""
    from db.tables import TblRegionWaypoint as W
    with db_session() as db:
        wps = db.query(W.name, W.rwp_id).filter_by(reg_id=region_id, old=0).order_by(W.name).all()
        return dict(wps)


def get_wpts(task_id: int):
    """query db get all wpts names and pks for region of task and put into dictionary"""
    region_id = get_task_region(task_id)
    return get_area_wps(region_id)


def get_participants(comp_id: int):
    """gets registered pilots list from database"""
    from db.tables import TblParticipant as R
    from pilot.participant import Participant
    pilots = []
    with db_session() as db:
        results = db.query(R).filter_by(comp_id=comp_id).all()
        for p in results:
            pil = Participant(comp_id=comp_id)
            p.populate(pil)
            pilots.append(pil)
    return pilots


def get_tasks_result_files(comp_id: int):
    """ returns a list of (task_id, active result filename) for tasks in comp"""
    from db.tables import TblResultFile as R
    files = []
    with db_session() as db:
        '''getting active json files list'''
        results = db.query(R.task_id, R.filename.label('file'))
        files = results.filter(R.task_id.isnot(None)).filter_by(comp_id=comp_id, active=1).order_by(R.task_id).all()
    return files


def create_classifications(cat_id: int) -> dict:
    """create the output to generate classifications list"""
    from db.tables import TblClasCertRank as CC, TblCompetition as C, TblRanking as R, TblCertification as CCT, \
        TblClassification as CT
    rank = dict()
    with db_session() as db:
        '''get rankings definitions'''
        query = db.query(R.rank_name.label('rank'), CCT.cert_name.label('cert'), CT.female, CT.team) \
            .select_from(R) \
            .join(CC, R.rank_id == CC.c.rank_id) \
            .join(CCT, (CCT.cert_id <= CC.c.cert_id) & (CCT.comp_class == R.comp_class)) \
            .join(CT, CT.cat_id == CC.c.cat_id) \
            .filter(CC.c.cert_id > 0, CC.c.cat_id == cat_id)
        result = query.all()
    if len(result) > 0:
        for res in result:
            if res.rank in rank:
                rank[res.rank].append(res.cert)
            else:
                rank[res.rank] = [res.cert]
        rank['female'] = result.pop().female
        rank['team'] = result.pop().team
    else:
        print(f'Ranking list is empty')
    return rank


def read_rankings(comp_id: int) -> dict:
    """reads sub rankings list for the task and creates a dictionary"""
    from db.tables import TblCompetition as C
    '''get rankings definitions'''
    try:
        return create_classifications(C.get_by_id(comp_id).cat_id)
    except (TypeError, AttributeError) as e:
        print(f'Error trying to retrieve rankings for comp id {comp_id}.')
        return {}


def create_comp_code(name: str, date: datetime.date):
    """creates comp_code from name and date if nothing was given
        standard code is 6 chars + 2 numbers"""
    names = [n for n in name.split() if not any(char.isdigit() for char in str(n))]
    if len(names) >= 2:
        string = str(names[0])[0:3] + str(names[1])[0:3]
    else:
        string = str(names[0])[0:5]
    number = date.strftime('%y')
    i = 2
    code = string.upper() + number
    while not is_shortcode_unique(code, date):
        code = string.upper() + number + '_' + str(i)
        i += 1
    return code


def get_task_filepath(task_id: int):
    """ returns complete trackfile path"""
    from db.conn import db_session
    from db.tables import TaskObjectView as T
    from Defines import TRACKDIR
    from pathlib import Path
    with db_session() as db:
        task = db.query(T).filter_by(task_id=task_id).one()
        return Path(TRACKDIR, task.comp_path, task.task_path)


def get_formulas(comp_class):
    """ Gets available formula names for comp class from formula scripts in formulas folder.
        To be used if frontend to get formula multiplechoice populated
        output:
            List of formula name"""
    import os
    import importlib
    from dataclasses import dataclass

    @dataclass
    class FormulaList:
        name: str
        lib: str

    all_files = os.listdir("formulas")
    formulas = []
    for formula in all_files:
        fields = formula.split('.')
        if len(fields) > 1 and fields[1] == 'py' and not any(x in fields[0] for x in ('test', 'old')):
            ''' read formula types'''
            lib = 'formulas.' + fields[0]
            flib = importlib.import_module(lib, package=None)
            if flib.formula_class in (comp_class, 'BOTH'):
                formulas.append(FormulaList(name=flib.formula_name, lib=fields[0]))
    return formulas


def get_fsdb_task_path(task_path):
    """returns tracks folder from fsdb field tracklog_folder"""
    from pathlib import PureWindowsPath
    folder = PureWindowsPath(task_path)
    return None if not folder.parts else folder.parts[-1]


def is_shortcode_unique(shortcode: str, date: datetime.date):
    """ checks if given shortcode already exists as folder, returns True / False"""
    from pathlib import Path
    from Defines import TRACKDIR
    # print(Path(TRACKDIR, str(date.year), shortcode))
    if Path(TRACKDIR, str(date.year), shortcode).is_dir():
        return False
    return True
