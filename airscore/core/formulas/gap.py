"""
FAI GAP Formula Library

contains
    - All procedures to calculate and allocate points according to FAI GAP Formula

Use:    lib = Task.formula.get_lib()
        lib = Formula.get_lib()

Stuart Mackintosh - 2019

TO DO:
Add support for FAI Sphere ???
"""

from collections import namedtuple
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

def store_LC(res_id, lead_coeff):
    '''store LC to database'''
    from db_tables import tblTaskResult as R
    # It shouldn't be necessary any longer, as we should not store final LC

    with Database() as db:
        q = db.session.query(R)
        res = q.get(res_id)
        res.tarLeadingCoeff = lead_coeff
        db.session.commit()

parameters.allow_jump_the_gun = False
parameters.max_jump_the_gun = 0  # seconds
parameters.stopped_elapsed_calc = 'shortest_time'
parameters.coef_func = coef2
parameters.coef_func_scaled = coef_scaled
parameters.coef_landout = coef_landout

def lc_calc(res, t):
    LC          = 0
    leading     = 0
    trailing    = 0
    SS_distance = t.SS_distance
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
        my_start    = res['real_start_time']

        '''add the leading part, from start time of first pilot to start, to my start time'''
        if my_start > first_start:
            leading = parameters.coef_landout((my_start - first_start), SS_distance)
            leading = parameters.coef_func_scaled(leading, SS_distance)
        if not res['ES_time']:
            '''pilot did not make ESS'''
            best_dist_to_ess    = (t.opt_dist_to_ESS - res['distance'])
            # my_last_time        = res['last_time']          # should not need to check if < task deadline as we stop in Flight_result.check_flight()
            # last_ess            = t.stats['maxarr'] if t.stats['maxarr'] > 0 else min(t.task_deadline, t.stats['max_time'])
            # task_time           = (max(my_last_time,last_ess) - my_start)
            task_time           = task_deadline - my_start
            trailing            = parameters.coef_landout(task_time, best_dist_to_ess)
            trailing            = parameters.coef_func_scaled(trailing, SS_distance)

        LC = leading + res['fixed_LC'] + trailing

    else:
        '''pilot didn't make SS or has a assigned status without a track'''
        task_time         = task_deadline - first_start
        max_LC            = parameters.coef_landout(task_time, SS_distance)
        max_LC            = parameters.coef_func_scaled(max_LC, SS_distance)

        LC = max_LC

    print ("""Pilot: {} - Distance: {} - Time: {} - LC: {} \n""".format(res['track_id'], res['distance'], res['time'], LC))

    return LC

def task_totals(task_id):
    '''
    This new version uses a view to collect task totals.
    It means we do not need to store totals in task table anylonger,
    as they are calculated on runtime from mySQL using all task results
    '''
    from db_tables import TaskStatsView as T

    with Database() as db:
        # get the task stats details.
        q = db.session.query(T)
        stats = db.as_dict(q.get(task_id))

    if not stats:
        print(query)
        print('No rows in TaskTotalsView for task ', task_id)
        return

    return stats

def difficulty_calculation(task, pilots):
    from dataclasses import dataclass

    formula = task.formula
    stats   = task.stats

    @dataclass
    class Diffslot:
        dist:       int
        diff:       int   = 0
        rel_diff:   float = 0.0
        diff_score: float = 0.0

    '''distance spread'''
    min_dist_kmx10  = int(formula.min_dist/100)     # min_dist (Km) * 10
    distspread      = dict()
    best_dist       = 0
    best_dist_kmx10 = 0
    for p in pilots:
        if not p['goal_time'] and not p['result'] in ('abs', 'dnf'):
            dist = int(max(p['distance']/100, min_dist_kmx10))
            if dist in distspread.keys():
                distspread[dist] += 1
            else:
                distspread[dist] = 1
            if dist > best_dist_kmx10: best_dist_kmx10 = dist
            if p['distance']/1000 > best_dist: best_dist = p['distance']/1000

    # Sanity
    if best_dist == 0: return []

    pilot_lo    = stats['pilots_launched'] - stats['pilots_goal']

    ''' the difficulty for each 100-meter section of the task is calculated
        by counting the number of pilots who landed further along the task'''
    look_ahead  = max(30, round(30*best_dist/pilot_lo))
    kmdiff      = []

    for i in range(best_dist_kmx10+10):
        diff = sum([0 if x not in distspread.keys() else distspread[x]
                        for x in range(i, min(i+look_ahead, best_dist_kmx10))])
        kmdiff.append(Diffslot(i,diff))

    sum_diff = sum([x.diff for x in kmdiff])

    ''' Relative difficulty is then calculated by dividing each 100-meter slot’s
        difficulty by twice the sum of all difficulty values.'''
    # sum_rel_diff = 0
    sum_rel_diff = sum([(0.5 * x.diff / sum_diff) for x in kmdiff if x.dist <= min_dist_kmx10])
    for i, el in enumerate(kmdiff):
        el.rel_diff = 0.5 * el.diff / sum_diff
        if el.dist > min_dist_kmx10:
            sum_rel_diff += el.rel_diff
        el.diff_score = sum_rel_diff if el.dist < best_dist_kmx10 else 0.5

    return kmdiff

