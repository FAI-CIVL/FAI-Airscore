from task import Task, get_task_json
from comp import Comp
import statistics
from datetime import timedelta, time, datetime
from formulas.libs.gap import difficulty_calculation


def km(distance_in_km, decimals=5):
    """takes an int or float of meters and returns a string in kilometers to {decimals} places with 'km' as a postfix"""
    if distance_in_km:
        return f"{distance_in_km / 1000:.{decimals}f} km"
    return None


def h(time_in_hours, decimals=5):
    """takes an int or float of seconds and returns a string in hours to {decimals} places with 'h' as a postfix"""
    if time_in_hours:
        return f"{time_in_hours / (60 * 60):.{decimals}f} h"
    return None


def fraction(points, avail_points):
    if not avail_points or (avail_points == 0):
        return 0
    else:
        return points / avail_points


def lf_df(task, pil_distance):
    """
    calculates the linear distance factor and difficulty factor from GAP
    Args:
        task: Task obj.
        pil_distance: distance flown
    """
    maxdist = task.max_distance
    diff = task.difficulty
    lf = 0.5 * pil_distance / maxdist
    dist10 = int(pil_distance / 100)  # int(dist in Km * 10)
    df = diff[dist10].diff_score + ((diff[dist10 + 1].diff_score - diff[dist10].diff_score)
                                    * (pil_distance / 100 - dist10))
    return lf, df


def ft_score(comp_id):
    comp = Comp(comp_id)
    tasks = comp.get_tasks_details()
    task_results = []

    for task in tasks:
        task_results.append(get_task_json(task['task_id']))

    # comp_result = get_comp_json(comp_id)
    # if comp_result == 'error':
    #     pass # do something here

    bestTime = []
    validity = []
    validityWorkingDistance = []
    validityWorkingLaunch = []
    validityWorkingStop = []
    validityWorkingTime = []
    score = []

    for task in task_results:
        task_obj = Task.read(task['info']['id'])
        task_obj.get_results()
        task_obj.difficulty = difficulty_calculation(task_obj)
        fastest = None
        stats = task['stats']
        formula = task['formula']
        if task['stats']['fastest_in_goal']:
            fastest = h(task['stats']['fastest_in_goal'])

        bestTime.append(fastest)
        ssTimes = []
        distances_flown = []

        results = []
        rank = 1
        prev_score = None
        distances = []
        for result in task['results']:
            if result['result_type'] != 'abs':
                distances.append(result['distance'])
                distances_flown.append(result['distance_flown'])
                if result['goal_time']:
                    lf = 0.5
                    df = 0.5
                else:
                    lf, df = lf_df(task_obj, result['distance_flown'])
                if prev_score is None:
                    rank = 1
                elif result['score'] < prev_score:
                    rank += 1
                prev_score = result['score']
                ss = None
                es = None
                if result['SSS_time']:
                    ss = (datetime.combine(task_obj.date, time())
                          + timedelta(seconds=result['SSS_time'])).strftime('%Y-%m-%dT%H:%M:%SZ')
                    if result['ESS_time']:
                        ssTimes.append(result['ESS_time'] - result['real_start_time'])
                        es = (datetime.combine(task_obj.date, time())
                              + timedelta(seconds=result['ESS_time'])).strftime(
                            '%Y-%m-%dT%H:%M:%SZ')
                results.append([[str(result['ID'] or str(result['par_id'])),
                                 result['name']],
                                {'breakdown': {
                                    'distance': result['distance_score'],
                                    'leading': result['departure_score'],
                                    'arrival': result['arrival_score'],
                                    'time': result['time_score'],
                                    'effort': df,
                                    'reach': lf,
                                },
                                    'place': str(rank),
                                    'total': result['score'],
                                    'fractions': {
                                        'distance': fraction(result['distance_score'], stats['avail_dist_points']),
                                        'leading': fraction(result['departure_score'], stats['avail_dep_points']),
                                        'arrival': fraction(result['arrival_score'], stats['avail_arr_points']),
                                        'time': fraction(result['time_score'], stats['avail_time_points']),
                                        'effort': fraction(df, 0.5),
                                        'reach': fraction(lf, 0.5),
                                    },
                                    'reach': {
                                        'extra': km(result['distance'], 6),  # TODO check that this is correct
                                        'flown': km(result['distance_flown'], 6)
                                    },
                                    'landedMade': None,  # TODO
                                    'ss': ss,
                                    'es': es,
                                    'timeElapsed': h(result['ss_time']),  # TODO check that this is correct
                                    'leadingArea': None,
                                    'leadingCoef': result['lead_coeff']
                                }
                                ])

        score.append(results)

        validity.append({'distance': stats['dist_validity'],
                         'time': stats['time_validity'],
                         'launch': stats['launch_validity'],
                         'stop': stats['stop_validity'],
                         'task': stats['day_quality']})

        NomDistArea = (((formula['nominal_goal'] + 1) *
                        (formula['nominal_dist'] / 1000 -
                         formula['min_dist'] / 1000)) +
                       max(0, (formula['nominal_goal'] *
                               stats['max_distance'] / 1000 -
                               formula['nominal_dist'] / 1000))) / 2

        validityWorkingDistance.append({'area': NomDistArea,
                                        'flying': stats['pilots_launched'],
                                        'minimumDistance': km(formula['min_dist'], 3),
                                        'nominalDistance': km(formula['nominal_dist'], 1),
                                        'nominalGoal': formula['nominal_goal'],
                                        'reachMax': {'extra': km(stats['max_distance']),
                                                     'flown': km(stats['max_distance'])},
                                        'sum': km(stats['tot_dist_flown'])})

        validityWorkingLaunch.append({'flying': stats['pilots_launched'],
                                      'nominalLaunch': formula['nominal_launch'],
                                      'present': stats['pilots_present'],
                                      })

        validityWorkingStop.append({'flying': stats['pilots_launched'],
                                    'landed': stats['pilots_landed'],
                                    'launchToEssDistance': km(task['info']['SS_distance'], 3),
                                    'pilotsAtEss': stats['pilots_ess'],
                                    'reachStats': {
                                        'extra': {
                                            'max': km(stats['max_distance'], 6),
                                            'mean': km(statistics.mean(distances), 6),
                                            'stdDev': km(statistics.stdev(distances), 6),
                                        },
                                        'flown': {
                                            'max': km(max(distances_flown), 6),
                                            'mean': km(sum(distances_flown) / stats['pilots_launched'], 6),
                                            'stdDev': km(statistics.stdev(distances_flown), 6),
                                        }
                                    },
                                    'stillFlying': stats['pilots_launched'] - stats['pilots_landed']
                                    })

        validityWorkingTime.append({'gsBestTime': fastest,
                                    'nominalDistance': km(formula['nominal_dist'], 1),
                                    'nominalTime': h(formula['nominal_time'], 6),
                                    'reachMax': {
                                        'extra': km(stats['max_distance']),
                                        'flown': km(max(distances_flown)),
                                    },
                                    'ssBestTime': h(min(ssTimes))
                                    })

    return {'bestTime': bestTime,
            'validity': validity,
            'validityWorkingDistance': validityWorkingDistance,
            'validityWorkingLaunch': validityWorkingLaunch,
            'validityWorkingStop': validityWorkingStop,
            'validityWorkingTime': validityWorkingTime,
            'score': score}


