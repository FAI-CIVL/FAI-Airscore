"""
waypoint file reader:

- AirScore -
Stuart Mackintosh - Antonio Golfari
2019

"""
from pprint import pprint as pp


def dms_to_dec(C, d, m, s=0):
    return (float(d) + float(m) / 60 + float(s) / (60 * 60)) * (-1 if C in ['W', 'S'] else 1)


def dm_to_dec(coord):
    C = coord[-1]
    dm = float(coord[0:-1])
    d = int(dm) // 100
    m = dm - 100 * d
    return dms_to_dec(C, d, m)


def get_GEO(lines):
    """get wpts list from waypoints file
    file format:
    D01       N 42 30 53.19    E 12 52 59.38    1206  DECOLLO ALTO
    dump:
    ['D01', 'N', '42', '30', '53.19', 'E', '12', '52', '59.38', '1206', 'DECOLLO', 'ALTO']
    """
    wpts = []
    for line in lines:
        wp = line.split()
        code = str(wp[0])
        lat = dms_to_dec(wp[1], wp[2], wp[3], wp[4])
        lon = dms_to_dec(wp[5], wp[6], wp[7], wp[8])
        alt = int(wp[9])
        desc = ' '.join(wp[10:])
        wpts.append([code, lat, lon, alt, desc])
    return wpts


