"""
File created from install / settongs
Use: from Defines import BINDIR, TRACKDIR

Antonio Golfari - 2018
"""
import os

import yaml
from environs import Env

env = Env()
env.read_env()

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
with open('../../defines.yaml', 'rb') as f:
    """use safe_load instead load"""
    config = yaml.safe_load(f)

try:
    f = open('../../dev.yaml', 'rb')
    """use safe_load instead load"""
    dev = yaml.safe_load(f)

except IOError:
    dev = {}

os.chdir(dname)
''' Application Settings'''
# FLASKCONTAINER = config['docker']['container']  # Flask Docker Container Name
# FLASKPORT = config['docker']['port']  # Flask Docker Container Port
BINDIR = config['dir']['bin']  # script directory
TRACKDIR = config['dir']['tracks']  # track file directory
LOGDIR = config['dir']['log']  # log files directory
RESULTDIR = config['dir']['result']  # log files directory
IMAGEDIR = config['dir']['image']  # image/icon files directory
EXAMPLEFILEDIR = config['dir']['example_file']  # misc files directory used for downloads (templates, examples, ...)
MAPOBJDIR = config['dir']['map']  # mapobj files directory
AIRSPACEDIR = config['dir']['airspace']  # openair files directory
AIRSPACEMAPDIR = config['dir']['airspace_map']  # airspace map files directory
AIRSPACECHECKDIR = config['dir']['airspace_check']  # airspace check files directory
WAYPOINTDIR = config['dir']['waypoint']  # waypoint files directory
LIVETRACKDIR = config['dir']['livetracking']  # waypoint files directory
IGCPARSINGCONFIG = config['dir']['igc_parsing_config']  # igc parsing config files
TEMPFILES = config['dir']['temp_files']  # tempfile folder when we need one that can be seen by workers

''' Track file Settings'''
track_sources = [s for s in config['igc_sources'] if config['igc_sources'][s]]  # external available sources for tracks
track_formats = ['igc']  # accepted track formats
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
filename_formats = [
    'id',
    'other name name.live.other-other.other.id',
    'fai_name',
    'name_name',
    'name_name_id',
    'name_name_name_id',
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
MYSQLUSER = dev.get('db', {}).get('User') or env.str('MYSQLUSER')  # mysql db user
MYSQLPASSWORD = dev.get('db', {}).get('Pass') or env.str('MYSQLPASSWORD')  # mysql db password
MYSQLHOST = dev.get('db', {}).get('Server') or env.str('MYSQLHOST')  # mysql host name
DATABASE = dev.get('db', {}).get('Name') or env.str('DATABASE')  # mysql db name

''' Other Settings'''
XC_LOGIN = dev.get('xcontest', {}).get('User') or env.str('XCONTEST_USER')
XC_password = dev.get('xcontest', {}).get('Pass') or env.str('XCONTEST_PASS')
G_Record_validation_Server = config['g_record_validation_server']

'''Competition options'''
SANCTIONS = config['sanctions']

'''File libraries'''
WAYPOINT_AIRSPACE_FILE_LIBRARY = config['waypoint/airspace_file_library']

'''Admin DB'''
ADMIN_DB = config['use_internal_admin_DB']
ADMIN_SELF_REG = config['internal_admin_DB']['allow_self_registration']
ADMIN_AUTH_URL = config['external_admin_DB']['auth_url']
ADMIN_AUTH_TYPE = config['external_admin_DB']['auth_type']


'''Pilot DB'''
PILOT_DB = config['use_internal_pilot_DB']
PILOT_DB_WRITE = config['internal_pilot_DB']['write_to_internal_pilot_DB']
SELF_REG_DEFAULT = config['internal_pilot_DB']['self_registration_default']
OPEN_EVENT = config['internal_pilot_DB']['allow_open_event']

'''Live Tracking servers'''
FM_LIVE = config['flymaster_live_server']

'''Telegram Bot'''
TELEGRAM = config['telegram']
TELEGRAM_API = dev.get('telegram', {}).get('API') or env.str('TELEGRAM_API')
TELEGRAM_CHANNEL = dev.get('telegram', {}).get('channel') or env.str('TELEGRAM_CHANNEL')

'''Ladders'''
LADDERS = config['ladders']


'''FAI Sphere'''
FAI_SPHERE = config['FAI_sphere']
