"""
Module for operations on comp / task / formulas
Use:    import compUtils
        comPk = compUtils.get_comp(tasPk)

Antonio Golfari - 2018
"""

# Use your utility module.
from myconn import Database

def get_comp(tasPk):
    """Get comPk from tasPk"""
    if str(tasPk).isdigit() and tasPk > 0:
        with Database() as db:
            query = """    SELECT
                                `comPk`
                            FROM
                                `tblTask`
                            WHERE
                                `tasPk` = %s """
            if db.rows(query, [tasPk]) > 0:
                return db.fetchone(query, [tasPk])['comPk']
    else:
        print(f"Error: {tasPk} is NOT a valid task ID")


def get_class(tasPk):
    """Get comPk from tasPk"""
    if str(tasPk).isdigit() and tasPk > 0:
        with Database() as db:
            query = """    SELECT
                                comClass
                            FROM
                                TaskView
                            WHERE
                                tasPk = %s
                            LIMIT 1"""
            if db.rows(query, [tasPk]) > 0:
                return db.fetchone(query, [tasPk])['comClass']
    else:
        print (f"Error: {tasPk} is NOT a valid task ID")

def get_task_date(tasPk):
    """Get date from tasPk in date format"""
    if str(tasPk).isdigit() and tasPk > 0:
        with Database() as db:
            query = """    SELECT
                                `tasDate`
                            FROM
                                `TaskView`
                            WHERE
                                `tasPk` = %s
                            LIMIT 1"""
            if db.rows(query, [tasPk]) > 0:
                date = db.fetchone(query, [tasPk])['tasDate']
                return date
    else:
        print (f"Error: {tasPk} is NOT a valid task ID")

def get_registration(comPk):
    """Check if comp has a registration"""
    reg = 0
    if comPk > 0:
        with Database() as db:
            query = """    SELECT (CASE WHEN
                                `comEntryRestrict` LIKE '%%registered%%' THEN 1 ELSE 0
                            END) AS `Reg`
                            FROM
                                `tblCompetition`
                            WHERE
                                `comPk` = %s
                            LIMIT 1"""
            if db.rows(query, [comPk]) > 0:
                reg = db.fetchone(query, [comPk])['Reg']
    else:
        print("comp registration - Error: NOT a valid ID \n")

    return reg

def get_offset(task_id):
    with Database() as db:
        query = """    SELECT
                            `comTimeOffset` AS offset
                        FROM
                            `TaskView`
                        WHERE
                            `tasPk` = %s
                        LIMIT 1"""
        return db.fetchone(query, [task_id])['offset']

def get_registered_pilots(comPk):
    """Gets list of registered pilots for the comp"""
    list = []
    if comPk:
        with Database() as db:
            query = """    SELECT
                                R.`pilPk`,
                                P.`pilFirstName`,
                                P.`pilLastName`,
                                P.`pilFAI`,
                                P.`pilXContestUser`
                            FROM
                                `tblRegistration` R
                            JOIN `PilotView` P USING(`pilPk`)
                            WHERE
                                R.`comPk` = %s"""
            if db.rows(query, [comPk]) > 0:
                """create a list from results"""
                list = [{   'pilPk': row['pilPk'],
                            'pilFirstName': row['pilFirstName'],
                            'pilLastName': row['pilLastName'],
                            'pilFAI': row['pilFAI'],
                            'pilXContestUser': row['pilXContestUser']}
                        for row in db.fetchall(query, [comPk])]
            else:
                print("No pilot found registered to the comp...")
    else:
        print(f"Registered List - Error: NOT a valid Comp ID \n")

    return (list)

def is_registered(pil_id, comp_id):
    """Check if pilot is registered to the comp"""
    reg_id = 0
    if (pil_id > 0 and comp_id > 0):
        with Database() as db:
            query = """    SELECT
                                `R`.`regPk`
                            FROM
                                `tblRegistration` `R`
                            WHERE
                                `R`.`comPk` = %s
                                AND `R`.`pilPk` = %s
                            LIMIT 1"""
            params = [pil_id, comp_id]
            if db.rows(query, params) > 0:
                reg_id = 0 + db.fetchone(query, params)['regPk']
    else:
        print("is_registered - Error: NOT a valid ID \n")

    return reg_id

