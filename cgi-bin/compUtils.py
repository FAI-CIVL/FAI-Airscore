"""
Module for operations on comp / task / formulas
Use:    import compUtils
        comPk = compUtils.get_comp(tasPk)

Antonio Golfari - 2018
"""

# Use your utility module.
from myconn import Database

def get_comp(tasPk, test = 0):
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
        print ("Error: {} is NOT a valid task ID".format(tasPk))

def get_class(tasPk, test = 0):
    """Get comPk from tasPk"""
    if str(tasPk).isdigit() and tasPk > 0:
        with Database() as db:
            query = ("""    SELECT
                                comClass
                            FROM
                                TaskView
                            WHERE
                                tasPk = {}
                            LIMIT 1""".format(tasPk))
            if db.rows(query) > 0:
                return db.fetchone(query)['comClass']
    else:
        print ("Error: {} is NOT a valid task ID".format(tasPk))

def get_task_date(tasPk, test = 0):
    """Get date from tasPk in date format"""
    if str(tasPk).isdigit() and tasPk > 0:
        with Database() as db:
            query = ("""    SELECT
                                tasDate
                            FROM
                                TaskView
                            WHERE
                                tasPk = {}
                            LIMIT 1""".format(tasPk))
            if db.rows(query) > 0:
                date = db.fetchone(query)['tasDate']
                if test:
                    print ('task date: {} \n'.format(date))
                return date
    else:
        print ("Error: {} is NOT a valid task ID".format(tasPk))

def get_registration(comPk, test=0):
    """Check if comp has a registration"""
    message = ''
    reg = 0
    if comPk:
        with Database() as db:
            query = ("""    SELECT (CASE WHEN
                                `comEntryRestrict` LIKE '%%registered%%' THEN 1 ELSE 0
                            END) AS Reg
                            FROM
                                `tblCompetition`
                            WHERE
                                `comPk` = {}
                            LIMIT 1""".format(comPk))
            message += ("Query: {}  \n".format(query))
            if db.rows(query) > 0:
                reg = db.fetchone(query)['Reg']
    else:
        message += ("comp registration - Error: NOT a valid ID \n")
    if test:
        """TEST MODE"""
        message += ("registration: {} \n".format(reg))
        print (message)

    return (reg)

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

def get_registered_pilots(comPk, test=0):
    """Gets list of registered pilots for the comp"""
    message = ''
    list = []
    if comPk:
        with Database() as db:
            query = ("""    SELECT
                                R.`pilPk`,
                                P.`pilFirstName`,
                                P.`pilLastName`,
                                P.`pilFAI`,
                                P.`pilXContestUser`
                            FROM
                                `tblRegistration` R
                            JOIN `PilotView` P USING(`pilPk`)
                            WHERE
                                R.`comPk` = {}""".format(comPk))
            message += ("Query: {}  \n".format(query))
            if db.rows(query) > 0:
                """create a list from results"""
                message += ("creating a list of pilots...")
                list = [{   'pilPk': row['pilPk'],
                            'pilFirstName': row['pilFirstName'],
                            'pilLastName': row['pilLastName'],
                            'pilFAI': row['pilFAI'],
                            'pilXContestUser': row['pilXContestUser']}
                        for row in db.fetchall(query)]
            else:
                message += ("No pilot found registered to the comp...")
    else:
        message += ("Registered List - Error: NOT a valid Comp ID \n")

    if test:
        """TEST MODE"""
        print (message)

    return (list)

def is_registered(pilPk, comPk, test = 0):
    """Check if pilot is registered to the comp"""
    message = ''
    regPk = 0
    if (pilPk > 0 and comPk > 0):
        with Database() as db:
            query = ("""    SELECT
                                R.regPk
                            FROM
                                tblRegistration R
                            WHERE
                                R.comPk = {}
                                AND R.pilPk = {}
                            LIMIT 1""".format(comPk, pilPk))
            message += ("Query: {}  \n".format(query))
            if db.rows(query) > 0:
                regPk = 0 + db.fetchone(query)['regPk']
    else:
        message += ("is_registered - Error: NOT a valid ID \n")

    if test == 1:
        """TEST MODE"""
        message += ("regPk: {} \n".format(regPk))
        print (message)

    return (regPk)

def get_glider(pilPk):
    """Get glider info for pilot, to be used in results"""
    glider = dict()
    glider['name'] = 'Unknown'
    glider['cert'] = None

    if (pilPk > 0):
        with Database() as db:
            query = """    SELECT
                                pilGlider, pilGliderBrand, gliGliderCert
                            FROM
                                PilotView
                            WHERE
                                pilPk = %s
                            LIMIT 1"""
            if db.rows(query, [pilPk]) > 0:
                row = db.fetchone(query, [pilPk])
                glider['name'] = " ".join([row['pilGliderBrand'], row['pilGlider']])
                glider['cert'] = row['gliGliderCert']

    else:
        print ("get_glider - Error: NOT a valid Pilot ID \n")

    return (glider)

def get_nat_code(iso):
    """Get Country Code from ISO2 or ISO3"""
    if not (2 <= len(iso) <= 3):
        return None
    else:
        cond = 'C.natIso' + str(len(iso))
        with Database() as db:
            #print("* get country *")
            query = ("""SELECT
                            C.natID AS Code
                        FROM tblCountryCodes C
                        WHERE {} = '{}' LIMIT 1""".format(cond, iso))
            try:
                return 0 + db.fetchone(query)['Code']
            except:
                return None

def read_formula(comPk):

    query = """ SELECT
                    F.*,
                    FC.*
                FROM
                    tblCompetition C
                    JOIN tblForComp FC USING (comPk)
                    LEFT OUTER JOIN tblFormula F USING (forPk)
                WHERE
                    C.comPk = %s
                LIMIT 1"""
    with Database() as db:
        # get the formula details.
        formula = db.fetchone(query, [comPk])
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

def get_task_file_path(tasPk, JSON=False, test = 0):
    """gets path to task tracks folder"""
    from Defines import FILEDIR, JSONDIR
    from os import path as p

    if JSON:
        dir = JSONDIR
    else:
        dir = FILEDIR

    path = None
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
            # print('filedir={}, year={}, cname={}, tname={}, tdate={}'.format(dir, year, cname, tname, tdate))
            path = str(p.join(dir, year, cname, ('_'.join([tname, tdate]))))
    if test:
        print('Get Task tracks folder:')
        print(query)
        print('task folder: {}'.format(path))
    return path

def get_task_region(task_id):
    with Database() as db:
        query = """    SELECT `regPk` FROM `tblTask`
                        WHERE `tasPk` = '%s' LIMIT 1"""
        region_id = 0 + db.fetchone(query, [task_id])['regPk']
    return region_id

def get_area_wps(region_id):
    """query db get all wpts names and pks for region of task and put into dictionary"""
    with Database() as db:
        query = """ SELECT `rwpName`, `rwpPk` FROM `tblRegionWaypoint`
                    WHERE regPk = '%s' AND rwpOld = '0' ORDER BY rwpName"""
        wps = dict()
        for row in db.fetchall(query, [region_id]):
            wps[row['rwpName']] = row['rwpPk']
    return wps

def get_wpts(task_id):
    region_id   = get_task_region(task_id)
    wps         = get_area_wps(region_id)
    return wps
