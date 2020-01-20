"""
FSDB Library

contains
    FSDB class
    read    - A XML reader to read an FSDB file and import to AirScore
    create  - A XML writer to export AirScore results to an FSDB file

Use: from fsdb import read, write

Stuart Mackintosh, Antonio Golfari - 2019
"""

import time
import lxml.etree as ET

from lxml.etree import CDATA
from comp import Comp
from task import Task
from formula import Formula
from pilot import Pilot, update_all_results
from participant import Participant, mass_import_participants
from calcUtils import get_isotime, km, sec_to_time
from compUtils import create_comp_code, is_ext
from Defines import RESULTDIR
from math import trunc
from datetime import time, datetime
from myconn import Database
from sqlalchemy.exc import SQLAlchemyError


class FSDB(object):
    """ A Class to deal with FSComp FSDB files  """

    def __init__(self, comp=None, tasks=None, filename=None):
        self.filename = filename  # str:  filename
        self.comp = comp  # Comp obj.
        self.tasks = tasks  # list: Task obj. list with Flight_result obj list

    @property
    def comp_class(self):
        if self.tasks:
            return self.comp.comp_class
        return None

    @property
    def formula(self):
        return self.comp.formula

    @classmethod
    def read(cls, fp, from_CIVL=0):
        """ A XML reader to read FSDB files
            Unfortunately the fsdb format isn't published so much of this is simply an
            exercise in reverse engineering.

            Input:
                - fp:           STR: filepath
                - from_CIVL:    BOOL: look for pilot on CIVL database
        """

        """read the fsdb file"""
        try:
            tree = ET.parse(fp)
            root = tree.getroot()
        except ET.Error:
            print("FSDB Read Error.")
            return None

        pilots = []
        tasks = []

        """Comp Info"""
        print("Getting Comp Info...")
        fs_comp = root.find('FsCompetition')
        comp = Comp.from_fsdb(fs_comp)

        """Formula"""
        comp.formula = Formula.from_fsdb(fs_comp)
        comp.formula.comp_class = comp.comp_class

        """Pilots"""
        print("Getting Pilots Info...")
        if from_CIVL:
            print('*** get from CIVL database')
        p = root.find('FsCompetition').find('FsParticipants')
        for pil in p.iter('FsParticipant'):
            pilot = Participant.from_fsdb(pil, from_CIVL=from_CIVL)
            # pp(pilot.as_dict())
            pilots.append(pilot)

        comp.participants = pilots

        """Tasks"""
        print("Getting Tasks Info...")
        t = root.find('FsCompetition').find('FsTasks')
        for tas in t.iter('FsTask'):
            '''create task obj'''
            task = Task.from_fsdb(tas)
            '''check if task was valid'''
            if task is not None:
                """Task Results"""
                task.time_offset = int(comp.time_offset * 3600)
                node = tas.find('FsParticipants')
                if node is not None:
                    task.pilots = []
                    print("Getting Results Info...")
                    for res in node.iter('FsParticipant'):
                        '''pilots results'''
                        pilot = Pilot.from_fsdb(task, res)
                        task.pilots.append(pilot)
                tasks.append(task)

        return cls(comp, tasks, fp)

    @classmethod
    def create(cls, comp_id, ref_id=None):
        """ creates a FSDB Object from an AirScore competition
            input:
                - comp_id       int: comPk event ID"""

        '''check comp is not an external event'''

        if is_ext(comp_id):
            # TODO probably with new logic we are able to create FSDB from ext comps?
            return None

        comp = Comp.from_json(comp_id, ref_id)
        '''check comp has already been scored'''
        if comp is None:
            print(f"Comp (ID {comp_id}) has not been scored yet.")
            return None

        timestamp = int(time.time() + comp.time_offset * 3600)
        dt = datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
        filename = RESULTDIR + '_'.join([comp.comp_code, dt]) + '.fsdb'

        '''get tasks and results'''
        tasks = []
        for tas in comp.tasks:
            task_id = tas['id']
            task = Task.create_from_json(task_id=task_id)
            tasks.append(task)

        fsdb = FSDB(comp=comp, filename=filename, tasks=tasks)
        return fsdb

    def to_file(self, filename=None):
        """ """

        formula = self.comp.formula
        pilots = self.comp.participants

        '''create dicts of attributes for each section'''
        comp_attr = {'id': '',  # still to do
                     'name': self.comp.comp_name,
                     'location': self.comp.comp_site,
                     'from': self.comp.date_from,
                     'to': self.comp.date_to,
                     'utc_offset': self.comp.time_offset / 3600,
                     'discipline': self.comp.comp_class.lower(),
                     'ftv_factor': round(1 - formula.validity_param, 2),
                     'fai_sanctioning': (1 if self.comp.sanction == 'FAI 1'
                                         else 2 if self.comp.sanction == 'FAI 2' else 0)
                     }

        formula_attr = {'id': formula.formula_type.upper() + formula.formula_version,
                        'min_dist': km(formula.min_dist, 1),
                        'nom_dist': km(formula.nominal_dist, 1),
                        'nom_time': formula.nominal_time / 3600,
                        'nom_launch': formula.nominal_launch,
                        'nom_goal': formula.nominal_goal,
                        'day_quality_override': 0,  # still to implement
                        'bonus_gr': formula.glide_bonus,
                        'jump_the_gun_factor': (0 if formula.max_JTG == 0
                                                else round(1 / formula.JTG_penalty_per_sec, 1)),
                        'jump_the_gun_max': formula.max_JTG,
                        'normalize_1000_before_day_quality': 0,  # still to implement
                        'time_points_if_not_in_goal': round(1 - formula.no_goal_penalty, 1),
                        'use_1000_points_for_max_day_quality': 0,  # still to implement
                        'use_arrival_position_points': 1 if formula.formula_arrival == 'position' else 0,
                        'use_arrival_time_points': 1 if formula.formula_arrival == 'time' else 0,
                        'use_departure_points': 1 if formula.formula_departure == 'departure' else 0,
                        'use_difficulty_for_distance_points': 1 if formula.formula_distance == 'difficulty' else 0,
                        'use_distance_points': 1 if formula.formula_distance != 'off' else 0,
                        'use_distance_squared_for_LC': 1 if formula.comp_class == 'PG' else 0,  # still to implement
                        'use_leading_points': 1 if formula.formula_departure == 'leadout' else 0,
                        'use_semi_circle_control_zone_for_goal_line': 1,  # still to implement
                        'use_time_points': 1 if formula.formula_time == 'on' else 0,
                        'scoring_altitude': 'GPS' if formula.scoring_altitude == 'GPS' else 'QNH',
                        'final_glide_decelerator': 'none' if formula.arr_alt_bonus == 0 else 'aatb',
                        'no_final_glide_decelerator_reason': '',
                        'min_time_span_for_valid_task': 60 if self.comp_class == 'PG' else 0,  # still to implement
                        'score_back_time': formula.score_back_time / 60,
                        'use_proportional_leading_weight_if_nobody_in_goal': '',  # still to implement
                        'leading_weight_factor': (0 if formula.formula_departure != 'leadout'
                                                  else round(formula.lead_factor, 3)),
                        'turnpoint_radius_tolerance': formula.tolerance,
                        'use_arrival_altitude_points': 0 if formula.arr_alt_bonus == 0 else ''  # still to implement
                        }
        if formula.arr_alt_bonus > 0:
            formula_attr['aatb_factor'] = round(formula.arr_alt_bonus, 3)

        '''create the file structure'''
        root = ET.Element('Fs')
        root.set('version', '3.5')
        root.set('comment', 'generated by AirScore')
        '''FsCompetition'''
        comp = ET.SubElement(root, 'FsCompetition')
        for k, v in comp_attr.items():
            comp.set(k, str(v))

        formula = ET.SubElement(comp, 'FsScoreFormula')
        for k, v in formula_attr.items():
            formula.set(k, str(v))

        notes = ET.SubElement(comp, 'FsCompetitionNotes')
        notes.text = CDATA('Generated by AirScore')
        # notes.text = '<![CDATA[Generated by AirScore]]>'

        '''FsParticipants'''
        participants = ET.SubElement(comp, 'FsParticipants')
        for p in pilots:
            pil = ET.SubElement(participants, 'FsParticipant')
            pilot_attr = {'id': p.ID,
                          'name': p.name,
                          'birthday': p.info.pilot_birthdate_str,
                          'glider': p.info.glider,
                          'glider_main_colors': '',
                          'fai_licence': 1 if p.info.fai_id else 0,
                          'female': p.info.female,
                          'nat_code_3166_a3': p.nat,
                          'sponsor': p.info.sponsor,
                          'CIVLID': p.civl_id,
                          }
            custom_attr = {'fai_n': p.info.fai_id,
                           'class': p.info.glider_cert,
                           'team': p.info.team,
                           'LIVE': p.info.live_id
                           }

            for k, v in pilot_attr.items():
                pil.set(k, str(v))
            cus = ET.SubElement(pil, 'FsCustomAttributes')
            for k, v in custom_attr.items():
                sub = ET.SubElement(cus, 'FsCustomAttribute')
                sub.set('name', k)
                sub.set('value', str(v))

        '''FsTasks'''
        tasks = ET.SubElement(comp, 'FsTasks')
        for idx, t in enumerate(self.tasks):
            task = ET.SubElement(tasks, 'FsTask')
            task.set('id', str(idx + 1))
            task.set('name', t.task_name)
            task.set('tracklog_folder', '')

            task_f = ET.SubElement(task, 'FsScoreFormula')
            task_d = ET.SubElement(task, 'FsTaskDefinition')
            task_s = ET.SubElement(task, 'FsTaskState')
            task_p = ET.SubElement(task, 'FsParticipants')
            task_sp = ET.SubElement(task, 'FsTaskScoreParams')

            # tf = dict(t.formula.to_dict(), **t.stats)

            '''FsTaskState'''
            task_s.set('task_state', ('REGULAR' if not t.stopped_time else 'STOPPED'))  # ?
            task_s.set('score_back_time', str(t.formula.score_back_time / 60))
            task_s.set('cancel_reason', t.comment)

            '''FsScoreFormula'''
            # we permit just few changes in single tasks from comp formula, so we just update those
            tf_attr = formula_attr
            tf_attr.update({'jump_the_gun_factor': (0 if not not t.formula.JTG_penalty
                                                    else round(1 / t.formula.JTG_penalty, 1)),
                            'time_points_if_not_in_goal': 1 - t.formula.no_goal_penalty,
                            'use_arrival_position_points': 1 if t.formula.arrival == 'position' else 0,
                            'use_arrival_time_points': 1 if t.formula.arrival == 'time' else 0,
                            'use_departure_points': 1 if t.formula.departure == 'departure' else 0,
                            'use_difficulty_for_distance_points': 1 if t.formula.distance == 'difficulty' else 0,
                            'use_distance_points': 0 if t.formula.distance == 'off' else 1,
                            'use_leading_points': 0 if t.formula.departure == 'off' else 1,
                            'use_time_points': 0 if t.formula.time == 'off' else 1,
                            'scoring_altitude': 'GPS' if formula.scoring_altitude == 'GPS' else 'QNH',
                            'final_glide_decelerator': 'none' if formula.arr_alt_bonus == 0 else 'aatb',
                            'use_arrival_altitude_points': 0 if t.formula.arr_alt_bonus == 0 else 1,
                            'turnpoint_radius_tolerance': t.formula.tolerance,
                            })

            for k, v in tf_attr.items():
                task_f.set(k, str(v))

            '''FsTaskDefinition'''
            tps = t.turnpoints
            td_attr = {'ss': [i + 1 for i, tp in enumerate(tps) if tp.type == 'speed'].pop(0),
                       'es': [i + 1 for i, tp in enumerate(tps) if tp.type == 'endspeed'].pop(0),
                       'goal': next(tp.shape for tp in tps if tp.type == 'goal').upper(),
                       'groundstart': 0,  # still to implement
                       'qnh_setting': 1013.25  # still to implement
                       }

            for k, v in td_attr.items():
                task_d.set(k, str(v))

            t_open = get_isotime(t.date, t.window_open_time, t.time_offset)
            t_close = get_isotime(t.date, t.task_deadline, t.time_offset)
            ss_open = get_isotime(t.date, t.start_time, t.time_offset)
            if t.start_close_time:
                ss_close = get_isotime(t.date, t.start_close_time, t.time_offset)
            else:
                ss_close = t_close
            if t.window_close_time:
                w_close = get_isotime(t.date, t.window_close_time, t.time_offset)
            else:
                w_close = ss_close

            for i, tp in enumerate(tps):
                task_tp = ET.SubElement(task_d, 'FsTurnpoint')
                tp_attr = {'id': tp.name,
                           'lat': round(tp.lat, 5),
                           'lon': round(tp.lon, 5),
                           'altitude': tp.altitude,
                           'radius': tp.radius,
                           'open': t_open if i < (td_attr['ss'] - 1) else ss_open,
                           'close': w_close if i == 0 else ss_close if i == (td_attr['ss'] - 1) else t_close
                           }
                for k, v in tp_attr.items():
                    task_tp.set(k, str(v))

                '''we add also FsTaskDistToTp during tp iteration'''
                sp_dist = ET.SubElement(task_sp, 'FsTaskDistToTp')
                sp_dist.set('tp_no', str(i + 1))
                sp_dist.set('distance', str(t.partial_distance[i]))

            '''add start gates'''
            gates = 1
            if t.SS_interval > 0:
                if t.start_close_time:
                    gates = trunc((t.start_close_time - t.start_time) / t.SS_interval)
                else:
                    gates = trunc((t.task_deadline - t.start_time) / t.SS_interval)
            for i in range(gates):
                task_sg = ET.SubElement(task_d, 'FsStartGate')
                intv = 0 if not t.SS_interval else t.SS_interval * i
                time = get_isotime(t.date, (t.start_time + intv), t.time_offset)
                task_sg.set('open', str(time))

            '''FsTaskScoreParams'''
            launch_ess = [t.partial_distance[i] for i, tp in enumerate(t.turnpoints) if tp.type == 'endspeed'].pop()
            sp_attr = {'ss_distance': km(t.SS_distance),
                       'task_distance': km(t.opt_dist),
                       'launch_to_ess_distance': km(launch_ess),
                       'no_of_pilots_present': t.pilots_present,
                       'no_of_pilots_flying': t.pilots_launched,
                       'no_of_pilots_lo': t.pilots_launched - t.pilots_goal,
                       'no_of_pilots_reaching_nom_dist': len(
                           [x for x in t.valid_results if x.distance_flown > t.formula.nominal_dist]),
                       'no_of_pilots_reaching_es': t.pilots_ess,
                       'no_of_pilots_reaching_goal': t.pilots_goal,
                       'sum_flown_distance': km(t.tot_dist_flown),
                       'best_dist': km(t.max_distance),
                       'best_time': round(t.fastest / 3600, 14),
                       'worst_time': round(max([0 if (
                               x.ESS_time is None or x.SSS_time is None or (x.ESS_time - x.SSS_time < 0)) else (
                               x.ESS_time - x.SSS_time) for x in t.valid_results]) / 3600, 14),
                       'no_of_pilots_in_competition': len(self.comp.participants),
                       'no_of_pilots_landed_before_stop': t.pilots_landed,
                       'sum_dist_over_min': km(t.tot_dist_over_min),
                       'sum_real_dist_over_min': km(t.tot_dist_over_min),  # not yet implemented
                       'best_real_dist': km(t.max_distance),  # not yet implemented
                       'last_start_time': get_isotime(t.date,
                                                      max([x.SSS_time for x in t.valid_results if x.SSS_time is not None]),
                                                      t.time_offset),
                       'first_start_time': get_isotime(t.date, t.min_dept_time, t.time_offset),
                       'first_finish_time': get_isotime(t.date, t.min_ess_time, t.time_offset),
                       'max_time_to_get_time_points': round(0 / 3600, 14),  # not yet implemented
                       'no_of_pilots_with_time_points': len([x for x in t.valid_results if x.time_score > 0]),
                       'goal_ratio': (0 if t.pilots_launched == 0 else round(t.pilots_goal / t.pilots_launched, 15)),
                       'arrival_weight': 0 if t.arrival == 0 else round(t.arr_weight, 3),
                       'departure_weight': 0 if t.departure != 'on' else round(t.dep_weight, 3),
                       'leading_weight': 0 if t.departure != 'leadout' else round(t.dep_weight, 3),
                       'time_weight': 0 if t.arrival == 'off' else round(t.time_weight, 3),
                       'distance_weight': round(t.dist_weight, 3),  # not yet implemented
                       'smallest_leading_coefficient': round(t.min_lead_coeff, 14),
                       'available_points_distance': round(t.avail_dist_points, 14),
                       'available_points_time': round(t.avail_time_points, 14),
                       'available_points_departure': (0 if not t.formula.departure == 'departure'
                                                      else round(t.avail_dep_points, 14)),
                       'available_points_leading': (0 if not t.formula.departure == 'leadout'
                                                    else round(t.avail_dep_points, 14)),
                       'available_points_arrival': round(t.avail_arr_points, 14),
                       'time_validity': round(t.time_validity, 3),
                       'launch_validity': round(t.launch_validity, 3),
                       'distance_validity': round(t.dist_validity, 3),
                       'stop_validity': round(t.stop_validity, 3),
                       'day_quality': round(t.day_quality, 3),
                       'ftv_day_validity': (round(t.day_quality if not t.formula.type == 'pwc'
                                                  else t.max_score / 1000, 4)),
                       'time_points_stop_correction': 0  # not yet implemented
                       }
            for k, v in sp_attr.items():
                task_sp.set(k, str(v))

            '''FsParticipants'''
            for i, pil in enumerate(t.pilots):
                '''create pilot result for the task'''
                pil_p = ET.SubElement(task_p, 'FsParticipant')
                pil_p.set('id', str(pil.par_id))
                if not (pil.result_type in ('abs', 'dnf')):
                    '''only if pilot flew'''
                    pil_fd = ET.SubElement(pil_p, 'FsFlightData')
                    pil_r = ET.SubElement(pil_p, 'FsResult')
                    res = pil.result
                    if not (res.result_type in ['mindist', 'min_dist']):
                        fd_attr = {'distance': km(res.distance_flown),
                                   'bonus_distance': km(res.total_distance),
                                   # ?? seems 0 for PG and more than dist for HG
                                   'started_ss': '' if not res.real_start_time else get_isotime(t.date,
                                                                                                res.real_start_time,
                                                                                                t.time_offset),
                                   'finished_ss': '' if not res.ESS_time else get_isotime(t.date, res.ESS_time,
                                                                                          t.time_offset),
                                   'altitude_at_ess': res.ESS_altitude,
                                   'finished_task': '' if not res.goal_time else get_isotime(t.date, res.goal_time,
                                                                                             t.time_offset),
                                   'tracklog_filename': res.track_file,
                                   'lc': res.lead_coeff,
                                   'iv': '',  # ?? not implemented
                                   'ts': get_isotime(t.date, res.first_time, t.time_offset),
                                   'alt': res.last_altitude,  # ??
                                   'bonus_alt': '',  # ?? not implemented
                                   'max_alt': res.max_altitude,
                                   'last_tracklog_point_distance': '',  # not implemented yet
                                   'bonus_last_tracklog_point_distance': '',  # ?? not implemented
                                   'last_tracklog_point_time': get_isotime(t.date, res.landing_time, t.time_offset),
                                   'last_tracklog_point_alt': res.landing_altitude,
                                   'landed_before_deadline': '1' if res.landing_time < (
                                       t.task_deadline if not t.stopped_time else t.stopped_time) else '0'
                                   # only deadline?
                                   }
                        for k, v in fd_attr.items():
                            pil_fd.set(k, str(v))

                    r_attr = {'rank': i + 1,  # not implemented, tey should be ordered tho
                              # Rank IS NOT SAFE (I guess)
                              'points': round(res.score),
                              'distance': km(res.total_distance if res.total_distance else res.distance_flown),
                              'ss_time': sec_to_time(res.ss_time).strftime('%H:%M:%S'),
                              'finished_ss_rank': '',  # not implemented
                              'distance_points': round(res.distance_score, 1),
                              'time_points': round(res.time_score, 1),
                              'arrival_points': round(res.arrival_score, 1),
                              'departure_points': 0 if not t.formula.departure == 'departure' else round(
                                  res.departure_score, 1),
                              'leading_points': 0 if not t.formula.departure == 'leadout' else round(
                                  res.departure_score, 1),
                              'penalty': 0 if not res.penalty else res.penalty,  # ??
                              'penalty_points': 0 if not res.penalty else res.penalty,  # ??
                              'penalty_reason': '' if not res.comment else res.comment,
                              'penalty_points_auto': 0,  # ??
                              'penalty_reason_auto': 0,  # ??
                              'penalty_min_dist_points': 0,  # ??
                              'got_time_but_not_goal_penalty': res.ESS_time > 0 and not res.goal_time,
                              'started_ss': '' if not res.real_start_time else get_isotime(t.date, res.SSS_time,
                                                                                           t.time_offset),
                              'ss_time_dec_hours': 0,  # ??
                              'ts': get_isotime(t.date, res.first_time, t.time_offset),  # flight origin time
                              'real_distance': km(res.distance_flown),
                              'last_distance': '',  # ?? last fix distance?
                              'last_altitude_above_goal': res.last_altitude,
                              'altitude_bonus_seconds': 0,  # not implemented
                              'altitude_bonus_time': sec_to_time(0).strftime('%H:%M:%S'),  # not implemented
                              'altitude_at_ess': res.ESS_altitude,
                              'scored_ss_time': sec_to_time(res.ss_time).strftime('%H:%M:%S'),  # ??
                              'landed_before_stop': res.landing_time < (
                                  t.task_deadline if not t.stopped_time else t.stopped_time)
                              }

                    for k, v in r_attr.items():
                        pil_r.set(k, str(v))

        '''creates the file to store'''
        fsdb = ET.tostring(root,
                           pretty_print=True,
                           xml_declaration=True,
                           encoding='UTF-8')

        if not filename:
            filename = self.filename

        with open(filename, "wb") as file:
            file.write(fsdb)

        return filename

    def add_comp(self, session=None):
        """
            Add comp to AirScore database
        """
        '''check if we have comp_code'''
        if self.comp.comp_code is None:
            self.comp.comp_code = create_comp_code(self.comp.comp_name, self.comp.date_from)

        self.comp.to_db()
        self.comp.formula.comp_id = self.comp.comp_id
        self.comp.formula.to_db()

    def add_tasks(self, session=None):
        """
            Add comp tasks to AirScore database
        """

        if self.comp.comp_id is None:
            return

        with Database(session) as db:
            try:
                for t in self.tasks:
                    t.comp_id = self.comp.comp_id
                    t.to_db(db.session)
                db.session.commit()

            except SQLAlchemyError:
                print('Tasks storing error')
                db.session.rollback()

    def add_results(self, session=None):
        """
            Add results for each comp task to AirScore database
        """
        if self.comp.comp_id is None:
            return

        for t in self.tasks:
            if len(t.results) == 0 or t.task_id is None:
                print(f"task {t.task_code} does not have a db ID or has not been scored.")
                pass
            update_all_results(task_id=t.task_id, pilots=t.pilots, session=session)

    def add_participants(self, session=None):
        """
            Add participants to AirScore database
        """
        if self.comp.comp_id is None or len(self.comp.participants) == 0:
            print(f"Comp does not have a db ID or has not participants.")
            return

        mass_import_participants(self.comp.comp_id, self.comp.participants)
