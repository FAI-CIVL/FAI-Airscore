"""script to calculate tassk distances, optimised and non optimised and write to the DB
python3 update_task.py <taskid>
this is to used in current front end. eventually will be deprecated when we go to flask app

"""

import task
import logging
import sys
import Defines as d


def main():
    print("starting..")
    """Main module. Takes tasPk as parameter"""
    log_dir = d.LOGDIR
    print("log setup")
    logging.basicConfig(filename=log_dir + 'main.log',level=logging.INFO,format='%(asctime)s %(message)s')
    task_id = 0

    ##check parameter is good.
    if len(sys.argv)==2 and sys.argv[1].isdigit():
        task_id = int(sys.argv[1])

    else:
        logging.error("number of arguments != 1 and/or task_id not a number")
        print("number of arguments != 1 and/or task_id not a number")
        exit()

    tsk = task.Task.read_task(task_id)
    tsk.calculate_optimised_task_length()
    tsk.calculate_task_length()
    tsk.update_task()

if __name__== "__main__":
    main()