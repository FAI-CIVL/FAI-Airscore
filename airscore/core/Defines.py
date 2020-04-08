"""
File created from install / settongs
Use: from Defines import BINDIR, FILEDIR

Antonio Golfari - 2018
"""
import os

import yaml

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
with open('defines.yaml', 'rb') as f:
    """use safe_load instead load"""
    config = yaml.safe_load(f)

with open('secret.yaml', 'rb') as f:
    """use safe_load instead load"""
    secret = yaml.safe_load(f)

''' Application Settings'''
BINDIR = config['dir']['bin']  # script directory
FILEDIR = config['dir']['file']  # files directory
LOGDIR = config['dir']['log']  # log files directory
RESULTDIR = config['dir']['result']  # log files directory
IMAGEDIR = config['dir']['image']  # image/icon files directory
MAPOBJDIR = config['dir']['map']  # mapobj files directory
AIRSPACEDIR = config['dir']['airspace']  # openair files directory
AIRSPACEMAPDIR = config['dir']['airspace_map']  # openair files directory
AIRSPACECHECKDIR = config['dir']['airspace_check']  # openair files directory
WAYPOINTDIR = config['dir']['waypoint']  # waypoint files directory

track_sources = ['xcontest', 'flymaster']     # external available sources for tracks
track_formats = ['igc']   # track accepted formats
wpt_formats = ['GEO', 'UTM', 'CUP', 'GPX', 'CompeGPS']

''' Database Settings'''
MYSQLUSER = secret['db']['User']  # mysql db user
MYSQLPASSWORD = secret['db']['Pass']  # mysql db password
MYSQLHOST = secret['db']['Server']  # mysql host name
DATABASE = secret['db']['Name']  # mysql db name

''' Other Settings'''
XC_LOGIN = secret['xcontest']['User']
XC_password = secret['xcontest']['Pass']
G_Record_validation_Server = config['g_record_validation_server']

'''Competition options'''
SANCTIONS = config['sanctions']

'''file libraries'''
WAYPOINT_AIRSPACE_FILE_LIBRARY = config['waypoint/airspace_file_library']