"""
PWC Formula Library

contains
    - All procedures to calculate and allocate points according to PWC GAP Formula

Use:    lib = Task.formula.get_lib()
        lib = Formula.get_lib()

Stuart Mackintosh - 2019

TO DO:
Add support for FAI Sphere ???
"""

from collections import namedtuple
from formulas.gap import  task_totals, points_weight, pilot_distance, pilot_speed, pilot_departure_leadout
from myconn import Database

parameters = namedtuple('formula', 'allow_jump_the_gun, stopped_elapsed_calc, coeff_func, coeff_func_scaled, coef_landout')


def coef2(task_time, best_dist_to_ess, new_dist_to_ess):
    best_dist_to_ess    = best_dist_to_ess/1000     # we use Km
    new_dist_to_ess     = new_dist_to_ess/1000      # we use Km
    return task_time * (best_dist_to_ess**2 - new_dist_to_ess**2)


def coef_scaled(coeff, essdist):
    essdist             = essdist/1000              # we use Km
    return coeff / (1800 * (essdist ** 2))


def coef_landout(total_time_to_end, new_dist_to_ess):
    new_dist_to_ess     = new_dist_to_ess/1000      # we use Km
    return new_dist_to_ess ** 2 * total_time_to_end

parameters.allow_jump_the_gun = False
parameters.max_jump_the_gun = 0  # seconds
parameters.stopped_elapsed_calc = 'shortest_time'
parameters.coef_func = coef2
parameters.coef_func_scaled = coef_scaled
parameters.coef_landout = coef_landout

def store_LC(res_id, lead_coeff):
    '''store LC to database'''
    query = """ UPDATE `tblTaskResult`
                SET `tarLeadingCoeff` = %s
                WHERE `tarPk` = %s """
    params = [lead_coeff, res_id]

    with Database() as db:
        db.execute(query, params)

def lc_calc(res, t):
    LC          = 0
    leading     = 0
    trailing    = 0
    SS_Distance = t.SS_distance
    first_start = t.stats['min_dept_time']

    '''find task_deadline to use for LC calculation'''
    task_deadline = min((t.task_deadline if not t.stopped_time else t.stopped_time), t.stats['max_time'])
    if t.stats['max_ess_time'] and res['last_time']:
        if (res['last_time'] < t.stats['max_ess_time']):
            task_deadline = t.stats['max_ess_time']
        else:
            task_deadline = min(res['last_time'], task_deadline)

    '''Checking if we have a assigned status without a track, and if pilot actually did the start pilon'''
    if (res['result'] not in ('abs', 'dnf', 'mindist')) and res['SS_time']:
        my_start    = res['start_time']

        '''add the leading part, from start time of first pilot to start, to my start time'''
        if my_start > first_start:
            leading = parameters.coef_landout((my_start - first_start), SS_Distance)
            leading = parameters.coef_func_scaled(leading, SS_Distance)
        if not res['ES_time']:
            '''pilot did not make ESS'''
            best_dist_to_ess    = (t.opt_dist_to_ESS - res['distance'])
            # my_last_time        = res['last_time']          # should not need to check if < task deadline as we stop in Flight_result.check_flight()
            # last_ess            = t.stats['maxarr'] if t.stats['maxarr'] > 0 else min(t.task_deadline, t.stats['max_time'])
            # task_time           = (max(my_last_time,last_ess) - my_start)
            task_time           = task_deadline - my_start
            trailing            = parameters.coef_landout(task_time, best_dist_to_ess)
            trailing            = parameters.coef_func_scaled(trailing, SS_Distance)

        LC = leading + res['fixed_LC'] + trailing

    else:
        '''pilot didn't make SS or has a assigned status without a track'''
        task_time         = task_deadline - first_start
        max_LC            = parameters.coef_landout(task_time, SS_Distance)
        max_LC            = parameters.coef_func_scaled(max_LC, SS_Distance)

        LC = max_LC

    print ("""Pilot: {} - Distance: {} - Time: {} - LC: {} \n""".format(res['track_id'], res['distance'], res['time'], LC))

    return LC

def launch_validity(stats, formula):
    '''
    C.4.1 Launch Validity
    ‘Pilots Present’ are pilots arriving on take-off, with their gear, with the intention of flying.
    For scoring purposes, ‘Pilots Present’ are all pilots not in the ‘Absent’ status (ABS):
    Pilots who took off, plus pilots present who did not fly (DNF). DNFs need to be attributed carefully.
    A pilot who does not launch due to illness, for instance, is not a DNF, but an ABS.

    LVR = min (1, (num pilots launched + nominal launch) / pilots present )
    Launch Validity = 0.028*LRV + 2.917*LVR^2 - 1.944*LVR^3
    '''

    if stats['pilots_present'] == 0 or formula.nominal_launch == 0:
        '''avoid div by zero'''
        return 0

    nomlau  = stats['pilots_present'] * (1 - formula.nominal_launch)
    LVR     = min(1, (stats['pilots_launched'] + nomlau) / stats['pilots_present'])
    launch  = 0.028 * LVR + 2.917 * LVR**2 - 1.944 * LVR**3
    launch  = min(launch, 1) if launch > 0 else 0           #sanity
    print("PWC Launch validity: {}".format(launch))
    return launch

