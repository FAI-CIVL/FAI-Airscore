from airspace import AirspaceCheck
from calcUtils import sec_to_time
from formulas.libs.leadcoeff import LeadCoeff
from pilot.track import FlightParsingConfig
from pilot.flightresult import FlightResult
from pilot.waypointachieved import WaypointAchieved
from livetracking import LiveResult, LiveFix, reset_igc_file
from pathlib import Path
from route import (
    distance,
    distance_flown,
    get_fix_dist_to_goal,
    in_goal_sector,
    start_made_civl,
    tp_made_civl,
    tp_time_civl,
)
from task import Task

from .flightpointer import FlightPointer


def check_fixes(
    result: FlightResult or LiveResult,
    fixes: list,
    task: Task,
    tp: FlightPointer,
    lead_coeff: LeadCoeff = None,
    airspace: AirspaceCheck = None,
    livetracking: bool = False,
    igc_parsing_config: FlightParsingConfig = None,
    deadline: int = None,
    print=print,
):
    """ In normal track mode, checks an IGC track fixes against the Task route.
        In livetracking mode, checks a list of fixes against the LiveTask route
        """
    '''initialize'''
    total_fixes = len(fixes)
    tolerance = task.formula.tolerance or 0
    min_tol_m = task.formula.min_tolerance or 0
    max_jump_the_gun = task.formula.max_JTG or 0  # seconds
    jtg_penalty_per_sec = 0 if max_jump_the_gun == 0 else task.formula.JTG_penalty_per_sec
    distances2go = task.distances_to_go  # Total task Opt. Distance, in legs list
    dist_to_ESS = task.SS_distance

    ''' Altitude Source: '''
    alt_source = 'GPS' if task.formula.scoring_altitude is None else task.formula.scoring_altitude
    alt_compensation = 0 if alt_source == 'GPS' or task.QNH == 1013.25 else task.alt_compensation

    '''Stopped task managing'''
    if task.stopped_time:
        if not deadline:
            '''Using stop_time (stopped_time - score_back_time)'''
            deadline = task.stop_time
        goal_altitude = task.goal_altitude or 0
        glide_ratio = task.formula.glide_bonus or 0
        stopped_distance = 0
        stopped_altitude = 0
        total_distance = 0

    if not livetracking:
        percentage_complete = 0
    else:
        '''get if pilot already started in previous track slices'''
        already_started = tp.start_done
        '''get if pilot already made ESS in previous track slices'''
        already_ESS = any(e.name == 'ESS' for e in result.waypoints_achieved)

    for i in range(total_fixes - 1):
        # report percentage progress
        if not livetracking and int(i / len(fixes) * 100) > percentage_complete:
            percentage_complete = int(i / len(fixes) * 100)
            print(f"{percentage_complete}|% complete")

        '''Get two consecutive trackpoints as needed to use FAI / CIVL rules logic
        '''
        # start_time = tt.time()
        my_fix = fixes[i]
        next_fix = fixes[i + 1]
        if livetracking:
            alt = next_fix.alt
            '''check coherence'''
            if next_fix.rawtime - my_fix.rawtime < 1:
                continue
            alt_rate = abs(next_fix.alt - my_fix.alt) / (next_fix.rawtime - my_fix.rawtime)
            if (
                alt_rate > igc_parsing_config.max_alt_change_rate
                or not igc_parsing_config.min_alt < alt < igc_parsing_config.max_alt
            ):
                continue

            '''check flying'''
            speed = next_fix.speed  # km/h
            if not result.first_time:
                '''not launched yet'''
                if evaluate_launched(next_fix, tp.launch, igc_parsing_config):
                    '''pilot launched'''
                    result.first_time = next_fix.rawtime
                    result.live_comment = 'flying'
                    print(f"{result.name}: LAUNCHED {next_fix.rawtime} first_time {result.first_time}")
                else:
                    '''still on launch'''
                    continue

            else:
                '''check if pilot landed
                to avoid inconsistency with pilots landing on takeoff to address a problem, 
                we reset pilot for restart if landed in takeoff area before start opening'''
                if evaluate_landed(result, next_fix, config=igc_parsing_config):
                    print(f"{result.name}: SEEMS LANDED {next_fix}")
                    '''checking track'''
                    landing_fix = get_landing_fix(Path(task.file_path, result.track_file))
                    if landing_fix:
                        '''cope with top landing and restart'''
                        if not tp.start_done and next_fix.distance_to(tp.launch) < 1:  # kilometers from launch
                            result.first_time = None
                            result.distance_flown = 0
                            result.live_comment = 'top-landed'
                            '''deleting previous fixes from track file'''
                            reset_igc_file(result, task)
                        else:
                            '''assuming pilot landed'''
                            result.landing_time = next_fix.rawtime
                            result.landing_altitude = alt
                            result.live_comment = 'landed'
                        break
                    else:
                        result.suspect_landing_fix = None
        else:
            alt = next_fix.gnss_alt if alt_source == 'GPS' else next_fix.press_alt + alt_compensation

            if next_fix.rawtime < result.first_time:
                '''skip'''
                continue
            if result.landing_time and next_fix.rawtime > result.landing_time:
                '''pilot landed out'''
                # print(f'fix {i}: landed out - {next_fix.rawtime} - {alt}')
                break

        '''max altitude'''
        if alt > result.max_altitude:
            result.max_altitude = alt

        '''handle stopped task
        Pilots who were at a position between ESS and goal at the task stop time will be scored for their 
        complete flight, including the portion flown after the task stop time. 
        This is to remove any discontinuity between pilots just before goal and pilots who had just reached goal 
        at task stop time.
        '''
        if task.stopped_time and next_fix.rawtime > deadline and not tp.ess_done:
            result.still_flying_at_deadline = True
            result.stopped_distance = stopped_distance
            result.stopped_altitude = stopped_altitude
            result.total_distance = total_distance
            break

        '''check if task deadline has passed'''
        if task.task_deadline < next_fix.rawtime:
            # Task has ended
            result.still_flying_at_deadline = True
            break

        '''check if pilot has arrived in goal (last turnpoint) so we can stop.'''
        if tp.made_all:
            break

        '''check if start closing time passed and pilot did not start'''
        if task.start_close_time and task.start_close_time < my_fix.rawtime and not tp.start_done:
            # start closed
            break

        '''check tp type is known'''
        if tp.type not in ('launch', 'speed', 'waypoint', 'endspeed', 'goal'):
            assert False, f"Unknown turnpoint type: {tp.type}"

        '''check window is open'''
        if task.window_open_time > next_fix.rawtime:
            continue

        '''launch turnpoint managing'''
        if tp.type == "launch":
            if task.check_launch == 'on':
                # Set radius to check to 200m (in the task def it will be 0)
                # could set this in the DB or even formula if needed..???
                tp.next.radius = 200  # meters
                if tp.next.in_radius(my_fix, tolerance, min_tol_m):
                    result.waypoints_achieved.append(create_waypoint_achieved(my_fix, tp, my_fix.rawtime, alt))
                    tp.move_to_next()
            else:
                tp.move_to_next()

        # to do check for restarts for elapsed time tasks and those that allow jump the gun
        # if started and task.task_type != 'race' or result.jump_the_gun is not None:

        '''start turnpoint managing'''
        '''given all n crossings for a turnpoint cylinder, sorted in ascending order by their crossing time,
        the time when the cylinder was reached is determined.
        turnpoint[i] = SSS : reachingTime[i] = crossing[n].time
        turnpoint[i] =? SSS : reachingTime[i] = crossing[0].time

        We need to check start in 3 cases:
        - pilot has not started yet
        - race has multiple starts
        - task is elapsed time
        '''
        if pilot_can_start(task, tp, my_fix):
            # print(f'time: {my_fix.rawtime}, start: {task.start_time} | Interval: {task.SS_interval} | my start: {result.real_start_time} | better_start: {pilot_get_better_start(task, my_fix.rawtime, result.SSS_time)} | can start: {pilot_can_start(task, tp, my_fix)} can restart: {pilot_can_restart(task, tp, my_fix, result)} | tp: {tp.name}')
            ''' using NO WPT DIRECTION for start as for other waypoints - FAI GAP RULES 2020 '''
            if tp_made_civl(my_fix, next_fix, tp.next, tolerance, min_tol_m):
                time = int(round(tp_time_civl(my_fix, next_fix, tp.next), 0))
                result.waypoints_achieved.append(create_waypoint_achieved(my_fix, tp, time, alt))  # pilot has started
                result.real_start_time = time
                if not livetracking:
                    print(f"Pilot started SS at {sec_to_time(result.real_start_time)}")
                result.best_distance_time = time
                tp.move_to_next()

        elif pilot_can_restart(task, tp, my_fix, result):
            # print(f'time: {my_fix.rawtime}, start: {task.start_time} | Interval: {task.SS_interval} | my start: {result.real_start_time} | better_start: {pilot_get_better_start(task, my_fix.rawtime, result.SSS_time)} | can start: {pilot_can_start(task, tp, my_fix)} can restart: {pilot_can_restart(task, tp, my_fix, result)} | tp: {tp.name}')
            ''' using NO WPT DIRECTION for start as for other waypoints - FAI GAP RULES 2020 '''
            if tp_made_civl(my_fix, next_fix, tp.last_made, tolerance, min_tol_m):
                tp.pointer -= 1
                time = int(round(tp_time_civl(my_fix, next_fix, tp.next), 0))
                result.waypoints_achieved.pop()
                result.waypoints_achieved.append(
                    create_waypoint_achieved(my_fix, tp, time, alt)
                )  # pilot has started again
                result.real_start_time = time
                result.best_distance_time = time
                if not livetracking:
                    print(f"Pilot restarted SS at {sec_to_time(result.real_start_time)}")
                if lead_coeff:
                    lead_coeff.reset()
                tp.move_to_next()

        if tp.start_done:
            '''Turnpoint managing'''
            if tp.next.shape == 'circle' and tp.next.type in ('endspeed', 'waypoint'):
                if tp_made_civl(my_fix, next_fix, tp.next, tolerance, min_tol_m):
                    time = int(round(tp_time_civl(my_fix, next_fix, tp.next), 0))
                    result.waypoints_achieved.append(
                        create_waypoint_achieved(my_fix, tp, time, alt)
                    )  # pilot has achieved turnpoint
                    if not livetracking:
                        print(f"Pilot took {tp.name} at {sec_to_time(time)} at {alt}m")
                    tp.move_to_next()

            if tp.ess_done and tp.type == 'goal':
                if (tp.next.shape == 'circle' and tp_made_civl(my_fix, next_fix, tp.next, tolerance, min_tol_m)) or (
                    tp.next.shape == 'line' and (in_goal_sector(task, next_fix))
                ):
                    result.waypoints_achieved.append(
                        create_waypoint_achieved(next_fix, tp, next_fix.rawtime, alt)
                    )  # pilot has achieved goal
                    result.best_distance_time = next_fix.rawtime
                    if not livetracking:
                        print(f"Goal at {sec_to_time(next_fix.rawtime)}")
                    tp.done()
                    break

        '''update result data
        Once launched, distance flown should be max result among:
        - previous value;
        - optimized dist. to last turnpoint made;
        - total optimized distance minus opt. distance from next wpt to goal minus dist. to next wpt;
        '''
        if tp.pointer > 0:
            if tp.start_done and not tp.ess_done:
                '''optimized distance calculation each fix'''
                dist_to_goal, dist_to_ESS = get_fix_dist_to_goal(task, next_fix, tp.pointer)
                fix_dist_flown = task.opt_dist - dist_to_goal
                # print(f'time: {next_fix.rawtime} | fix: {tp.name} | Optimized Distance used')
            else:
                '''simplified and faster distance calculation'''
                fix_dist_flown = distance_flown(
                    next_fix, tp.pointer, task.optimised_turnpoints, task.turnpoints[tp.pointer], distances2go
                )
                # print(f'time: {next_fix.rawtime} | fix: {tp.name} | Simplified Distance used')

            if fix_dist_flown > result.distance_flown:
                '''time of trackpoint with shortest distance to ESS'''
                result.best_distance_time = next_fix.rawtime
                '''updating best distance flown'''
                result.distance_flown = fix_dist_flown

            '''stopped task
            ∀p : p ∈ PilotsLandedBeforeGoal :
                bestDistance p = max(minimumDistance, 
                                     taskDistance − min(∀trackp.pointi : shortestDistanceToGoal(trackp.pointi )
                                     − (trackp.pointi.altitude − GoalAltitude)*GlideRatio)) 
            ∀p :p ∈ PilotsReachedGoal : bestDistance p = taskDistance
            '''
            if task.stopped_time and glide_ratio and total_distance < task.opt_dist:
                alt_over_goal = max(0, alt - goal_altitude)
                if fix_dist_flown + glide_ratio * alt_over_goal > total_distance:
                    '''calculate total distance with glide bonus'''
                    stopped_distance = fix_dist_flown
                    stopped_altitude = alt
                    total_distance = min(fix_dist_flown + glide_ratio * alt_over_goal, task.opt_dist)

        '''Leading coefficient
        LC = taskTime(i)*(bestDistToESS(i-1)^2 - bestDistToESS(i)^2 )
        i : i ? TrackPoints In SS'''
        if lead_coeff and tp.start_done and not tp.ess_done:
            lead_coeff.update(result, my_fix, next_fix, dist_to_ESS)

        '''Airspace Check'''
        if task.airspace_check and airspace:
            # map_fix = [next_fix.rawtime, next_fix.lat, next_fix.lon, alt]
            plot, penalty = airspace.check_fix(next_fix, alt)
            if plot:
                # map_fix.extend(plot)
                '''Airspace Infringement: check if we already have a worse one'''
                airspace_name = plot[2]
                infringement_type = plot[3]
                dist = plot[4]
                separation = plot[5]
                result.infringements.append(
                    [next_fix, alt, airspace_name, infringement_type, dist, penalty, separation]
                )
                # print([next_fix, alt, airspace_name, infringement_type, dist, penalty])

    result.last_altitude = 0 if 'alt' not in locals() else alt
    result.last_time = 0 if 'next_fix' not in locals() else next_fix.rawtime
    if livetracking:
        result.height = (
            0 if not result.first_time or result.landing_time or 'next_fix' not in locals() else next_fix.height
        )


