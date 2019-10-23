"""
FSDB Object
used to read and create fsdb files (FSComp)
Use: import fsdb

Antonio Golfari - 2018
"""

import string, datetime
from calcUtils import *
from compUtils import *
from datetime import date, time, datetime
from task import Task
from route import Flight_result

class FSDB:
    """ A Class to deal with FSComp FSDB files  """
    def __init__(self, info=None, formula=None, pilots=None, tasks=None, filename=None):
        self.filename = filename
        self.info = info
        self.formula = formula
        self.pilots = pilots
        self.tasks = tasks
        #self.formula = Formula()

    @classmethod
    def read(cls, fp):
        """ A XML reader to read FSDB files
            Unfortunately the fsdb format isn't published so much of this is simply an
            exercise in reverse engineering.
        """
        import lxml.etree as ET

        message = ''
        """read the fsdb file"""
        try:
            tree = ET.parse(fp)
            root = tree.getroot()
        except:
            print ("FSDB Read Error.")
            sys.exit()

        info = dict()
        formula = dict()
        pilots = []
        tasks = []
        results = []

        """Comp Info"""
        print ("Getting Comp Info...")
        comp = root.find('FsCompetition')
        info['comName'] = comp.attrib.get('name')
        info['comClass'] = (comp.attrib.get('discipline')).upper()
        info['comLocation'] = comp.attrib.get('location')
        info['comDateFrom'] = datetime.strptime(comp.attrib.get('from'), '%Y-%m-%d')
        info['comDateTo'] = datetime.strptime(comp.attrib.get('to'), '%Y-%m-%d')
        info['comTimeOffset'] = float(comp.attrib.get('utc_offset'))
        formula['comOverallParam'] = 1.00 - float(comp.attrib.get('ftv_factor'))

        """Formula Info"""
        print ("Getting Formula Info...")
        form = root.find('FsCompetition').find('FsScoreFormula')
        formula['forName'] = form.get('id')
        if formula['comOverallParam'] > 0:
            formula['comOverallScore'] = 'ftv'
        else:
            formula['comOverallScore'] = 'all'
        formula['forMinDistance'] = 0 + float(form.get('min_dist'))
        formula['forNomDistance'] = 0 + float(form.get('nom_dist'))
        formula['forNomTime'] = 0 + (float(form.get('nom_time')) * 60)
        formula['forNomLaunch'] = 0 + float(form.get('nom_launch'))
        formula['forNomGoal'] = 0 + float(form.get('nom_goal'))

        """Pilots"""
        print ("Getting Pilots Info...")
        p = root.find('FsCompetition').find('FsParticipants')
        for pil in p.iter('FsParticipant'):
            pilot = dict()
            pilot['name'] = pil.get('name')
            pilot['id'] = 0 + int(pil.get('id'))
            pilot['glider'] = pil.get('glider')
            """check fai is int"""
            pilot['pilFAI'] = get_int(pil.get('fai_licence'))
            pilot['pilPk'] = cls.get_pilot(pilot['name'], pilot['pilFAI'])
            if pilot['pilPk'] is None:
                '''need to insert new ext. pilot'''
                print ("   ** pilot {} is not in DB **".format(pilot['name']))
                pilot['pilNat'] = get_nat_code(pil.get('nat_code_3166_a3'))
                pilot['pilSex'] = 'F' if int(pil.get('female')) == 1 else 'M'
            pilots.append(pilot)

        """Tasks"""
        print ("Getting Tasks Info...")
        t = root.find('FsCompetition').find('FsTasks')
        for tas in t.iter('FsTask'):
            '''create task obj'''
            task = Task.create_from_fsdb(tas)

            """Task Results"""
            node = tas.find('FsParticipants')
            if node is not None:
                for res in node.iter('FsParticipant'):
                    '''pilots results'''
                    task.results.append(Flight_result.from_fsdb(res, task.departure, task.arrival))
            tasks.append(task)

        return cls(info, formula, pilots, tasks, fp)

    def add(self, test = 0):
        """
            Add comp to Airscore database
        """
        from myconn import Database

        message = ''
        comPk = None
        tasPk = None
        #forPk = None


        with Database() as db:
            """insert comp"""
            message += ("*** Inserting Comp: ***\n ")
            compquery = ("""INSERT INTO
                                `tblCompetition`
                                (`comName`, `comLocation`, `comDateFrom`, `comDateTo`,
                                `comEntryRestrict`, `comTimeOffset`, `comClass`, `comLocked`, `comExt`)
                            VALUES
                                ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
                                """.format(self.info['comName'], self.info['comLocation'], self.info['comDateFrom'].isoformat(),
                                self.info['comDateTo'].isoformat(), 'registered', self.info['comTimeOffset'], self.info['comClass'], '1', '1'))

            message += ("Comp Query: \n {}".format(compquery))

            if test == 0:
                try:
                    comPk = db.execute(compquery)

                    formulaquery = ("""INSERT INTO
                                        `tblForComp`
                                        (`extForName`, `comPk`, `comOverallScore`, `comOverallParam`,
                                        `forNomGoal`, `forMinDistance`, `forNomDistance`, `forNomTime`, `forNomLaunch`)
                                    VALUES
                                        ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
                                        """.format(self.formula['forName'], comPk, self.formula['comOverallScore'], self.formula['comOverallParam'],
                                        self.formula['forNomGoal'], self.formula['forMinDistance'], self.formula['forNomDistance'],
                                        self.formula['forNomTime'], self.formula['forNomLaunch']))
                    message += ("Formula Query: \n {}".format(formulaquery))

                    db.execute(formulaquery)
                except:
                    print ("DB Error inserting comp.")
                    sys.exit()
                finally:
                    print("{} inserted with id {}".format(self.info['comName'], comPk))

            """pilots info"""
            message += ("*** Pilots Info: ***\n ")
            for pil in self.pilots:
                """check if pilot exists"""
                if pil['pilPk'] is None:
                    """create new pilot"""
                    names = []
                    names = pil['name'].replace("'", "''").replace('.', ' ').replace('_', ' ').replace('-', ' ').split(maxsplit=1)
                    createpilquery = ("""   INSERT INTO
                                                `tblExtPilot`(`pilFirstName`, `pilLastName`,
                                                `pilNat`, `pilSex`, `pilGlider`, `pilFAI`)
                                            VALUES
                                                ('{}', '{}', '{}', '{}', '{}', '{}')
                                    """.format(names[0], names[1], pil['pilNat'], pil['pilSex'], pil['glider'], pil['pilFAI']))
                    message += ("Pilot Creation Query: \n {}".format(createpilquery))

                    if test == 0:
                        pil['pilPk'] = db.execute(createpilquery)
                        if pil['pilPk'] is None:
                            print ("DB Error inserting ext. pilot.")
                            sys.exit()
                        print("Pilot {} inserted with id {}".format(names[0], pil['pilPk']))

            """DO WE NEED TO REGISTER PILOTS TO COMP??"""
