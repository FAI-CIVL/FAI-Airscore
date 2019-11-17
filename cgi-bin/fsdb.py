"""
FSDB Library

contains
    FSDB class
    read    - A XML reader to read an FSDB file and import to AirScore
    create  - A XML writer to export AirScore results to an FSDB file

Use: from fsdb import read, write

Stuart Mackintosh, Antonio Golfari - 2019
"""

import string, datetime
from calcUtils import *
from compUtils import *
from datetime import date, time, datetime
from task import Task

class FSDB(object):
    """ A Class to deal with FSComp FSDB files  """
    def __init__(self, info=None, formula=None, pilots=None, tasks=None, filename=None):
        self.filename   = filename      # str:  filename
        self.info       = info          # dict: info section
        self.formula    = formula       # dict: formula section
        self.pilots     = pilots        # list: pilots list
        self.tasks      = tasks         # list: task info and results

    @property
    def comp_class(self):
        if self.tasks:
            return self.tasks[0].comp_class
        return None

    @classmethod
    def read(cls, fp):
        """ A XML reader to read FSDB files
            Unfortunately the fsdb format isn't published so much of this is simply an
            exercise in reverse engineering.

            Input:
                - fp:   STR: filepath
        """
        import lxml.etree as ET
        from calcUtils import get_date, get_time

        """read the fsdb file"""
        try:
            tree = ET.parse(fp)
            root = tree.getroot()
        except:
            print ("FSDB Read Error.")
            sys.exit()

        info    = dict()
        formula = dict()
        pilots  = []
        tasks   = []
        results = []

        """Comp Info"""
        print("Getting Comp Info...")
        comp                        = root.find('FsCompetition')
        info['comName']             = comp.attrib.get('name')
        info['comClass']            = (comp.attrib.get('discipline')).upper()
        info['comLocation']         = comp.attrib.get('location')
        # info['comDateFrom']         = datetime.strptime(comp.attrib.get('from'), '%Y-%m-%d')
        # info['comDateTo']           = datetime.strptime(comp.attrib.get('to'), '%Y-%m-%d')
        info['comDateFrom']         = get_date(comp.attrib.get('from'))
        info['comDateTo']           = get_date(comp.attrib.get('to'))
        info['comTimeOffset']       = float(comp.attrib.get('utc_offset'))
        formula['comOverallParam']  = 1.0 - float(comp.attrib.get('ftv_factor'))

        """Formula Info"""
        print ("Getting Formula Info...")
        form = root.find('FsCompetition').find('FsScoreFormula')
        formula['forName'] = form.get('id')
        if formula['comOverallParam'] > 0:
            formula['comOverallScore'] = 'ftv'
        else:
            formula['comOverallScore'] = 'all'

        # formula['forNomTime']           = 0 + int(float(form.get('nom_time')) * 60)         # nom. time, minutes
        # formula['forNomLaunch']         = 0 + int(form.get('use_departure_points'))                 # nom. launch
        # formula['forGoalSSPenalty']     = 1.0 - float(form.get('time_points_if_not_in_goal'))  # ESS but not Goal Penalty
        # formula['forStoppedGlideBonus'] = 0 + float(form.get('bonus_gr'))                 # stopped task glide ratio bonus

        formula['forMinDistance']   = 0 + float(form.get('min_dist'))                   # min. distance, Km
        formula['forNomDistance']   = 0 + float(form.get('nom_dist'))                   # nom. distance, Km
        formula['forNomTime']       = 0 + int(float(form.get('nom_time')) * 60)         # nom. time, minutes
        formula['forNomLaunch']     = 0 + float(form.get('nom_launch'))                 # nom. launch
        formula['forNomGoal']       = 0 + float(form.get('nom_goal'))                   # nom. goal
        formula['forMinTime']       = 0 + int(form.get('min_time_span_for_valid_task')) # min. time for valid task, minutes
        formula['forScorebackTime'] = 0 + int(form.get('score_back_time'))              # Scoreback Time, minutes
        # formula['tolerance']        = 0 + float(form.get('turnpoint_radius_tolerance')) * 100  # tolerance

        """Pilots"""
        print ("Getting Pilots Info...")
        p = root.find('FsCompetition').find('FsParticipants')
        for pil in p.iter('FsParticipant'):
            pilot           = dict()
            pilot['name']   = pil.get('name')
            pilot['id']     = 0 + int(pil.get('id'))
            pilot['glider'] = pil.get('glider')
            """check fai is int"""
            pilot['pilFAI'] = get_int(pil.get('fai_licence'))
            pilot['pilPk']  = get_pilot(pilot['name'], pilot['pilFAI'])
            if pilot['pilPk'] is None:
                '''need to insert new ext. pilot'''
                print (f"   ** pilot {pilot['name']} is not in DB **")
                pilot['pilNat'] = get_nat_code(pil.get('nat_code_3166_a3'))
                pilot['pilSex'] = 'F' if int(pil.get('female')) == 1 else 'M'
            pilots.append(pilot)

        """Tasks"""
        print("Getting Tasks Info...")
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

    @classmethod
    def create(cls, comp_id):
        ''' creates a FSDB Object from an AirScore competition
            input:
                - comp_id       int: comPk event ID'''

        '''check comp is not an external event'''
        from compUtils import is_ext, get_comp_json
        from result import get_task_json
        from task import Task as T
        from os import path as p
        import Defines as d
        import json

        if is_ext(comp_id):
            return None

        '''check comp has already been scored'''
        file = get_comp_json(comp_id)
        if not file or not p.isfile(file):
            return None

        '''read json file'''
        with open(file, 'r+') as f:
            data = json.load(f)

        timestamp       = data['data']['timestamp']
        status          = data['data']['status']
        info            = data['info']
        formula         = {}
        pilots          = []
        tasks           = []

        dt              = datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
        filename        = d.JSONDIR + '_'.join([info['comp_code'],dt]) + '.fsdb'

        '''get partecipants list'''
        for pil in data['results']:
            p = {x:pil[x] for x in ['pil_id', 'name', 'fai', 'civl', 'nat', 'glider', 'sponsor', 'team']}
            p['female'] = 0 if pil['sex'] == 'M' else 1
            pilots.append(p)

        '''get tasks and results'''
        for tas in data['tasks']:
            # file = get_task_json(comp_id)
            # if p.isfile(file):
            #     with open(file, 'r+') as f:
            #         t = json.load(f)
            task_id = tas['id']
            task = T.create_from_json(task_id)
            tasks.append(task)
            if not formula:
                formula = vars(task.formula)
                formula.update({x:data['formula'][x] for x in ['overall_validity', 'validity_param', 'team_size', 'team_scoring', 'team_over']})

        fsdb = FSDB(info=info, filename=filename, formula=formula, pilots=pilots, tasks=tasks)
        return fsdb

    def to_file(self, filename = None):
        ''' '''
        from lxml import etree as T
        from lxml.etree import CDATA
        from calcUtils import get_isotime
        from math import trunc

        # '''create the list of sections'''
        # sections    = [ 'FsScoreFormula',
        #                 'FsCompetitionNotes',
        #                 ]

        '''create dicts of attributes for each section'''
        comp_attr =    {'id':           '',         #still to do
                        'name':         self.info['comp_name'],
                        'location':     self.info['comp_site'],
                        'from':         self.info['date_from'],
                        'to':           self.info['date_to'],
                        'utc_offset':   self.info['time_offset']/3600,
                        'discipline':   self.info['comp_class'].lower(),
                        'ftv_factor':   round(1 - self.formula['validity_param'], 2),
                        'fai_sanctioning': ''       #still to do
                        }

        formula_attr = {'id':                   self.formula['type'].upper()+self.formula['version'],
                        'min_dist':             km(self.formula['min_dist'], 1),
                        'nom_dist':             km(self.formula['nominal_dist'], 1),
                        'nom_time':             self.formula['nominal_time']/3600,
                        'nom_launch':           self.formula['nominal_launch'],
                        'nom_goal':             self.formula['nominal_goal'],
                        'day_quality_override': 0,      #still to implement
                        'bonus_gr':             self.formula['glide_bonus'],
                        'jump_the_gun_factor':  2 if self.comp_class == 'HG' else 0,       #still to implement
                        'jump_the_gun_max':     300,    #still to implement
                        'normalize_1000_before_day_quality':    0,      #still to implement
                        'time_points_if_not_in_goal':   1 - self.formula['no_goal_penalty'],
                        'use_1000_points_for_max_day_quality':  0,      #still to implement
                        'use_arrival_position_points':  1 if self.formula['arrival'] == 'position' else 0,
                        'use_arrival_time_points':      1 if self.formula['arrival'] == 'time' else 0,
                        'use_departure_points':         1 if self.formula['departure'] == 'departure' else 0,
                        'use_difficulty_for_distance_points': 1 if self.comp_class == 'HG' else 0,       #still to implement
                        'use_distance_points':          1,              #still to implement
                        'use_distance_squared_for_LC':  1 if self.comp_class == 'PG' else 0,       #still to implement
                        'use_leading_points':           1 if self.formula['departure'] == 'leadout' else 0,
                        'use_semi_circle_control_zone_for_goal_line': 1,       #still to implement
                        'use_time_points':              1,                     #still to implement
                        'scoring_altitude':             'GPS',                 #still to implement
                        'final_glide_decelerator':      0,                     #still to implement
                        'no_final_glide_decelerator_reason': '',
                        'min_time_span_for_valid_task': 60 if self.comp_class == 'PG' else 0,       #still to implement
                        'score_back_time':              self.formula['score_back_time']/60,
                        'use_proportional_leading_weight_if_nobody_in_goal': '',        #still to implement
                        'leading_weight_factor':        '',                    #still to implement
                        'turnpoint_radius_tolerance':   self.formula['tolerance'],
                        'use_arrival_altitude_points':  0 if self.formula['arr_alt_bonus'] == 'off' else '' #still to implement
                        }

        '''create the file structure'''
        root    = T.Element('Fs')
        # fsdb    = ET.ElementTree(root)
        root.set('version', '3.5')
        root.set('comment', 'generated by AirScore')
        '''FsCompetition'''
        comp    = T.SubElement(root, 'FsCompetition')
        for k,v in comp_attr.items():
            comp.set(k, str(v))

        formula = T.SubElement(comp, 'FsScoreFormula')
        for k,v in formula_attr.items():
            formula.set(k, str(v))

        notes   = T.SubElement(comp, 'FsCompetitionNotes')
        notes.text = CDATA('Generated by AirScore')

        '''FsParticipants'''
        pilots  = T.SubElement(comp, 'FsParticipants')
        for p in self.pilots:
            pil = T.SubElement(pilots, 'FsParticipant')
            pilot_attr =   {'id':       p['pil_id'],
                            'name':     p['name'],
                            'birthday': '',
                            'glider':   p['glider'],
                            'glider_main_colors': '',
                            'fai_licence': 1 if p['fai'] else 0,
                            'female':   p['female'],
                            'nat_code_3166_a3': p['nat'],
                            'sponsor':  p['sponsor'],
                            'CIVLID':   p['civl'],
                            }
            custom_attr =  {'fai_n':    p['fai'],
                            'team':     p['team']
                            }

            for k,v in pilot_attr.items():
                pil.set(k, str(v))
            cus = T.SubElement(pil, 'FsCustomAttributes')
            for k,v in custom_attr.items():
                sub = T.SubElement(cus, 'FsCustomAttribute')
                sub.set('name', k)
                sub.set('value', str(v))

        '''FsTasks'''
        tasks    = T.SubElement(comp, 'FsTasks')
        for id, t in enumerate(self.tasks):
            task    = T.SubElement(tasks, 'FsTask')
            task.set('id', str(id+1))
            task.set('name', t.task_name)
            task.set('tracklog_folder', '')

            task_f  = T.SubElement(task, 'FsScoreFormula')
            task_d  = T.SubElement(task, 'FsTaskDefinition')
            task_s  = T.SubElement(task, 'FsTaskState')
            task_p  = T.SubElement(task, 'FsParticipants')
            task_sp = T.SubElement(task, 'FsTaskScoreParams')

            tf      = dict(t.formula.to_dict(), **t.stats)

            '''FsTaskState'''
            task_s.set('task_state', ('REGULAR' if not t.stopped_time  else 'STOPPED')) #?
            task_s.set('score_back_time', str(tf['score_back_time']/60))
            task_s.set('cancel_reason', '')     #still to implement

            '''FsScoreFormula'''
            tf_attr =  {'id':                   tf['type'].upper()+tf['version'],
                        'min_dist':             km(tf['min_dist'], 1),
                        'nom_dist':             km(tf['nominal_dist'], 1),
                        'nom_time':             tf['nominal_time']/3600,
                        'nom_launch':           tf['nominal_launch'],
                        'nom_goal':             tf['nominal_goal'],
                        'day_quality':          tf['day_quality'],
                        'day_quality_override': 0,         #still to implement
                        'bonus_gr':             tf['glide_bonus'],
                        'jump_the_gun_factor':  2 if self.comp_class == 'HG' else 0,       #still to implement
                        'jump_the_gun_max':     300,                            #still to implement
                        'normalize_1000_before_day_quality': 0,                 #still to implement
                        'time_validity_based_on_pilot_with_speed_rank': '',     #still to implement
                        'time_points_if_not_in_goal':   1 - tf['no_goal_penalty'],
                        'use_1000_points_for_max_day_quality': '',
                        'use_arrival_position_points':  1 if tf['arrival'] == 'position' else 0,
                        'use_arrival_time_points':      1 if tf['arrival'] == 'time' else 0,
                        'use_departure_points':         1 if tf['departure'] == 'departure' else 0,
                        'use_difficulty_for_distance_points': '',       #still to implement
                        'use_distance_points':  '',                     #still to implement
                        'use_distance_squared_for_LC': '',              #still to implement
                        'use_leading_points':           0 if tf['departure'] == 'off' else 1,
                        'use_semi_circle_control_zone_for_goal_line': '',       #still to implement
                        'use_time_points':      1,                      #still to implement
                        'scoring_altitude':     'GPS',                  #still to implement
                        'final_glide_decelerator': 'GPS',               #still to implement
                        'no_final_glide_decelerator_reason': '',
                        'min_time_span_for_valid_task': 60 if self.comp_class == 'PG' else 0,             #still to implement
                        'score_back_time':              tf['score_back_time']/60,
                        'use_proportional_leading_weight_if_nobody_in_goal': '',        #still to implement
                        'leading_weight_factor': '',                    #still to implement
                        'turnpoint_radius_tolerance':   tf['tolerance'],
                        'use_arrival_altitude_points':  0 if tf['tolerance'] == 'off' else '' #still to implement
                        }
            for k,v in tf_attr.items():
                task_f.set(k, str(v))

            '''FsTaskDefinition'''
            tps     = t.turnpoints
            td_attr =  {'ss':             [idx+1 for idx,tp in enumerate(tps) if tp.type == 'speed'].pop(),
                        'es':             [idx+1 for idx,tp in enumerate(tps) if tp.type == 'endspeed'].pop(),
                        'goal':           ([tp.shape for tp in tps if tp.type == 'goal'].pop()).upper(),
                        'groundstart':    0,        #still to implement
                        'qnh_setting':    1013.25   #still to implement
                        }

            for k,v in td_attr.items():
                task_d.set(k, str(v))

            t_open      = get_isotime(t.date, t.window_open_time, t.time_offset)
            t_close     = get_isotime(t.date, t.task_deadline, t.time_offset)
            ss_open     = get_isotime(t.date, t.start_time, t.time_offset)
            if t.start_close_time:
                ss_close = get_isotime(t.date, t.start_close_time, t.time_offset)
            else:
                ss_close = t_close
            if t.window_close_time:
                w_close = get_isotime(t.date, t.window_close_time, t.time_offset)
            else:
                w_close = ss_close

            for idx, tp in enumerate(tps):
                task_tp = T.SubElement(task_d, 'FsTurnpoint')
                tp_attr =  {'id':       tp.name,
                            'lat':      round(tp.lat, 5),
                            'lon':      round(tp.lon, 5),
                            'altitude': tp.altitude,
                            'radius':   tp.radius,
                            'open':     t_open if idx < (td_attr['ss'] - 1) else ss_open,
                            'close':    w_close if idx == 0 else ss_close if idx == (td_attr['ss'] - 1) else t_close
                            }
                for k,v in tp_attr.items():
                    task_tp.set(k, str(v))

                '''we add also FsTaskDistToTp during tp iteration'''
                sp_dist = T.SubElement(task_sp, 'FsTaskDistToTp')
                sp_dist.set('tp_no', str(idx+1))
                sp_dist.set('distance', str(t.partial_distance[idx]))

            '''add start gates'''
            gates = 1
            if t.SS_interval > 0:
                if t.start_close_time:
                    gates = trunc((t.start_close_time - t.start_time)/t.SS_interval)
                else:
                    gates = trunc((t.task_deadline - t.start_time)/t.SS_interval)
            for i in range(gates):
                task_sg = T.SubElement(task_d, 'FsStartGate')
                int     = 0 if not t.SS_interval else t.SS_interval*i
                time    = get_isotime(t.date, (t.start_time + int), t.time_offset)
                task_sg.set('open', str(time))

            '''FsTaskScoreParams'''
            launch_ess  = [t.partial_distance[id] for id, tp in enumerate(t.turnpoints) if tp.type == 'endspeed'].pop()
            sp_attr     =  {'ss_distance':                      km(t.SS_distance),
                            'task_distance':                    km(t.opt_dist),
                            'launch_to_ess_distance':           km(launch_ess),
                            'no_of_pilots_present':             tf['pilots_present'],
                            'no_of_pilots_flying':              tf['pilots_launched'],
                            'no_of_pilots_lo':                  tf['pilots_launched'] - tf['pilots_goal'],
                            'no_of_pilots_reaching_nom_dist':   len([x for x in t.results if x.distance_flown > t.formula.nominal_dist]),
                            'no_of_pilots_reaching_es':         tf['pilots_ess'],
                            'no_of_pilots_reaching_goal':       tf['pilots_goal'],
                            'sum_flown_distance':               km(tf['tot_dist_flown']),
                            'best_dist':                        km(tf['max_distance']),
                            'best_time':                        round(tf['fastest']/3600, 14),
                            'worst_time':                       round(max([0 if (x.ESS_time is None or x.SSS_time is None or (x.ESS_time - x.SSS_time < 0)) else (x.ESS_time - x.SSS_time) for x in t.results])/3600, 14),
                            'no_of_pilots_in_competition':      len(self.pilots),
                            'no_of_pilots_landed_before_stop':  tf['pilots_landed'],
                            'sum_dist_over_min':                km(tf['tot_dist_over_min']),
                            'sum_real_dist_over_min':           km(tf['tot_dist_over_min']),        # not yet implemented
                            'best_real_dist':                   km(tf['max_distance']),             # not yet implemented
                            'last_start_time':                  get_isotime(t.date, max([x.SSS_time for x in t.results if x.SSS_time is not None]), t.time_offset),
                            'first_start_time':                 get_isotime(t.date, tf['min_dept_time'], t.time_offset),
                            'first_finish_time':                get_isotime(t.date, tf['min_ess_time'], t.time_offset),
                            'max_time_to_get_time_points':      round(0/3600, 14),                  # not yet implemented
                            'no_of_pilots_with_time_points':    len([x for x in t.results if x.time_score > 0]),
                            'goal_ratio':                       0 if tf['pilots_launched'] == 0 else round(tf['pilots_goal']/tf['pilots_launched'], 15),
                            'arrival_weight':                   round(0, 3),                        # not yet implemented
                            'departure_weight':                 round(0, 3),                        # not yet implemented
                            'leading_weight':                   round(0, 3),                        # not yet implemented
                            'time_weight':                      round(0, 3),                        # not yet implemented
                            'distance_weight':                  round(0, 3),                        # not yet implemented
                            'smallest_leading_coefficient':     round(tf['min_lead_coeff'], 14),
                            'available_points_distance':        round(tf['avail_dist_points'], 14),
                            'available_points_time':            round(tf['avail_time_points'], 14),
                            'available_points_departure':       0 if not t.formula.departure == 'departure' else round(tf['avail_dep_points'], 14),
                            'available_points_leading':         0 if not t.formula.departure == 'leadout' else round(tf['avail_dep_points'], 14),
                            'available_points_arrival':         round(tf['avail_arr_points'], 14),
                            'time_validity':                    round(tf['time_validity'], 3),
                            'launch_validity':                  round(tf['launch_validity'], 3),
                            'distance_validity':                round(tf['dist_validity'], 3),
                            'stop_validity':                    round(tf['stop_validity'], 3),
                            'day_quality':                      round(tf['day_quality'], 3),
                            'ftv_day_validity':                 round(tf['day_quality'] if not t.formula.type == 'pwc' else tf['max_score']/1000, 4),
                            'time_points_stop_correction':      0                                   # not yet implemented
                            }
            for k,v in sp_attr.items():
                task_sp.set(k, str(v))

            '''FsParticipants'''
            for idx, pil in enumerate(t.results):
                '''create pilot result for the task'''
                pil_p = T.SubElement(task_p, 'FsParticipant')
                pil_p.set('id', str(pil.pil_id))
                if not (pil.result_type in ('abs', 'dnf')):
                    '''only if pilot flew'''
                    pil_fd  = T.SubElement(pil_p, 'FsFlightData')
                    pil_r   = T.SubElement(pil_p, 'FsResult')
                    if not (pil.result_type == 'min_dist'):
                        fd_attr =  {'distance':             km(pil.distance_flown),
                                    'bonus_distance':       km(pil.total_distance),  #?? seems 0 for PG and more than dist for HG
                                    'started_ss':           '' if not pil.pilot_start_time else get_isotime(t.date, pil.pilot_start_time, t.time_offset),
                                    'finished_ss':          '' if not pil.ESS_time else get_isotime(t.date, pil.ESS_time, t.time_offset),
                                    'altitude_at_ess':      pil.ESS_altitude,
                                    'finished_task':        '' if not pil.goal_time else get_isotime(t.date, pil.goal_time, t.time_offset),
                                    'tracklog_filename':    pil.track_file,
                                    'lc':                   pil.lead_coeff,
                                    'iv':                   '', # ?? not implemented
                                    'ts':                   get_isotime(t.date, pil.first_time, t.time_offset),
                                    'alt':                  pil.last_altitude,   # ??
                                    'bonus_alt':            '',  # ?? not implemented
                                    'max_alt':              pil.max_altitude,
                                    'last_tracklog_point_distance': '',     # not implemented yet
                                    'bonus_last_tracklog_point_distance': '', # ?? not implemented
                                    'last_tracklog_point_time': get_isotime(t.date, pil.landing_time, t.time_offset),
                                    'last_tracklog_point_alt':  pil.landing_altitude,
                                    'landed_before_deadline':   '1' if pil.landing_time < (t.task_deadline if not t.stopped_time else t.stopped_time) else '0'     # only deadline?
                                    }
                        for k,v in fd_attr.items():
                            pil_fd.set(k, str(v))

                    r_attr =   {'rank':             idx+1,  # not implemented, tey should be ordered tho
                                                            # Rank IS NOT SAFE (I guess)
                                'points':           round(pil.score),
                                'distance':         km(pil.total_distance if pil.total_distance else pil.distance_flown),
                                'ss_time':          sec_to_time(pil.total_time).strftime('%H:%M:%S'),
                                'finished_ss_rank': '',     # not implemented
                                'distance_points':  round(pil.distance_score,1),
                                'time_points':      round(pil.time_score,1),
                                'arrival_points':   round(pil.arrival_score,1),
                                'departure_points': 0 if not t.formula.departure == 'departure' else round(pil.departure_score, 1),
                                'leading_points':   0 if not t.formula.departure == 'leadout' else round(pil.departure_score, 1),
                                'penalty':          0 if not pil.penalty else pil.penalty,  # ??
                                'penalty_points':   0 if not pil.penalty else pil.penalty,  # ??
                                'penalty_reason':   '' if not pil.comment else pil.comment,
                                'penalty_points_auto':      0,      # ??
                                'penalty_reason_auto':      0,      # ??
                                'penalty_min_dist_points':  0,      # ??
                                'got_time_but_not_goal_penalty':    pil.ESS_time > 0 and not pil.goal_time,
                                'started_ss':       '' if not pil.pilot_start_time else get_isotime(t.date, pil.SSS_time, t.time_offset),
                                'ss_time_dec_hours':        0,      # ??
                                'ts':               get_isotime(t.date, pil.first_time, t.time_offset),             # flight origin time
                                'real_distance':    km(pil.distance_flown),
                                'last_distance':    '',             # ?? last fix distance?
                                'last_altitude_above_goal': pil.last_altitude,
                                'altitude_bonus_seconds':   0,      # not implemented
                                'altitude_bonus_time':      sec_to_time(0).strftime('%H:%M:%S'),    # not implemented
                                'altitude_at_ess':          pil.ESS_altitude,
                                'scored_ss_time':           sec_to_time(pil.total_time).strftime('%H:%M:%S'),   # ??
                                'landed_before_stop':       pil.landing_time < (t.task_deadline if not t.stopped_time else t.stopped_time)
                                }

                    for k,v in r_attr.items():
                        pil_r.set(k, str(v))

        '''creates the file to store'''
        fsdb = T.tostring(root,
                            pretty_print=True,
                            xml_declaration=True,
                            encoding='UTF-8')

        if not filename:
            filename = self.filename

        with open(filename, "wb") as file:
            file.write(fsdb)

        return filename

    def add(self):
        """
            Add comp to Airscore database
        """
        from myconn import Database

        comPk = None
        tasPk = None
        #forPk = None


        with Database() as db:
            """insert comp"""
            compquery = """INSERT INTO
                                `tblCompetition`
                                (`comName`, `comLocation`, `comDateFrom`, `comDateTo`,
                                `comEntryRestrict`, `comTimeOffset`, `comClass`, `comLocked`, `comExt`)
                            VALUES
                                (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                """
            params = [self.info['comName'], self.info['comLocation'], self.info['comDateFrom'].isoformat(),
                                self.info['comDateTo'].isoformat(), 'registered', self.info['comTimeOffset'], self.info['comClass'], 1, 1]

            try:
                comPk = db.execute(compquery, params)

                '''insert formula'''
                formulaquery = """INSERT INTO
                                    `tblForComp`
                                    (`extForName`, `comPk`, `comOverallScore`, `comOverallParam`,
                                    `forNomGoal`, `forMinDistance`, `forNomDistance`, `forNomTime`, `forNomLaunch`, `forMinTime`, `forScorebackTime`)
                                VALUES
                                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                    """
                params = [self.formula['forName'], comPk, self.formula['comOverallScore'], self.formula['comOverallParam'],
                                    self.formula['forNomGoal'], self.formula['forMinDistance'], self.formula['forNomDistance'],
                                    self.formula['forNomTime'], self.formula['forNomLaunch'],self.formula['forMinTime'],self.formula['forScorebackTime']]

                db.execute(formulaquery, params)
            except:
                print ("DB Error inserting comp.")
                sys.exit()
            finally:
                print("{} inserted with id {}".format(self.info['comName'], comPk))

            """pilots info"""
            for pil in self.pilots:
                """check if pilot exists"""
                if pil['pilPk'] is None:
                    """create new pilot"""
                    names = []
                    names = pil['name'].replace("'", "''").replace('.', ' ').replace('_', ' ').replace('-', ' ').split(maxsplit=1)
                    createpilquery = """   INSERT INTO
                                                `tblExtPilot`(`pilFirstName`, `pilLastName`,
                                                `pilNat`, `pilSex`, `pilGlider`, `pilFAI`)
                                            VALUES
                                                (%s,%s,%s,%s,%s,%s)
                                    """
                    params = [names[0], names[1], pil['pilNat'], pil['pilSex'], pil['glider'], pil['pilFAI']]

                    pil['pilPk'] = db.execute(createpilquery, params)
                    if pil['pilPk'] is None:
                        print ("DB Error inserting ext. pilot.")
                        sys.exit()
                    print(f"Pilot {names[0]} inserted with id {pil['pilPk']}")

            """DO WE NEED TO REGISTER PILOTS TO COMP??"""
