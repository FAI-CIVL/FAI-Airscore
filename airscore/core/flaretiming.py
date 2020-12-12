from task import Task, get_task_json_filename
from comp import Comp
import statistics
from datetime import timedelta, time, datetime
from dataclasses import dataclass
from pilot.flightresult import FlightResult
import collections
from result import open_json_file


def km(distance_in_km, decimals=5) -> str:
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
    diff = task.difficulty
    linear_fraction = 0.5 * pil_distance / task.max_distance
    dist10 = int(pil_distance / 100)  # int(dist in Km * 10)
    diff_fraction = diff[dist10].diff_score
    if len(diff) > dist10 + 1:
        if diff[dist10 + 1].diff_score > diff_fraction:
            diff_fraction += ((diff[dist10 + 1].diff_score - diff[dist10].diff_score) * (pil_distance / 100 - dist10))

    return linear_fraction, diff_fraction


def ft_score(comp_id):
    comp = Comp(comp_id)
    tasks = comp.get_tasks_details()
    task_results = []

    for task in tasks:
        filename = get_task_json_filename(task['task_id'])
        if filename:
            task_results.append(open_json_file(filename))

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
        task_obj.difficulty, _, _, _ = difficulty_calculation(task_obj)
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
            if result['result_type'] != 'abs' and result['result_type'] != 'nyp':
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
        if not ssTimes:
            min_ssTime = None
        else:
            min_ssTime = min(ssTimes)

        validityWorkingTime.append({'gsBestTime': fastest,
                                    'nominalDistance': km(formula['nominal_dist'], 1),
                                    'nominalTime': h(formula['nominal_time'], 6),
                                    'reachMax': {
                                        'extra': km(stats['max_distance']),
                                        'flown': km(max(distances_flown)),
                                    },
                                    'ssBestTime': h(min_ssTime)
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
        filename = get_task_json_filename(task['task_id'])
        if filename:
            task_results.append(open_json_file(filename))

    for task in task_results:
        task_obj = Task.read(task['info']['id'])
        task_obj.get_results()
        pilotsAtEss.append(task_obj.pilots_ess)
        task_arrivals = []

        for result in task['results']:
            if result['result_type'] != 'abs' and result['result_type'] != 'nyp':

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


def difficulty_calculation(task):

    formula = task.formula
    pilot_lo = task.pilots_launched - task.pilots_goal
    lo_results = [p for p in task.valid_results if not p.goal_time]
    best_dist_flown = task.max_distance / 1000  # Km
    if not lo_results:
        '''all pilots are in goal
        I calculate diff array just for correct min_distance_points calculation'''
        lo_results.append(FlightResult(name='dummy', distance_flown=formula.min_dist))

    @dataclass
    class Diffslot:
        dist_x10: int
        diff: int = 0
        rel_diff: float = 0.0
        diff_score: float = 0.0

    formula = task.formula
    best_dist_flown = max(task.max_distance, formula.min_dist) / 1000  # Km
    lo_results = [p for p in task.valid_results if not p.goal_time]
    if not lo_results:
        """all pilots are in goal
        I calculate diff array just for correct min_distance_points calculation"""
        lo_results.append(FlightResult(name='dummy', distance_flown=formula.min_dist))
    pilots_lo = len(lo_results)

    '''distance spread'''
    min_dist_kmx10 = int(formula.min_dist / 100)  # min_dist (Km) * 10
    distspread = dict()
    detailed_distspread = dict()
    best_dist = 0  # best dist. (Km)
    best_dist_kmx10 = 0  # best dist. (Km) * 10

    for p in lo_results:
        detail = {'name': p.name,
                  'ID': p.ID,
                  'dist': p.distance,
                 }
        dist_kmx10 = max(int(p.distance / 100), min_dist_kmx10)
        dist = p.distance / 1000  # Km
        distspread[dist_kmx10] = 1 if dist_kmx10 not in distspread.keys() else distspread[dist_kmx10] + 1

        if dist_kmx10 not in detailed_distspread.keys():
            detailed_distspread[dist_kmx10] = [detail]
        else:
            detailed_distspread[dist_kmx10].append(detail)
        if dist_kmx10 > best_dist_kmx10:
            best_dist_kmx10 = dist_kmx10
        if dist > best_dist:
            best_dist = dist

    # Sanity
    if best_dist == 0:
        return []

    ''' the difficulty for each 100-meter section of the task is calculated
        by counting the number of pilots who landed further along the task'''
    best_dist_kmx10r = int((best_dist_kmx10 + 10) / 10) * 10
    look_ahead = max(30, round(30 * best_dist_flown / pilots_lo))
    kmdiff = []

    for i in range(best_dist_kmx10r):
        diff = sum([0 if x not in distspread.keys() else distspread[x]
                    for x in range(i, min(i + look_ahead, best_dist_kmx10r))])
        kmdiff.append(Diffslot(i, diff))

    sum_diff = sum([x.diff for x in kmdiff])

    ''' Relative difficulty is then calculated by dividing each 100-meter slot’s
        difficulty by twice the sum of all difficulty values.'''

    sum_rel_diff = 0 if sum_diff == 0 else sum([(0.5*x.diff/sum_diff) for x in kmdiff if x.dist_x10 <= min_dist_kmx10])
    for el in kmdiff:
        if el.dist_x10 <= min_dist_kmx10:
            el.diff_score = sum_rel_diff
        elif el.dist_x10 >= best_dist_kmx10:
            el.diff_score = 0.5
        else:
            if sum_diff > 0:
                el.rel_diff = 0.5 * el.diff / sum_diff
            sum_rel_diff += el.rel_diff
            el.diff_score = sum_rel_diff

    return kmdiff, sum_diff, look_ahead, detailed_distspread


def ft_landout(comp_id):
    comp = Comp.read(comp_id)
    tasks = comp.get_tasks_details()
    task_results = []

    for task in tasks:
        filename = get_task_json_filename(task['task_id'])
        if filename:
            task_results.append(open_json_file(filename))

    minDistance = km(comp.formula.min_dist, 3)
    bestDistance = []
    chunking = []
    landout = []
    lookahead = []
    difficulty = []

    for task in task_results:
        task_obj = Task.read(task['info']['id'])
        task_obj.get_results()

        bestDistance.append(km(task_obj.max_distance, 6))
        task_obj.difficulty, sumDiff, look_ahead, d = difficulty_calculation(task_obj)
        detail = collections.OrderedDict(sorted(d.items()))

        chunking.append({'startChunk': [0, '0.0 km'],
                         'endChunk': [task_obj.difficulty[-1].dist_x10, km(task_obj.difficulty[-1].dist_x10*10, 1)],
                         'sumOf': sumDiff,
                         })
        all_downers = task_obj.pilots_launched - task_obj.pilots_goal
        landout.append(all_downers)
        lookahead.append(look_ahead)
        task_difficulty = []
        downed = 0
        for i, chunk in enumerate(detail):
            if detail[chunk]:
                downs = []
                downers = []
                for pilot in detail[chunk]:
                    downs.append(km(pilot['dist'], 3))
                    downers.append([str(pilot['ID']),
                                    pilot['name'],
                                    ])
                downed = downed + len(detail[chunk])
                task_difficulty.append({
                                        'chunk': chunk,
                                        'startChunk': km(chunk*100, 1),
                                        'endChunk': km((chunk+1)*100, 1),
                                        'endAhead': km((chunk+look_ahead)*100, 1),
                                        'down': len(detail[chunk]),
                                        'downs': downs,
                                        'downers': downers,
                                        'downward': all_downers - downed
                                        })
        difficulty.append(task_difficulty)
    return {
            'minDistance': minDistance,
            'bestDistance': bestDistance,
            'chunking': chunking,
            'landout': landout,
            'lookahead': lookahead,
            'difficulty': difficulty,
            }
