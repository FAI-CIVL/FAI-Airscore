"""
Test Importing CSV File for Competition
Use: python3 test_csv.py [filename] [optional test]

Antonio Golfari - 2018
"""

import csv
import sys, datetime, os
import lxml.etree as ET
from datetime import date, time, datetime
from operator import itemgetter

def csv_read(filename):
    """Reads csv file and returns a dictionary"""
    reader = dict()
    result = dict()
    with open(filename, 'rt') as f:
        try:
            reader = csv.DictReader(f, delimiter=';')
        except:
            print ("CSV Read Error.")
            sys.exit()
#         for row in reader:
#             print(row)
#             result[row]
        result = list(reader)
    return result


def main():
    """Main module"""
    test = 0
    mycsv = dict()
    """check parameter is good."""
    if len(sys.argv) > 1:
        """Get tasPk"""  
        filename = sys.argv[1]
        if len(sys.argv) > 2:
            """Test Mode""" 
            print('Running in TEST MODE')
            test = 1

        mycsv = csv_read(filename)
        if test == 1:
            print ('Parsed CSV File:')
            print("\n \n")
            for row in mycsv:
                print(row)
    else:
        print('Usage: python test_csv.py <filename> <test>')

if __name__ == "__main__":
    main()
