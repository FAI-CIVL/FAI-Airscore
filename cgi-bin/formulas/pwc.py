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
    SS_Distance = t.SSDistance

    '''Checking if we have a assigned status without a track, and if pilot actually did the start pilon'''
    if res['result'] not in ('abs', 'dnf', 'mindist') and res['startSS']:
        my_start    = res['start']
        first_start = t.stats['mindept']
        ss_start    = t.start_time

        '''add the leading part, from start time of first pilot to start, to my start time'''
        # if not my_start:
        #     my_start = 0  # this is to avoid my_start being none if pilot didn't make start and causing error below
        if my_start > first_start:
            leading = parameters.coef_landout((my_start - first_start), SS_Distance)
            leading = parameters.coef_func_scaled(leading, SS_Distance)
        if not res['endSS']:
            '''pilot did not make ESS'''
            best_dist_to_ess    = (t.EndSSDistance - res['distance'])
            my_last_time        = res['last_time']          # should not need to check if < task deadline as we stop in Flight_result.check_flight()
            last_ess            = t.stats['maxarr'] if ( t.stats['maxarr'] - t.start_time > 0 ) else t.end_time
            task_time           = (max(my_last_time,last_ess) - my_start)
            trailing            = parameters.coef_landout(task_time, best_dist_to_ess)
            trailing            = parameters.coef_func_scaled(trailing, SS_Distance)

        LC = leading + res['fixed_LC'] + trailing

    else:
        '''pilot didn't make SS or has a assigned status without a track'''
        best_dist_to_ess    = t.EndSSDistance
        task_time           = t.stats['maxarr'] if ( t.stats['maxarr'] - t.start_time > 0 ) else t.end_time
        trailing            = parameters.coef_landout(task_time, best_dist_to_ess)
        trailing            = parameters.coef_func_scaled(trailing, SS_Distance)

        LC = trailing

    print ("""Pilot: {} - Distance: {} - Time: {} - LC: {} \n""".format(res['tarPk'], res['distance'], res['time'], LC))
    '''write final LC to tblTaskResult table in tarLeadingCoeff column'''
    # making a def because I suppose that in the future we could avoid storing total LC in DB
    store_LC(res['tarPk'], LC)

    return LC

def launch_validity(taskt, formula):
    '''
    C.4.1 Launch Validity
    ‘Pilots Present’ are pilots arriving on take-off, with their gear, with the intention of flying.
    For scoring purposes, ‘Pilots Present’ are all pilots not in the ‘Absent’ status (ABS):
    Pilots who took off, plus pilots present who did not fly (DNF). DNFs need to be attributed carefully.
    A pilot who does not launch due to illness, for instance, is not a DNF, but an ABS.

    LVR = min (1, (num pilots launched + nominal launch) / pilots present )
    Launch Validity = 0.028*LRV + 2.917*LVR^2 - 1.944*LVR^3
    '''

    nomlau  = taskt['pilots'] * (1 - formula['forNomLaunch'])
    LVR     = min(1, (taskt['launched'] + nomlau) / taskt['pilots'])
    launch  = 0.028 * LVR + 2.917 * LVR**2 - 1.944 * LVR**3
    launch  = min(launch, 1) if launch > 0 else 0           #sanity
    print("PWC Launch validity: {}".format(launch))
    return launch

def day_quality(task, formula):
    from formulas.gap import distance_validity, time_validity, stopped_validity

    if not task.launchvalid:
        print("Launch invalid - quality set to 0")
        return (0, 0, 0, 0)

    taskt = task.stats

    if taskt['pilots'] == 0:
        print("No pilots present - quality set to 0")
        return (0, 0, 0, 0)

    stopv = 1
    if task.stopped_time:
        stopv   = stopped_validity(task, formula)

    launch      = launch_validity(taskt, formula)
    distance    = distance_validity(taskt, formula)
    time        = time_validity(taskt, formula)

    return distance, time, launch, stopv

def ordered_results(task, formula, results):

    taskt = task.stats

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
        t = db.fetchall(query, [task.tasPk])

    for res in t:

        taskres = {}

        taskres['tarPk'] = res['tarPk']
        taskres['traPk'] = res['traPk']
        taskres['penalty'] = res['tarPenalty']
        taskres['distance'] = res['tarDistance']
        taskres['stopalt'] = res['tarLastAltitude']

        # Handle Stopped Task
        if task.stopped_time and taskres['stopalt'] > 0 and formula['glidebonus'] > 0:
            if taskres['stopalt'] > task.goalalt:
                print("Stopped height bonus: ", (formula['glidebonus'] * taskres['stopalt']))
                taskres['distance'] = taskres['distance'] + formula['glidebonus'] * (taskres['stopalt'] - task.goalalt)
                if taskres['distance'] > task.SSDistance:
                    taskres['distance'] = task.SSDistance

        # set pilot to min distance if they're below that ..
        if taskres['distance'] < formula['forMinDistance']:
            taskres['distance'] = formula['forMinDistance']

        taskres['result']       = res['tarResultType']
        taskres['startSS']      = res['tarSS']
        taskres['start']        = res['tarStart']
        taskres['endSS']        = res['tarES']
        taskres['timeafter']    = (res['tarES'] - taskt['minarr']) if res['tarES'] else None
        taskres['place']        = res['Place']
        taskres['time']         = (taskres['endSS'] - taskres['startSS']) if taskres['endSS'] else 0
        taskres['goal']         = res['tarGoal']
        taskres['last_time']    = res['tarLastTime']
        taskres['fixed_LC']     = res['tarLeadingCoeff2']

        if taskres['time'] < 0:
            taskres['time'] = 0

        '''
        Leadout Points Adjustment
        C.6.3.1
        '''
        #if taskres['result'] not in ('abs', 'dnf', 'mindist') and taskres['startSS']:
        taskres['LC'] = lc_calc(taskres, task) # PWC LeadCoeff (with squared distances)
        # else:
        #     taskres['LC'] = 0

        pilots.append(taskres)

    return pilots

def points_allocation(task, formula, results = None):   # from PWC###

    taskt   = task.stats
    tasPk   = task.tasPk
    quality = taskt['quality']
    Ngoal   = taskt['goal']
    Tmin    = taskt['fastest']
    Tfarr   = taskt['minarr']

    sorted_pilots = ordered_results(task, formula, results)

    '''
    Update Min LC
    in ordered_results we calculate final LC
    so we need to update LCmin for the task
    '''
    task.stats['LCmin'] = min(res['LC'] for res in sorted_pilots if res['result'] not in ('dnf', 'abs', 'mindist'))

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

    task.stats['distp']     = Adistance
    task.stats['timep']     = Aspeed
    task.stats['depp']      = Astart
    task.stats['arrp']      = Aarrival
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
            Pspeed = Pspeed * (1 - formula['forGoalSSpenalty'])
            Parrival = Parrival * (1 - formula['forGoalSSpenalty'])

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
