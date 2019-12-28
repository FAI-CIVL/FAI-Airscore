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
from myconn import Database


def coef_func(task_time, best_dist_to_ess, new_dist_to_ess):
    best_dist_to_ess = best_dist_to_ess / 1000  # we use Km
    new_dist_to_ess = new_dist_to_ess / 1000  # we use Km
    return task_time * (best_dist_to_ess ** 2 - new_dist_to_ess ** 2)


def coef_scaled(coeff, essdist):
    essdist = essdist / 1000  # we use Km
    return coeff / (1800 * (essdist ** 2))


def coef_landout(total_time_to_end, new_dist_to_ess):
    new_dist_to_ess = new_dist_to_ess / 1000  # we use Km
    return new_dist_to_ess ** 2 * total_time_to_end


def store_LC(res_id, lead_coeff):
    """store LC to database"""
    from db_tables import tblTaskResult as R
    # It shouldn't be necessary any longer, as we should not store final LC

    with Database() as db:
        q = db.session.query(R)
        res = q.get(res_id)
        res.tarLeadingCoeff = lead_coeff
        db.session.commit()


def lc_calc(res, t):
    LC = 0
    leading = 0
    trailing = 0
    SS_distance = t.SS_distance
    first_start = t.min_dept_time

    '''find task_deadline to use for LC calculation'''
    task_deadline = min((t.task_deadline if not t.stopped_time else t.stopped_time), t.max_time)
    if t.max_ess_time and res.last_time:
        if res.last_time < t.max_ess_time:
            task_deadline = t.max_ess_time
        else:
            task_deadline = min(res.last_time, task_deadline)

    '''Checking if we have a assigned status without a track, and if pilot actually did the start pilon'''
    if (res.result_type not in ('abs', 'dnf', 'mindist')) and res.SSS_time:
        my_start = res.real_start_time

        '''add the leading part, from start time of first pilot to start, to my start time'''
        if my_start > first_start:
            leading = coef_landout((my_start - first_start), SS_distance)
            leading = coef_scaled(leading, SS_distance)
        if not res.ESS_time:
            '''pilot did not make ESS'''
            best_dist_to_ess = (t.opt_dist_to_ESS - res.distance)
            task_time = task_deadline - my_start
            trailing = coef_landout(task_time, best_dist_to_ess)
            trailing = coef_scaled(trailing, SS_distance)

        LC = leading + res.fixed_LC + trailing

    else:
        '''pilot didn't make SS or has an assigned status without a track'''
        task_time = task_deadline - first_start
        LC = coef_landout(task_time, SS_distance)
        LC = coef_scaled(LC, SS_distance)

    return LC


def difficulty_calculation(task):
    from dataclasses import dataclass

    formula = task.formula
    results = task.valid_results

    @dataclass
    class Diffslot:
        dist: int
        diff: int = 0
        rel_diff: float = 0.0
        diff_score: float = 0.0

    '''distance spread'''
    min_dist_kmx10 = int(formula.min_dist / 100)  # min_dist (Km) * 10
    distspread = dict()
    best_dist = 0
    best_dist_kmx10 = 0
    for p in results:
        if not p.goal_time:
            dist = int(max(p.distance / 100, min_dist_kmx10))
            if dist in distspread.keys():
                distspread[dist] += 1
            else:
                distspread[dist] = 1
            if dist > best_dist_kmx10:
                best_dist_kmx10 = dist
            if p.distance / 1000 > best_dist:
                best_dist = p.distance / 1000

    # Sanity
    if best_dist == 0:
        return []

    pilot_lo = task.pilots_launched - task.pilots_goal

    ''' the difficulty for each 100-meter section of the task is calculated
        by counting the number of pilots who landed further along the task'''
    look_ahead = max(30, round(30 * best_dist / pilot_lo))
    kmdiff = []

    for i in range(best_dist_kmx10 + 10):
        diff = sum([0 if x not in distspread.keys() else distspread[x]
                    for x in range(i, min(i + look_ahead, best_dist_kmx10))])
        kmdiff.append(Diffslot(i, diff))

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


