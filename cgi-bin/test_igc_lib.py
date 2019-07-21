import os,sys

from compUtils import read_formula
from trackUtils import get_pil_track
from calcUtils import sec_to_str
from pprint import pprint

import itertools

#database connections
from myconn import Database

#use Track to get track from DB
from track import Track

import igc_lib as IGC

def main():
    print("starting..")
    """Main module. Takes pilPk and tasPk as parameter"""
#     log_dir = d.LOGDIR
#     print("log setup")
#     logging.basicConfig(filename=log_dir + 'main.log',level=logging.INFO,format='%(asctime)s %(message)s')
    test = 0
    pilot_id = 0
    timestamp = 0.0
    timestamp2 = 0.0
    track = None
    flight = None

    ##check parameter is good.
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
        if len(sys.argv) > 2:
            print ("Test Mode")
            test = 1

    else:
        #logging.error("number of arguments != 1 and/or task_id not a number")
        print("Error, uncorrect arguments type or number.")
        print("usage: python test_igc_lib.py filename <test>")
        exit()

    """create task and track objects"""
    try:
        track = Track.read_file(filename=filename, test=test)
        pilot_id = track.pilPk
        timestamp = track.flight.date_timestamp
    except:
        print('Track Error: ')

    try:
        flight = IGC.Flight.create_from_file(filename)
        timestamp2 = flight.date_timestamp
    except:
        print('Flight Error: ')

    if test:
        print("pil ID: {} ".format(pilot_id))
        print("timestamp: {} ".format(timestamp))
        print("date: {} ".format(track.date))
        print("timestamp from flight: {} ".format(timestamp2))

if __name__== "__main__":
    main()