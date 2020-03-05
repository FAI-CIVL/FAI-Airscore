"""
Module for operations on comp / task / formulas
Use:    import compUtils
        com_id = compUtils.get_comp(tas_id)
Antonio Golfari - 2019
"""

import json

from sqlalchemy import and_

import Defines
# Use your utility module.
from myconn import Database


def get_comp(task_id):
    """Get com_id from tas_id"""
    from db_tables import TblTask as T
    if type(task_id) is int and task_id > 0:
        with Database() as db:
            tasks = db.session.query(T)
        return tasks.get(task_id).comp_id


def get_class(task_id):
    """Get comp_id from task_id"""
    from db_tables import TblTask as T, TblCompetition as C
    if type(task_id) is int and task_id > 0:
        with Database() as db:
            result = db.session.query(C).join(T, T.comp_id == C.comp_id).filter(T.task_id == task_id).one()
        return result.comp_class


def get_task_date(task_id):
    """Get date from task_id in date format"""
    from db_tables import TblTask as T
    if type(task_id) is int and task_id > 0:
        with Database() as db:
            task = db.session.query(T).get(task_id)
        return task.date


def get_registration(comp_id):
    """Check if comp has a registration"""
    from db_tables import TblCompetition as C
    if comp_id > 0:
        with Database() as db:
            comps = db.session.query(C)
        return comps.get(comp_id).restricted == 1


def get_offset(task_id):
    from db_tables import TblTask as T
    with Database() as db:
        off = db.session.query(T).get(task_id).time_offset
    return off


def is_registered(civl_id, comp_id):
    """Check if pilot is registered to the comp"""
    from db_tables import TblParticipant as R
    from sqlalchemy.exc import SQLAlchemyError
    if civl_id > 0 and comp_id > 0:
        with Database() as db:
            try:
                pilot = db.session.query(R).filter(R.comp_id == comp_id, R.civl_id == civl_id).one()
                return pilot.par_id
            except SQLAlchemyError:
                print(f'No pilot with CIVLID {civl_id} is registered')
    return False


def is_ext(comp_id):
    """True if competition is external"""
    from db_tables import TblCompetition as C
    if comp_id > 0:
        with Database() as db:
            comps = db.session.query(C)
            # ext = db.session.query(C.comExt).filter(C.comp_id==comp_id).limit(1).scalar()
        return bool(comps.get(comp_id).external)


def get_comp_json_filename(comp_id):
    """returns active json results file"""
    from db_tables import TblResultFile as R
    from sqlalchemy.exc import SQLAlchemyError
    with Database() as db:
        try:
            result = db.session.query(R).filter(and_(R.comp_id == comp_id, R.task_id.is_(None), R.active == 1)).one()
            return result.filename
        except SQLAlchemyError:
            print(f"No file found")
    return None


def get_comp_json(comp_id):
    filename = get_comp_json_filename(comp_id)
    if not filename:
        return "error"
    with open(Defines.RESULTDIR + filename, 'r') as myfile:
        data = myfile.read()
    if not data:
        return "error"
    return json.loads(data)


def get_nat_code(iso):
    """Get Country Code from ISO2 or ISO3"""
    from db_tables import TblCountryCode as CC
    if not (type(iso) is str and len(iso) in (2, 3)): return None
    column = getattr(CC, 'natIso' + str(len(iso)))
    with Database() as db:
        return db.session.query(CC.natId).filter(column == iso).limit(1).scalar()


def get_task_path(task_id):
    """ """
    from db_tables import TblTask as T
    if type(task_id) is int and task_id > 0:
        with Database() as db:
            return db.session.query(T.task_path).filter(T.task_id == task_id).limit(1).scalar()


def get_comp_path(comp_id):
    """ """
    from db_tables import TblCompetition as C
    if type(comp_id) is int and comp_id > 0:
        with Database() as db:
            return db.session.query(C.comp_path).filter(C.comp_id == comp_id).limit(1).scalar()


def create_comp_path(date, code):
    from os import path
    return path.join(str(date.year), str(code).lower())


def get_task_region(task_id):
    from db_tables import TblTask as T
    if type(task_id) is int and task_id > 0:
        with Database() as db:
            return db.session.query(T.reg_id).filter(T.task_id == task_id).limit(1).scalar()


def get_area_wps(region_id):
    """query db get all wpts names and pks for region of task and put into dictionary"""
    from db_tables import TblRegionWaypoint as W
    if type(region_id) is int and region_id > 0:
        with Database() as db:
            wps = db.session.query(W.name,
                                   W.rwp_id).filter(and_(W.reg_id == region_id,
                                                        W.old == 0)).order_by(W.name).all()
        return dict(wps)


def get_wpts(task_id):
    region_id = get_task_region(task_id)
    return get_area_wps(region_id)


def get_participants(comp_id):
    """gets registered pilots list from database"""
    from db_tables import TblParticipant as R
    from participant import Participant

    with Database() as db:
        q = db.session.query(R).filter(R.comp_id == comp_id)
        result = q.all()
        pilots = []
        for p in result:
            pil = Participant(comp_id=comp_id)
            db.populate_obj(pil, p)
            pilots.append(pil)
    return pilots


def get_tasks_result_files(comp_id):
    from db_tables import TblResultFile as R
    files = []
    with Database() as db:
        '''getting active json files list'''
        files = db.session.query(R.task_id,
                                 R.filename.label('file')).filter(and_(R.comp_id == comp_id,
                                                                       R.task_id.isnot(None), R.active == 1)).order_by(
                                                                       R.task_id).all()
    return files


def read_rankings(comp_id):
    """reads sub rankings list for the task and creates a dictionary"""
    from db_tables import TblClasCertRank as CC, TblCompetition as C, TblRanking as R, TblCertification as CCT, \
        TblClassification as CT
    from sqlalchemy import and_
    from sqlalchemy.exc import SQLAlchemyError

    rank = dict()

    with Database() as db:
        '''get rankings definitions'''
        try:
            class_id = db.session.query(C).get(comp_id).cat_id
            query = db.session.query(R.rank_name.label('rank'), CCT.cert_name.label('cert'), CT.female,
                                     CT.team).select_from(R).join(CC, R.rank_id == CC.rank_id) \
                .join(CCT, and_(CCT.cert_id <= CC.cert_id, CCT.comp_class == R.comp_class)
                      ).join(CT, CT.cat_id == CC.cat_id).filter(and_(CC.cert_id > 0, CC.cat_id == class_id))
            result = query.all()
        except SQLAlchemyError:
            print(f'Ranking Query Error')

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


def create_comp_code(name, date):
    """creates comp_code from name and date if nothing was given
        standard code is 6 chars + 2 numbers"""
    names = [n for n in name.split() if not any(char.isdigit() for char in str(n))]
    if len(names) >= 2:
        string = str(names[0])[0:3] + str(names[1])[0:3]
    else:
        string = str(names[0])[0:5]
    number = date.strftime('%y')
    return string.upper() + number


def get_task_filepath(task_id, session=None):
    """ returns complete trackfile path"""
    from myconn import Database
    from db_tables import TaskObjectView as T
    from sqlalchemy.exc import SQLAlchemyError
    from Defines import FILEDIR
    from os import path as p

    with Database(session) as db:
        try:
            task = db.session.query(T).get(task_id)
            return p.join(FILEDIR, task.comp_path, task.task_path)
        except SQLAlchemyError:
            print('Error trying to retrieve flie path from database')
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
