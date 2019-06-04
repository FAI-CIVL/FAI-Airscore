from collections import namedtuple
from formulas.gap import  task_totals, day_quality, points_weight, pilot_distance, pilot_speed, pilot_departure_leadout
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

def lc_calc(res, t):
    leading     = 0
    trailing    = 0
    my_start    = res['start']
    first_start = t.stats['firstdepart']
    ss_start    = t.start_time
    SS_Distance = t.SSDistance
    '''add the leading part, from start time of first pilot to start, to my start time'''
    if not my_start:
        my_start = 0  # this is to avoid my_start being none if pilot didn't make start and causing error below
    if my_start > first_start:
        leading = parameters.coef_landout((my_start - first_start), SS_Distance)
        leading = parameters.coef_func_scaled(leading, SS_Distance)
    if not res['endSS']:
        '''pilot did not make ESS'''
        best_dist_to_ess    = (t.EndSSDistance - res['distance'])
        my_last_time        = res['last_time']          # should not need to check if < task deadline as we stop in Flight_result.check_flight()
        last_ess            = t.stats['lastarrival']
        task_time           = (max(my_last_time,last_ess) - my_start)
        trailing            = parameters.coef_landout(task_time, best_dist_to_ess)
        trailing            = parameters.coef_func_scaled(trailing, SS_Distance)

    return leading + res['Lead_coeff'] + trailing

def ordered_results(task, taskt, formula, results):

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
        taskres['timeafter']    = res['tarES'] - taskt['firstarrival']
        taskres['place']        = res['Place']
        taskres['time']         = taskres['endSS'] - taskres['startSS']
        taskres['goal']         = res['tarGoal']
        taskres['last_time']    = res['tarLastTime']
        taskres['Lead_coeff']   = res['tarLeadingCoeff2']

        if taskres['time'] < 0:
            taskres['time'] = 0

        '''
        Leadout Points Adjustment
        C.6.3.1
        '''
        taskres['coeff'] = lc_calc(taskres, task) # PWC LeadCoeff (with squared distances)
        # # FIX: adjust against fastest ..
        # if ((res['tarES'] - res['tarSS']) < 1) and (res['tarSS'] > 0): # only pilots that started and didn't make ESS
        #     # Fix - busted if no one is in goal?
        #     #print(res['traPk'], " didn't make ess, adjusting leCof")
        #     if taskt['goal'] > 0:
        #         #print("goal > 0")
        #         maxtime = taskt['lastarrival']  # Time of the last in ESS
        #         if res['tarLastTime'] > task.end_time:
        #             maxtime = task.end_time  # If I was still flying after task deadline
        #
        #         elif res['tarLastTime'] > taskt['lastarrival']:
        #             maxtime = res['tarLastTime']  # If I was still flying after the last ESS time
        #
        #         # adjust for late starters
        #         print("No goal, adjust pilot coeff from: ", res['tarLeadingCoeff2'])
        #         BestDistToESS = task.EndSSDistance / 1000 - res['tarDistance'] / 1000  # PWC bestDistToESS in Km
        #         taskres['coeff'] = res['tarLeadingCoeff2'] - (task.end_time - maxtime) * BestDistToESS ** 2 / ( 1800 * (task.SSDistance / 1000) ** 2 )
        #
        #         print(" to: ", taskres['coeff'])
        #         print("(maxtime - sstart)   =      ", (maxtime - task.start_time))
        #         print("ref->{'tarLeadingCoeff2'] = ", res['tarLeadingCoeff2'])
        #         print("Result taskres{coeff}  =    ", taskres['coeff'])
        #         # adjust mincoeff?
        #         if taskres['coeff'] < taskt['mincoeff2']:
        #             taskt['mincoeff2'] = taskres['coeff']

        pilots.append(taskres)

    return pilots

def points_allocation(task, taskt, formula, results = None):   # from PWC###

    # Find fastest pilot into goal and calculate leading coefficients
    # for each track .. (GAP2002 only?)

    tasPk = task.tasPk
    quality = taskt['quality']
    Ngoal = taskt['goal']
    Tmin = taskt['fastest']
    Tfarr = taskt['firstarrival']

    sorted_pilots = ordered_results(task, taskt, formula, results)

    '''
    Update Min LC
    '''
    task.stats['mincoeff2'] = min(res['coeff'] for res in sorted_pilots)

    # Get basic GAP allocation values
    Adistance, Aspeed, Astart, Aarrival = points_weight(task, taskt, formula)

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
        penalty = pil['penalty']
        if not penalty:
            penalty= 0

        # Pilot distance score
        # FIX: should round pil->distance properly?
        # my pilrdist = round(pil->{'distance'}/100.0) * 100

        Pdist = pilot_distance(taskt, pil, Adistance)

        # Pilot speed score
        Pspeed = pilot_speed(formula, task, taskt, pil, Aspeed)

        # Pilot departure/leading points
        Pdepart = pilot_departure_leadout(task, taskt, pil, Astart)

        # Pilot arrival score    this is always off in pwc
        # Parrival = pilot_arrival(formula, task, taskt, pil, Aarrival)
        Parrival=0
        # Penalty for not making goal .
        if not pil['goal']:
            pil['goal'] = 0

        if pil['goal'] == 0:
            Pspeed = Pspeed - Pspeed * formula['forGoalSSpenalty']
            Parrival = Parrival - Parrival * formula['forGoalSSpenalty']

        # Sanity
        if pil['result'] == 'dnf' or pil['result'] == 'abs':
            Pdist = 0
            Pspeed = 0
            Parrival = 0
            Pdepart = 0

        # Penalties
        # penalty = self->pilot_penalty(formula, task, taskt, pil, Astart, Aspeed)

        # Total score
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