def ft_route(comp_id):
    from numpy import cumsum
    from task import Task

    comp = Comp(comp_id)
    tasks = comp.get_tasks_details()
    route = []

    for t in tasks:
        task = Task.read(t['task_id'])
        task.calculate_task_length()
        task.calculate_optimised_task_length()
        wpts = []
        opt_wpts = []

        for tp in task.turnpoints:
            wpts.append({'lat': tp.lat,
                         'lon': tp.lon})

        for tp in task.optimised_turnpoints:
            opt_wpts.append({'lat': tp.lat,
                             'lon': tp.lon})

        point = {'distance': km(task.distance),
                 'legs': [km(leg) for leg in task.legs],
                 'legsSum': [km(leg) for leg in cumsum(task.legs).tolist()],
                 'flipSum': [km(leg) for leg in cumsum(task.legs[::-1]).tolist()[::-1]],
                 'waypoints': wpts}

        ellipse = {'distance': km(task.opt_dist),
                   'legs': [km(leg) for leg in task.optimised_legs],
                   'legsSum': [km(leg) for leg in cumsum(task.optimised_legs).tolist()],
                   'flipSum': [km(leg) for leg in cumsum(task.optimised_legs[::-1]).tolist()[::-1]],
                   'waypoints': opt_wpts}
        route.append({'point': point,
                      'ellipse': ellipse,
                      'sphere': None,
                      'projected': None,
                      'planar': None,
                      'spherical': None})

    return route


def ft_arrival(comp_id):
    comp = Comp(comp_id)
    tasks = comp.get_tasks_details()

    # for task in tasks:
    #     task_results.append(get_task_json(task['task_id']))

    pilotsAtEss = []
    arrivalRank = []
    task_results = []

    for task in tasks:
        task_results.append(get_task_json(task['task_id']))

    for task in task_results:
        task_obj = Task.read(task['info']['id'])
        task_obj.get_results()
        pilotsAtEss.append(task_obj.pilots_ess)
        task_arrivals = []

        for result in task['results']:
            if result['result_type'] != 'abs':

                if result['ESS_time']:
                    task_arrivals.append([result['ESS_time'], result['ID'], result['name'], result['arrival_score']])
        if task_arrivals:
            task_arrivals.sort(key=lambda l: l[0])

            first = task_arrivals[0][0]
            first_points = task_arrivals[0][3]
            task_arrival_rank = []
            rank = 1
            prev = first
            for arrival in task_arrivals:
                if arrival[0] != prev:
                    rank += 1
                task_arrival_rank.append([[str(arrival[1]),
                                          arrival[2]],
                                          {'lag': h(arrival[0] - first),
                                           'rank': str(rank),
                                           'frac': fraction(arrival[3], first_points)},
                                          ])
            arrivalRank.append(task_arrival_rank)
    return {'pilotsAtEss': pilotsAtEss,
            'arrivalRank': arrivalRank}

#
#     pilotsAtEss:
#     - 0
#     - 32
#     - 46
#     - 37
#     - 27
#     - 46
#     - 7
#     - 29
#     arrivalRank:
#     - []
#     - - - - '103'
#     - Roberto
#     Nichele
#
#
# - lag: 0.000000
# h
# rank: '1'
# frac: 1
# - - - '89'
# - Scott
# Barrett
# - lag: 0.003611
# h
# rank: '2'
# frac: 0.93333713
# - - - '60'
# - Rohan
# Holtkamp
# - lag: 0.018611
# h
# rank: '3'
# frac: 0.87052124
# - - - '99'
#
#
