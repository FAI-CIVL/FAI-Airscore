'''
standard gap formulas.
 TODO will need it's own version of formulas in pwc in order to be used for gap scoring

'''

from myconn import Database

def task_totals(task, formula):
    '''
    This new version uses a view to collect task totals.
    It means we do not need to store totals in task table anylonger,
    as they are calculated on runtime from mySQL using all task results
    '''

    tasPk = task.tasPk
    launchvalid = task.launchvalid
    mindist = formula['forMinDistance']
    glidebonus = 0
    landed = 0
    tqtime = None


    #todo: 'Landed' misses people who made ESS but actually landed before goal
    query ="""  SELECT
                    `TotalPilots`,
                    `TotalDistance`,
                    `TotDistOverMin`,
                    `TotalLaunched`,
                    `Deviation`,
                    `TotalLanded`,
                    `TotalESS`,
                    `TotalGoal`,
                    `maxDist`,
                    `firstStart`,
                    `lastStart`,
                    `firstSS`,
                    `lastSS`,
                    `firstESS`,
                    `lastESS`,
                    `minTime`,
                    `LCmin`
                FROM
                    `TaskTotalsView`
                WHERE
                    `tasPk` = %s
                LIMIT 1"""
    params = [tasPk]
    with Database() as db:
        # get the formula details.
        t = db.fetchone(query, params)

    if not t:
        print(query)
        print('No rows in TaskTotalsView for task ', tasPk)
        return

    task.stats['distance']      = t['TotalDistance']
    task.stats['launched']      = int(t['TotalLaunched'])
    task.stats['pilots']        = int(t['TotalPilots'])     # pilots present on take-off, ABS are not counted
    task.stats['stddev']        = t['Deviation']
    task.stats['distovermin']   = t['TotDistOverMin']
    task.stats['ess']           = int(t['TotalESS'])
    task.stats['goal']          = int(t['TotalGoal'])
    task.stats['maxdist']       = t['maxDist']
    task.stats['fastest']       = t['minTime']
    task.stats['minarr']        = t['firstESS'] if t['minTime'] > 0 else 0
    task.stats['maxarr']        = t['lastESS']
    task.stats['tqtime']        = t['minTime'] # ???
    #task.stats['LCmin']         = t['LCmin']   # not already calculated
    task.stats['mindept']       = t['firstStart']
    task.stats['lastdept']      = t['lastStart']

    if task.stopped_time:     # Null is returned as None
        glidebonus = formula['glidebonus']
        print("F: glidebonus=", glidebonus)
        task.stats['landed'] = t['Landed']

    return task.stats


