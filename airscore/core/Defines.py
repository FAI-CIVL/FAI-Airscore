"""
File created from install / settongs
Use: from Defines import BINDIR, TRACKDIR

Antonio Golfari - 2018
"""
import os
import yaml

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
with open('../../defines.yaml', 'rb') as f:
    """use safe_load instead load"""
    config = yaml.safe_load(f)

with open('../../secret.yaml', 'rb') as f:
    """use safe_load instead load"""
    secret = yaml.safe_load(f)
os.chdir(dname)
''' Application Settings'''
FLASKCONTAINER = config['docker']['container']  # Flask Docker Container Name
FLASKPORT = config['docker']['port']  # Flask Docker Container Port
BINDIR = config['dir']['bin']  # script directory
TRACKDIR = config['dir']['tracks']  # track file directory
LOGDIR = config['dir']['log']  # log files directory
RESULTDIR = config['dir']['result']  # log files directory
IMAGEDIR = config['dir']['image']  # image/icon files directory
MAPOBJDIR = config['dir']['map']  # mapobj files directory
AIRSPACEDIR = config['dir']['airspace']  # openair files directory
AIRSPACEMAPDIR = config['dir']['airspace_map']  # airspace map files directory
AIRSPACECHECKDIR = config['dir']['airspace_check']  # airspace check files directory
WAYPOINTDIR = config['dir']['waypoint']  # waypoint files directory
LIVETRACKDIR = config['dir']['livetracking']  # waypoint files directory
IGCPARSINGCONFIG = config['dir']['igc_parsing_config']  # igc parsing config files
TEMPFILES = config['dir']['temp_files']  # tempfile folder when we need one that can be seen by other containers. e.g. workers

''' Track file Settings'''
track_sources = ['xcontest', 'flymaster']     # external available sources for tracks
track_formats = ['igc']   # track accepted formats
'''accepted filename formats
id
name
civl
live
fai
other: other not used
examples: 
    '0068.igc' = 'id' 
    'LiveTrack Antoine Saraf.361951.20190717-113625.5836.47.igc' = 'other name name.live.other-other.other.id' '''
filename_formats = ['id', 'other name name.live.other-other.other.id', 'fai_name', 'name_name',
                    'other name name name.live.other-other.other.id',
                    'other name name name name.live.other-other.other.id',
                    'name_name.other-other.other.id',
                    'name_name.other-other.other.other',
                    'name_name_name.other-other.other.id',
                    'name_name_name_name.other-other.other.id',
                    'other name name.live.other-other.other.other',
                    ]

''' Waypoint file Settings'''
wpt_formats = ['GEO', 'UTM', 'CUP', 'GPX', 'CompeGPS', 'OziExplorer']
ALLOWED_WPT_EXTENSIONS = ['wpt', 'cup', 'gpx', 'ozi']

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

'''pilot DB'''
PILOT_DB = config['use_internal_pilot_DB']
PILOT_DB_WRITE = config['internal_pilot_DB']['write_to_internal_pilot_DB']
SELF_REG_DEFAULT = config['internal_pilot_DB']['self_registration_default']

'''Live Tracking servers'''
FM_LIVE = config['flymaster_live_server']

'''Telegram Bot'''
TELEGRAM_API = secret['telegram']['API']
TELEGRAM_CHANNEL = secret['telegram']['channel']

'''Ladders'''
LADDERS = config['ladders']
