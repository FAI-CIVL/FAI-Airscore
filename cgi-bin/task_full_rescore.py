"""
Score a task. At the moment this is only set up for PWC formula tasks.
python3 task_full_rescore_test.py <taskid>
"""

from    task        import Task as T
from    result      import Task_result as R
from    logger      import Logger
import  importlib
import  sys
import  Defines as d

def adjust_flight_result(task, results, lib):
    from flight_result import Flight_result

    maxtime = task.duration
    for pilot in results:
        if pilot['result'].last_fix_time - pilot['result'].SSS_time > maxtime:
            flight = pilot['track'].flight
            last_time = pilot['result'].SSS_time + maxtime
            pilot['result'] = Flight_result.check_flight(flight, task, lib.parameters, 5, deadline=last_time)
    return results

def verify_tracks(task, lib):
    from myconn import Database
    from igc_lib import Flight
    from track import Track
    from flight_result import Flight_result

    query = """ SELECT
                    `track_id` AS `id`,
                    `name`,
                    `track_file` AS `file`
                FROM
                    `TaskResultView`
                WHERE
                    `task_id` = %s"""
    params = [task.id]

    with Database() as db:
        tracks = db.fetchall(query, params)

    if tracks:
        print('getting tracks...')
        # with Database() as db:
        results = []
        for t in tracks:
            print('{} ({}) Result:'.format(t['name'], t['id']))
            igc_file    = t['file']
            # flight      = Flight.create_from_file(igc_file)
            track       = Track.read_file(igc_file)
            if track.flight:
                result  = Flight_result.check_flight(track.flight, task, lib.parameters, 5)
                print('   Goal: {} | part. LC: {}'.format(bool(result.goal_time),result.Fixed_LC))
                result.store_result(task.id, t['id'])
                results.append({'track': track, 'result': result})
        return results


def main(args):
    '''create logging and disable output'''
    Logger('ON', 'task_full_rescore.txt')

    print("starting..")
    """Main module. Takes tasPk as parameter"""
    task_id = 0

    #check parameter is good.
    if len(sys.argv)==2 and sys.argv[1].isdigit():
        task_id = int(sys.argv[1])

    else:
        print("number of arguments != 1 and/or task_id not a number")
        exit()

    print(f"Task ID: {task_id}")

    task = T.read(task_id)
    task.calculate_task_length()
    task.calculate_optimised_task_length()

    print(task)

    lib = task.formula.get_lib()

    ''' manage Stopped Task    '''
    if task.stopped_time:
        if task.comp_class == 'PG' :
            '''
            If (class == 'PG' and (SS_Interval or type == 'ELAPSED TIME')
                We cannot check tracks just once.
                We need to find last_SS_time and then check again tracks until duration == stopTime - last_SS_time

            We need to calculate stopTime from announcingTime'''
            '''     In paragliding the score-back time is set as part of the competition parameters
                    (see section 5.7).
                    taskStopTime = taskStopAnnouncementTime − competitionScoreBackTime
                    In paragliding, a stopped task will be scored if the flying time was one hour or more.
                    For Race to Goal tasks, this means that the Task Stop Time must be one hour or more
                    after the race start time. For all other tasks, in order for them to be scored,
                    the task stop time must be one hour or more after the last pilot started.
                    minimumTime = 60 min .
                    typeOfTask = RaceToGoal ∧ numberOfStartGates = 1:
                        taskStopTime − startTime < minimumTime : taskValidity = 0
                    TypeOfTask ≠ RaceToGoal ∨ numberOfStartGates > 1:
                        taskStopTime − max(∀p :p ∈ StartedPilots :startTime p ) < minimumTime : taskValidity = 0
            '''
            if not task.is_valid():
                return f'task duration is not enough, task with id {task.id} is not valid, scoring is not needed'

            # min_task_duration = 3600
            # last_time = task.stopped_time - task.formula.score_back_time
            results = verify_tracks(task, lib)

            if task.task_type == 'elapsed time' or task.SS_interval:
                '''need to check track and get last_start_time'''
                task.stats.update(lib.task_totals(task_id))
                # duration = last_time - task.last_start_time
                if not task.is_valid():
                    return f'duration is not enough for all pilots, task with id {task.id} is not valid, scoring is not needed.'
                results = adjust_flight_result(task, results, lib)

        elif task.comp_class == 'HG':
        '''     In hang-gliding, stopped tasks are “scored back” by a time that is determined
                by the number of start gates and the start gate interval:
                The task stop time is one start gate interval, or 15 minutes in case of a
                single start gate, before the task stop announcement time.
                numberOfStartGates = 1 : taskStopTime = taskStopAnnouncementTime − 15min.
                numberOfStartGates > 1 : taskStopTime = taskStopAnnouncementTime − startGateInterval.
                In hang gliding, a stopped task can only be scored if either a pilot reached goal
                or the race had been going on for a certain minimum time.
                The minimum time depends on whether the competition is the Women’s World Championship or not.
                The race start time is defined as the time when the first valid start was taken by a competition pilot.
                typeOfCompetition = Women's : minimumTime = 60min.
                typeOfCompetition ≠ Women's : minimumTime = 90min.
                taskStopTime − timeOfFirstStart < minimumTime ∧ numberOfPilotsInGoal(taskStopTime) = 0 : taskValidity = 0
        '''

            if not task.is_valid():
                return f'task duration is not enough, task with id {task.id} is not valid, scoring is not needed'

            # min_task_duration = 3600 * 1.5 # 90 min
            # last_time   = ( (task.stopped_time - task.formula.score_back_time)
            #                 if not task.SS_interval
            #                 else (task.stopped_time - task.SS_interval))
            # duration    = last_time - task.start_time

            verify_tracks(task, lib)

    else:
        '''get all results for the task'''
        verify_tracks(task, lib)

    task.stats.update(lib.task_totals(task_id))

    if task.stats['pilots_present'] == 0:
        print(f'''Task (ID {task_id}) has no results yet''')
        return 0

    task.stats.update(lib.day_quality(task))
    results = lib.points_allocation_new(task)
    R.create_result(task, results)

    ''' now restore stdout function '''
    Logger('OFF')

if __name__== "__main__":
    import sys
    main(sys.argv[1:])
