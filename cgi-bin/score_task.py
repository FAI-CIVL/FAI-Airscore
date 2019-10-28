from logger     import Logger
from task       import Task as T
from pprint     import pprint

def main(args):

    '''create logging and disable output'''
    Logger('ON', 'score_task.txt')

    print("starting..")
    """Main module. Takes tasPk as parameter"""

    '''check parameter is good'''
    if not (args[0].isdigit() and int(args[0]) > 0):
        print("number of arguments != 1 and/or task_id not a number")
        exit()

    task_id = int(args[0])
    print(f"Task ID: {task_id}")
    task = T.read(task_id)
    print(task)
    task.create_scoring()

    ''' now restore stdout function '''
    Logger('OFF')

if __name__== "__main__":
    import sys
    main(sys.argv[1:])