def launch_validity(task):
    """
    9.1 Launch Validity
    ‘Pilots Present’ are pilots arriving on take-off, with their gear, with the intention of flying.
    For scoring purposes, ‘Pilots Present’ are all pilots not in the ‘Absent’ status (ABS):
    Pilots who took off, plus pilots present who did not fly (DNF). DNFs need to be attributed carefully.
    A pilot who does not launch due to illness, for instance, is not a DNF, but an ABS.

    LVR = min (1, num_pilots_flying / (pilots_present * nom_launch) )
    Launch Validity = 0.027*LRV + 2.917*LVR^2 - 1.944*LVR^3
    ?? Setting Nominal Launch = 10 (max number of DNF that still permit full validity) ??
    """
    if task.pilots_present == 0 or task.formula.nominal_launch == 0:
        '''avoid div by zero'''
        return 0

    LVR = min(1, (task.pilots_launched) / (task.pilots_present * task.formula.nominal_launch))
    launch = 0.027 * LVR + 2.917 * LVR ** 2 - 1.944 * LVR ** 3
    launch = min(launch, 1) if launch > 0 else 0  # sanity
    return launch


def distance_validity(task):
    """
    9.2 Distance Validity
    NomDistArea = ( ((NomGoal + 1) * (NomDist − MinDist)) + max(0, (NomGoal * BestDistOverNom)) ) / 2
    DVR = SumOfFlownDistancesOverMinDist / (NumPilotsFlying * NomDistArea)
    Dist. Validity = min (1, DVR)
    """
    nomgoal = task.formula.nominal_goal  # nom goal percentage
    nomdist = task.formula.nominal_dist  # nom distance
    mindist = task.formula.min_dist  # min distance
    totalflown = task.tot_dist_over_min  # total distance flown by pilots over min. distance
    BestDistOverNom = task.max_distance - nomdist  # best distance flown ove minimum dist.
    # bestdistovermin = stats['max_distance'] - mindist     # best distance flown ove minimum dist.
    NumPilotsFlying = task.pilots_launched  # Num Pilots flown

    if not (NumPilotsFlying > 0):  # sanity
        return 0

    NomDistArea = (((nomgoal + 1) * (nomdist - mindist)) + max(0, (nomgoal * BestDistOverNom))) / 2
    DVR = totalflown / (NumPilotsFlying * NomDistArea)

    return min(1.000, DVR)


def time_validity(task):
    """
    9.3 Time Validity
    Time validity depends on the fastest time to complete the speed section, in relation to nominal time.
    If the fastest time to complete the speed section is longer than nominal time, then time validity is always equal to 1.
    If no pilot finishes the speed section, then time validity is not based on time but on distance:

    If one pilot reached ESS: TVR = min(1, BestTime / NominalTime)
    If no pilot reached ESS: TVR = min(1, BestDistance / NominalDistance)

    TimeVal = max(0, min(1, -0.271 + 2.912*TVR - 2.098*TVR^2 + 0.457*TVR^3))
    """
    if task.pilots_ess > 0:
        TVR = min(1, (task.fastest / task.formula.nominal_time))
    else:
        TVR = min(1, (task.max_distance / task.formula.nominal_dist))

    time = max(0, min(1.000, -0.271 + 2.912 * TVR - 2.098 * TVR ** 2 + 0.457 * TVR ** 3))

    return time


def stopped_validity(task):
    """
    12.3.3 Stopped Task Validity
    NumberOfPilotsReachedESS > 0 : StoppedTaskValidity = 1
    NumberOfPilotsReachedESS = 0 :
    StoppedTaskValidity = min(1, sqrt((bestDistFlown - avgDistFlown)/(TaskDistToESS-bestDistFlown+1)*sqrt(stDevDistFlown/5))+(pilotsLandedBeforeStop/pilotsLaunched)^3)

    For this formula we need to use Km as there are numeric constants
    """
    from math import sqrt

    if task.fastest and task.fastest > 0:
        return 1.000

    if task.pilots_launched == 0:
        '''avoid div by zero'''
        return 0

    avgdist = task.tot_dist_flown / task.pilots_launched / 1000  # avg distance in Km
    distlaunchtoess = task.opt_dist_to_ESS / 1000  # TaskDistToESS in Km
    max_distance = task.max_distance / 1000  # bestDistFlown in Km
    std_dev = task.std_dev_dist / 1000  # stDevDistFlown in Km

    stopv = min(1.000,
                (sqrt((max_distance - avgdist) / (distlaunchtoess - max_distance + 1) * sqrt(std_dev / 5))
                 + (task.pilots_landed / task.pilots_launched) ** 3))
    return stopv