def get_UTM(lines):
    """get wpts list from waypoints file
    file format:
    B00      32T   0468693   5164352   1440  B00144 ANDERMATT LANDING
    dump:
    ['B00', '32T', '0468693', '5164352', '1440', 'B00144', 'ANDERMATT', 'LANDING']
    """
    from pyproj import Proj
    import re
    wpts = []
    '''create UTM proj'''
    map = re.findall("\d+", lines[0].split()[1])[0]
    myProj = Proj(f"+proj=utm +zone={map} +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
    for line in lines:
        wp = line.split()
        code = str(wp[0])
        lon, lat = myProj(wp[2], wp[3], inverse=True)
        alt = int(wp[4])
        desc = ' '.join(wp[5:])
        wpts.append([code, lat, lon, alt, desc])
    return wpts


def get_CUP(lines):
    """get wpts list from waypoints file
    file format:
    "DEC NORMA 0025",D01,,4135.458N,01257.424E,450.0m,1,,,,
    dump:
    ['T OFF MEDUNO', 'D01', '', '4613.850N', '01248.417E', '980.0m', '1', '', '', '', '']
    """
    import csv

    wpts = []
    reader = csv.reader(lines)
    for row in reader:
        # pp(row)
        desc = row[0]
        code = row[1]
        lat = dm_to_dec(row[3])
        lon = dm_to_dec(row[4])
        alt = int(float(row[5][0:-1]))
        wpts.append([code, lat, lon, alt, desc])
    return wpts


def get_GPX(dump):
    """get wpts list from waypoints file
    file format:
    <wpt lat="46.230833" lon="12.806944">
      <ele>980.0</ele>
      <time>2019-07-12T10:42:58</time>
      <name>D01</name>
      <cmt>T OFF MEDUNO</cmt>
      <desc>T OFF MEDUNO</desc>
      <sym>Dot</sym>
    </wpt>
    dump:
    ['T OFF MEDUNO', 'D01', '', '4613.850N', '01248.417E', '980.0m', '1', '', '', '', '']
    """
    import lxml.etree as ET

    try:
        # pp(dump)
        tree = ET.XML(dump)
    except:
        print("File Read Error.")
        return []
    wpts = []
    for el in tree.xpath('//*[local-name()="wpt"]'):
        desc = el.xpath('.//*[local-name()="desc"]')[0].text
        code = el.xpath('.//*[local-name()="name"]')[0].text
        lat = el.get('lat')
        lon = el.get('lon')
        alt = int(float(el.xpath('.//*[local-name()="ele"]')[0].text))
        wpts.append([code, lat, lon, alt, desc])
    return wpts


def get_CompeGPS(lines):
    """get wpts list from waypoints file
    file format:
    W  A02 A 2.1848190∫S 79.9659330∫W 13-SEP-2017 01:58:10 23.000000 A02 PUERTO AZUL
    w Waypoint,,,,,,,,,
    dump:
    ['W', 'A01', 'A', '46.2678333333ºN', '13.1401666667ºE', '27-MAR-62', '00:00:00', '198.000000', 'GODO', 'LANDING']
    """
    wpts = []
    for line in lines:
        wp = line.split()
        # pp(wp)
        if wp[0] == 'W':
            code = str(wp[1])
            lat = float(wp[3][0:-2]) * (-1 if wp[3][-1] == 'S' else 1)
            lon = float(wp[4][0:-2]) * (-1 if wp[4][-1] == 'W' else 1)
            alt = int(float(wp[7]))
            desc = ' '.join(wp[8:])
            wpts.append([code, lat, lon, alt, desc])
    return wpts


def get_OziExplorer(lines):
    """get wpts list from waypoints file
    file format:
    https://www.oziexplorer4.com/eng/help/fileformats.html
    """
    wpts = []
    for line in lines:
        wp = line.split(',')
        code = str(wp[1])
        lat = float(wp[2][0:-2])
        lon = float(wp[3][0:-2])
        alt = int(float(wp[14])) * 0.3048
        desc = wp[10]
        wpts.append([code, lat, lon, alt, desc])
    return wpts


def get_waypoints_from_file(filename):
    """Reads waypoint file, in different formats:
    - GEO
    - UTM
    - SeeYou CUP
    - GPX
    - CompeGPS
    returns a list of list:
    [code lat lon alt desc]"""

    from pathlib import Path

    if not Path(filename).is_file():
        print(f"error: file {filename} does not exist")
        return []

    '''try to open file in different encodings'''
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            dump = file.read()
            # lines = dump.splitlines()
    except UnicodeDecodeError:
        with open(filename, 'r', encoding='latin-1') as file:
            dump = file.read()
            # lines = dump.splitlines()
    return get_waypoints_from_filedata(dump)


def get_waypoints_from_filedata(filedata: str) -> tuple:
    """Reads wpts from filedata"""
    wpts = []
    file_format = None
    lines = filedata.splitlines()
    try:
        if str(lines[0]).startswith('$FormatGEO'):
            pp('GEO')
            file_format = 'GEO'
            wpts = get_GEO(lines[1:])
        elif str(lines[0]).startswith('$FormatUTM'):
            pp('UTM')
            file_format = 'UTM'
            wpts = get_UTM(lines[1:])
        elif str(lines[0]).startswith(('Title,Code,', 'name,code,')):
            pp('CUP')
            file_format = 'CUP'
            wpts = get_CUP(lines[1:])
        elif str(lines[0]).startswith('<?xml ver'):
            pp('GPX')
            file_format = 'GPX'
            wpts = get_GPX(filedata.encode())
        elif str(lines[0]).startswith('G  WGS 84'):
            pp('CompeGPS')
            file_format = 'CompeGPS'
            wpts = get_CompeGPS(lines[2:])
        elif str(lines[0]).startswith('OziExplorer Waypoint File'):
            pp('OziExplorer')
            file_format = 'OziExplorer'
            wpts = get_OziExplorer(lines[4:])
    except (IndexError, Exception):
        print(f'Error: cannot recognise file format')
        return 'error', None
    print(f'format: {file_format}')

    return file_format, wpts


def get_turnpoints_from_file(filename, data=False):
    """takes a filename or filedata (if data=True)
    Returns a list of Turnpoints objects from waypoint file
    """
    from route import Turnpoint

    if data:
        file_format, wpts = get_waypoints_from_filedata(filename)
    else:
        file_format, wpts = get_waypoints_from_file(filename)
    if not wpts:
        print(f"error: file does not contain any waypoint")
        return None, []
    turnpoints = []
    for wpt in wpts:
        tp = Turnpoint(name=wpt[0], lat=wpt[1], lon=wpt[2], altitude=wpt[3], description=wpt[4])
        turnpoints.append(tp)
    return file_format, turnpoints


def allowed_wpt_extensions(filename):
    from Defines import ALLOWED_WPT_EXTENSIONS

    # We only want files with a . in the filename
    if not "." in filename:
        return False
    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]
    # Check if the extension is in ALLOWED_IMAGE_EXTENSIONS
    if ext.lower() in ALLOWED_WPT_EXTENSIONS:
        return True
    else:
        return False


def get_turnpoints_from_file_storage(file_storage):
    """used in flask frontend"""
    from logger import Logger

    '''try to open file in different encodings'''
    # Logger('ON', 'read_waypoints.txt')
    try:
        file = file_storage.stream.read().decode('UTF-8')
    except UnicodeDecodeError:
        file_storage.stream.seek(0)
        file = file_storage.stream.read().decode('latin-1')
    file_format, wpts = get_turnpoints_from_file(file, data=True)
    # Logger('OFF')
    return file_format, wpts
