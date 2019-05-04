import sys, time
from result import Task_result
from pprint import pprint

def main():
    print("starting..")
    """Main module. prints result from a task"""

    result = None
    test = 0

    ##check parameter is good.
    if len(sys.argv) >= 2 and sys.argv[1].isdigit():
        task_id = int(sys.argv[1])
        if len(sys.argv) > 2:
            print ("Test Mode")
            test = 1

    else:
        #logging.error("number of arguments != 1 and/or task_id not a number")
        print("Error, uncorrect arguments type or number.")
        print("usage: python test_task_result.py task_id <test>")
        exit()

    """create result object using method 1"""
    start = time.time()
    result = Task_result.read_db(task_id=task_id, test=test)
    file = result.to_json()
    end = time.time()
    # try:
    #     result = Task_Result.read_db(task_id=task_id, test=test)
    # except:
    #     print('Task Result Error: ')

    if test:
        print('processing time: {}'.format(end - start))
        print(result)
        print('json file:')
        print(file)

if __name__== "__main__":
    main()