def day_quality(task):
    from formulas.gap import distance_validity, time_validity, stopped_validity

    val =   {
            'dist_validity':    0.000,
            'time_validity':    0.000,
            'launch_validity':  0.000,
            'stop_validity':    1.000,
            'day_quality':      0.000
            }

    if not task.launch_valid:
        print("Launch invalid - dist quality set to 0")
        return val

    if task.stats['pilots_present'] == 0:
        print("No pilots results - quality set to 0")
        return val

    if task.stopped_time: val['stop_validity'] = stopped_validity(task)

    stats   = task.stats
    formula = task.formula

    val['launch_validity']  = launch_validity(stats, formula)
    val['dist_validity']    = distance_validity(stats, formula)
    val['time_validity']    = time_validity(stats, formula)
    val['day_quality']      = min( (val['stop_validity']*val['launch_validity']*val['dist_validity']*val['time_validity']), 1.000)

    return val

def points_weight(task):
    from math import sqrt

    comp_class  = task.comp_class               # HG / PG
    stats       = task.stats
    formula     = task.formula
    quality     = stats['day_quality']

    if not(stats['pilots_launched'] > 0):       # sanity
        return 0, 0, 0, 0

    '''Goal Ratio'''
    goal_ratio = stats['pilots_goal'] / stats['pilots_launched']

    '''
    DistWeight:         0.9 - 1.665* goalRatio + 1.713*GolalRatio^2 - 0.587*goalRatio^3

    LeadWeight:         (1 - DistWeight)/8 * 1.4

    ArrWeight:          0

    TimeWeight:         1 − DistWeight − LeadWeight
    '''

    dist_weight = 0.9 - 1.665 * goal_ratio + 1.713 * goal_ratio**2 - 0.587 * goal_ratio**3
    lead_weight = (1 - dist_weight) / 8 * 1.4
    time_weight = 1 - dist_weight - lead_weight

    Adistance   = 1000 * quality * dist_weight            # AvailDistPoints
    Astart      = 1000 * quality * lead_weight            # AvailLeadPoints
    if formula.version == '2017':  Astart  += 50          # PWC2017 Augmented LeadPoints
    Aarrival    = 0                                       # AvailArrPoints
    Aspeed      = 1000 * quality * time_weight            # AvailSpeedPoints

    return Adistance, Aspeed, Astart, Aarrival

def get_results(task):

    stats   = task.stats
    formula = task.formula

    # Get all pilots and process each of them
    # pity it can't be done as a single update ...

    query = """ SELECT
                    `track_id`,
                    `pil_id`,
                    `name`,
                    `sponsor`,
                    `nat`,
                    `sex`,
                    `glider`,
                    `class`,
                    `distance`,
                    `speed`,
                    `start_time`,
                    `goal_time`,
                    `result`,
                    `SS_time`,
                    `ES_time`,
                    `turnpoints_made`,
                    `penalty`,
                    `comment`,
                    `fixed_LC`,
                    `last_altitude`,
                    `last_time`,
                    `track_file`,
                    `g_record`
                FROM
                    `TaskResultView`
                WHERE
                    `task_id` = %s
                """

    with Database() as db:
        pilots = db.fetchall(query, [task.id])

    for res in pilots:
        '''manage ABS pilots'''
        if not (res['result'] == 'abs'):
            # Handle Stopped Task
            if task.stopped_time and res['last_altitude'] > task.goal_altitude and formula.glide_bonus > 0:
                print("Stopped height bonus: ", (formula.glide_bonus * (res['last_altitude'] - task.goal_altitude)))
                res['distance'] = min( (res['distance'] + formula.glide_bonus * (res['last_altitude'] - task.goal_altitude)), task.SS_distance )
            # set pilot to min distance if they're below that ..
            res['distance'] = max(formula.min_dist, res['distance'])

            res['timeafter']    = (res['ES_time'] - stats['min_ess_time']) if res['ES_time'] else None
            res['time']         = (res['ES_time'] - res['SS_time']) if res['ES_time'] else 0

            #sanity
            res['time'] = max(res['time'], 0)
        else:
            res['time']         = None
            res['timeafter']    = None

        '''
        Leadout Points Adjustment
        C.6.3.1
        '''
        res['lead_coeff'] = lc_calc(res, task) # PWC LeadCoeff (with squared distances)

    return pilots

