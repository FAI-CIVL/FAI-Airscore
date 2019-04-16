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
    comPk = 0
    if str(tasPk).isdigit() and tasPk > 0:
        with Database() as db:
            query = ("""    SELECT 
                                comPk 
                            FROM 
                                tblTask 
                            WHERE 
                                tasPk = {} """.format(tasPk))
            if db.rows(query) > 0:
                return db.fetchone(query)['comPk']
    else:
        print ("Error: {} is NOT a valid task ID".format(tasPk))

def get_class(tasPk, test = 0):
    """Get comPk from tasPk"""
    if str(tasPk).isdigit() and tasPk > 0:
        with Database() as db:
            query = ("""    SELECT 
                                comClass 
                            FROM 
                                tblTaskView 
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
                                tblTaskView 
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
                            JOIN `tblPilot` P USING(`pilPk`)
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

def get_glider(pilPk, test = 0):
    """Get glider info for pilot, to be used in results"""
    message = ''
    info = dict()
    info['glider'] = 'Unknown'
    info['cert'] = None

    if (pilPk > 0):
        with Database() as db:
            query = ("""    SELECT 
                                pilGlider, pilGliderBrand, gliGliderCert 
                            FROM 
                                tblPilot 
                            WHERE 
                                pilPk = {}
                            LIMIT 1""".format(pilPk))
            message += ("Query: {}  \n".format(query))
            if db.rows(query) > 0:
                row = 0 + db.fetchone(query)
                info['glider'] = " ".join(row['pilGliderBrand'], row['pilGlider'])
                info['cert'] = row['gliGliderCert']
    else:
        message += ("get_glider - Error: NOT a valid Pilot ID \n")

    if test == 1:
        """TEST MODE"""
        message += ("Glider Info: \n")
        message += ("{}, cert. {} \n".format(info['glider'], info['cert']))
        print (message)

    return (info)

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
    formula['forNomDistance'] *=1000
    formula['forNomTime'] *= 60
    formula['forDiffDist'] *= 1000
#    formula['ScaleToValidity'] = formula['forScaleToValidity']
    # FIX: add failsafe checking?
    if formula['forMinDistance'] <= 0:

        print("WARNING: mindist <= 0, using 5000m instead")
        formula['forMinDistance'] = 5000

    return formula