"""usage: python create_task_result.py task_id 'status' <test>"""

import sys, time
from result import Task_result
from pprint import pprint

def main():

    """Main module. prints result from a task"""

    result = None
    test = 0

    '''check parameters are good'''
    if len(sys.argv) >= 3 and sys.argv[1].isdigit():
        task_id = int(sys.argv[1])
        status = str(sys.argv[2])
        if len(sys.argv) > 3:
            print ("Test Mode")
            print("starting..")
            test = 1

    else:
        #logging.error("number of arguments != 1 and/or task_id not a number")
        print("Error, uncorrect arguments type or number.")
        print("usage: python test_task_result.py task_id 'status' <test>")
        exit()

    """create result object using method 1"""
    start = time.time()
    result = Task_result.read_db(task_id=task_id, test=test)
    filename = result.to_json(status=status)
    ref_id = result.to_db(test=test)
    end = time.time()

    if test:
        print('processing time: {}'.format(end - start))
        print(result)
        print('json file:')
        print(filename)
    else:
        print(ref_id)

if __name__== "__main__":
    main()