def day_quality(task, formula):
    from math import sqrt

    taskt = task.stats

    tmin = None
    if taskt['pilots'] == 0:
        launch = 0
        distance = 0
        time = 0.1
        return (distance, time, launch)


    '''
    C.4.1 Launch Validity
    LVR = min (1, (num pilots launched + nominal launch) / total pilots )
    Launch Validity = 0.028*LRV + 2.917*LVR^2 - 1.944*LVR^3
    ?? Setting Nominal Launch = 10 (max number of DNF that still permit full validity) ??
    '''

    if task.launchvalid == 0:
        print("Launch invalid - dist quality set to 0")
        launch = 0
    else:
        nomlau = taskt['pilots'] * (1 - formula['forNomLaunch'])
        x = (taskt['launched'] + nomlau) / taskt['pilots']
        x = min(1, x)
        launch = 0.028 *x + 2.917 *x *x - 1.944 *x *x *x
        launch = min(launch, 1) if launch > 0 else 0
        print("Launch validity = launch")

    '''
    C.4.2 Distance Validity
    DVR = (Total flown Distance over MinDist) / [ (PilotsFlying / 2) * (NomGoal +1) * (NomDist - MinDist) * NomGoal * (BestDist - NomDist) ]
    Dist. Validity = min (1, DVR)
    '''

    nomgoal = formula['forNomGoal']   # nom goal percentage
    nomdist = formula['forNomDistance']  # nom distance
    mindist = formula['forMinDistance']  # min distance
    maxdist = taskt['maxdist']  # max distance
    totalflown = taskt['distovermin']  # total distance flown by pilots over min. distance
    bestdistovernom = taskt['maxdist'] - nomdist  # best distance flown ove minimum dist.
    # bestdistovermin = taskt['maxdist'] - mindist  # best distance flown ove minimum dist.
    numlaunched = taskt['launched'] # Num Pilots flown

    print("nom goal * best dist over nom : ", (nomgoal * bestdistovernom))

    # distance = 2 * totalflown / ( taskt['launched'] * ( (1+nomgoal) * (int( formula['nomdist']-formula['mindist']) + .5 ) ) * (nomgoal * bestdist) )
    if (nomgoal * bestdistovernom) > 0:
        print("It is positive")
        nomdistarea = ((nomgoal + 1) * (nomdist - mindist) + (nomgoal * bestdistovernom)) / 2
        print("NomDistArea : ", nomdistarea)

    else:
        print("It is negative or null")
        nomdistarea = (nomgoal + 1) * (nomdist - mindist) / 2


    print("Nom. Goal parameter: ", nomgoal)
    print("Min. Distance : ", mindist)
    print("Nom. Distance: ", nomdist)
    print("Total Flown Distance : ", taskt['distance'])
    print("Total Flown Distance over min. dist. : " , totalflown)
    print("Pilots launched : ", numlaunched)
    print("Best Distance: ", maxdist)
    print("NomDistArea : ", nomdistarea)

    distance = totalflown / (numlaunched * nomdistarea)
    distance = min(1, distance)

    print("Total : ", (totalflown / (numlaunched * nomdistarea)))
    print("PWC distance validity = ", distance)

    '''
    C.4.3 Time Validity
    if no pilot @ ESS
    TVR = min(1, BestDist/NomDist)
    else
    TVR = min(1, BestTime/NomTime)
    TimeVal = max(0, min(1, -0.271 + 2.912*TVR - 2.098*TVR^2 + 0.457*TVR^3))
    '''

    if taskt['ess'] > 0:
        tmin = taskt['tqtime']
        x = tmin / formula['forNomTime']
        print("ess > 0, x before min ", x)
        x = min(1, x)
        print("ess > 0, x = ", x)
    else:
        x = taskt['maxdist'] / formula['forNomDistance']
        print("none in goal, x before min ", x)
        x = min(1, x)
        print("none in goal, x = ", x)

    time = -0.271 + 2.912 *x - 2.098 *x *x + 0.457 *x *x *x
    print("time quality before min time")
    time = min(1, time)
    print("time quality before max time")
    time = max(0, time)

    print("PWC time validity (tmin={} x={}) = {}".format(tmin, x, time))

    '''
    C.7.1 Stopped Task Validity
    If ESS > 0 -> StopVal = 1
    else StopVal = min (1, sqrt((bestDistFlown - avgDistFlown)/(TaskDistToESS-bestDistFlown+1)*sqrt(stDevDistFlown/5))+(pilotsLandedBeforeStop/pilotsLaunched)^3)
    '''
    # Fix - need distlaunchtoess, landed
    avgdist = taskt['distance'] / taskt['launched']
    distlaunchtoess = task.EndSSDistance
    # when calculating stopv, to avoid dividing by zero when max distance is greater than distlaunchtoess i.e. when someone reaches goal if statement added.
    maxSSdist = 0
    if taskt['fastest'] and taskt['fastest'] > 0:
        stopv = 1

    else:
        x = (taskt['landed'] / taskt['launched'])
        stopv = sqrt((taskt['maxdist'] - avgdist) / (maxSSdist+1) * sqrt(taskt['stddev'] / 5) ) + x ** 3
        stopv = min(1, stopv)

    return distance, time, launch, stopv