def day_quality(task):
    task.dist_validity = 0.000
    task.time_validity = 0.000
    task.launch_validity = 0.000
    task.stop_validity = 1.000
    task.day_quality = 0.000

    if not task.launch_valid:
        print("Launch invalid - dist quality set to 0")
        return None

    if task.pilots_present == 0:
        print("No pilots results - quality set to 0")
        return None

    if task.stopped_time:
        task.stop_validity = stopped_validity(task)

    task.launch_validity = launch_validity(task)
    task.dist_validity = distance_validity(task)
    task.time_validity = time_validity(task)
    task.day_quality = min(
        (task.stop_validity * task.launch_validity * task.dist_validity * task.time_validity), 1.000)


def points_weight(task):
    comp_class = task.comp_class  # HG / PG
    formula = task.formula
    quality = task.day_quality

    if not task.pilots_launched:  # sanity
        return 0, 0, 0, 0

    '''Goal Ratio'''
    goal_ratio = task.pilots_goal / task.pilots_launched

    '''
    DistWeight:         0.9 - 1.665* goalRatio + 1.713*GolalRatio^2 - 0.587*goalRatio^3

    LeadWeight:
            HG:         (1 - DistWeight)/8 * 1.4 (lead_factor = 1)
            PG:
                GoalRatio > 0:
                        (1 - DistWeight)/8 * 1.4 * 2 (lead_factor = 2)
                GoalRatio = 0:
                        (BestDist / TaskDist) * 0.1

    ArrWeight:
            HG:         (1 - DistWeight)/8
            PG:         0

    TimeWeight:         1 − DistWeight − LeadWeight − ArrWeight
    '''

    ''' Distance Weight'''
    if task.formula.formula_distance != 'off':
        task.dist_weight = 0.9 - 1.665 * goal_ratio + 1.713 * goal_ratio ** 2 - 0.587 * goal_ratio ** 3
    else:
        task.dist_weight = 0

    ''' Arrival Weight'''
    if task.formula.formula_arrival != 'off':
        task.arr_weight = (1 - task.dist_weight) / 8
        if task.formula.formula_arrival == 'time':
            task.arr_weight *= 2  # (1 - dist_weight) / 4
    else:
        task.arr_weight = 0

    ''' Departure Weight'''
    if task.formula.formula_departure != 'off':
        task.dep_weight = (1 - task.dist_weight) / 8 * 1.4 * formula.lead_factor
        if comp_class == 'PG' and goal_ratio == 0:
            task.dep_weight = task.max_distance / task.opt_dist * 0.1
    else:
        task.dep_weight = 0

    ''' Time weight'''
    task.time_weight = 1 - task.dist_weight - task.dep_weight - task.arr_weight

    ''' Available Points'''
    task.avail_dist_points = 1000 * quality * task.dist_weight  # AvailDistPoints
    task.avail_dep_points = 1000 * quality * task.dep_weight  # AvailLeadPoints
    task.avail_arr_points = 1000 * quality * task.arr_weight  # AvailArrPoints
    task.avail_time_points = 1000 * quality * task.time_weight  # AvailTimePoints