def launch_validity(stats, formula):
    '''
    9.1 Launch Validity
    ‘Pilots Present’ are pilots arriving on take-off, with their gear, with the intention of flying.
    For scoring purposes, ‘Pilots Present’ are all pilots not in the ‘Absent’ status (ABS):
    Pilots who took off, plus pilots present who did not fly (DNF). DNFs need to be attributed carefully.
    A pilot who does not launch due to illness, for instance, is not a DNF, but an ABS.

    LVR = min (1, num_pilots_flying / (pilots_present * nom_launch) )
    Launch Validity = 0.027*LRV + 2.917*LVR^2 - 1.944*LVR^3
    ?? Setting Nominal Launch = 10 (max number of DNF that still permit full validity) ??
    '''

    if stats['pilots_present'] == 0 or formula.nominal_launch == 0:
        '''avoid div by zero'''
        return 0

    LVR = min(1, (stats['pilots_launched']) / (stats['pilots_present'] * formula.nominal_launch))
    launch = 0.027 * LVR + 2.917 * LVR**2 - 1.944 * LVR**3
    launch = min(launch, 1) if launch > 0 else 0           #sanity
    print("GAP Launch validity = launch")

    return launch

def distance_validity(stats, formula):
    '''
    9.2 Distance Validity
    NomDistArea = ( ((NomGoal + 1) * (NomDist − MinDist)) + max(0, (NomGoal * BestDistOverNom)) ) / 2
    DVR = SumOfFlownDistancesOverMinDist / (NumPilotsFlying * NomDistArea)
    Dist. Validity = min (1, DVR)
    '''

    nomgoal         = formula.nominal_goal                  # nom goal percentage
    nomdist         = formula.nominal_dist                  # nom distance
    mindist         = formula.min_dist                      # min distance
    totalflown      = stats['tot_dist_over_min']            # total distance flown by pilots over min. distance
    BestDistOverNom = stats['max_distance'] - nomdist       # best distance flown ove minimum dist.
    # bestdistovermin = stats['max_distance'] - mindist     # best distance flown ove minimum dist.
    NumPilotsFlying = stats['pilots_launched']              # Num Pilots flown

    if not(NumPilotsFlying > 0):                            # sanity
        return 0

    NomDistArea     = ( ((nomgoal + 1)*(nomdist - mindist)) + max(0, (nomgoal * BestDistOverNom)) ) / 2
    DVR             = totalflown / (NumPilotsFlying * NomDistArea)

    print("Nom. Goal: {}% | Min. Distance: {} Km | Nom. Distance: {} Km".format(nomgoal*100, mindist/1000, nomdist/1000))
    print("Total Flown Distance over min. dist.: {} Km".format(totalflown/1000))
    print("Pilots launched: {} | Best Distance over Nom.: {} Km".format(NumPilotsFlying, BestDistOverNom/1000))
    print("NomDistArea: {}".format(NomDistArea))
    print('DVR = {}'.format(DVR))

    distance        = min(1.000, DVR)

    print("Distance validity = {}".format(distance))
    return distance