def points_weight(task, formula):
    from math import sqrt

    taskt = task.stats

    quality = taskt['quality']
    x = taskt['goal'] / taskt['launched']  # GoalRatio

    '''
    DistWeight = 0.9 - 1.665* goalRatio + 1.713*GolalRatio^2 - 0.587*goalRatio^3
    '''
    distweight = 0.9 - 1.665 * x + 1.713 * x * x - 0.587 * x *x *x
    print("PWC 2016 Points Allocatiom distWeight = ", distweight)
    # distweight = 1 - 0.8 * sqrt(x)
    # print("NOT Using 2016 Points Allocatiom distWeight = ", distweight)

    '''
    LeadingWeight = (1 - DistWeight)/8 * 1.4
    '''
    leadweight = (1 - distweight) / 8 * 1.4
    print("LeadingWeight = ", leadweight)
    Adistance = 1000 * quality * distweight  # AvailDistPoints
    print("Available Dist Points = ", Adistance)
    Astart = 1000 * quality * leadweight  # AvailLeadPoints
    print("Available Lead Points = ", Astart)

    '''calculating speedweight and Aspeed using PWC2016 formula, without arrivalweight'''
    # we could safely delete everything concerning Arrival Points in PWC GAP.
    Aarrival = 0
    speedweight = 1 - distweight - leadweight
    Aspeed = 1000 * quality * speedweight  # AvailSpeedPoints
    print("Available Speed Points = ", Aspeed)
    print("points_weight: (", formula['forVersion'], ") Adist=" , Adistance, ", Aspeed=", Aspeed, ", Astart=", Astart ,", Aarrival=", Aarrival)
    return Adistance, Aspeed, Astart, Aarrival


def pilot_departure_leadout(task, pil, Astart):
    from math import sqrt

    taskt = task.stats
    # C.6.3 Leading Points

    LCmin = taskt['LCmin']  # min(tarLeadingCoeff2) as LCmin : is PWC's LCmin?
    LCp = pil['LC']  # Leadout coefficient

    # Pilot departure score
    Pdepart = 0
    '''Departure Points type = Leading Points'''
    if task.departure == 'leadout':  # In PWC is always the case, we can ignore else cases
        print("  - PWC  leadout: LC ", LCp, ", LCMin : ", LCmin)
        if LCp > 0:

            if LCp <= LCmin:
                print("======= being LCp <= LCmin  =========")
                Pdepart = Astart
            elif LCmin <= 0:
                # this shouldn't happen
                print("=======  being LCmin <= 0   =========")
                Pdepart = 0

            else: # We should have ONLY this case
                # $Pdepart = $Astart * (1-(($LCp-$LCmin)*($LCp-$LCmin)/sqrt($LCmin))**(1/3))
                # $Pdepart = $Alead * (1-(($LCp-$LCmin)*($LCp-$LCmin)/sqrt($LCmin))**(1/3)) # Why $Alead is not working?

                # LeadingFactor = max (0, 1 - ( (LCp -LCmin) / sqrt(LCmin) )^(2/3))
                # LeadingPoints = LeadingFactor * AvailLeadPoints
                LF = 1 - ( (LCp - LCmin) ** 2 / sqrt(LCmin) ) ** (1 / 3)
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


def pilot_speed(task, pil, Aspeed):
    from math import sqrt

    taskt = task.stats

    # C.6.2 Time Points
    Tmin = taskt['fastest']
    Pspeed = 0
    Ptime = 0

    if pil['time'] > 0 and Tmin > 0:  # checking that task has pilots in ESS, and that pilot is in ESS
        Ptime = pil['time']
        SF = 1 - ((Ptime-Tmin) / 3600 / sqrt(Tmin / 3600) ) ** (5 / 6)

        if SF > 0:
            Pspeed = Aspeed * SF


    print(pil['traPk'], " Ptime: {}, Tmin={}".format(Ptime, Tmin))

    return Pspeed


def pilot_distance(task, pil, Adistance):
    """

    :type pil: object
    """

    maxdist = task.stats['maxdist']
    Pdist = Adistance * pil['distance']/maxdist

    return Pdist
