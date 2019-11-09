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

def task_totals(task_id):
    '''
    This new version uses a view to collect task totals.
    It means we do not need to store totals in task table anylonger,
    as they are calculated on runtime from mySQL using all task results
    '''

    query = """SELECT
                    `pilots_present`,
                    `tot_dist_flown`,
                    `tot_dist_over_min`,
                    `pilots_launched`,
                    `std_dev`,
                    `pilots_landed`,
                    `pilots_goal`,
                    `pilots_ess`,
                    `max_distance`,
                    `min_dept_time`,
                    `max_dept_time`,
                    `first_SS`,
                    `last_SS`,
                    `min_ess_time`,
                    `max_ess_time`,
                    `fastest_in_goal`,
                    `fastest`,
                    `max_time`
                FROM
                    `TaskStatsView`
                WHERE
                    `task_id` = %s
                LIMIT 1"""
    params = [task_id]
    with Database() as db:
        # get the formula details.
        stats = db.fetchone(query, params)

    if not stats:
        print(query)
        print('No rows in TaskTotalsView for task ', task_id)
        return

    return stats

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

def day_quality(task, formula):

    if not task.launch_valid:
        print("Launch invalid - dist quality set to 0")
        launch      = 0
        distance    = 0
        time        = 0
        return (distance, time, launch)

    stats = task.stats

    if stats['pilots_present'] == 0:
        launch      = 0
        distance    = 0
        time        = 0.1
        return (distance, time, launch)

    stopv = 1
    if task.stopped_time:
        stopv   = stopped_validity(task, formula)

    launch      = launch_validity(stats, formula)
    distance    = distance_validity(stats, formula)
    time        = time_validity(stats, formula)

    return distance, time, launch, stopv

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
        lead_weight      = (1 - dist_weight) / 8 * 1.4
        arr_weight   = (1 - dist_weight) / 8
    else:
        arr_weight   = 0
        if goal_ratio > 0:
            lead_weight = (1 - dist_weight) / 8 * 1.4 * 2
        else:
            lead_weight = stats['max_distance'] / task.opt_dist * 0.1

    time_weight = 1 - dist_weight - lead_weight - arr_weight

    Adistance   = 1000 * quality * dist_weight            # AvailDistPoints
    Astart      = 1000 * quality * lead_weight            # AvailLeadPoints
    Aarrival    = 1000 * quality * arrival_weight         # AvailArrPoints
    Aspeed      = 1000 * quality * time_weight            # AvailSpeedPoints

    return Adistance, Aspeed, Astart, Aarrival


def pilot_departure_leadout(task, pil):
    from math import sqrt

    stats   = task.stats
    Astart  = task['avail_dep_points']

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


def pilot_distance(task, pil):
    """

    :type pil: object
    """

    maxdist     = task.stats['max_distance']
    Adistance   = task.stats['avail_dist_points']
    Pdist       = Adistance * pil['distance'] / maxdist

    return Pdist
