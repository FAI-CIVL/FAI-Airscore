import kml
from track import Track
from calcUtils import *

import sys, datetime, os, lxml, json, geojson
#from aerofiles.igc.reader import Reader
from datetime import date, time, datetime
from pprint import pprint

def main():
    """Main module"""
    test = 0
    text  = dict()
    """check parameter is good."""
    if len(sys.argv) > 1:
        """Get tasPk"""
        track = sys.argv[1]
        if len(sys.argv) > 2:
            """Test Mode"""
            print('Running in TEST MODE')
            test = 1
        """check if traPk or filename"""
        if track.isdigit():
            mytrack = Track.read_db(track)
        else:
            mytrack = Track.read_file(track)
        print ("track imported in object Track() \n")
        print('Fixes: \n')
        for fix in mytrack.flight.fixes:
            print ('{} | {} {} | {}\n'.format(fix.lat, fix.lon, fix.gnss_alt, fix.rawtime))
        print ("file: {} \n".format(mytrack.filename))
        print ("pilot ID: {} \n".format(mytrack.pilPk))
        print ("Glider: {} | cert. {}\n".format(mytrack.glider, mytrack.cert))
        print ("raw date: {} \n".format(mytrack.flight.date_timestamp))
        geojson_file = mytrack.to_geojson()
        pprint(geojson_file)

        #result = mytrack.add()
        #with open(mytrack.filename, 'r', encoding='utf-8') as f:
            #result = kml.Reader().read(f)

        #print("Type: {} \n".format(type(result)))
        #print("vars: {} \n".format(vars(result)))


        #j = json.dumps(result, cls=DateTimeEncoder)

        #with open('json_kml.json', 'wb') as fp:
            #fp.write(j.encode("utf-8"))


if __name__ == "__main__":
    main()
