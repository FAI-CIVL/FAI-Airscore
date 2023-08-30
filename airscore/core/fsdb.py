"""
FSDB Library

contains
    FSDB class
    read    - A XML reader to read an FSDB file and import to AirScore
    create  - A XML writer to export AirScore results to an FSDB file

Use: from fsdb import read, write

Stuart Mackintosh, Antonio Golfari - 2019
"""

from datetime import datetime
from pathlib import Path

import lxml.etree as ET
from calcUtils import c_round, get_int, get_isotime, km, sec_to_time
from comp import Comp
from compUtils import is_ext
from formula import Formula
from lxml.etree import CDATA
from pilot.flightresult import FlightResult, update_all_results
from pilot.participant import Participant, mass_import_participants
from task import Task
from ranking import get_fsdb_custom_attributes


class FSDB(object):
    """ A Class to deal with FSComp FSDB files  """

    def __init__(self, comp=None, tasks=None, filename=None, custom_attributes=None):
        self.filename = filename  # str:  filename
        self.comp = comp  # Comp obj.
        self.custom_attributes = custom_attributes  # list: CompAttribute obj. list
        self.tasks = tasks  # list: Task obj. list with FlightResult obj list

    @property
    def comp_class(self):
        if self.tasks:
            return self.comp.comp_class
        return None

    @property
    def formula(self):
        return self.comp.formula

    @classmethod
    def read(cls, fp: Path, short_name: str = None, keep_task_path=False, from_CIVL=False):
        """A XML reader to read FSDB files
        Unfortunately the fsdb format isn't published so much of this is simply an
        exercise in reverse engineering.

        Input:
            - fp:           STR: filepath
            - from_CIVL:    BOOL: look for pilot on CIVL database
        """

        """read the fsdb file"""
        root = read_fsdb_file(fp)

        pilots = []
        tasks = []
        comp_attributes = []

        """Comp Info"""
        print("Getting Comp Info...")
        fs_comp = root.find('FsCompetition')
        comp = Comp.from_fsdb(fs_comp, short_name)

        """Formula"""
        comp.formula = Formula.from_fsdb(fs_comp, comp.comp_class)

        '''adding standard igc config'''
        comp.igc_config_file = 'standard'

        """Pilots"""
        print("Getting Pilots Info...")
        if from_CIVL:
            print('*** get from CIVL database')
        p = root.find('FsCompetition').find('FsParticipants')
        if p is not None:
            comp_attributes = get_fsdb_custom_attributes(p)
            for pil in p.iter('FsParticipant'):
                pilot = Participant.from_fsdb(pil, from_CIVL=from_CIVL)
                # pp(pilot.as_dict())
                pilots.append(pilot)

            comp.participants = pilots

        """Tasks"""
        print("Getting Tasks Info...")
        t = root.find('FsCompetition').find('FsTasks')
        if t is not None:
            for tas in t.iter('FsTask'):
                '''create task obj'''
                task = Task.from_fsdb(tas, comp.formula, comp.time_offset, keep_task_path)
                '''check if task was valid'''
                if task is not None:
                    if not task.task_path:
                        task.create_path()
                    # task.time_offset = int(comp.time_offset)
                    """Task Results"""
                    node = tas.find('FsParticipants')
                    if node is not None:
                        task.pilots = []
                        print("Getting Results Info...")
                        for res in node.iter('FsParticipant'):
                            '''pilots results'''
                            pilot = FlightResult.from_fsdb(res, task)
                            # pilot.name = next((p.name for p in pilots if p.ID == pilot.ID), f'Pilot {pilot.ID}')
                            task.pilots.append(pilot)
                    tasks.append(task)

        return cls(comp, tasks, fp, comp_attributes)

    @classmethod
    def create(cls, comp_id, ref_id=None):
        """creates a FSDB Object from an AirScore competition
        input:
            - comp_id       int: comp_id event ID"""
        import time

        '''check comp is not an external event'''
        if is_ext(comp_id):
            # TODO probably with new logic we are able to create FSDB from ext comps?
            return None

        comp = Comp.from_json(comp_id, ref_id)
        '''check comp has already been scored'''
        if comp is None:
            print(f"Comp (ID {comp_id}) has not been scored yet.")
            return None

        timestamp = int(time.time() + comp.time_offset)
        dt = datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')
        filename = '_'.join([comp.comp_code, dt]) + '.fsdb'

        '''get tasks and results'''
        tasks = []
        for tas in comp.tasks:
            task_id = tas['id']
            task = Task.create_from_json(task_id=task_id)
            tasks.append(task)

        fsdb = FSDB(comp=comp, filename=filename, tasks=tasks)
        return fsdb

    @staticmethod
    def create_participants(comp_id: int):
        """ create FSDB file with participants, to use for Flymaster Livetracking setup on lt.flymaster.net site"""
        from compUtils import get_participants

        fsdb = FSDB()
        fsdb.comp = Comp.read(comp_id)
        fsdb.filename = f"{fsdb.comp.comp_name.replace(' - ', '_').replace(' ', '_')}_participants.fsdb"
        fsdb.comp.participants = get_participants(comp_id)
        return fsdb.to_file(participants_fsdb=True)

    def to_file(self, participants_fsdb: bool = False):
        """returns:
        - filename: STR
        - fsdb:     FSDB xml data, to be used in frontend."""
        from frontendUtils import get_pretty_data
        from compUtils import get_comp_json, get_comp_json_filename
        from task import get_task_json
        from result import get_comp_team_scoring, get_comp_country_scoring

        formula = self.comp.formula
        pilots = self.comp.participants
        custom = {}
        if any(el for el in pilots if el.fai_id):
            custom['fai_n'] = 'fai_id'
        if any(el for el in pilots if el.glider_cert):
            custom['class'] = 'glider_cert'
        if any(el for el in pilots if el.team):
            custom['team'] = 'team'
        if any(el for el in pilots if el.live_id):
            custom['LIVE'] = 'live_id'

        '''create dicts of attributes for each section'''
        comp_attr = {
            'id': '',  # still to do
            'name': self.comp.comp_name,
            'location': self.comp.comp_site,
            'from': self.comp.date_from,
            'to': self.comp.date_to,
            'utc_offset': self.comp.time_offset / 3600,
            'discipline': self.comp.comp_class.lower(),
            'ftv_factor': c_round(1 - formula.validity_param, 4),
            'fai_sanctioning': (1 if self.comp.sanction == 'FAI 1' else 2 if self.comp.sanction == 'FAI 2' else 0),
        }

        formula_attr = {
            'id': formula.formula_name,
            'min_dist': km(formula.min_dist, 0),
            'nom_dist': km(formula.nominal_dist, 0),
            'nom_time': formula.nominal_time / 3600,
            'nom_launch': formula.nominal_launch,
            'nom_goal': formula.nominal_goal,
            'day_quality_override': 0,  # still to implement
            'bonus_gr': get_int(formula.glide_bonus) or '',
            'jump_the_gun_factor': (0 if formula.max_JTG == 0 else c_round(1 / formula.JTG_penalty_per_sec, 1)),
            'jump_the_gun_max': formula.max_JTG,
            'normalize_1000_before_day_quality': 0,  # still to implement
            'time_points_if_not_in_goal': c_round(1 - formula.no_goal_penalty, 1),
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
            'score_back_time': int((formula.score_back_time or 0) / 60) or '',
            'use_proportional_leading_weight_if_nobody_in_goal': '',  # still to implement
            'leading_weight_factor': (0 if formula.formula_departure != 'leadout' else c_round(formula.lead_factor, 3)),
            'turnpoint_radius_tolerance': formula.tolerance,
            'use_arrival_altitude_points': 0 if formula.arr_alt_bonus == 0 else '',  # still to implement
        }
        if formula.arr_alt_bonus > 0:
            formula_attr['aatb_factor'] = c_round(formula.arr_alt_bonus, 3)

        '''create the file structure'''
        root = ET.Element('Fs')
        root.set('version', '3.5')
        root.set('comment', 'generated by AirScore')
        '''FsCompetition'''
        comp = ET.SubElement(root, 'FsCompetition')
        for k, v in comp_attr.items():
            comp.set(k, str(v))

        f = ET.SubElement(comp, 'FsScoreFormula')
        for k, v in formula_attr.items():
            f.set(k, str(v))

        notes = ET.SubElement(comp, 'FsCompetitionNotes')
        notes.text = CDATA('Generated by AirScore')
        # notes.text = '<![CDATA[Generated by AirScore]]>'

        '''FsParticipants'''
        participants = ET.SubElement(comp, 'FsParticipants')
        for p in pilots:
            pil = ET.SubElement(participants, 'FsParticipant')
            pilot_attr = {
                'id': p.ID or p.par_id,
                'name': p.name,
                'birthday': p.pilot_birthdate_str or '',
                'glider': p.glider or '',
                'glider_main_colors': '',
                'fai_licence': 1 if p.fai_id else 0,
                'female': p.female,
                'nat_code_3166_a3': p.nat or '',
                'sponsor': p.sponsor or '',
                'CIVLID': p.civl_id or '',
            }

            custom_attr = {k: getattr(p, v) or '' for k, v in custom.items()} if custom else {}

            for k, v in pilot_attr.items():
                pil.set(k, str(v))
            if custom_attr:
                cus = ET.SubElement(pil, 'FsCustomAttributes')
                for k, v in custom_attr.items():
                    sub = ET.SubElement(cus, 'FsCustomAttribute')
                    sub.set('name', k)
                    sub.set('value', str(v))

        if not participants_fsdb:
            '''FsTasks'''
            task_ids = dict()
            tasks = ET.SubElement(comp, 'FsTasks')
            for idx, t in enumerate(self.tasks):
                task = ET.SubElement(tasks, 'FsTask')
                task.set('id', str(idx + 1))
                task_ids[idx+1] = t.task_code
                task.set('name', t.task_name)
                task.set('tracklog_folder', '')

                task_f = ET.SubElement(task, 'FsScoreFormula')
                task_d = ET.SubElement(task, 'FsTaskDefinition')
                task_s = ET.SubElement(task, 'FsTaskState')
                task_p = ET.SubElement(task, 'FsParticipants')
                task_sp = ET.SubElement(task, 'FsTaskScoreParams')
                task_tr = ET.SubElement(task, 'FsTaskResults')

                # tf = dict(t.formula.to_dict(), **t.stats)

                '''FsTaskState'''
                task_s.set('task_state', ('REGULAR' if not t.stopped_time else 'STOPPED'))  # ?
                task_s.set('score_back_time', f'{int(t.formula.score_back_time / 60)}')
                task_s.set('cancel_reason', t.comment)

                '''FsScoreFormula'''
                # we permit just few changes in single tasks from comp formula, so we just update those
                tf_attr = formula_attr
                tf_attr.update(
                    {
                        'jump_the_gun_factor': (
                            0 if not t.formula.JTG_penalty_per_sec else round(1 / t.formula.JTG_penalty_per_sec, 1)
                        ),
                        'time_points_if_not_in_goal': 1 - t.formula.no_goal_penalty,
                        'use_arrival_position_points': 1 if t.formula.arrival == 'position' else 0,
                        'use_arrival_time_points': 1 if t.formula.arrival == 'time' else 0,
                        'use_departure_points': 1 if t.formula.departure == 'departure' else 0,
                        'use_difficulty_for_distance_points': 1 if t.formula.distance == 'difficulty' else 0,
                        'use_distance_points': 0 if t.formula.distance == 'off' else 1,
                        'use_leading_points': 0 if t.formula.departure == 'off' else 1,
                        'use_time_points': 0 if t.formula.time == 'off' else 1,
                        'scoring_altitude': 'GPS' if t.formula.scoring_altitude == 'GPS' else 'QNH',
                        'final_glide_decelerator': 'none' if t.formula.arr_alt_bonus == 0 else 'aatb',
                        'use_arrival_altitude_points': 0 if t.formula.arr_alt_bonus == 0 else 1,
                        'turnpoint_radius_tolerance': t.formula.tolerance,
                    }
                )

                for k, v in tf_attr.items():
                    task_f.set(k, str(v))

                '''FsTaskDefinition'''
                tps = t.turnpoints
                td_attr = {
                    'ss': [i + 1 for i, tp in enumerate(tps) if tp.type == 'speed'].pop(0),
                    'es': [i + 1 for i, tp in enumerate(tps) if tp.type == 'endspeed'].pop(0),
                    'goal': next(tp.shape for tp in tps if tp.type == 'goal').upper(),
                    'groundstart': 0,  # still to implement
                    'qnh_setting': 1013.25,  # still to implement
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
                    tp_attr = {
                        'id': tp.name,
                        'lat': round(tp.lat, 5),
                        'lon': round(tp.lon, 5),
                        'altitude': tp.altitude,
                        'radius': tp.radius,
                        'open': t_open if i < (td_attr['ss'] - 1) else ss_open,
                        'close': w_close if i == 0 else ss_close if i == (td_attr['ss'] - 1) else t_close,
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
                    gates += t.start_iteration
                for i in range(gates):
                    task_sg = ET.SubElement(task_d, 'FsStartGate')
                    intv = 0 if not t.SS_interval else t.SS_interval * i
                    i_time = get_isotime(t.date, (t.start_time + intv), t.time_offset)
                    task_sg.set('open', str(i_time))

                '''FsTaskScoreParams'''
                launch_ess = [t.partial_distance[i] for i, tp in enumerate(t.turnpoints) if tp.type == 'endspeed'].pop()
                sp_attr = {
                    'ss_distance': km(t.SS_distance),
                    'task_distance': km(t.opt_dist),
                    'launch_to_ess_distance': km(launch_ess),
                    'no_of_pilots_present': t.pilots_present,
                    'no_of_pilots_flying': t.pilots_launched,
                    'no_of_pilots_lo': t.pilots_launched - t.pilots_goal,
                    'no_of_pilots_reaching_nom_dist': len(
                        [x for x in t.valid_results if x.distance_flown > t.formula.nominal_dist]
                    ),
                    'no_of_pilots_reaching_es': t.pilots_ess,
                    'no_of_pilots_reaching_goal': t.pilots_goal,
                    'sum_flown_distance': km(t.tot_dist_flown),
                    'best_dist': km(t.max_distance or 0),
                    'best_time': round((t.fastest or 0) / 3600, 14),
                    'worst_time': round(max((x.ESS_time or 0) - (x.SSS_time or 0) for x in t.valid_results) / 3600, 14),
                    'no_of_pilots_in_competition': len(self.comp.participants),
                    'no_of_pilots_landed_before_stop': 0 if not t.stopped_time else t.pilots_landed,
                    'sum_dist_over_min': km(t.tot_dist_over_min),
                    'sum_real_dist_over_min': km(t.tot_dist_over_min),  # not yet implemented
                    'best_real_dist': km(t.max_distance_flown),
                    'last_start_time': get_isotime(
                        t.date, max([x.SSS_time for x in t.valid_results if x.SSS_time is not None]), t.time_offset
                    ),
                    'first_start_time': (
                        '' if not t.min_dept_time else get_isotime(t.date, t.min_dept_time, t.time_offset)
                    ),
                    'first_finish_time': (
                        '' if not t.min_ess_time else get_isotime(t.date, t.min_ess_time, t.time_offset)
                    ),
                    'max_time_to_get_time_points': round(0 / 3600, 14),  # not yet implemented
                    'no_of_pilots_with_time_points': len([x for x in t.valid_results if x.time_score > 0]),
                    'goalratio': (0 if t.pilots_launched == 0 else round(t.pilots_goal / t.pilots_launched, 15)),
                    'arrival_weight': 0 if t.arrival == 0 else c_round(t.arr_weight, 3),
                    'departure_weight': 0 if t.departure != 'on' else c_round(t.dep_weight, 3),
                    'leading_weight': 0 if t.departure != 'leadout' else c_round(t.dep_weight, 3),
                    'time_weight': 0 if t.arrival == 'off' else c_round(t.time_weight, 3),
                    'distance_weight': c_round(t.dist_weight, 3),  # not yet implemented
                    'smallest_leading_coefficient': '' if not t.min_lead_coeff else round(t.min_lead_coeff, 14),
                    'available_points_distance': round(t.avail_dist_points, 14),
                    'available_points_time': round(t.avail_time_points, 14),
                    'available_points_departure': (
                        0 if not t.formula.departure == 'departure' else round(t.avail_dep_points, 14)
                    ),
                    'available_points_leading': (
                        0 if not t.formula.departure == 'leadout' else round(t.avail_dep_points, 14)
                    ),
                    'available_points_arrival': round(t.avail_arr_points, 14),
                    'time_validity': c_round(t.time_validity, 3),
                    'launch_validity': c_round(t.launch_validity, 3),
                    'distance_validity': c_round(t.dist_validity, 3),
                    'stop_validity': c_round(t.stop_validity, 3),
                    'day_quality': c_round(t.day_quality, 3),
                    'ftv_day_validity': t.ftv_validity,
                    'time_points_stop_correction': 0,  # not yet implemented
                }
                for k, v in sp_attr.items():
                    task_sp.set(k, str(v))

                '''FsParticipants'''
                for i, pil in enumerate(t.pilots):
                    '''create pilot result for the task'''
                    pil_p = ET.SubElement(task_p, 'FsParticipant')
                    pil_p.set('id', str(pil.ID or pil.par_id))
                    if not (pil.result_type in ('abs', 'dnf', 'nyp')):
                        '''only if pilot flew'''
                        pil_fd = ET.SubElement(pil_p, 'FsFlightData')
                        pil_r = ET.SubElement(pil_p, 'FsResult')
                        if not (pil.result_type in ['mindist', 'min_dist']):
                            fd_attr = {
                                'distance': km(pil.distance_flown),
                                'bonus_distance': km(pil.distance),
                                # ?? seems 0 for PG and more than dist for HG
                                'started_ss': ''
                                if not pil.real_start_time
                                else get_isotime(t.date, pil.real_start_time, t.time_offset),
                                'finished_ss': ''
                                if not pil.ESS_time
                                else get_isotime(t.date, pil.ESS_time, t.time_offset),
                                'altitude_at_ess': get_int(pil.ESS_altitude),
                                'finished_task': ''
                                if not pil.goal_time
                                else get_isotime(t.date, pil.goal_time, t.time_offset),
                                'tracklog_filename': pil.track_file,
                                'lc': pil.lead_coeff,
                                'iv': pil.fixed_LC or '',
                                'ts': ''
                                if not pil.first_time
                                else get_isotime(t.date, pil.first_time, t.time_offset),
                                'alt': get_int(pil.last_altitude),  # ??
                                'bonus_alt': '',  # ?? not implemented
                                'max_alt': get_int(pil.max_altitude),
                                'last_tracklog_point_distance': '',  # not implemented yet
                                'bonus_last_tracklog_point_distance': '',  # ?? not implemented
                                'last_tracklog_point_time': ''
                                if not pil.landing_time
                                else get_isotime(t.date, pil.landing_time, t.time_offset),
                                'last_tracklog_point_alt': ''
                                if not pil.landing_altitude
                                else get_int(pil.landing_altitude),
                                'landed_before_deadline': '1'
                                if pil.landing_time < (t.task_deadline if not t.stopped_time else t.stopped_time)
                                else '0',
                                'reachedGoal': 1 if pil.goal_time else 0
                                # only deadline?
                            }
                            for k, v in fd_attr.items():
                                pil_fd.set(k, str(v))

                        r_attr = {
                            'rank': i + 1,  # not implemented, they should be ordered tho
                            # Rank IS NOT SAFE (I guess)
                            'points': c_round(pil.score),
                            'distance': km(pil.total_distance if pil.total_distance else pil.distance_flown),
                            'ss_time': '' if not pil.ss_time else sec_to_time(pil.ss_time).strftime('%H:%M:%S'),
                            'finished_ss_rank': '' if not pil.ESS_time and pil.ESS_rank else pil.ESS_rank,
                            'distance_points': 0 if not pil.distance_score else c_round(pil.distance_score, 1),
                            'time_points': 0 if not pil.time_score else c_round(pil.time_score, 1),
                            'arrival_points': 0 if not pil.arrival_score else c_round(pil.arrival_score, 1),
                            'departure_points': 0
                            if not t.formula.departure == 'departure'
                            else c_round(pil.departure_score, 1),
                            'leading_points': 0
                            if not t.formula.departure == 'leadout'
                            else c_round(pil.departure_score, 1),
                            'penalty': 0
                            if not [n for n in pil.notifications if n.percentage_penalty > 0]
                            else max(n.percentage_penalty for n in pil.notifications),
                            'penalty_points': 0
                            if not [n for n in pil.notifications if n.flat_penalty > 0]
                            else max(n.flat_penalty for n in pil.notifications),
                            'penalty_reason': '; '.join(
                                [
                                    n.comment
                                    for n in pil.notifications
                                    if n.flat_penalty + n.percentage_penalty > 0 and not n.notification_type == 'jtg'
                                ]
                            ),
                            'penalty_points_auto': sum(
                                n.flat_penalty for n in pil.notifications if n.notification_type == 'jtg'
                            ),
                            'penalty_reason_auto': ''
                            if not [n for n in pil.notifications if n.notification_type == 'jtg']
                            else next(n for n in pil.notifications if n.notification_type == 'jtg').flat_penalty,
                            'penalty_min_dist_points': 0,  # ??
                            'got_time_but_not_goal_penalty': (pil.ESS_time or 0) > 0 and not pil.goal_time,
                            'started_ss': ''
                            if not pil.real_start_time
                            else get_isotime(t.date, pil.SSS_time, t.time_offset),
                            'ss_time_dec_hours': 0 if not pil.ESS_time else round(pil.ss_time / 3600, 14),
                            'ts': (
                                '' if not pil.first_time else get_isotime(t.date, pil.first_time, t.time_offset)
                            ),  # flight origin time
                            'real_distance': km(pil.distance_flown),
                            'last_distance': '',  # ?? last fix distance?
                            'last_altitude_above_goal': get_int(pil.last_altitude),
                            'altitude_bonus_seconds': 0,  # not implemented
                            'altitude_bonus_time': sec_to_time(0).strftime('%H:%M:%S'),  # not implemented
                            'altitude_at_ess': get_int(pil.ESS_altitude),
                            'scored_ss_time': (
                                '' if not pil.ss_time else sec_to_time(pil.ss_time).strftime('%H:%M:%S')
                            ),
                            'landed_before_stop': t.stopped_time and pil.landing_time < t.stopped_time,
                        }
                        if pil.ESS_time:
                            r_attr['finished_ss'] = (get_isotime(t.date, pil.ESS_time, t.time_offset),)

                        for k, v in r_attr.items():
                            pil_r.set(k, str(v))

                '''FsTaskResults'''
                result = get_pretty_data(get_task_json(t.task_id))
                r = result['results']
                rankings = result['rankings']
                for el in rankings:
                    rank_id = el['rank_id']
                    taskresult = ET.SubElement(task_tr, 'FsTaskResult')
                    taskresult.set('id', str(el['rank_name']).lower())
                    taskresult.set('title', el['rank_name'])
                    taskresult.set('ts', '')
                    taskresult.set('result_pattern', ('#0.0' if formula.task_result_decimal == 1 else '#0'))
                    scorep = ET.SubElement(taskresult, 'FsTaskScoreParams')
                    for k, v in sp_attr.items():
                        scorep.set(k, str(v))
                    for i, tp in enumerate(tps):
                        sp_dist = ET.SubElement(scorep, 'FsTaskDistToTp')
                        sp_dist.set('tp_no', str(i + 1))
                        sp_dist.set('distance', str(t.partial_distance[i]))
                    '''FsTaskResultParticipants'''
                    taskp = ET.SubElement(taskresult, 'FsTaskResultParticipants')
                    for p in [x for x in r if x['rankings'][rank_id]]:
                        pr = ET.SubElement(taskp, 'FsTaskParticipantResult')
                        pr.set('id', str(p['ID']))
                        pr.set('rank', str(p['rankings'][rank_id]).split(' ')[0])
                        pr.set('distance_points', p['distance_score'] or '0')
                        pr.set('ddeparture_points', '0')
                        pr.set('arrival_points', p['arrival_score'] or '0')
                        pr.set('leading_points', p['departure_score'] or '0')
                        pr.set('time_points', p['time_score'] or '0')
                        pr.set('points', p['score'].split('>')[1].split('<')[0] or '0')
                        if p['result_type'].lower() in ('abs', 'dnf', 'nyp'):
                            pr.set('no_distance', p['result_type'].upper())

            '''FsCompetitionResults'''
            compresults = ET.SubElement(comp, 'FsCompetitionResults')
            result = get_pretty_data(get_comp_json(self.comp.comp_id))
            rankings = result['rankings']
            r = result['results']
            for el in rankings:
                rank_id = el['rank_id']
                cr = ET.SubElement(compresults, 'FsCompetitionResult')
                cr.set('id', str(el['rank_name']).lower())
                cr.set('title', str(el['rank_name']))
                cr.set('top', 'all')  # ?
                cr.set('tasks', ';'.join([str(i) for i in task_ids.keys()]))
                cr.set('ts', '')
                cr.set('task_result_pattern', '#0.0' if formula.task_result_decimal == 1 else '#0')
                cr.set('comp_result_pattern', '#0.0' if formula.comp_result_decimal == 1 else '#0')
                for p in [x for x in r if x['rankings'][rank_id]]:
                    pr = ET.SubElement(cr, 'FsParticipant')
                    pr.set('id', str(p['ID']))
                    pr.set('points', p['score'].split('>')[1].split('<')[0])
                    pr.set('rank', str(p['rankings'][rank_id]).split(' ')[0])
                    res = list(p['results'].items())
                    for x in res:
                        pt = ET.SubElement(pr, 'FsTask')
                        pt.set('id', str(next(k for k, v in task_ids.items() if v == x[0])))
                        pt.set('points', x[1]['pre'])
                        pt.set('counting_points', x[1]['score'])
                        pt.set('counts', '1')

            if formula.team_scoring or formula.country_scoring:
                '''FsTeamResults'''
                teamresults = ET.SubElement(comp, 'FsTeamResults')
                if formula.team_scoring:
                    filename = get_comp_json_filename(self.comp.comp_id)
                    results = get_comp_team_scoring(filename)
                    tr = ET.SubElement(teamresults, 'FsTeamResult')
                    tr.set('id', 'team')
                    tr.set('title', 'Team Results')
                    tr.set('tasks', ';'.join([str(i) for i in task_ids.keys()]))
                    tr.set('ts', '')
                    tr.set('task_result_pattern', '#0.0' if formula.task_result_decimal == 1 else '#0')
                    tr.set('comp_result_pattern', '#0.0' if formula.comp_result_decimal == 1 else '#0')
                    for idx, team in enumerate(sorted(results['teams'], key=lambda k: k['score'], reverse = 1), start=1):
                        team_pilots = sorted([p for p in results['data'] if p['team'].lower() == team['name'].lower()], key=lambda k: k['score'], reverse = 1)
                        print(f"Team: {team['name']} | pilots: {[p['name'] for p in team_pilots]}")
                        t = ET.SubElement(tr, 'FsTeam')
                        t.set('rank', str(idx))
                        t.set('name', str(team['name']))
                        t.set('points', str(team['score']))
                        for p in team_pilots:
                            par = ET.SubElement(t, 'FsParticipant')
                            par.set('id', str(p['ID']))
                            res = list(el for el in p['results'].items() if el[0] in task_ids.values())
                            print(f"res: {res}")
                            for x in res:
                                print(f"ID: {x[0]} | items: {task_ids.items()}")
                                pt = ET.SubElement(par, 'FsTask')
                                pt.set('id', str(next(k for k, v in task_ids.items() if v == x[0]))) 
                                pt.set('counts', str(x[1]['perf']))

                if formula.country_scoring:
                    results = get_comp_country_scoring(filename)
                    tr = ET.SubElement(teamresults, 'FsTeamResult')
                    tr.set('id', 'nat_code_3166_a3')
                    tr.set('title', 'Nations Results')
                    tr.set('tasks', ';'.join([str(i) for i in task_ids.keys()]))
                    tr.set('ts', '')
                    tr.set('task_result_pattern', '#0.0' if formula.task_result_decimal == 1 else '#0')
                    tr.set('comp_result_pattern', '#0.0' if formula.comp_result_decimal == 1 else '#0')
                    for idx, team in enumerate(sorted(results['teams'], key=lambda k: k['score'], reverse = 1), start=1):
                        team_pilots = sorted([p for p in results['data'] if p['team'].lower() == team['name'].lower()], key=lambda k: k['score'], reverse = 1)
                        print(f"Team: {team['name']} | pilots: {[p['name'] for p in team_pilots]}")
                        t = ET.SubElement(tr, 'FsTeam')
                        t.set('rank', str(idx))
                        t.set('name', str(team['name']))
                        t.set('points', str(team['score']))
                        for p in team_pilots:
                            par = ET.SubElement(t, 'FsParticipant')
                            par.set('id', str(p['ID']))
                            res = list(el for el in p['results'].items() if el[0] in task_ids.values())
                            print(f"res: {res}")
                            for x in res:
                                print(f"ID: {x[0]} | items: {task_ids.items()}")
                                pt = ET.SubElement(par, 'FsTask')
                                pt.set('id', str(next(k for k, v in task_ids.items() if v == x[0]))) 
                                pt.set('counts', str(x[1]['perf']))

        '''creates the file to store'''
        fsdb = ET.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')

        return self.filename, fsdb

    def save_file(self, filename: str = None):
        """write fsdb file to results folder, with default filename:
        comp_code_datetime.fsdb"""
        from Defines import RESULTDIR

        _, fsdb = self.to_file()
        if not filename:
            filename = self.filename
        file = Path(RESULTDIR, filename)
        with open(file, "wb") as file:
            file.write(fsdb)

    def add_comp(self):
        """
        Add comp to AirScore database
        """
        from ranking import create_overall_ranking

        self.comp.to_db()
        self.comp.formula.comp_id = self.comp.comp_id
        self.comp.formula.to_db()
        create_overall_ranking(self.comp.comp_id)

    def add_custom_attributes(self, comp_id: int = None):
        """
        Add comp to AirScore database
        """
        if self.custom_attributes and (comp_id is not None or self.comp.comp_id is not None):
            for attr in self.custom_attributes:
                attr.comp_id = comp_id or self.comp.comp_id
                attr.to_db()

    def add_tasks(self, comp_id: int = None):
        """
        Add comp tasks to AirScore database
        """

        if comp_id is None and self.comp.comp_id is None:
            return False
        for t in self.tasks:
            t.comp_id = comp_id or self.comp.comp_id
            # t.create_path()
            '''recalculating legs to avoid errors when fsdb task misses launch and/or goal'''
            if t.geo is None:
                t.get_geo()
            t.calculate_task_length()
            t.calculate_optimised_task_length()
            '''storing'''
            t.to_db()
            '''adding folders'''
            t.comp_path = self.comp.comp_path
            Path(t.file_path).mkdir(parents=True, exist_ok=True)
        return True

    def add_results(self):
        """
        Add results for each comp task to AirScore database
        """
        from result import TaskResult

        if self.comp.comp_id is None:
            return False

        for t in self.tasks:
            if len(t.results) == 0 or t.task_id is None:
                print(f"task {t.task_code} does not have a db ID or has not been scored.")
                pass
            '''get results par_id from participants'''
            for pilot in t.pilots:
                par = next(p for p in self.comp.participants if p.ID == pilot.ID)
                [setattr(pilot, attr, getattr(par, attr)) for attr in TaskResult.results_list if hasattr(par, attr)]
            inserted = update_all_results(task_id=t.task_id, pilots=t.pilots)
            if not inserted:
                return False

        return True

    def add_participants(self, comp_id: int = None):
        """
        Add participants to AirScore database
        """

        if (comp_id is None and self.comp.comp_id is None) or len(self.comp.participants) == 0:
            print(f"Comp does not have a db ID or has not participants.")
            return False

        for p in self.comp.participants:
            p.comp_id = comp_id or self.comp.comp_id
            if self.custom_attributes and hasattr(p, 'attributes'):
                '''creates Participant.custom'''
                for attr in p.attributes:
                    attr_id = next((el.attr_id for el in self.custom_attributes
                                    if el.attr_value == attr['attr_value']), None)
                    p.custom[attr_id] = attr['meta_value']
                p.attributes = None

        response = mass_import_participants(comp_id or self.comp.comp_id, self.comp.participants, check_ids=False)

        return response

    def create_results_files(self):
        from result import create_json_file

        for task in self.tasks:
            task.comp_id = self.comp.comp_id
            task.comp_name = self.comp.comp_name
            task.comp_site = self.comp.comp_site
            task.comp_class = self.comp.comp_class
            elements = task.create_json_elements()
            ref_id, filename, _ = create_json_file(
                comp_id=self.comp.comp_id,
                task_id=task.id,
                code='_'.join([self.comp.comp_code, task.task_code]),
                elements=elements,
                status='Imported from FSDB',
            )
            print(f' - created file {filename} for {task.task_name}')
        Comp.create_results(self.comp.comp_id, status='Created from FSDB imported results', name_suffix='Overview')

    def add_all(self):
        print(f"add all FSDB info to database...")
        print(f"adding comp...")
        self.add_comp()
        if self.comp.comp_id is not None:
            print(f"comp ID: {self.comp.comp_id}")
            self.add_custom_attributes()
            print(f"adding participants...")
            par_resp = self.add_participants()
            print(f"adding tasks...")
            tasks_resp = self.add_tasks()
            if par_resp and tasks_resp:
                print(f"adding results...")
                self.add_results()
                print(f"creating original results files...")
                self.create_results_files()
            print(f"Done.")
            return self.comp.comp_id
        else:
            return None


def read_fsdb_file(file: Path) -> ET:
    """read the fsdb file"""
    try:
        tree = ET.parse(file)
    except TypeError:
        tree = ET.parse(file.as_posix())
    except ET.Error:
        print("FSDB Read Error.")
        return None
    finally:
        root = tree.getroot()
        return root