def time_validity(stats, formula):
    '''
    9.3 Time Validity
    Time validity depends on the fastest time to complete the speed section, in relation to nominal time.
    If the fastest time to complete the speed section is longer than nominal time, then time validity is always equal to 1.
    If no pilot finishes the speed section, then time validity is not based on time but on distance:

    If one pilot reached ESS: TVR = min(1, BestTime / NominalTime)
    If no pilot reached ESS: TVR = min(1, BestDistance / NominalDistance)

    TimeVal = max(0, min(1, -0.271 + 2.912*TVR - 2.098*TVR^2 + 0.457*TVR^3))
    '''

    if stats['pilots_ess'] > 0:
        TVR = min(1, (stats['fastest'] / formula.nominal_time))
        print("ess > 0, TVR = {}".format(TVR))
    else:
        TVR = min(1, (stats['max_distance'] / formula.nominal_dist))
        print("none in goal, TVR = {}".format(TVR))

    time = max(0, min(1.000, (-0.271 + 2.912 * TVR - 2.098 * TVR**2 + 0.457 * TVR**3)))

    print("Time validity = {}".format(time))
    return time

def stopped_validity(task):
    '''
    12.3.3 Stopped Task Validity
    NumberOfPilotsReachedESS > 0 : StoppedTaskValidity = 1
    NumberOfPilotsReachedESS = 0 :
    StoppedTaskValidity = min(1, sqrt((bestDistFlown - avgDistFlown)/(TaskDistToESS-bestDistFlown+1)*sqrt(stDevDistFlown/5))+(pilotsLandedBeforeStop/pilotsLaunched)^3)

    For this formula we need to use Km as there are numeric constants
    '''
    from math import sqrt

    stats   = task.stats
    formula = task.formula

    if stats['fastest'] and stats['fastest'] > 0:
        return 1.000

    avgdist         = stats['tot_dist_flown'] / stats['pilots_launched'] / 1000     # avg distance in Km
    distlaunchtoess = task.opt_dist_to_ESS / 1000                                   # TaskDistToESS in Km
    max_distance    = stats['max_distance'] / 1000                                  # bestDistFlown in Km
    std_dev         = stats['std_dev'] / 1000                                       # stDevDistFlown in Km

    if stats['pilots_launched'] == 0:
        '''avoid div by zero'''
        return 0

    stopv = min(1.000,
                (sqrt((max_distance - avgdist) / (distlaunchtoess - max_distance + 1) * sqrt(std_dev / 5) )
                + (stats['pilots_landed'] / stats['pilots_launched'])**3))
    return stopv

