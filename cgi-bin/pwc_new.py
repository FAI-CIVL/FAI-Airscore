from collections import namedtuple
from myconn import Database


parameters = namedtuple('formula', 'allow_jump_the_gun, stopped_elapsed_calc, coeff_func, coeff_func_scaled, coef_landout')


def coef2(task_time, best_dist_to_ess, new_dist_to_ess):
    return task_time * (best_dist_to_ess**2 - new_dist_to_ess**2)


def coef_scaled(coeff, essdist):
    return coeff / (1800 * (essdist / 1000) ** 2)


def coef_landout(total_time_to_end, new_dist_to_ess):
    return new_dist_to_ess ** 2 * total_time_to_end

parameters.allow_jump_the_gun = False
parameters.max_jump_the_gun = 0  # seconds
parameters.stopped_elapsed_calc = 'shortest_time'
parameters.coef_func = coef2
parameters.coef_func_scaled = coef_scaled
parameters.coef_landout = coef_landout



#
# Find the task totals and update ..
#   tasTotalDistanceFlown, tasPilotsLaunched, tasPilotsTotal
#   tasPilotsGoal, tasPilotsLaunched,
#
# FIX: TotalDistance wrong with 'lo' type results?

#USE ALSO FOR GAP
#

def task_totals(task, formula):


    tasPk = task.tasPk
    launchvalid = task.launchvalid
    mindist = formula['forMinDistance']
    glidebonus = 0
    landed = 0
    taskt = {}
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
                    `minLC`
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
        print('No rows in tblTaskTotalsView for task ', tasPk)
        return

    totdist         = t['TotalDistance']
    launched        = int(t['TotalLaunched'])
    pilots          = t['TotalPilots']
    stddev          = t['Deviation']
    totdistovermin  = t['TotDistOverMin']
    ess             = t['TotalESS']
    goal            = t['TotalGoal']
    maxdist         = t['maxDist']
    maxbonusdist    = t['maxBonusDistance']
    minarr          = t['firstESS']
    maxarr          = t['lastESS']
    fastest         = t['minTime']
    tqtime          = fastest # ???
    mincoeff2       = t['minLC']
    mindept         = t['firstStart']
    lastdept        = t['lastStart']

    if task.stopped_time:     # Null is returned as None
        glidebonus = formula['glidebonus']
        print("F: glidebonus=", glidebonus)
        landed = t['Landed']



    # query="select (tarES-tarSS) as MinTime" \
    #       " from tblTaskResult " \
    #       "where tasPk=%s and tarES > 0 and (tarES-tarSS) > 0 " \
    #       "order by (tarES-tarSS) asc limit 2"
    # with Database() as db:
    #     t = db.fetchall(query, [tasPk])
    #
    # fastest = 0
    # for row in t:
    #
    #     if fastest == 0:
    #         fastest = row['MinTime']
    #         tqtime = fastest
    #     else:
    #         tqtime = row['MinTime']

    # Sanity
    if fastest == 0: minarr = 0

    # FIX: lead out coeff2 - first departure in goal and adjust min coeff
    # query="select min(tarLeadingCoeff2) as MinCoeff2 " \
    #     "from tblTaskResult " \
    #     "where tasPk=%s and tarLeadingCoeff2 is not NULL"
    #
    # with Database() as db:
    #     t = db.fetchone(query, [tasPk])
    #
    # mincoeff2 = 0
    # if t['MinCoeff2'] is not None:
    #     mincoeff2 = t['MinCoeff2']

    # print "TTT: min leading coeff=mincoeff\n"

    # maxdist = 0
    # mindept = 0
    # lastdept = 0

    # if someone got to goal, maxdist should be dist to goal (to avoid stopped glide creating a max dist > task dist)
    # done in view's query
    # if goal > 0:
    #     query="select tasShortRouteDistance as GoalDist from tblTask where tasPk=%s"
    #
    #     with Database() as db:
    #         t = db.fetchone(query, [tasPk])
    #     if t:
    #         maxdist = t['GoalDist']

    # Sanity
    # if maxdist < mindist: maxdist = mindist # done in view's query

    # print "TT: glidebonus=glidebonus maxdist=maxdist\n"

    # query="select min(tarSS) as MinDept, " \
    #             "max(tarSS) as LastDept " \
    #             "from tblTaskResult " \
    #             "where tasPk=%s " \
    #             "and tarSS > 0 " \
    #             "and tarGoal > 0"
    #
    # with Database() as db:
    #     t = db.fetchone(query, [tasPk])
    #
    # if t:
    #     mindept = t['MinDept']
    #     lastdept = t['LastDept']

    # task quality
    taskt['pilots'] = pilots
    taskt['maxdist'] = maxdist
    taskt['distance'] = totdist
    taskt['distovermin'] = totdistovermin
    taskt['stddev'] = stddev
    taskt['landed'] = landed
    taskt['launched'] = launched
    taskt['launchvalid'] = launchvalid
    taskt['goal'] = goal
    taskt['ess'] = ess
    taskt['fastest'] = fastest
    taskt['tqtime'] = tqtime
    taskt['firstdepart'] = mindept
    taskt['lastdepart'] = lastdept
    taskt['firstarrival'] = minarr
    taskt['lastarrival'] = maxarr
    #taskt['mincoeff'] = mincoeff
    taskt['mincoeff2'] = mincoeff2
    taskt['endssdistance'] = task.EndSSDistance
    taskt['quality'] = None

    return taskt