def pilot_leadout(task, res):
    """
    Args:
        task: Task obj.
        res: Flight_result object
    """
    from math import sqrt

    Astart = task.avail_dep_points

    # C.6.3 Leading Points

    LCmin = task.min_lead_coeff
    LCp = res.lead_coeff

    # Pilot departure score
    Pdepart = 0
    '''Departure Points type = Leading Points'''
    if task.departure == 'leadout':  # In PWC is always the case, we can ignore else cases
        if LCp > 0:
            if LCp <= LCmin:
                Pdepart = Astart
            elif LCmin <= 0:  # this shouldn't happen
                Pdepart = 0
            else:  # We should have ONLY this case
                # LeadingFactor = max (0, 1 - ( (LCp -LCmin) / sqrt(LCmin) )^(2/3))
                # LeadingPoints = LeadingFactor * AvailLeadPoints
                LF = 1 - ((LCp - LCmin) / sqrt(LCmin)) ** (2 / 3)

                if LF > 0:
                    Pdepart = Astart * LF
    # Sanity
    if 0 + Pdepart != Pdepart:
        Pdepart = 0
    if Pdepart < 0:
        Pdepart = 0
    return Pdepart


def pilot_departure(task, res):
    """
    Args:
        task: Task obj.
        res: Flight_result object
    """

    Astart = task.avail_dep_points
    Aspeed = task.avail_time_points

    # Pilot departure score
    Pdepart = 0
    '''Departure Points type = Departure'''
    if task.departure == 'departure':
        DF = (res.real_start_time - task.min_dept_time) / task.formula.nominal_time
        if DF < 1 / 2:
            Pdepart = res.time_points * Astart / Aspeed * (1 - 6.312 * DF + 10.932 * DF ** 2 - 2.99 * DF ** 3)

    # Sanity
    if 0 + Pdepart != Pdepart:
        Pdepart = 0
    if Pdepart < 0:
        Pdepart = 0

    return Pdepart


def pilot_speed(task, res):
    """
    Args:
        task: Task obj.
        res: Flight_result object
    """
    from math import sqrt

    Aspeed = task.avail_time_points

    # C.6.2 Time Points
    Tmin = task.fastest
    Pspeed = 0
    Ptime = 0

    if res.ESS_time and Tmin > 0:  # checking that task has pilots in ESS, and that pilot is in ESS
        # we need to change this! It works correctly only if Time Pts is 0 when pil not in goal
        # for HG we need a fastest and a fastest in goal in TaskStatsView
        Ptime = res.time
        SF = 1 - ((Ptime - Tmin) / 3600 / sqrt(Tmin / 3600)) ** (2 / 3)

        if SF > 0:
            Pspeed = Aspeed * SF

    return Pspeed


def pilot_arrival(task, res):
    """ 11.4 Arrival points
        Arrival points depend on the position at which a pilot crosses ESS:
        The first pilot completing the speed section receives the maximum
        available arrival points, while the others are awarded arrival points
        according to the number of pilots who reached ESS before them.
        The last pilot to reach ESS will always receive at least 20%
        of the available arrival points.
        ACp = 1 − (PositionAtESSp − 1) / NumberOfPilotsReachingESS
        AFp = 0.2 + 0.037*ACp + 0.13*ACp**2 + 0.633*ACp**3
    """

    Aarrival = task.avail_arr_points

    if not res.ESS_time:
        return 0

    if task.arrival == 'position':
        '''FAI position arrival points'''
        # TODO ESS_rank
        AC = 1 - (res.ESS_rank - 1) / task.pilots_ess
    elif task.arrival == 'time':
        '''OZGAP time arrival points'''
        time_after = res.time_after / 3600  # hours decimals
        AC = 1 - 0.667 * time_after

    AF = 0.2 + 0.037 * AC + 0.13 * AC ** 2 + 0.633 * AC ** 3
    Parrival = AF * Aarrival

    return Parrival


