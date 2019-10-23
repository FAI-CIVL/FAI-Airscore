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
    if t.stats['max_ess_time']:
        if (res['last_time'] < t.stats['max_ess_time']):
            task_deadline = t.stats['max_ess_time']
        else:
            task_deadline = min(res['last_time'], task_deadline)

    '''Checking if we have a assigned status without a track, and if pilot actually did the start pilon'''
    if res['result'] not in ('abs', 'dnf', 'mindist') and res['SS_time']:
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
    #print(""" ** start_time: {} | task_deadline: {} | task_time: {} | leading p.: {} | trailing p.: {} \n""".format(res['start'], task_deadline, task_time, leading, trailing))
    '''write final LC to tblTaskResult table in tarLeadingCoeff column'''
    # making a def because I suppose that in the future we could avoid storing total LC in DB
    #store_LC(res['tarPk'], LC)

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

    nomlau  = stats['pilots_present'] * (1 - formula.nominal_launch)
    LVR     = min(1, (stats['pilots_launched'] + nomlau) / stats['pilots_present'])
    launch  = 0.028 * LVR + 2.917 * LVR**2 - 1.944 * LVR**3
    launch  = min(launch, 1) if launch > 0 else 0           #sanity
    print("PWC Launch validity: {}".format(launch))
    return launch

def day_quality(task, formula):
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

    if task.stopped_time: val['stop_validity'] = stopped_validity(task, formula)

    val['launch_validity']  = launch_validity(task.stats, formula)
    val['dist_validity']    = distance_validity(task.stats, formula)
    val['time_validity']    = time_validity(task.stats, formula)
    val['day_quality']      = min( (val['stop_validity']*val['launch_validity']*val['dist_validity']*val['time_validity']), 1.000)
    #print("dict: {}".format(val['day_quality']))
    # f"quality: {val['stop_validity']}*{val['launch_validity']}*{val['dist_validity']}*{val['time_validity']} = {val['day_quality']}"

    return val

def ordered_results(task, formula, results):

    stats = task.stats

    pilots=[]

    # Get all pilots and process each of them
    # pity it can't be done as a single update ...

    query = """SELECT
                                @x := @x + 1 AS Place,
                                tarPk,
                                traPk,
                                tarDistance,
                                tarStart,
                                tarSS,
                                tarES,
                                tarPenalty,
                                tarResultType,
                                tarLeadingCoeff2,
                                tarGoal,
                                tarLastAltitude,
                                tarLastTime
                            FROM
                                tblTaskResult
                            WHERE
                                tasPk = %s
                            AND
                                tarResultType <> 'abs'
                            ORDER BY
                                CASE WHEN(
                                    tarGoal=0
                                OR tarES IS null
                                ) THEN - 999999
                                ELSE tarLastAltitude END,
                                tarDistance DESC"""

    with Database() as db:
        db.execute('set @x=0')
        t = db.fetchall(query, [task.task_id])

    for res in t:

        taskres = {}

        taskres['tarPk'] = res['tarPk']
        taskres['traPk'] = res['traPk']
        taskres['penalty'] = res['tarPenalty']
        taskres['distance'] = res['tarDistance']
        taskres['stopalt'] = res['tarLastAltitude']

        # Handle Stopped Task
        if task.stopped_time and taskres['stopalt'] > 0 and formula.glide_bonus > 0:
            if taskres['stopalt'] > task.goal_altitude:
                print("Stopped height bonus: ", (formula.glide_bonus * taskres['stopalt']))
                taskres['distance'] = taskres['distance'] + formula.glide_bonus * (taskres['stopalt'] - task.goal_altitude)
                if taskres['distance'] > task.SS_distance:
                    taskres['distance'] = task.SS_distance

        # set pilot to min distance if they're below that ..
        if taskres['distance'] < formula.min_dist:
            taskres['distance'] = formula.min_dist

        taskres['result']       = res['tarResultType']
        taskres['startSS']      = res['tarSS']
        taskres['start']        = res['tarStart']
        taskres['endSS']        = res['tarES']
        taskres['timeafter']    = (res['tarES'] - stats['min_ess_time']) if res['tarES'] else None
        taskres['place']        = res['Place']
        taskres['time']         = (taskres['endSS'] - taskres['startSS']) if taskres['endSS'] else 0
        taskres['goal']         = res['tarGoal']
        taskres['last_time']    = res['tarLastTime']
        taskres['fixed_LC']     = res['tarLeadingCoeff2']
        #taskres['lead_coeff']           = res['tarLeadingCoeff']

        if taskres['time'] < 0:
            taskres['time'] = 0

        '''
        Leadout Points Adjustment
        C.6.3.1
        '''
        #if taskres['result'] not in ('abs', 'dnf', 'mindist') and taskres['startSS']:
        taskres['lead_coeff'] = lc_calc(taskres, task) # PWC LeadCoeff (with squared distances)
        # else:
        #     taskres['lead_coeff'] = 0


        pilots.append(taskres)

    return pilots

def get_results_new(task, formula):

    stats = task.stats

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
        pilots = db.fetchall(query, [task.task_id])

    for res in pilots:
        '''manage ABS pilots'''
        if res['result'] is not 'abs':
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

            '''
            Leadout Points Adjustment
            C.6.3.1
            '''
            #if taskres['result'] not in ('abs', 'dnf', 'mindist') and taskres['startSS']:
            res['lead_coeff'] = lc_calc(res, task) # PWC LeadCoeff (with squared distances)
            # else:
            #     taskres['lead_coeff'] = 0

    return pilots