#             regpilquery = ("""  INSERT INTO
#                                     `tblRegistration`(`comPk`, `regPaid`, `gliPk`, `pilPk`)
#                                 VALUES
#                                     ('{}', '{}', '{}', '{}')
#                                 """.format(comPk, 0, pil['glider'], pil['pilPk']))

            """task info"""
            for task in self.tasks:
                tasquery = """ INSERT INTO
                                    `tblTask`(`comPk`, `tasDate`, `tasName`, `tasTaskStart`, `tasFinishTime`, `tasStartTime`,
                                    `tasStartCloseTime`, `tasFastestTime`, `tasMaxDistance`,
                                    `tasTaskType`, `tasDistance`, `tasShortRouteDistance`, `tasSSDistance`,
                                    `tasSSInterval`, `tasTotalDistanceFlown`, `tasQuality`, `tasDistQuality`, `tasTimeQuality`,
                                    `tasLaunchQuality`, `tasAvailDistPoints`, `tasAvailLeadPoints`, `tasAvailTimePoints`, `tasAvailArrPoints`
                                    `tasLaunchValid`, `tasPilotsLaunched`, `tasPilotsTotal`, `tasPilotsGoal`, `tasDeparture`,
                                    `tasArrival`, `tasHeightBonus`, `tasComment`, `tasLocked`)
                                VALUES
                                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                     %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                     %s,%s,%s,%s,%s,%s)
                            """
                params = [comPk, task.window_open_time.date(), task.task_name, task.window_open_time, task.task_deadline, task.start_time,
                            task.start_close_time, task.stats['fastest'], task.stats['max_distance'],
                            task.task_type, task.distance, task.opt_dist, task.SS_distance,
                            task.SS_interval, task.stats['tot_dist_flown'], task.stats['day_quality'], task.stats['dist_validity'], task.stats['time_validity'],
                            task.stats['launch_validity'], task.stats['avail_dist_points'], task.stats['avail_dep_points'], task.stats['avail_time_points'], task.stats['avail_arr_points'],
                            '1', task.stats['pilots_launched'], task.stats['pilots_present'], task.stats['pilots_goal'], task.departure,
                            task.arrival, task.formula.arr_alt_bonus, task.comment, '1']

                try:
                    tasPk = db.execute(tasquery)
                    if task.stopped_time is not None:
                        stopquery = """UPDATE
                                            `tblTask`
                                        SET
                                            `tasStoppedTime` = %s
                                        WHERE
                                            `tasPk` = %s"""
                        params = [task.stopped_time, tasPk]
                        db.execute(stopquery, params)
                except:
                    print ("DB Error inserting Task.")
                    sys.exit()
                finally:
                    print(f"{task.task_name} inserted with id {tasPk}")

                """task waypoints"""
                legs = task.optimised_legs
                for wpt in task.turnpoints:
                    try:
                        rwpPk = None
                        wptquery = """ INSERT INTO
                                            `tblRegionWaypoint`(`rwpName`, `rwpLatDecimal`, `rwpLongDecimal`, `rwpAltitude`)
                                        VALUES (%s,%s,%s,%s)"""
                        params = [wpt.name, wpt.lat, wpt.lon, wpt.altitude]
                        rwpPk = db.execute(wptquery, params)
                        '''get optimised distance for leg'''
                        dist = legs.pop(0)
                        routequery = """   INSERT INTO
                                                `tblTaskWaypoint`(`tasPk`, `rwpPk`, `tawNumber`, `tawType`,
                                                `tawHow`, `tawShape`, `tawRadius`, `ssrCumulativeDist`)
                                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                                            """
                        params = [tasPk, rwpPk, wpt.id, wpt.type,
                                    wpt.how, wpt.shape, wpt.radius, dist]
                        db.execute(routequery, params)
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

                        resquery = """ INSERT INTO
                                            `tblExtResult`(`tasPk`, `pilPk`, `tarDistance`, `tarSpeed`, `tarSS`, `tarES`,
                                            `tarGoal`, `tarPenalty`, `tarComment`, `tarSpeedScore`, `tarDistanceScore`,
                                            `tarArrivalScore`, `tarDepartureScore`, `tarScore`, `tarLastAltitude`, `tarResultType`, `traGlider`)
                                        VALUES
                                            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                    """
                        params = [tasPk, pilPk, res.total_distance, speed, tarSS, tarES,
                                        tarGoal, res.penalty, res.comment, res.time_score, res.distance_score,
                                        res.arrival_score, res.departure_score, res.score, res.last_altitude, res.result_type, traGlider]
                        db.execute(resquery, params)
                    except:
                        print ("DB Error inserting Result.")
                        sys.exit()
                print(f"   Results inserted for {task.task_name}")

