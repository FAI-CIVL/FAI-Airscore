from task import get_task_json
from comp import Comp


def ft_score(comp_id):

    comp = Comp(comp_id)
    tasks = comp.get_tasks_details()
    task_results = []

    def km(distance_in_km, decimals=5):
        return f"{distance_in_km:.{decimals}f} km"

    def h(time_in_hours, decimals=5):
        return f"{time_in_hours:.{decimals}f} h"

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
        fastest = None
        stats = task['stats']
        formula = task['formula']
        if task['stats']['fastest_in_goal']:
            fastest = h(task['stats']['fastest_in_goal'] / (60 * 60))

        bestTime.append(fastest)
        validity.append({'distance': km(stats['dist_validity']),
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
                                        'minimumDistance': km(formula['min_dist'] / 1000),
                                        'nominalDistance': km(formula['nominal_dist'] / 1000),
                                        'nominalGoal': formula['nominal_goal'],
                                        'reachMax': {'extra': km(stats['max_distance'] / 1000),
                                                     # TODO extra (flown distance + glide bonus in stopped tasks)
                                                     'flown': km(stats['max_distance'] / 1000)},
                                        'sum': km(stats['tot_dist_flown'] / 1000)})

        validityWorkingLaunch.append({'flying': stats['pilots_launched'],
                                      'nominalLaunch': formula['nominal_launch'],
                                      'present': stats['pilots_present']})

        validityWorkingStop.append({'flying': stats['pilots_launched'],  # TODO
                                    'landed': 0,  # TODO
                                    'launchToEssDistance': km(task['info']['SS_distance'], 3),
                                    'pilotsAtEss': 0,  # TODO
                                    'reachStats': {
                                        'extra': {
                                            'max': '124.018000 km -TODO',  # TODO
                                            'mean': '37.200457 km -TODO',  # TODO
                                            'stdDev': '30.230148 km -TODO'  # TODO
                                        },
                                        'flown': {
                                            'max': km(stats['max_distance'] / 1000, 6),  # TODO
                                            'mean': km(stats['tot_dist_flown'] / stats['pilots_launched'], 6),  # TODO
                                            'stdDev': '30.230148 km -TODO'  # TODO
                                        }
                                    },
                                    'stillFlying': 94  # TODO
                                    })

        validityWorkingTime.append({'gsBestTime': 'null-TODO',  # TODO
                                    'nominalDistance': km(formula['nominal_dist'], 1),
                                    'nominalTime': h(formula['nominal_time'], 6),
                                    'reachMax': {
                                        'extra': km(stats['max_distance'] / 1000),
                                        # TODO extra (flown distance + glide bonus in stopped tasks)
                                        'flown': km(stats['max_distance'] / 1000)
                                    },
                                    'ssBestTime': 'null-TODO'  # TODO
                                    })
        results = []
        rank = 1
        prev_score = None
        for result in task['results']:
            if result['result_type'] != 'abs':
                if not prev_score:
                    rank = 1
                elif result['score'] < prev_score:
                    rank += 1
                prev_score = result['score']

                results.append([[str(result['ID'] or str(result['par_id'])),
                                 result['name']],
                                {'breakdown': {
                                    'distance': result['distance_score'],
                                    'leading': result['departure_score'],
                                    'arrival': result['arrival_score'],
                                    'time': result['time_score'],
                                    'effort': 297.26,
                                    'reach': 297.18
                                },
                                    'place': str(rank),
                                    'total': result['score'],
                                    'fractions': {
                                        'distance': fraction(result['distance_score'], stats['avail_dist_points']),
                                        'leading': fraction(result['departure_score'], stats['avail_dep_points']),
                                        'arrival': fraction(result['arrival_score'], stats['avail_arr_points']),
                                        'time': fraction(result['time_score'], stats['avail_time_points']),
                                        'effort': 1,
                                        'reach': 0.99969724
                                    },
                                    'reach': {
                                        'extra': km(result['distance'], 6),  # TODO check that this is correct
                                        'flown': km(result['distance_flown'], 6)
                                    },
                                    'landedMade': '123.977000km',
                                    'ss': result['SSS_time'],  # TODO FORMAT 2012 - 01 - 05T03: 03:12Z,
                                    'es': result['ESS_time'],
                                    'timeElapsed': result['ss_time'],  # TODO check that this is correct
                                    'leadingArea': '1261556.0000 km^2 s',
                                    'leadingCoef': result['lead_coeff']
                                }
                                ])

        score.append(results)

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

    def km(distance_in_km, decimals=5):
        return f"{distance_in_km:.{decimals}f} km"

    comp = Comp(comp_id)
    tasks = comp.get_tasks_details()
    route = []
    for t in tasks:
        task = Task.read(t['task_id'])
        task.calculate_optimised_task_length()
        wpts = []
        for tp in task.turnpoints:
            wpts.append({'lat': tp.lat,
                         'lon': tp.lon})

        point = {'distance': km(task.opt_dist/1000),
                 'legs': [km(l / 1000) for l in task.optimised_legs],
                 'legsSum': [km(l / 1000) for l in cumsum(task.optimised_legs).tolist()],
                 'flipSum': [km(l / 1000) for l in cumsum(task.optimised_legs[::-1]).tolist()[::-1]],
                 'waypoints': wpts}
        route.append({'point': point,
                      'ellipse': point})

    return route
