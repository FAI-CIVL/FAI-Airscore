"""
Module for operations on tracks
Use:    import trackUtils
        pilPk = compUtils.get_track_pilot(filename)
        
Antonio Golfari - 2018
"""

# Use your utility module.
import kml
from myconn import Database
from calcUtils import *

import sys, os, aerofiles, json
from datetime import date, time, datetime

class Formula():
    """
    Create an object Track and
    a collection of functions to handle tracks.
    
    var: filename, pilot
    """
    def __init__(self, filename = None, pilot = None, task = None, glider = None, cert = None, type = None, test = 0):
        self.type = type
        self.pilPk = pilot
        self.tasPk = task
        self.glider = glider
        self.cert = cert