def day_quality(task):

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

    LeadWeight:
            HG:         (1 - DistWeight)/8 * 1.4
            PG:
                GoalRatio > 0:
                        (1 - DistWeight)/8 * 1.4 * 2
                GoalRatio = 0:
                        (BestDist / TaskDist) * 0.1

    ArrWeight:
            HG:         (1 - DistWeight)/8
            PG:         0

    TimeWeight:         1 − DistWeight − LeadWeight − ArrWeight
    '''

    dist_weight = 0.9 - 1.665 * goal_ratio + 1.713 * goal_ratio**2 - 0.587 * goal_ratio**3

    if comp_class == 'HG':
        lead_weight  = (1 - dist_weight) / 8 * 1.4
        arr_weight   = (1 - dist_weight) / 8
        if task.arrival=='time':
            arr_weight *= 2         # (1 - dist_weight) / 4

    else:
        arr_weight   = 0
        if goal_ratio > 0:
            lead_weight = (1 - dist_weight) / 8 * 1.4 * 2
        else:
            lead_weight = stats['max_distance'] / task.opt_dist * 0.1

    time_weight = 1 - dist_weight - lead_weight - arr_weight

    Adistance   = 1000 * quality * dist_weight            # AvailDistPoints
    Astart      = 1000 * quality * lead_weight            # AvailLeadPoints
    Aarrival    = 1000 * quality * arr_weight             # AvailArrPoints
    Aspeed      = 1000 * quality * time_weight            # AvailSpeedPoints

    return Adistance, Aspeed, Astart, Aarrival

def pilot_leadout(task, pil):
    from math import sqrt

    stats   = task.stats
    Astart  = stats['avail_dep_points']

    # C.6.3 Leading Points

    LCmin   = stats['min_lead_coeff']   # min(tarFixedLC) as LCmin : is PWC's LCmin?
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
                print("LeadFactor = ", LF)
                if LF > 0:
                    Pdepart = Astart * LF
                    print("=======  Normal Pdepart   =========")

        print("======= PDepart = {}  =========".format(Pdepart))

    # Sanity
    if 0 + Pdepart != Pdepart:
        Pdepart = 0
    if Pdepart < 0:
        Pdepart = 0

    print("    Pdepart: ", Pdepart)
    return Pdepart

def pilot_departure(task, pil):
    ''' I don't think this part is still in use '''

    stats   = task.stats
    Astart  = stats['avail_dep_points']
    Aspeed  = stats['avail_time_points']

    # Pilot departure score
    Pdepart = 0
    '''Departure Points type = Departure'''
    if task.departure == 'departure':
        DF = (pil['real_start_time'] - stats['min_dept_time']) / task.formula.nominal_time
        if DF < 1/2:
            Pdepart = pil['time_points']*Astart/Aspeed* (1 - 6.312*DF + 10.932*DF**2 - 2.99*DF**3)

    # Sanity
    if 0 + Pdepart != Pdepart:
        Pdepart = 0
    if Pdepart < 0:
        Pdepart = 0

    print("    Pdepart: ", Pdepart)
    return Pdepart

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
        SF = 1 - ((Ptime-Tmin) / 3600 / sqrt(Tmin / 3600) )**(2/3)

        if SF > 0:
            Pspeed = Aspeed * SF


    print(pil['track_id'], " Ptime: {}, Tmin={}".format(Ptime, Tmin))

    return Pspeed

def pilot_arrival(task, pil):
    ''' 11.4 Arrival points
        Arrival points depend on the position at which a pilot crosses ESS:
        The first pilot completing the speed section receives the maximum
        available arrival points, while the others are awarded arrival points
        according to the number of pilots who reached ESS before them.
        The last pilot to reach ESS will always receive at least 20%
        of the available arrival points.
        ACp = 1 − (PositionAtESSp − 1) / NumberOfPilotsReachingESS
        AFp = 0.2 + 0.037*ACp + 0.13*ACp**2 + 0.633*ACp**3
    '''
    from math import sqrt

    stats       = task.stats
    Aarrival    = stats['avail_arr_points']

    if task.arrival == 'position':
        '''FAI position arrival points'''
        AC = 1 - (pil['ES_rank'] - 1) / stats['pilots_ess']
    elif task.arrival == 'time':
        '''OZGAP time arrival points'''
        time_after = pil['time_after']/3600     # hours decimals
        AC = 1 - 0.667*time_after

    AF = 0.2 + 0.037*AC + 0.13*AC**2 + 0.633*AC**3
    Parrival = AF * Aarrival

    print(pil['track_id'], f" Parrival: {Parrival}")

    return Parrival

def pilot_distance(task, pil):
    """
    :type pil: object
    """

    maxdist     = task.stats['max_distance']
    Adistance   = task.stats['avail_dist_points']

    if pil['goal_time']:
        return Adistance

    if task.comp_class == 'PG':
        Pdist   = Adistance * pil['distance'] / maxdist
    elif task.comp_class == 'HG':
        ''' One half of the available distance points are assigned to each pilot
            linearly, based on the pilot’s distance flown in relation to the best
            distance flown in the task.
            The other half is assigned taking into consideration the difficulty
            of the kilometers flown.'''
        diff    = task.stats['difficulty']
        LF      = 0.5 * pil['distance'] / maxdist
        dist10  = int(pil['distance']/100)          # int(dist in Km * 10)
        DF      = diff[dist10].diff_score + ((diff[dist10+1].diff_score - diff[dist10].diff_score)
                                                * (pil['distance']/100 - dist10))
        Pdist   = Adistance * (LF + DF)

    return Pdist