#             regpilquery = ("""  INSERT INTO
#                                     `tblRegistration`(`comPk`, `regPaid`, `gliPk`, `pilPk`)
#                                 VALUES
#                                     ('{}', '{}', '{}', '{}')
#                                 """.format(comPk, 0, pil['glider'], pil['pilPk']))

            """task info"""
            message += ("*** Task Info: ***\n ")
            for task in self.tasks:
                tasquery = (""" INSERT INTO
                                    `tblTask`(`comPk`, `tasDate`, `tasName`, `tasTaskStart`, `tasFinishTime`, `tasStartTime`,
                                    `tasStartCloseTime`, `tasFastestTime`, `tasMaxDistance`,
                                    `tasTaskType`, `tasDistance`, `tasShortRouteDistance`, `tasSSDistance`,
                                    `tasSSInterval`, `tasTotalDistanceFlown`, `tasQuality`, `tasDistQuality`, `tasTimeQuality`,
                                    `tasLaunchQuality`, `tasAvailDistPoints`, `tasAvailLeadPoints`, `tasAvailTimePoints`, `tasAvailArrPoints`
                                    `tasLaunchValid`, `tasPilotsLaunched`, `tasPilotsTotal`, `tasPilotsGoal`, `tasDeparture`,
                                    `tasArrival`, `tasHeightBonus`, `tasComment`, `tasLocked`)
                                VALUES
                                    ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}',
                                     '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'
                                     '{}', '{}', '{}', '{}', '{}')
                            """.format(comPk, task.window_open_time.date(), task.task_name, task.window_open_time, task.task_deadline, task.start_time,
                                        task.start_close_time, task.stats['fastest'], task.stats['max_distance'],
                                        task.task_type, task.distance, task.opt_dist, task.SS_distance,
                                        task.SS_interval, task.stats['tot_dist_flown'], task.stats['day_quality'], task.stats['dist_validity'], task.stats['time_validity'],
                                        task.stats['launch_validity'], task.stats['avail_dist_points'], task.stats['avail_dep_points'], task.stats['avail_time_points'], task.stats['avail_arr_points']
                                        '1', task.stats['pilots_launched'], task.stats['pilots_present'], task.stats['pilots_goal'], task.departure,
                                        task.arrival, task., task.comment, '1'))
                message += ("{} Query: \n {}".format(task.task_name, tasquery))

                if test == 0:
                    try:
                        tasPk = db.execute(tasquery)
                        if task.stopped_time is not None:
                            stopquery = ("""UPDATE
                                                `tblTask`
                                            SET
                                                `tasStoppedTime` = '{}'
                                            WHERE
                                                `tasPk` = {}""".format(task.stopped_time, tasPk))
                            db.execute(stopquery)
                    except:
                        print ("DB Error inserting Task.")
                        sys.exit()
                    finally:
                        print("{} inserted with id {}".format(task.task_name, tasPk))

                """task waypoints"""
                legs = task.optimised_legs
                for wpt in task.turnpoints:
                    try:
                        rwpPk = None
                        wptquery = (""" INSERT INTO
                                            `tblRegionWaypoint`(`rwpName`, `rwpLatDecimal`, `rwpLongDecimal`, `rwpAltitude`)
                                        VALUES ('{}', '{}', '{}', '{}')""".format(wpt.name, wpt.lat, wpt.lon, wpt.altitude))
                        message += ("WPT Query: \n {}".format(wptquery))
                        if test == 0:
                            rwpPk = db.execute(wptquery)
                        '''get optimised distance for leg'''
                        dist = legs.pop(0)
                        routequery = ("""   INSERT INTO
                                                `tblTaskWaypoint`(`tasPk`, `rwpPk`, `tawNumber`, `tawType`,
                                                `tawHow`, `tawShape`, `tawRadius`, `ssrCumulativeDist`)
                                            VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
                                            """.format(tasPk, rwpPk, wpt.id, wpt.type,
                                                wpt.how, wpt.shape, wpt.radius, dist))
                        message += ("Route Query: \n {}".format(routequery))
                        if test == 0:
                            db.execute(routequery)
                    except:
                        print ("DB Error inserting Turnpoints.")
                        sys.exit()
                    finally:
                        print("   Turnpoints correctly inserted")

                """task results"""
                for res in task.results:
                    #id = res.ext_id
                    try:
                        '''get pilPk'''
                        pil = next((item for item in self.pilots if item['id'] == res.ext_id), None)
                        pilPk = pil['pilPk']
                        traGlider = pil['glider']
                        #print ("pilot id: {} - pilPk: {}".format(res.ext_id, pilPk))
                        '''get speed'''
                        speed = (task.SS_distance / 1000) / res.SSS_time if (res.SSS_time is not None and res.SSS_time > 0) else 0
                        '''transform time in seconds from midnight and adjust for timezone'''
                        tz = self.info['comTimeOffset'] * 3600
                        print ("Goal Time: {}".format(res.goal_time))
                        tarSS = time_to_seconds(res.Start_time) - tz if res.Start_time is not None else 0
                        tarES = time_to_seconds(res.ESS_time) - tz if res.ESS_time is not None else 0
                        tarGoal = time_to_seconds(res.goal_time) - tz if res.goal_time is not None else 0

                        resquery = (""" INSERT INTO
                                            `tblExtResult`(`tasPk`, `pilPk`, `tarDistance`, `tarSpeed`, `tarSS`, `tarES`,
                                            `tarGoal`, `tarPenalty`, `tarComment`, `tarSpeedScore`, `tarDistanceScore`,
                                            `tarArrivalScore`, `tarDepartureScore`, `tarScore`, `tarLastAltitude`, `tarResultType`, `traGlider`)
                                        VALUES
                                            ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}',
                                             '{}', '{}', '{}', '{}', '{}')
                                    """.format(tasPk, pilPk, res.Total_distance, speed, tarSS, tarES,
                                        tarGoal, res.Penalty, res.Comment, res.Time_score, res.distance_score,
                                        res.Arrival_score, res.Departure_score, res.Score, res.Stopped_altitude, res.result_type, traGlider))
                        message += ("Result Query: \n {}".format(resquery))
                        if test == 0:
                            db.execute(resquery)
                    except:
                        print ("DB Error inserting Result.")
                        sys.exit()
                print("   Results inserted for {}".format(task.task_name))

        if test == 1:
            print (message)


    @staticmethod
    def get_pilot(name, fai = None, test = 0):
        """Get pilot from name or fai
        info comes from FSDB file, as FsParticipant attributes
        Not sure about best strategy to retrieve pilots ID from name and FAI n.
        """

        message = ''
        names = []
        names = name.replace("'", "''").replace('.', ' ').replace('_', ' ').replace('-', ' ').split()

        """Gets name from string"""
        message += ("Trying with name... \n")
        s = []
        t = []
        for i in names:
            s.append(" pilLastName LIKE '%%{}%%' ".format(i))
            t.append(" pilFirstName LIKE '%%{}%%' ".format(i))
        cond = ' OR '.join(s)
        cond2 = ' OR '.join(t)
        query = ("""    SELECT
                            pilPk
                        FROM
                            PilotView
                        WHERE
                            ({})
                        AND
                            ({})""".format(cond, cond2))

        #print ("get_pilot Query: {}  \n".format(query))

        """Get pilot"""
        with Database() as db:
            try:
                """using name"""
                return db.fetchone(query)['pilPk']
            except:
                if fai is not None and fai > 0:
                    query = ("""    SELECT
                                        pilPk
                                    FROM
                                        PilotView
                                    WHERE
                                        ({})
                                    AND
                                        pilFAI = {}""".format(cond, fai))

                    #print ("get_pilot Query: {}  \n".format(query))

                    """Get pilot using fai n."""
                    try:
                        return db.fetchone(query)['pilPk']
                    except:
                        return None
                else:
                    return None

    @staticmethod
    def get_time(str, test = 0):
        """
            Transform string in datetime.time
        """
        if str is not None:
            return (datetime.strptime((str)[:19], '%Y-%m-%dT%H:%M:%S')).time()
        else:
            return str

    @staticmethod
    def get_day(str, test = 0):
        """
            Transform string in datetime.day
        """
        if str is not None:
            return (datetime.strptime((str)[:19], '%Y-%m-%dT%H:%M:%S')).date()
        else:
            return str