def points_allocation(task, formula, results = None):   # from PWC###

    stats   = task.stats
    tasPk   = task.task_id
    quality = stats['day_quality']
    Ngoal   = stats['pilots_goal']
    Tmin    = stats['fastest']
    Tfarr   = stats['min_ess_time']

    sorted_pilots = ordered_results(task, formula, results)

    '''
    Update Min LC
    in ordered_results we calculate final LC
    so we need to update LCmin for the task
    '''
    task.stats['min_lead_coeff'] = min(res['lead_coeff'] for res in sorted_pilots if res['result'] not in ('dnf', 'abs', 'mindist'))

    # Get basic GAP allocation values
    Adistance, Aspeed, Astart, Aarrival = points_weight(task, formula)

    # Update point weights in tblTask
    # query = "UPDATE tblTask SET tasAvailDistPoints=%s, " \
    #         "tasAvailLeadPoints=%s, " \
    #         "tasAvailTimePoints=%s " \
    #         "WHERE tasPk=%s"
    # params = [Adistance, Astart, Aspeed, tasPk]
    #
    # with Database() as db:
    #     db.execute(query, params)

    task.stats['avail_dist_points']     = Adistance
    task.stats['avail_time_points']     = Aspeed
    task.stats['avail_dep_points']      = Astart
    task.stats['avail_arr_points']      = Aarrival
    task.update_points_allocation()

    # Score each pilot now
    for pil in sorted_pilots:
        tarPk = pil['tarPk']
        penalty = pil['penalty'] if pil['penalty'] else 0
        # if not penalty:
        #     penalty= 0


        # Sanity
        if pil['result'] in ('dnf', 'abs'):
            Pdist       = 0
            Pspeed      = 0
            Parrival    = 0
            Pdepart     = 0

        else:
            # Pilot distance score
            # FIX: should round pil->distance properly?
            # my pilrdist = round(pil->{'distance'}/100.0) * 100
            Pdist = pilot_distance(task, pil, Adistance)

            # Pilot speed score
            Pspeed = pilot_speed(task, pil, Aspeed)

            # Pilot departure/leading points
            Pdepart = pilot_departure_leadout(task, pil, Astart) if (pil['result'] != 'mindist' and pil['startSS']) else 0

        # Pilot arrival score    this is always off in pwc
        # Parrival = pilot_arrival(formula, task, pil, Aarrival)
        Parrival=0
        # Penalty for not making goal .
        if not pil['goal']:
            pil['goal'] = 0

        if pil['goal'] == 0:
            Pspeed = Pspeed * (1 - formula.no_goal_penalty)
            Parrival = Parrival * (1 - formula.no_goal_penalty)

        # Total score
        print('{} + {} + {} + {} + {}'.format(Pdist,Pspeed,Parrival,Pdepart,penalty))
        Pscore = Pdist + Pspeed + Parrival + Pdepart - penalty

        # Store back into tblTaskResult ...
        if tarPk:
            print("update tarPk: dP:{}, sP:{}, LeadP:{} - score {}".format(Pdist, Pspeed, Pdepart, Pscore))
            query = "update tblTaskResult " \
                    "SET tarDistanceScore=%s, " \
                    "tarSpeedScore=%s, " \
                    "tarArrivalScore=%s, " \
                    "tarDepartureScore=%s, " \
                    "tarScore=%s " \
                    "where tarPk=%s"

            params = [Pdist, Pspeed, Parrival, Pdepart, Pscore, tarPk]
            with Database() as db:
                db.execute(query, params)

def points_allocation_new(task, formula):   # from PWC###

    stats   = task.stats
    tasPk   = task.task_id
    quality = stats['day_quality']
    Ngoal   = stats['pilots_goal']
    Tmin    = stats['fastest']
    Tfarr   = stats['min_ess_time']

    pilots = get_results_new(task, formula)

    '''
    Update Min LC
    in ordered_results we calculate final LC
    so we need to update LCmin for the task
    '''
    task.stats['min_lead_coeff'] = min(res['lead_coeff'] for res in pilots if res['result'] not in ('dnf', 'abs', 'mindist'))

    # Get basic GAP allocation values
    Adistance, Aspeed, Astart, Aarrival = points_weight(task, formula)

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
            pil['Pdist']       = 0
            pil['Pspeed']      = 0
            pil['Parrival']    = 0
            pil['Pdepart']     = 0

        else:
            # Pilot distance score
            # FIX: should round pil->distance properly?
            # my pilrdist = round(pil->{'distance'}/100.0) * 100
            pil['dist_points'] = pilot_distance(task, pil, Adistance)

            # Pilot speed score
            pil['time_points'] = pilot_speed(task, pil, Aspeed)

            # Pilot departure/leading points
            pil['dep_points'] = pilot_departure_leadout(task, pil, Astart) if (pil['result'] != 'mindist' and pil['SS_time']) else 0

        # Pilot arrival score    this is always off in pwc
        # Parrival = pilot_arrival(formula, task, pil, Aarrival)
        pil['arr_points']=0
        # Penalty for not making goal .
        if not pil['goal_time']:
            pil['goal_time'] = 0
            pil['time_points'] = pil['time_points'] * (1 - formula.no_goal_penalty)
            #pil['Parrival'] = Parrival * (1 - formula['forGoalSSpenalty'])

        # Total score
        print('{} + {} + {} + {} - {}'.format(pil['dist_points'],pil['time_points'],pil['arr_points'],pil['dep_points'],penalty))
        pil['score'] = pil['dist_points'] + pil['time_points'] + pil['arr_points'] + pil['dep_points']

        #update task max score
        if pil['score'] > task.stats['max_score']: task.stats['max_score'] = pil['score']

        #apply Penalty
        if penalty:
            pil['score'] = max(0, pil['score'] - penalty)

    return pilots