def get_pilot(name, fai = None):
    """Get pilot from name or fai
    info comes from FSDB file, as FsParticipant attributes
    Not sure about best strategy to retrieve pilots ID from name and FAI n.
    """

    names = []
    names = name.replace("'", "''").replace('.', ' ').replace('_', ' ').replace('-', ' ').split()

    """Gets name from string"""
    print("Trying with name... \n")
    s = []
    t = []
    for i in names:
        s.append(" pilLastName LIKE '%%{}%%' ".format(i))
        t.append(" pilFirstName LIKE '%%{}%%' ".format(i))
    cond = ' OR '.join(s)
    cond2 = ' OR '.join(t)
    query = """ SELECT `pilPk`
                FROM `PilotView`
                WHERE
                    (%s)
                AND (%s)
                LIMIT 1"""
    params = [cond, cond2]

    """Get pilot"""
    with Database() as db:
        try:
            """using name"""
            return db.fetchone(query, params)['pilPk']
        except:
            if fai is not None:
                query = """    SELECT `pilPk`
                                FROM `PilotView`
                                WHERE
                                    (%s)
                                AND `pilFAI` = %s"""
                params = [cond, fai]

                #print ("get_pilot Query: {}  \n".format(query))

                """Get pilot using fai n."""
                try:
                    return db.fetchone(query, params)['pilPk']
                except:
                    return None
            else:
                return None

def translate(source, mode, type):
    ''' creates a dictionary with correct keys
        input:
            source:     dict - initial values
            mode:       str  - to_fsdb, from_fsdb
            type:       str  - task, formula, results, waypoints
    '''

    formula_list    = []