def get_glider(pilPk):
    """Get glider info for pilot, to be used in results"""
    glider = dict()
    glider['name'] = 'Unknown'
    glider['cert'] = None

    if (pilPk > 0):
        with Database() as db:
            query = """    SELECT
                                `pilGlider`, `pilGliderBrand`, `gliGliderCert`
                            FROM
                                `PilotView`
                            WHERE
                                `pilPk` = %s
                            LIMIT 1"""
            if db.rows(query, [pilPk]) > 0:
                row = db.fetchone(query, [pilPk])
                glider['name'] = " ".join([row['pilGliderBrand'], row['pilGlider']])
                glider['cert'] = row['gliGliderCert']

    else:
        print("get_glider - Error: NOT a valid Pilot ID \n")

    return (glider)

def get_nat_code(iso):
    """Get Country Code from ISO2 or ISO3"""
    if not (2 <= len(iso) <= 3):
        return None
    else:
        cond = 'C.natIso' + str(len(iso))
        with Database() as db:
            #print("* get country *")
            query = """SELECT
                            `C`.`natID` AS `Code`
                        FROM `tblCountryCodes` `C`
                        WHERE %s = %s
                        LIMIT 1"""
            params = [cond, iso]
            try:
                return 0 + db.fetchone(query, params)['Code']
            except:
                return None

def read_formula(comp_id):

    query = """ SELECT
                    `F`.*,
                    `FC`.*
                FROM
                    `tblCompetition` `C`
                    JOIN `tblForComp` `FC` USING (`comPk`)
                    LEFT OUTER JOIN `tblFormula` `F` USING (`forPk`)
                WHERE
                    `C`.`comPk` = %s
                LIMIT 1"""
    with Database() as db:
        # get the formula details.
        formula = db.fetchone(query, [comp_id])
    formula['forMinDistance'] *= 1000
    formula['forNomDistance'] *= 1000
    formula['forNomTime'] *= 60
    formula['forDiffDist'] *= 1000
#    formula['ScaleToValidity'] = formula['forScaleToValidity']
    # FIX: add failsafe checking?
    if formula['forMinDistance'] <= 0:
        print("WARNING: mindist <= 0, using 5000m instead")
        formula['forMinDistance'] = 5000

    return formula

def get_task_file_path(tasPk, comPk = None):
    """gets path to task tracks folder"""
    from Defines import FILEDIR
    from os import path as p
    path = None
    if not comPk:
        comPk   = get_comp(tasPk)
    date        = get_task_date(tasPk)
    query = """ SELECT
                    COUNT(`tasPk`)
                FROM `TaskView`
                WHERE `comPk` = %s
                AND DATE(`tasDate`) < DATE(%s)"""
    query = "  SELECT LOWER(T.`comCode`) AS comCode, " \
            "LOWER(T.`tasCode`) AS tasCode, " \
            "YEAR(C.`comDateFrom`) AS comYear, " \
            "DATE_FORMAT(T.`tasdate`, '%%Y%%m%%d') AS tasDate " \
            " FROM `TaskView` T JOIN `tblCompetition` C USING(`comPk`) " \
            "WHERE T.`tasPk` = %s LIMIT 1 "

    param = tasPk
    with Database() as db:
        t = db.fetchone(query, params=param)
        if t:
            cname = t['comCode']
            tname = t['tasCode']
            year = str(t['comYear'])
            tdate = str(t['tasDate'])
            print('filedir={}, year={}, cname={}, tname={}, tdate={}'.format(FILEDIR, year, cname, tname, tdate))
            path = str(p.join(FILEDIR, year, cname, ('_'.join([tname, tdate]))))
    return path

def get_task_region(task_id):
    with Database() as db:
        query = """    SELECT `regPk` FROM `tblTask`
                        WHERE `tasPk` = %s LIMIT 1"""
        region_id = 0 + db.fetchone(query, [task_id])['regPk']
    return region_id

def get_area_wps(region_id):
    """query db get all wpts names and pks for region of task and put into dictionary"""
    with Database() as db:
        query = """ SELECT
                        `rwpName`, `rwpPk`
                    FROM `tblRegionWaypoint`
                    WHERE
                        `regPk` = %s
                        AND `rwpOld` = 0
                    ORDER BY `rwpName`"""
        wps = dict()
        for row in db.fetchall(query, [region_id]):
            wps[row['rwpName']] = row['rwpPk']
    return wps

def get_wpts(task_id):
    region_id   = get_task_region(task_id)
    wps         = get_area_wps(region_id)
    return wps
