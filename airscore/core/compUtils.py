"""
Module for operations on comp / task / formulas
Use:    import compUtils
        com_id = compUtils.get_comp(tas_id)
Antonio Golfari - 2019
"""

import datetime
import json
from pathlib import Path

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


def get_comp_json_filename(comp_id: int, latest: bool = False, overview: bool = False):
    """returns active json results filename, or latest if latest is True"""
    from db.tables import TblResultFile as R

    with db_session() as db:
        results = db.query(R.filename).filter_by(comp_id=comp_id, task_id=None)
        if latest:
            filename = results.order_by(R.ref_id.desc()).limit(1).scalar()
        elif overview:
            filename = results.filter(R.filename.like('%Overview%')).limit(1).scalar()
        else:
            filename = results.filter_by(active=1).scalar()
        return filename


def get_comp_json(comp_id: int, latest: bool = False, overview: bool = False):
    """returns json data from comp result file, default the active one or latest if latest is True"""
    from result import open_json_file

    data = open_json_file(get_comp_json_filename(comp_id, latest, overview))
    return data if isinstance(data, dict) else 'error'


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

    if isinstance(task_id, int) and task_id > 0:
        return T.get_by_id(task_id).task_path


def get_comp_path(comp_id: int):
    """ returns comp folder name"""
    from db.tables import TblCompetition as C

    if isinstance(comp_id, int) and comp_id > 0:
        return C.get_by_id(comp_id).comp_path


def create_comp_path(date: datetime.date, code: str):
    """creates comp path from input:
    - comp date
    - comp_code"""

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
    from db.tables import TblParticipant as R, TblCompAttribute as CA, TblParticipantMeta as PA
    from pilot.participant import Participant

    pilots = []
    with db_session() as db:
        results = db.query(R).filter_by(comp_id=comp_id) or []
        attr_list = db.query(CA).filter_by(comp_id=comp_id) or []
        pilots_attributes = db.query(PA).filter(PA.attr_id.in_(el.attr_id for el in attr_list)) or []
        for p in results:
            pil = Participant(comp_id=comp_id)
            p.populate(pil)
            # print(f'pilot {pil.name}, {pil.custom}')
            for el in attr_list:
                val = next((x.meta_value for x in pilots_attributes
                            if x.attr_id == el.attr_id and x.par_id == p.par_id), None)
                # print(f'attr {el.attr_name} ({el.attr_id}), {val}')
                pil.custom[el.attr_id] = val
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


def create_comp_code(name: str, date: datetime.date) -> str:
    """creates comp_code from name and date if nothing was given
    standard code is 6 chars + 2 numbers, checks that folder does not exist, otherwise adds an index.
    """
    import random

    from calcUtils import toBase62

    names = [n for n in name.split() if not any(char.isdigit() for char in str(n))]
    if len(names) >= 2:
        string = str(names[0])[0:3] + str(names[1])[0:3]
    else:
        string = str(names[0])[0:5]
    number = date.strftime('%y')
    i = 2
    code = string.upper() + number
    while True:
        if not is_shortcode_unique(code, date):
            if i < 60:
                code = string.upper() + number + '_' + toBase62(i)
                i += 1
            else:
                '''generate random 6 char'''
                code = ''.join(random.choices(string.ascii_uppercase, k=6)) + number
        else:
            return code


def get_task_filepath(task_id: int):
    """ returns complete trackfile path"""
    from pathlib import Path

    from db.conn import db_session
    from db.tables import TaskObjectView as T
    from Defines import TRACKDIR

    with db_session() as db:
        task = db.query(T).filter_by(task_id=task_id).one()
        return Path(TRACKDIR, task.comp_path, task.task_path)


def get_formulas(comp_class):
    """Gets available formula names for comp class from formula scripts in formulas folder.
    To be used if frontend to get formula multiplechoice populated
    output:
        List of formula name"""
    import importlib
    import os
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

    if Path(Defines.TRACKDIR, str(date.year), shortcode).is_dir():
        return False
    return True


def get_tasks_details(comp_id: int) -> list:
    from db.tables import TaskObjectView as T

    with db_session() as db:
        results = (
            db.query(
                T.task_id,
                T.reg_id,
                T.region_name,
                T.task_num,
                T.task_name,
                T.date,
                T.opt_dist,
                T.comment,
                T.window_open_time,
                T.task_deadline,
                T.window_close_time,
                T.start_time,
                T.start_close_time,
                T.track_source,
                T.locked,
                T.cancelled
            )
            .filter_by(comp_id=comp_id)
            .all()
        )

        return [row._asdict() for row in results] if results else []