def points_allocation(task):   # from PWC###

    pilots = get_results(task)

    '''
    Update Min LC
    in ordered_results we calculate final LC
    so we need to update LCmin for the task
    '''
    task.stats['min_lead_coeff'] = min(res['lead_coeff'] for res in pilots if res['result'] not in ('dnf', 'abs', 'mindist'))

    stats   = task.stats
    task_id = task.id
    formula = task.formula

    # Get basic GAP allocation values
    Adistance, Aspeed, Astart, Aarrival = points_weight(task)

    task.stats['avail_dist_points'] = Adistance
    task.stats['avail_time_points'] = Aspeed
    task.stats['avail_dep_points']  = Astart
    task.stats['avail_arr_points']  = Aarrival
    #task.update_points_allocation()

    task.stats['max_score']         = 0

    # Score each pilot now
    for pil in pilots:
        tarPk   = pil['track_id']
        penalty = pil['penalty'] if pil['penalty'] else 0

        # Sanity
        if pil['result'] in ('dnf', 'abs'):
            pil['dist_points']  = 0
            pil['time_points']  = 0
            pil['arr_points']   = 0
            pil['dep_points']   = 0

        else:
            # Pilot distance score
            # FIX: should round pil->distance properly?
            # my pilrdist = round(pil->{'distance'}/100.0) * 100
            pil['dist_points']  = pilot_distance(task, pil)

            # Pilot speed score
            pil['time_points']  = pilot_speed(task, pil)

            # Pilot departure/leading points
            pil['dep_points']   = pilot_departure_leadout(task, pil) if (pil['result'] != 'mindist' and pil['SS_time']) else 0

            # Pilot arrival score    this is always off in pwc
            # Parrival = pilot_arrival(formula, task, pil)
            pil['arr_points']   = 0

            # Penalty for not making goal .
            if not pil['goal_time']:
                pil['goal_time']    = 0
                pil['time_points']  = pil['time_points'] * (1 - formula.no_goal_penalty)
                #pil['Parrival'] = Parrival * (1 - formula['forGoalSSpenalty'])

        # Total score
        pil['score'] = pil['dist_points'] + pil['time_points'] + pil['arr_points'] + pil['dep_points']

        print('{} + {} + {} + {} - {}'.format(pil['dist_points'],pil['time_points'],pil['arr_points'],pil['dep_points'],penalty))

        #update task max score
        if pil['score'] > task.stats['max_score']: task.stats['max_score'] = pil['score']

        #apply Penalty
        if penalty:
            pil['score'] = max(0, pil['score'] - penalty)

    return pilots

def pilot_speed(task, pil):
    from math import sqrt

    stats   = task.stats
    Aspeed  = stats['avail_time_points']

    # C.6.2 Time Points
    Tmin    = stats['fastest']
    Pspeed  = 0
    Ptime   = 0

    if pil['ES_time'] and Tmin > 0:   # checking that task has pilots in ESS, and that pilot is in ESS
                                        # we need to change this! It works correctly only if Time Pts is 0 when pil not in goal
                                        # for HG we need a fastest and a fastest in goal in TaskTotalsView
        Ptime = pil['time']
        SF = 1 - ((Ptime-Tmin) / 3600 / sqrt(Tmin / 3600) )**(5/6)

        if SF > 0:
            Pspeed = Aspeed * SF


    print(pil['track_id'], " Ptime: {}, Tmin={}".format(Ptime, Tmin))

    return Pspeed

def pilot_departure_leadout(task, pil):
    from math import sqrt

    stats   = task.stats
    Astart  = stats['avail_dep_points']

    # C.6.3 Leading Points

    LCmin   = stats['min_lead_coeff']   # min(tarLeadingCoeff2) as LCmin : is PWC's LCmin?
    LCp     = pil['lead_coeff']         # Leadout coefficient

    # Pilot departure score
    Pdepart = 0
    '''Departure Points type = Leading Points'''
    if task.departure == 'leadout':     # In PWC is always the case, we can ignore else cases
        print("  - PWC  leadout: LC ", LCp, ", LCMin : ", LCmin)
        if LCp > 0:
            if LCp <= LCmin:
                Pdepart = Astart
            elif LCmin <= 0:            # this shouldn't happen
                print("=======  being LCmin <= 0   =========")
                Pdepart = 0
            else:                       # We should have ONLY this case
                # LeadingFactor = max (0, 1 - ( (LCp -LCmin) / sqrt(LCmin) )^(2/3))
                # LeadingPoints = LeadingFactor * AvailLeadPoints
                LF = 1 - ( (LCp - LCmin) / sqrt(LCmin) )**(2/3)

                if LF > 0:
                    Pdepart = Astart * LF

    # Sanity
    if 0 + Pdepart != Pdepart:
        Pdepart = 0


    if Pdepart < 0:
        Pdepart = 0


    print("    Pdepart: ", Pdepart)
    return Pdepart
