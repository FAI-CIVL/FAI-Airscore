from task import Task, get_task_json
from comp import Comp
import statistics
from datetime import timedelta, time, datetime


def km(distance_in_km, decimals=5):
    """takes an int or float of meters and returns a string in kilometers to {decimals} places with 'km' as a postfix"""
    return f"{distance_in_km / 1000:.{decimals}f} km"


def ft_score(comp_id):
    comp = Comp(comp_id)
    tasks = comp.get_tasks_details()
    task_results = []

    def h(time_in_hours, decimals=5):
        """takes an int or float of seconds and returns a string in hours to {decimals} places with 'h' as a postfix"""
        return f"{time_in_hours / (60 * 60):.{decimals}f} h"

    def fraction(points, avail_points):
        if not avail_points or (avail_points == 0):
            return 0
        else:
            return points / avail_points

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
        fastest = None
        stats = task['stats']
        formula = task['formula']
        if task['stats']['fastest_in_goal']:
            fastest = h(task['stats']['fastest_in_goal'])

        bestTime.append(fastest)

        results = []
        rank = 1
        prev_score = None
        distances = []
        for result in task['results']:
            if result['result_type'] != 'abs':
                distances.append(result['distance_flown'])
                if not prev_score:
                    rank = 1
                elif result['score'] < prev_score:
                    rank += 1
                prev_score = result['score']
                ss = None
                es = None
                if result['SSS_time']:
                    ss = (datetime.combine(task_obj.date, time())
                          + timedelta(seconds=result['SSS_time'] - task_obj.time_offset)).strftime('%Y-%m-%dT%H:%M:%SZ')
                    if result['ESS_time']:
                        es = (datetime.combine(task_obj.date, time())
                              + timedelta(seconds=result['ESS_time'] - task_obj.time_offset)).strftime(
                            '%Y-%m-%dT%H:%M:%SZ')
                results.append([[str(result['ID'] or str(result['par_id'])),
                                 result['name']],
                                {'breakdown': {
                                    'distance': result['distance_score'],
                                    'leading': result['departure_score'],
                                    'arrival': result['arrival_score'],
                                    'time': result['time_score'],
                                    'effort': 297.26,  # TODO
                                    'reach': 297.18  # TODO
                                },
                                    'place': str(rank),
                                    'total': result['score'],
                                    'fractions': {
                                        'distance': fraction(result['distance_score'], stats['avail_dist_points']),
                                        'leading': fraction(result['departure_score'], stats['avail_dep_points']),
                                        'arrival': fraction(result['arrival_score'], stats['avail_arr_points']),
                                        'time': fraction(result['time_score'], stats['avail_time_points']),
                                        'effort': 1,  # TODO
                                        'reach': 0.99969724  # TODO
                                    },
                                    'reach': {
                                        'extra': km(result['distance'], 6),  # TODO check that this is correct
                                        'flown': km(result['distance_flown'], 6)
                                    },
                                    'landedMade': '123.977000km',
                                    'ss': ss,
                                    'es': es,
                                    'timeElapsed': result['ss_time'],  # TODO check that this is correct
                                    'leadingArea': '1261556.0000 km ^ 2 s',
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
                                        'minimumDistance': km(formula['min_dist']),
                                        'nominalDistance': km(formula['nominal_dist']),
                                        'nominalGoal': formula['nominal_goal'],
                                        'reachMax': {'extra': km(stats['max_distance']),
                                                     # TODO extra (flown distance + glide bonus in stopped tasks)
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
                                            'max': km(stats['max_distance'], 6),
                                            'mean': km(stats['tot_dist_flown'] / stats['pilots_launched'], 6),
                                            'stdDev': km(statistics.stdev(distances), 6),
                                        }
                                    },
                                    'stillFlying': stats['pilots_launched'] - stats['pilots_landed']
                                    })

        validityWorkingTime.append({'gsBestTime': 'null-TODO',  # TODO
                                    'nominalDistance': km(formula['nominal_dist'], 1),
                                    'nominalTime': h(formula['nominal_time'], 6),
                                    'reachMax': {
                                        'extra': km(stats['max_distance']),
                                        # TODO extra (flown distance + glide bonus in stopped tasks)
                                        'flown': km(stats['max_distance']),
                                    },
                                    'ssBestTime': 'null-TODO'  # TODO
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
                      'ellipse': ellipse})

    return route
