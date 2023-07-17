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

from math import sqrt


def launch_validity(task):
    """
    C.4.1 Launch Validity
    ‘Pilots Present’ are pilots arriving on take-off, with their gear, with the intention of flying.
    For scoring purposes, ‘Pilots Present’ are all pilots not in the ‘Absent’ status (ABS):
    Pilots who took off, plus pilots present who did not fly (DNF). DNFs need to be attributed carefully.
    A pilot who does not launch due to illness, for instance, is not a DNF, but an ABS.

    LVR = min (1, (num pilots launched + nominal launch) / pilots present )
    Launch Validity = 0.028*LRV + 2.917*LVR^2 - 1.944*LVR^3
    """

    if task.pilots_present == 0 or task.formula.nominal_launch == 0:
        '''avoid div by zero'''
        return 0

    nomlau = task.pilots_present * (1 - task.formula.nominal_launch)
    LVR = min(1, (task.pilots_launched + nomlau) / task.pilots_present)
    launch = 0.028 * LVR + 2.917 * LVR ** 2 - 1.944 * LVR ** 3
    launch = min(launch, 1) if launch > 0 else 0  # sanity

    return launch


def distance_validity(task):
    """
    C.4.2 Distance Validity
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
        print(f"ess > 0, TVR = {TVR}")
    else:
        TVR = min(1, (task.max_distance / task.formula.nominal_dist))
        print(f"none in goal, TVR = {TVR}")

    time = max(0, min(1.000, (-0.271 + 2.912 * TVR - 2.098 * TVR ** 2 + 0.457 * TVR ** 3)))

    return time


def stopped_validity(task):
    """
    12.3.3 Stopped Task Validity
    NumberOfPilotsReachedESS > 0 : StoppedTaskValidity = 1
    NumberOfPilotsReachedESS = 0 :
    StoppedTaskValidity = min(1, sqrt((bestDistFlown - avgDistFlown)/(TaskDistToESS-bestDistFlown+1)*sqrt(stDevDistFlown/5))+(pilotsLandedBeforeStop/pilotsLaunched)^3)

    For this formula we need to use Km as there are numeric constants
    """

    if task.fastest and task.fastest > 0:
        return 1.000

    if task.pilots_launched == 0:
        '''avoid div by zero'''
        return 0

    avgdist = task.tot_dist_flown / task.pilots_launched / 1000  # avg distance in Km
    distlaunchtoess = task.opt_dist_to_ESS / 1000  # TaskDistToESS in Km
    max_distance = task.max_distance_flown / 1000  # bestDistFlown in Km
    std_dev = task.std_dev_dist / 1000  # stDevDistFlown in Km

    stopv = min(
        1.000,
        (
            sqrt((max_distance - avgdist) / (distlaunchtoess - max_distance + 1) * sqrt(std_dev / 5))
            + (task.pilots_landed / task.pilots_launched) ** 3
        ),
    )
    return stopv


def day_quality(task):
    task.dist_validity = 0.000
    task.time_validity = 0.000
    task.launch_validity = 0.000
    task.stop_validity = 1.000
    task.day_quality = 0.000

    if task.cancelled:
        print("Task Cancelled - dist quality set to 0")
        return None

    if task.pilots_present == 0:
        print("No pilots results - quality set to 0")
        return None

    if task.stopped_time:
        task.stop_validity = stopped_validity(task)

    task.launch_validity = launch_validity(task)
    task.dist_validity = distance_validity(task)
    task.time_validity = time_validity(task)
    task.day_quality = min((task.stop_validity * task.launch_validity * task.dist_validity * task.time_validity), 1.000)


def points_weight(task):
    formula = task.formula
    quality = task.day_quality

    if not task.pilots_launched:  # sanity
        return 0, 0, 0, 0

    '''Goal Ratio'''
    goal_ratio = task.pilots_goal / task.pilots_launched

    '''
    DistWeight:         0.9 - 1.665* goalRatio + 1.713*GolalRatio^2 - 0.587*goalRatio^3
    LeadWeight:         (1 - DistWeight)/8 * 1.4
    ArrWeight:          0
    TimeWeight:         1 − DistWeight − LeadWeight
    '''
    task.dist_weight = 0.9 - 1.665 * goal_ratio + 1.713 * goal_ratio ** 2 - 0.587 * goal_ratio ** 3
    task.dep_weight = (1 - task.dist_weight) / 8 * 1.4 * formula.lead_factor
    task.time_weight = 1 - task.dist_weight - task.dep_weight
    task.arr_weight = 0

    task.avail_dist_points = 1000 * quality * task.dist_weight  # AvailDistPoints
    task.avail_dep_points = 1000 * quality * task.dep_weight  # AvailLeadPoints
    task.avail_arr_points = 0  # AvailArrPoints
    task.avail_time_points = 1000 * quality - task.avail_dep_points - task.avail_dist_points  # AvailSpeedPoints

    '''Stopped Task'''
    if task.stopped_time and task.pilots_ess:
        """C.7
        A fixed amount of points is subtracted from the time points of each pilot that makes goal 
        in a stopped task and is added instead to the distance points allocation. 
        This amount is the amount of time points a pilot would receive if he had reached ESS exactly at the Task Stop Time.
        """
        task.time_points_reduction = calculate_time_points_reduction(task)
        task.avail_dist_points += task.time_points_reduction
    else:
        task.time_points_reduction = 0


def pilot_leadout(task, res):
    """
    Args:
        task: Task obj.
        res: FlightResult object
    """

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
                LF = max(0, 1 - ((LCp - LCmin) / sqrt(LCmin)) ** (2 / 3))

                Pdepart = Astart * LF

    return Pdepart


def speed_fraction(task, res) -> float:
    if task.formula.no_goal_penalty < 1 or (task.stopped_time and not task.fastest_in_goal):
        Tmin = task.fastest  
    else:
        Tmin = task.fastest_in_goal
    Ptime = res.ss_time
    if not Tmin or res.ESS_time is None or Ptime < Tmin:
        # checking that task has pilots in ESS, and that pilot is in ESS
        return 0
    print(f"Pilot {res.ID} time {Ptime} | Tmin {Tmin}")
    return 1 - ((Ptime - Tmin) / (60 * sqrt(Tmin))) ** (5/6)  # 1 - ( ((Ptime - Tmin) / 3600) / sqrt(Tmin / 3600) ) ** (5/6)


def pilot_speed(task, res):
    """
    Args:
        task: Task obj.
        res: FlightResult object
    """

    if not res.ESS_time:
        return 0

    Aspeed = task.avail_time_points

    # C.6.2 Time Points
    Pspeed = 0
    Pred = task.time_points_reduction if hasattr(task, 'time_points_reduction') else 0
    SF = speed_fraction(task, res)

    if SF > Pred:
        Pspeed = Aspeed * SF - Pred

    return Pspeed


def pilot_distance(task, pil):
    """
    :type
        pil: FlightResult object
        task: Task obj.
    """
    if pil.goal_time:
        return task.avail_dist_points

    return pil.distance / task.max_distance * task.avail_dist_points


def pilot_penalty(task, res):

    score_before = res.before_penalty_score
    # applying flat penalty after percentage ones
    penalty = score_before * res.percentage_penalty + res.flat_penalty
    '''check 0 < score_after_all_penalties < max_avail_points'''
    max_avail_points = task.day_quality * 1000
    score_after_all_penalties = min(max(0, score_before - penalty), max_avail_points)
    actual_penalty = score_before - score_after_all_penalties
    return actual_penalty, score_after_all_penalties


def calculate_min_dist_score(t):
    from pilot.flightresult import FlightResult

    p = FlightResult(ID=0, name='dummy min_dist')
    p.distance_flown = t.formula.min_dist
    return pilot_distance(t, p)


def calculate_time_points_reduction(t):
    from pilot.flightresult import FlightResult

    p = FlightResult(ID=0, name='dummy time_points_reduction')
    p.distance_flown = t.opt_dist
    # rules state max start time among all pilot but will be corrected
    p.SSS_time = max(p.SSS_time for p in t.valid_results if p.ESS_time)
    p.ESS_time = t.stop_time
    return pilot_speed(t, p)


def process_results(task):
    formula = task.formula

    ''' get pilot.result non ABS or DNF, ordered by ESS time'''
    results = sorted(task.valid_results, key=lambda i: (float('inf') if not i.ESS_time else i.ESS_time))
    if len(results) == 0:
        return None

    for idx, res in enumerate(results, 1):
        '''set pilot to min distance if they're below that ..'''
        res.total_distance = max(formula.min_dist, res.distance or 0)

        if res.ESS_time:
            ''' Time after first on ESS'''
            res.time_after = res.ESS_time - task.min_ess_time
            ''' ESS arrival order'''
            res.ESS_rank = idx

        '''
        Leadout Points Adjustment
        C.6.3.1
        '''
        ''' Get Lead Coefficient calculation from Formula library'''
        lib = task.formula.get_lib()
        res.lead_coeff = lib.tot_lc_calc(res, task)


def points_allocation(task):
    """ Get task with pilots FlightResult obj. and calculates results"""

    ''' Get pilots not ABS or DNF '''
    results = task.valid_results
    formula = task.formula

    ''' Calculate Min Dist Score '''
    task.min_dist_score = calculate_min_dist_score(task)

    ''' Score each pilot now'''
    for res in results:

        '''initialize'''
        res.distance_score = 0
        res.time_score = 0
        res.arrival_score = 0
        res.departure_score = 0
        res.penalty = 0

        if res.result_type == 'mindist':
            res.distance_score = task.min_dist_score
        else:
            '''Pilot distance score'''
            res.distance_score = pilot_distance(task, res)

            ''' Pilot leading points'''
            if task.departure == 'leadout' and res.SSS_time:
                res.departure_score = pilot_leadout(task, res)

            if res.ESS_time:
                ''' Pilot speed points'''
                res.time_score = pilot_speed(task, res)

                ''' Penalty for not making goal'''
                if not res.goal_time:
                    res.goal_time = 0
                    res.time_score *= 1 - formula.no_goal_penalty

        ''' Apply Penalty'''
        if res.flat_penalty or res.percentage_penalty:
            res.penalty, res.score = pilot_penalty(task, res)
        else:
            res.score = res.before_penalty_score