def day_quality(taskt, formula):
    from math import sqrt
    tmin = None
    if taskt['pilots'] == 0:
        launch = 0
        distance = 0
        time = 0.1
        return (distance, time, launch)


    # C.4.1 Launch Validity
    # LVR = min (1, (num pilots launched + nominal launch) / total pilots )
    # Launch Validity = 0.028*LRV + 2.917*LVR^2 - 1.944*LVR^3
    # Setting Nominal Launch = 10 (max number of DNF that still permit full validity)

    nomlau = 10
    x = (taskt['launched'] + nomlau) / taskt['pilots']
    x = min(1, x)
    launch = 0.028 *x + 2.917 *x *x - 1.944 *x *x *x
    launch = min(launch, 1)

    if taskt['launchvalid'] == 0 or launch < 0:
        print("Launch invalid - dist quality set to 0")
        launch = 0

    print("PWC launch validity = launch")

    # C.4.2 Distance Validity
    # DVR = (Total flown Distance over MinDist) / [ (PilotsFlying / 2) * (NomGoal +1) * (NomDist - MinDist) * NomGoal * (BestDist - NomDist) ]
    # distance = min (1, DVR)

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

    # C.4.3 Time Validity
    # if no pilot @ ESS
    # TVR = min(1, BestDist/NomDist)
    # else
    # TVR = min(1, BestTime/NomTime)
    # TimeVal = max(0, min(1, -0.271 + 2.912*TVR - 2.098*TVR^2 + 0.457*TVR^3))

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

    # C.7.1 Stopped Task Validity
    # If ESS > 0 -> StopVal = 1
    # else StopVal = min (1, sqrt((bestDistFlown - avgDistFlown)/(TaskDistToESS-bestDistFlown+1)*sqrt(stDevDistFlown/5))+(pilotsLandedBeforeStop/pilotsLaunched)^3)
    # Fix - need distlaunchtoess, landed
    avgdist = taskt['distance'] / taskt['launched']
    distlaunchtoess = taskt['endssdistance']
    # when calculating stopv, to avoid dividing by zero when max distance is greater than distlaunchtoess i.e. when someone reaches goal if statement added.
    maxSSdist = 0
    if taskt['fastest'] and taskt['fastest'] > 0:
        stopv = 1

    else:
        x = (taskt['landed'] / taskt['launched'])
        stopv = sqrt((taskt['maxdist'] - avgdist) / (maxSSdist+1) * sqrt(taskt['stddev'] / 5) ) + x ** 3
        stopv = min(1, stopv)

    return distance, time, launch, stopv


def points_weight(task, taskt, formula):
    from math import sqrt

    quality = taskt['quality']
    x = taskt['goal'] / taskt['launched']  # GoalRatio

    # DistWeight = 0.9 - 1.665* goalRatio + 1.713*GolalRatio^2 - 0.587*goalRatio^3
    distweight = 0.9 - 1.665 * x + 1.713 * x * x - 0.587 * x *x *x
    print("PWC 2016 Points Allocatiom distWeight = ", distweight)
    # distweight = 1 - 0.8 * sqrt(x)
    # print("NOT Using 2016 Points Allocatiom distWeight = ", distweight)

    # leadingWeight = (1-distWeight)/8 * 1.4
    leadweight = (1 - distweight) / 8 * 1.4
    print("LeadingWeight = ", leadweight)
    Adistance = 1000 * quality * distweight  # AvailDistPoints
    print("Available Dist Points = ", Adistance)
    Astart = 1000 * quality * leadweight  # AvailLeadPoints
    print("Available Lead Points = ", Astart)

    # resetting $speedweight and $Aspeed using PWC2016 formula
    speedweight = 1 - distweight - leadweight
    Aspeed = 1000 * quality * speedweight  # AvailSpeedPoints
    print("Available Speed Points = ", Aspeed)
    print("points_weight: (", formula['forVersion'], ") Adist=" , Adistance, ", Aspeed=", Aspeed, ", Astart=", Astart ,", Aarrival=", Aarrival)
    return Adistance, Aspeed, Astart, Aarrival


def pilot_departure_leadout(task, taskt, pil, Astart):
    from math import sqrt
    # C.6.3 Leading Points

    LCmin = taskt['mincoeff2']  # min(tarLeadingCoeff2) as MinCoeff2 : is PWC's LCmin?
    LCp = pil['coeff']  # Leadout coefficient

    # Pilot departure score
    Pdepart = 0
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


def pilot_speed(formula, task, taskt, pil, Aspeed):
    from math import sqrt

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


def ordered_results(task, taskt, formula, results):

    pilots=[]

    # Get all pilots and process each of them
    # pity it can't be done as a single update ...

    query = """SELECT
                                @x := @x + 1 AS Place,
                                tarPk,
                                traPk,
                                tarDistance,
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

        taskres['result'] = res['tarResultType']
        taskres['startSS'] = res['tarSS']
        taskres['endSS'] = res['tarES']
        taskres['timeafter'] = res['tarES'] - taskt['firstarrival']
        taskres['place'] = res['Place']
        taskres['time'] = taskres['endSS'] - taskres['startSS']
        taskres['goal'] = res['tarGoal']

        if taskres['time'] < 0:
            taskres['time'] = 0

        # Leadout Points Adjustment
        # C.6.3.1
        #
        taskres['coeff'] = res['tarLeadingCoeff2']  # PWC LeadCoeff (with squared distances)
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


def pilot_distance(taskt, pil, Adistance):
    """

    :type pil: object
    """
    Pdist = Adistance * pil['distance']/taskt['maxdist']

    return Pdist