def calculate_final_results(
    result: FlightResult,
    task: Task,
    tp: FlightPointer,
    lead_coeff: LeadCoeff,
    airspace: AirspaceCheck = None,
    deadline: int = None,
    print=print,
):
    """"""
    '''final results'''
    print("100|% complete")

    if tp.start_done:
        evaluate_start(result, task, tp)

        '''ESS Time'''
        if tp.ess_done:
            evaluate_ess(result, task)

            if tp.made_all:
                evaluate_goal(result, task)

        else:
            '''save optimised best_dist_to_ESS for LC calculation'''
            result.best_dist_to_ESS = lead_coeff.best_dist_to_ess_m

    if result.result_type != 'goal':
        print(f"Pilot landed after {result.distance_flown / 1000:.2f}km")

    result.best_waypoint_achieved = str(result.waypoints_achieved[-1].name) if result.waypoints_achieved else None

    if lead_coeff:
        result.fixed_LC = lead_coeff.summing

    if task.airspace_check:
        infringements, notifications, penalty = airspace.get_infringements_result(result.infringements)
        result.infringements = infringements
        result.notifications.extend(notifications)


def pilot_can_start(task, tp, fix):
    """ returns True if pilot, in the track fix, is in the condition to take the start gate"""
    '''start turnpoint managing'''
    '''given all n crossings for a turnpoint cylinder, sorted in ascending order by their crossing time,
    the time when the cylinder was reached is determined.
    turnpoint[i] = SSS : reachingTime[i] = crossing[n].time
    turnpoint[i] =? SSS : reachingTime[i] = crossing[0].time

    We need to check start in 3 cases:
    - pilot has not started yet
    - race has multiple starts
    - task is elapsed time
    '''
    max_jump_the_gun = task.formula.max_JTG or 0
    if (
        (tp.type == "speed")
        and (fix.rawtime >= (task.start_time - max_jump_the_gun))
        and (not task.start_close_time or fix.rawtime <= task.start_close_time)
    ):
        return True
    else:
        return False