def get_results(task):
    from db_tables import TaskResultView as R

    stats   = task.stats
    formula = task.formula

    with Database() as db:
        q = db.session.query(R).filter(R.task_id==task.id).all()
        pilots = db.as_dict(q)

    for res in pilots:
        '''manage ABS pilots'''
        if not (res['result'] == 'abs'):
            # Handle Stopped Task
            if task.stopped_time and res['last_altitude'] > task.goal_altitude and formula.glide_bonus > 0:
                print("Stopped height bonus: ", (formula.glide_bonus * (res['last_altitude'] - task.goal_altitude)))
                res['distance'] = min( (res['distance'] + formula.glide_bonus * (res['last_altitude'] - task.goal_altitude)), task.SS_distance )
            # set pilot to min distance if they're below that ..
            res['distance'] = max(formula.min_dist, res['distance'])

            res['time_after']   = (res['ES_time'] - stats['min_ess_time']) if res['ES_time'] else None
            res['time']         = (res['ES_time'] - res['SS_time']) if res['ES_time'] else 0

            #sanity
            res['time'] = max(res['time'], 0)
        else:
            res['time']         = None
            res['time_after']   = None

        '''
        Leadout Points Adjustment
        C.6.3.1
        '''
        res['lead_coeff'] = lc_calc(res, task) # PWC LeadCoeff (with squared distances)

    return pilots

def points_allocation(task):   # from PWC###

    pilots = get_results(task)

    if task.departure == 'leadout':
        '''
        Update Min LC
        in ordered_results we calculate final LC
        so we need to update LCmin for the task
        '''
        task.stats['min_lead_coeff'] = min(res['lead_coeff'] for res in pilots if res['result'] not in ('dnf', 'abs', 'mindist'))

    if task.comp_class == 'HG':
        '''Difficulty Calculation'''
        task.stats['difficulty'] = difficulty_calculation(task, pilots)

    # Get basic GAP allocation values
    Adistance, Aspeed, Astart, Aarrival = points_weight(task)

    task.stats['avail_dist_points'] = Adistance
    task.stats['avail_time_points'] = Aspeed
    task.stats['avail_dep_points']  = Astart
    task.stats['avail_arr_points']  = Aarrival
    task.stats['max_score']         = 0

    # Score each pilot now
    for pil in pilots:
        tarPk   = pil['track_id']
        penalty = pil['penalty'] if pil['penalty'] else 0

        '''initialize'''
        pil['dist_points']  = 0
        pil['time_points']  = 0
        pil['arr_points']   = 0
        pil['dep_points']   = 0

        if not (pil['result'] in ('dnf', 'abs')):
            # Pilot distance score
            # FIX: should round pil->distance properly?
            # my pilrdist = round(pil->{'distance'}/100.0) * 100
            pil['dist_points']  = pilot_distance(task, pil)

            # Pilot departure/leading points
            if task.departure == 'leadout' and pil['result'] != 'mindist' and pil['SS_time']:
                pil['dep_points'] = pilot_leadout(task, pil)

            if pil['ES_time'] > 0:
                # Pilot speed score
                pil['time_points'] = pilot_speed(task, pil)

                if task.departure == 'departure':
                    '''does it even still exist dep. points?'''
                    pil['dep_points'] = pilot_departure(task, pil) if (pil['result'] != 'mindist' and pil['SS_time']) else 0

                # Pilot arrival score
                if not (task.arrival == 'off'):
                    pil['arr_points'] = pilot_arrival(task, pil)

                # Penalty for not making goal
                if not pil['goal_time']:
                    pil['goal_time']    = 0
                    pil['time_points']  = pil['time_points'] * (1 - task.formula.no_goal_penalty)
                    pil['arr_points']   = pil['arr_points'] * (1 - task.formula.no_goal_penalty)

        # Total score
        pil['score'] = pil['dist_points'] + pil['time_points'] + pil['arr_points'] + pil['dep_points']

        print('{} + {} + {} + {} - {}'.format(pil['dist_points'],pil['time_points'],pil['arr_points'],pil['dep_points'],penalty))

        #update task max score
        if pil['score'] > task.stats['max_score']: task.stats['max_score'] = pil['score']

        #apply Penalty
        if penalty:
            pil['score'] = max(0, pil['score'] - penalty)

    return pilots
