"""
Module for operations on comp / task / formulas
Use:    import compUtils
        com_id = compUtils.get_comp(tas_id)
Antonio Golfari - 2019
"""

import json
import datetime
import Defines
from sqlalchemy.exc import SQLAlchemyError
# Use your utility module.
from myconn import Database


def get_comp(task_id: int):
    """Get com_id from task_id"""
    from db_tables import TblTask as T
    with Database() as db:
        try:
            comp_id = db.session.query(T.comp_id).filter_by(task_id=task_id).scalar()
            return comp_id
        except SQLAlchemyError:
            print(f"No db data found")
            db.session.rollback()
            db.session.close()
            return None


def get_class(task_id: int):
    """Get comp_class ('PG', 'HG', 'BOTH') from task_id"""
    from db_tables import CompObjectView as C
    with Database() as db:
        try:
            comp_class = db.session.query(C.comp_class).filter_by(task_id=task_id).scalar()
            return comp_class
        except SQLAlchemyError:
            print(f"No db data found")
            db.session.rollback()
            db.session.close()
            return None


def get_task_date(task_id: int):
    """Get date from task_id in datetime.date format"""
    from db_tables import TblTask as T
    with Database() as db:
        try:
            task_date = db.session.query(T.date).filter_by(task_id=task_id).scalar()
            return task_date
        except SQLAlchemyError:
            print(f"No db data found")
            db.session.rollback()
            db.session.close()
            return None


def get_registration(comp_id: int):
    """Check if comp has mandatory registration"""
    from db_tables import TblCompetition as C
    with Database() as db:
        try:
            restricted = db.session.query(C.restricted).filter_by(comp_id=comp_id).scalar()
            return bool(restricted)
        except SQLAlchemyError:
            print(f"No db data found")
            db.session.rollback()
            db.session.close()
            return None


def get_offset(task_id: int):
    from db_tables import TblTask as T
    with Database() as db:
        try:
            off = db.session.query(T.time_offset).filter_by(task_id=task_id).scalar()
            return off
        except SQLAlchemyError:
            print(f"No db data found")
            db.session.rollback()
            db.session.close()
            return None


def is_registered(civl_id: int, comp_id: int):
    """Check if pilot is registered to the comp"""
    from db_tables import TblParticipant as R
    with Database() as db:
        try:
            par_id = db.session.query(R.par_id).filter_by(comp_id=comp_id, civl_id=civl_id).one().scalar()
            return par_id
        except SQLAlchemyError:
            print(f'No pilot with CIVLID {civl_id} is registered')
            db.session.rollback()
            db.session.close()
            return False


def is_ext(comp_id: int):
    """True if competition is external"""
    from db_tables import TblCompetition as C
    with Database() as db:
        try:
            # comps = db.session.query(C)
            ext = db.session.query(C.external).filter_by(comp_id=comp_id).one().scalar()
            return bool(ext)
        except SQLAlchemyError:
            print(f'No comp with ID {comp_id} is registered')
            db.session.rollback()
            db.session.close()
            return False


def get_comp_json_filename(comp_id: int, latest=False):
    """returns active json results filename, or latest if latest is True"""
    from db_tables import TblResultFile as R
    with Database() as db:
        try:
            results = db.session.query(R.filename).filter_by(comp_id=comp_id, task_id=None)
            if latest:
                filename = results.order_by(R.ref_id.desc()).limit(1).scalar()
            else:
                filename = results.filter_by(active=1).scalar()
            return filename
        except SQLAlchemyError:
            print(f"No file found")
            db.session.rollback()
            db.session.close()
            return False


def get_comp_json(comp_id: int, latest=False):
    """returns json data from comp result file, default the active one or latest if latest is True"""
    filename = get_comp_json_filename(comp_id, latest)
    if not filename:
        return "error"
    with open(Defines.RESULTDIR + filename, 'r') as myfile:
        data = myfile.read()
    if not data:
        return "error"
    return json.loads(data)


def get_nat_code(iso: str):
    """Get Country Code from ISO2 or ISO3"""
    from db_tables import TblCountryCode as CC
    if not (type(iso) is str and len(iso) in (2, 3)):
        return None
    column = getattr(CC, 'natIso' + str(len(iso)))
    with Database() as db:
        return db.session.query(CC.natId).filter(column == iso).limit(1).scalar()


def get_nat_name(iso: str):
    """Get Country name from ISO2 or ISO3"""
    from db_tables import TblCountryCode as CC
    if not (type(iso) is str and len(iso) in (2, 3)):
        return None
    column = getattr(CC, 'natIso' + str(len(iso)))
    with Database() as db:
        return db.session.query(CC.natName).filter(column == iso).limit(1).scalar()