def pilot_distance(task, pil):
    """
    Args:
        task: Task obj.
        pil: Flight_result object
    """

    maxdist = task.max_distance
    Adistance = task.avail_dist_points

    if pil.goal_time:
        return Adistance

    if task.formula.formula_distance == 'on':
        # PG Default
        Pdist = Adistance * pil.distance / maxdist

    elif task.formula.formula_distance == 'difficulty':
        # HG Default
        ''' One half of the available distance points are assigned to each pilot
            linearly, based on the pilot’s distance flown in relation to the best
            distance flown in the task.
            The other half is assigned taking into consideration the difficulty
            of the kilometers flown.'''
        diff = task.difficulty
        LF = 0.5 * pil.distance / maxdist
        dist10 = int(pil.distance / 100)  # int(dist in Km * 10)
        DF = diff[dist10].diff_score + ((diff[dist10 + 1].diff_score - diff[dist10].diff_score)
                                        * (pil.distance / 100 - dist10))
        Pdist = Adistance * (LF + DF)

    return Pdist


def process_results(task):
    formula = task.formula
    ''' get pilot.result non ABS or DNF, ordered by ESS time'''
    results = sorted(task.valid_results, key=lambda i: (float('inf') if not i.ESS_time else i.ESS_time))
    if len(results) == 0:
        return None

    for idx, res in enumerate(results, 1):
        '''Handle Stopped Task'''
        if task.stopped_time and res.last_altitude > task.goal_altitude and formula.glide_bonus > 0:
            print("Stopped height bonus: ", (formula.glide_bonus * (res.last_altitude - task.goal_altitude)))
            res.total_distance = min((res.distance_flown +
                                      formula.glide_bonus * (res.last_altitude - task.goal_altitude)),
                                     task.SS_distance)
        else:
            res.total_distance = res.distance_flown
        # set pilot to min distance if they're below that ..
        res.total_distance = max(formula.min_dist, res.total_distance)

        if res.ESS_time:
            ''' Time after first on ESS'''
            res.time_after = res.ESS_time - task.min_ess_time
            ''' ESS arrival order'''
            res.ESS_rank = idx
        # print(f'ESS: {res.ESS_time} | rank: {res.ESS_rank}')

        '''
        Leadout Points Adjustment
        C.6.3.1
        '''
        if formula.departure == 'leadout':
            res.lead_coeff = lc_calc(res, task)  # PWC LeadCoeff (with squared distances)


def points_allocation(task):
    """ Get task with pilots Flight_result obj. and calculates results"""

    ''' Get pilot.result not ABS or DNF '''
    results = task.valid_results
    formula = task.formula

    ''' Get basic GAP allocation values'''
    # dist_validity, time_validity, launch_validity, stop_validity, day_quality
    day_quality(task)
    # avail_dist_points, avail_time_points, avail_dep_points, avail_arr_points
    points_weight(task)
    # task.max_score = 0      # max_score is evaluated without penalties. Is it correct?

    if task.formula.formula_distance == 'difficulty':
        '''Difficulty Calculation'''
        task.difficulty = difficulty_calculation(task, results)

    ''' Score each pilot now'''
    for res in results:
        penalty = res.penalty if res.penalty else 0

        '''initialize'''
        res.distance_score = 0
        res.time_score = 0
        res.arrival_score = 0
        res.departure_score = 0

        '''Pilot distance score'''
        res.distance_score = pilot_distance(task, res)

        ''' Pilot leading points'''
        if task.departure == 'leadout' and res.result_type != 'mindist' and res.SSS_time:
            res.departure_score = pilot_leadout(task, res)

        if res.ESS_time:
            ''' Pilot speed points'''
            res.time_score = pilot_speed(task, res)

            ''' Pilot departure points'''
            if task.departure == 'departure' and res.result_type != 'mindist' and res.SSS_time:
                # does it even still exist dep. points?
                res.departure_score = pilot_departure(task, res)

            ''' Pilot arrival points'''
            if not (task.arrival == 'off'):
                res.arrival_score = pilot_arrival(task, res)

            ''' Penalty for not making goal'''
            if not res.goal_time:
                res.goal_time = 0
                res.time_score *= (1 - formula.no_goal_penalty)
                res.arrival_score *= (1 - formula.no_goal_penalty)

        ''' Total score'''
        res.score = res.distance_score + res.time_score + res.arrival_score + res.departure_score

        ''' Apply Penalty'''
        if penalty:
            res.score = max(0, res.score - penalty)
