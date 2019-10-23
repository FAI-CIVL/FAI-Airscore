"""
Score a task. At the moment this is only set up for PWC formula tasks.
python3 task_full_rescore_test.py <taskid>
"""

from    task        import Task as T
from    result      import Task_result as R
from    formula     import get_formula_lib, Task_formula
from    logger      import Logger
import  importlib
import  sys
import  Defines as d

def verify_tracks(task, lib):
    from myconn import Database
    from igc_lib import Flight
    from flight_result import Flight_result

    query = """ SELECT
                    `track_id` AS `id`,
                    `name`,
                    `track_file` AS `file`
                FROM
                    `TaskResultView`
                WHERE
                    `task_id` = %s"""
    params = [task.task_id]

    with Database() as db:
        tracks = db.fetchall(query, params)

    if tracks:
        print('getting tracks...')
        # with Database() as db:
        for track in tracks:
            print('{} ({}) Result:'.format(track['name'], track['id']))
            igc_file = track['file']
            flight = Flight.create_from_file(igc_file)
            result = Flight_result.check_flight(flight, task, lib.parameters, 5)
            # Lead_coeff = lc_calc(result, task)
            # result.Lead_coeff = Lead_coeff
            print('   Goal: {} | part. LC: {}'.format(bool(result.goal_time),result.Fixed_LC))
            result.store_result(task.task_id, track['id'])


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

    task = T.read_task(task_id)
    task.calculate_task_length()
    task.calculate_optimised_task_length()

    print(task)

    formula         = Task_formula.read(task_id)
    task.departure  = formula.departure
    task.arrival    = formula.arrival
    lib             = get_formula_lib(formula.type)

    '''get all results for the task'''
    results         = verify_tracks(task, lib)

    task.stats.update(lib.task_totals(task_id))

    if task.stats['pilots_present'] == 0:
        print(f'''Task (ID {task_id}) has no results yet''')
        return 0

    else:
        task.stats.update(lib.day_quality(task, formula))
        results = lib.points_allocation_new(task, formula)
        R.create_result(task, formula, results)

    ''' now restore stdout function '''
    Logger('OFF')

if __name__== "__main__":
    import sys
    main(sys.argv[1:])