def pilot_can_restart(task: Task, tp: FlightPointer, fix, result: FlightResult) -> bool:
    """ returns True if pilot, in the track fix, is in the condition to take the start gate"""
    '''start turnpoint managing'''
    '''given all n crossings for a turnpoint cylinder, sorted in ascending order by their crossing time,
    the time when the cylinder was reached is determined.
    turnpoint[i] = SSS : reachingTime[i] = crossing[n].time
    turnpoint[i] =? SSS : reachingTime[i] = crossing[0].time

    We need to check start in 3 cases:
    - pilot has not started yet
    - race has multiple starts
    - task is elapsed time
    '''
    max_jump_the_gun = task.formula.max_JTG or 0
    if tp.last_made.type == "speed" and (not task.start_close_time or fix.rawtime < task.start_close_time):
        if task.task_type == 'elapsed time':
            return True
        elif max_jump_the_gun > 0 and result.real_start_time < task.start_time:
            return True
        elif task.SS_interval and pilot_get_better_start(task, fix.rawtime, result.real_start_time):
            return True
    return False


def start_number_at_time(task: Task, time: int) -> int:
    if time < task.start_time or (task.start_close_time and time > task.start_close_time):
        return 0
    elif task.total_start_number <= 1:
        return task.total_start_number
    elif task.SS_interval > 0:
        return min(1 + int((time - task.start_time) / task.SS_interval), task.total_start_number)


