"""
Module for operations on comp / task / formulas
Use:    import compUtils
        comPk = compUtils.get_comp(tasPk)

Antonio Golfari - 2019
"""

# Use your utility module.
from myconn import Database
from sqlalchemy import and_, or_

def get_comp(task_id):
    """Get comPk from tasPk"""
    from db_tables import tblTask as T
    if type(task_id) is int and task_id > 0:
        with Database() as db:
            tasks = db.session.query(T)
        return tasks.get(task_id).comPk

def get_class(tasPk):
    """Get comPk from tasPk"""
    from db_tables import TaskView as T
    if type(tasPk) is int and tasPk > 0:
        with Database() as db:
            comp_class = db.session.query(T.c.comClass).filter(T.c.tasPk==tasPk).limit(1).scalar()
        return comp_class

def get_task_date(task_id):
    """Get date from tasPk in date format"""
    from db_tables import tblTask as T
    if type(task_id) is int and task_id > 0:
        with Database() as db:
            tasks = db.session.query(T)
            # date = db.session.query(T.tasDate).filter(T.tasPk==tasPk).limit(1).scalar()
        return tasks.get(task_id).tasDate

def get_registration(comp_id):
    """Check if comp has a registration"""
    from db_tables import tblCompetition as C
    if comp_id > 0:
        with Database() as db:
            comps = db.session.query(C)
        return comps.get(comp_id).comEntryRestrict == 'registered'

def get_offset(task_id):
    from db_tables import TaskView as T
    with Database() as db:
        off = db.session.query(T.c.comTimeOffset).filter(T.c.tasPk==task_id).limit(1).scalar()
    return off

def is_registered(pil_id, comp_id):
    """Check if pilot is registered to the comp"""
    from db_tables import tblRegistration
    reg_id = 0
    if (pil_id > 0 and comp_id > 0):
        with Database() as db:
            reg_id = db.session.query(tblRegistration.regPk).filter(tblRegistration.comPk==comp_id, tblRegistration.pilPk==pil_id).limit(1).scalar()
    return reg_id

def is_ext(comp_id):
    '''True if competition is external'''
    from db_tables import tblCompetition as C
    if comp_id > 0:
        with Database() as db:
            comps = db.session.query(C)
            # ext = db.session.query(C.comExt).filter(C.comPk==comp_id).limit(1).scalar()
        return bool(comps.get(comp_id).comExt)

def get_comp_json(comp_id):
    '''returns active json results file'''
    from db_tables import tblResultFile as R
    if comp_id > 0:
        with Database() as db:
            file = db.session.query(R.refJSON).filter(and_(R.comPk==comp_id, R.tasPk==None, R.refVisible==1)).limit(1).scalar()
            return file

def get_glider(pilPk):
    """Get glider info for pilot, to be used in results"""
    from db_tables import PilotView as P
    glider = {'name': 'Unknown', 'cert': None}

    if (pilPk > 0):
        with Database() as db:
            result = db.session.query(P.c.pilGlider, P.c.pilGliderBrand, P.c.gliGliderCert).filter(P.c.pilPk==pilPk).limit(1).first()
            if result:
                glider['name'] = " ".join([result.pilGliderBrand, result.pilGlider])
                glider['cert'] = result.gliGliderCert
    return glider

def get_nat_code(iso):
    """Get Country Code from ISO2 or ISO3"""
    from db_tables import tblCountryCode as CC
    if not (type(iso) is str and len(iso) in (2,3)): return None
    column = getattr(CC,'natIso' + str(len(iso)))
    with Database() as db:
        return db.session.query(CC.natId).filter(column==iso).limit(1).scalar()

def get_task_path(task_id):
    ''''''
    from db_tables import tblTask as T
    if type(task_id) is int and task_id > 0:
        with Database() as db:
            return db.session.query(T.tasPath).filter(T.tasPk==task_id).limit(1).scalar()

def get_comp_path(comp_id):
    ''''''
    from db_tables import tblCompetition as C
    if type(comp_id) is int and comp_id > 0:
        with Database() as db:
            return db.session.query(C.comPath).filter(C.comPk==comp_id).limit(1).scalar()

def create_comp_path(comp_id, short_name, date):
    ''' upon competition creation, creates the path to store tracks.
        It will not change if comp name will be updated'''
    # maybe should be moved to correct year if comp date will change?
    from db_tables import tblCompetition as C
    import datetime
    from os import path as p
    if not(type(comp_id)is int and comp_id > 0 and isinstance(date, datetime.date)):
        return
    if not(type(short_name) is str and len(short_name) > 0):
        '''create a short name'''
        # we need the name, maybe better create a class?
    year = str(date.year)
    path = p.join(year, short_name)
    with Database() as db:
        q = db.session.query(C).get(comp_id)
        if not q.comPath:
            q.comPath = path
            db.session.commit()
        return q.comPath

def create_task_path(task_id, tcode, date):
    ''' upon competition creation, creates the path to store tracks.
        It will not change if comp name will be updated'''
    # maybe should be moved to correct year if comp date will change?
    from db_tables import tblTask as T
    import datetime
    from os import path as p
    if not(type(task_id)is int and task_id > 0 and isinstance(date, datetime.date)):
        return
    if not(type(short_name) is str and len(short_name) > 0):
        '''create a short name'''
        # we need the name
    tdate = date.strftime('%Y-%m-%d')
    path = '_'.join([tcode, tdate])
    with Database() as db:
        q = db.session.query(T).get(task_id)
        if not q.tasPath:
            q.tasPath = path
            db.session.commit()
        return q.tasPath

def get_task_region(task_id):
    from db_tables import tblTask as T
    if type(task_id) is int and task_id > 0:
        with Database() as db:
            return db.session.query(T.regPk).filter(T.tasPk==task_id).limit(1).scalar()

def get_area_wps(region_id):
    """query db get all wpts names and pks for region of task and put into dictionary"""
    from db_tables import tblRegionWaypoint as W
    if type(region_id) is int and region_id > 0:
        with Database() as db:
            wps = db.session.query(W.rwpName,
                                    W.rwpPk).filter(and_(W.regPk==region_id,
                                                        W.rwpOld==0)).order_by(W.rwpName).all()
        return dict(wps)

def get_wpts(task_id):
    region_id = get_task_region(task_id)
    return get_area_wps(region_id)