def get_task_path(task_id: int):
    """ returns task folder name"""
    from db_tables import TblTask as T
    if type(task_id) is int and task_id > 0:
        with Database() as db:
            return db.session.query(T.task_path).filter_by(task_id=task_id).limit(1).scalar()


def get_comp_path(comp_id: int):
    """ returns comp folder name"""
    from db_tables import TblCompetition as C
    if type(comp_id) is int and comp_id > 0:
        with Database() as db:
            return db.session.query(C.comp_path).filter_by(comp_id=comp_id).limit(1).scalar()


def create_comp_path(date: datetime.date, code: str):
    """ creates comp path from input:
        - comp date
        - comp_code"""
    from pathlib import Path
    return Path(str(date.year), str(code).lower()).as_posix()


def get_task_region(task_id: int):
    """returns task region id from task_id"""
    from db_tables import TblTask as T
    with Database() as db:
        try:
            return db.session.query(T.reg_id).filter_by(task_id=task_id).limit(1).scalar()
        except SQLAlchemyError:
            print(f"No db data")
            db.session.rollback()
            db.session.close()
            return False


def get_area_wps(region_id: int):
    """query db get all wpts names and pks for region and put into dictionary"""
    from db_tables import TblRegionWaypoint as W
    with Database() as db:
        try:
            wps = db.session.query(W.name, W.rwp_id).filter_by(reg_id=region_id, old=0).order_by(W.name).all()
            return dict(wps)
        except SQLAlchemyError:
            print(f"No db data")
            db.session.rollback()
            db.session.close()
            return False


def get_wpts(task_id: int):
    """query db get all wpts names and pks for region of task and put into dictionary"""
    region_id = get_task_region(task_id)
    return get_area_wps(region_id)


def get_participants(comp_id: int):
    """gets registered pilots list from database"""
    from db_tables import TblParticipant as R
    from participant import Participant
    pilots = []
    with Database() as db:
        try:
            results = db.session.query(R).filter_by(comp_id=comp_id).all()
            for p in results:
                pil = Participant(comp_id=comp_id)
                db.populate_obj(pil, p)
                pilots.append(pil)
        except SQLAlchemyError:
            print(f"No db data")
            db.session.rollback()
            db.session.close()
    return pilots


def get_tasks_result_files(comp_id: int):
    """ returns a list of (task_id, active result filename) for tasks in comp"""
    from db_tables import TblResultFile as R
    files = []
    with Database() as db:
        try:
            '''getting active json files list'''
            results = db.session.query(R.task_id, R.filename.label('file'))
            files = results.filter(R.task_id.isnot(None)).filter_by(comp_id=comp_id, active=1).order_by(R.task_id).all()
        except SQLAlchemyError:
            print(f"No db data")
            db.session.rollback()
            db.session.close()
    return files


def read_rankings(comp_id: int):
    """reads sub rankings list for the task and creates a dictionary"""
    from db_tables import TblClasCertRank as CC, TblCompetition as C, TblRanking as R, TblCertification as CCT, \
        TblClassification as CT
    from sqlalchemy import and_
    rank = dict()
    with Database() as db:
        '''get rankings definitions'''
        try:
            class_id = db.session.query(C.cat_id).filter_by(comp_id=comp_id).scalar()
            if not class_id:
                print(f'Comp with ID {comp_id} does not exist or has no classifications id')
                db.session.close()
                return rank
            query = db.session.query(R.rank_name.label('rank'), CCT.cert_name.label('cert'), CT.female, CT.team) \
                .select_from(R) \
                .join(CC, R.rank_id == CC.c.rank_id) \
                .join(CCT, and_(CCT.cert_id <= CC.c.cert_id, CCT.comp_class == R.comp_class)) \
                .join(CT, CT.cat_id == CC.c.cat_id) \
                .filter(and_(CC.c.cert_id > 0, CC.c.cat_id == class_id))
            result = query.all()
        except SQLAlchemyError as e:
            print(f'Ranking Query Error')
            error = str(e.__dict__)
            db.session.rollback()
            db.session.close()
            return error
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


def get_task_filepath(task_id: int, session=None):
    """ returns complete trackfile path"""
    from myconn import Database
    from db_tables import TaskObjectView as T
    from Defines import TRACKDIR
    from pathlib import Path
    with Database(session) as db:
        try:
            task = db.session.query(T).filter_by(task_id=task_id).one()
            return Path(TRACKDIR, task.comp_path, task.task_path)
        except SQLAlchemyError:
            print('Error trying to retrieve flie path from database')
            db.session.rollback()
            db.session.close()
            return None


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