def pilot_get_better_start(task: Task, time: int, prev_time: int) -> bool:
    return start_number_at_time(task, time) > start_number_at_time(task, prev_time)


def create_waypoint_achieved(fix, tp: FlightPointer, time: int, alt: int) -> WaypointAchieved:
    """creates a dictionary to be added to result.waypoints_achived"""
    return WaypointAchieved(
        trw_id=None, wpt_id=tp.next.wpt_id, name=tp.name, lat=fix.lat, lon=fix.lon, rawtime=time, altitude=alt
    )


def evaluate_start(result: FlightResult, task: Task, tp: FlightPointer):
    from pilot.notification import Notification

    max_jump_the_gun = task.formula.max_JTG or 0  # seconds
    jtg_penalty_per_sec = 0 if max_jump_the_gun == 0 else task.formula.JTG_penalty_per_sec

    if tp.start_done:
        """
        start time
        if race, the first times
        if multistart, the first time of the last gate pilot made
        if elapsed time, the time of last fix on start
        SS Time: the gate time"""
        result.SSS_time = task.start_time

        if task.task_type == 'race' and task.SS_interval:
            result.SSS_time += max(0, (start_number_at_time(task, result.real_start_time) - 1) * task.SS_interval)

        elif task.task_type == 'elapsed time':
            result.SSS_time = max(result.real_start_time, task.start_time)  # jtg in elapsed time

        '''manage jump the gun'''
        if max_jump_the_gun > 0 and result.real_start_time < result.SSS_time:
            diff = result.SSS_time - result.real_start_time
            penalty = diff * jtg_penalty_per_sec
            # check
            comment = f"Jump the gun: {diff} seconds. Penalty: {penalty} points"
            result.notifications.append(Notification(notification_type='jtg', flat_penalty=penalty, comment=comment))


def evaluate_ess(result: FlightResult, task: Task):
    if any(e.name == 'ESS' for e in result.waypoints_achieved):
        result.ESS_time, result.ESS_altitude = min(
            [(x.rawtime, x.altitude) for x in result.waypoints_achieved if x.name == 'ESS'], key=lambda t: t[0]
        )
        result.speed = (task.SS_distance / 1000) / (result.ss_time / 3600)


def evaluate_goal(result: FlightResult, task: Task):
    """?p:p?PilotsLandingBeforeGoal:bestDistancep = max(minimumDistance, taskDistance-min(?trackp.pointi shortestDistanceToGoal(trackp.pointi)))
    ?p:p?PilotsReachingGoal:bestDistancep = taskDistance
    """
    if any(e.name == 'Goal' for e in result.waypoints_achieved):
        result.distance_flown = task.opt_dist
        result.goal_time, result.goal_altitude = min(
            [(x.rawtime, x.altitude) for x in result.waypoints_achieved if x.name == 'Goal'], key=lambda t: t[0]
        )
        result.result_type = 'goal'


def evaluate_launched(fix: LiveFix, launch, config: FlightParsingConfig) -> bool:
    print(f"launch dist. h: {int(fix.distance_to(launch)*1000)} v: {abs(launch.altitude - fix.alt)}, s: {fix.speed}")
    if (
            (abs(launch.altitude - fix.alt) > config.min_alt_difference
             or fix.distance_to(launch) * 1000 > config.min_distance)
            and fix.speed > config.min_gsp_flight
    ):
        print(f"AIRBORNE")
        return True
    print(f"not launched")
    return False


def evaluate_landed(p: LiveResult, fix: LiveFix, config: FlightParsingConfig) -> bool:
    if fix.speed < config.min_gsp_flight:
        if p.suspect_landing_fix:
            alt_diff = abs(p.suspect_landing_fix.alt - fix.alt)
            if alt_diff < config.min_alt_difference:
                time_diff = fix.rawtime - p.suspect_landing_fix.rawtime
                print(f"{p.name}: ALT DIFF: {alt_diff} TIME DIFF: {time_diff}")
                if time_diff > config.max_still_seconds:
                    '''probably landed'''
                    return True
        else:
            p.suspect_landing_fix = fix
    elif p.suspect_landing_fix:
        p.suspect_landing_fix = None
    return False


def get_landing_fix(track: Path, config: FlightParsingConfig = None):
    from pilot.track import Track
    f = Track.create_from_file(track, config)
    if hasattr(f, 'landing_fix') and f.landing_fix and not f.landing_fix == f.fixes[-1]:
        print(f"* Flight says pilot is LANDED! Flight landing fix: {f.landing_fix}")
        return f.landing_fix
    print(f"* Flight landing fix: Not valid")
    return None
