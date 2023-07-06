"""
Library that contains calculation methods
Use:    import trackUtils

Antonio Golfari - 2018
"""

import decimal
import json
from datetime import date, datetime, time


class DateTimeEncoder(json.JSONEncoder):
    """Transform DateTme to string for JSON encoding"""

    def default(self, o):
        if isinstance(o, datetime) or isinstance(o, date) or isinstance(o, time):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        elif isinstance(obj, decimal.Decimal):
            return (str(obj) for obj in [obj])
        else:
            return json.JSONEncoder.default(self, obj)


def c_round(x, digits=0, precision=15):
    from decimal import ROUND_HALF_UP, Decimal, getcontext

    round_context = getcontext()
    round_context.rounding = ROUND_HALF_UP
    tmp = round(Decimal(x), precision)
    return float(tmp.__round__(digits)) if digits > 0 else int(tmp.__round__(digits))


def igc_coords(lat: float, lon: float) -> (str, str):
    from math import modf

    NS = 'N' if lat >= 0 else 'S'
    EW = 'E' if lon >= 0 else 'W'
    d, i = modf(abs(lat))
    igclat = f"{str(int(i)).zfill(2)}{str(round(d*60000)).zfill(5)}{NS}"
    d, i = modf(abs(lon))
    igclon = f"{str(int(i)).zfill(3)}{str(round(d*60000)).zfill(5)}{EW}"
    return igclat, igclon


def km(dist: float, n: int = 3):
    """meters to km, with n as number of decimals"""
    try:
        return c_round(dist / 1000, n)
    except ValueError:
        return None


def get_int(string) -> int:
    if isinstance(string, (int, float)):
        return int(string)
    try:
        return int(string)
    except ValueError:
        lstr = string.replace('.', ' ').replace('_', ' ').replace('-', ' ').split()
        for i in lstr:
            if i.isdigit():
                return int(i)
        return 0
    except TypeError:
        return 0


def decimal_to_seconds(d_time):
    return int(d_time * 3600)


def time_to_seconds(t):
    return t.hour * 3600 + t.minute * 60 + t.second


def datetime_to_seconds(t):
    return (t - t.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()


def string_to_seconds(string):
    """gets as input any date time string, with standard time as 14:15:00"""
    import re

    reg = re.compile(r'\d\d:\d\d:\d\d')
    try:
        time_str = reg.findall(string).pop()
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)
    except:
        return None


def decimal_to_time(time):
    hours = int(time)
    minutes = (time * 60) % 60
    seconds = (time * 3600) % 60
    return f'{hours:d}:{minutes:02d}:{seconds:02d}'


def time_difference(t1, t2):
    # Create datetime objects for each time (a and b)
    dtA = datetime.combine(date.today(), t1)
    dtB = datetime.combine(date.today(), t2)
    # Get the difference between datetimes (as timedelta)
    diff = dtB - dtA

    return diff


def get_datetime(t):
    """
    Transform string in datetime.datetime
    """
    try:
        return datetime.strptime(t[:19], '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return t


def get_date(t) -> datetime.date or any:
    """
    Transform string in datetime.date
    Gets first 10 positions in string ('YYYY-mm-dd')
    It should work with any separator
    """
    try:
        d = t[:10]
        s = d[4]
        f = f"%Y{s}%m{s}%d"
        return datetime.strptime(d, f).date()
    except (ValueError, TypeError, IndexError) as e:
        return t


def get_time(t):
    """
    Transform string in datetime.time
    Gets first 19 positions in string ('YYYY-MM-DD hh:mm:ss')
    """
    try:
        return datetime.strptime(t[:19], '%Y-%m-%dT%H:%M:%S').time()
    except ValueError:
        return t


def epoch_to_date(sec, offset=0):
    """
    Transform string in datetime.datetime
    """
    try:
        return datetime.fromtimestamp(sec + offset).date()
    except TypeError:
        print("an error occurred")
        return sec


def epoch_to_datetime(sec, rawtime=0, offset=0):  # offset is not used??
    """
    Transform epoch in datetime.datetime
    """
    try:
        return datetime.fromtimestamp(sec + rawtime + offset)
    except TypeError:
        print("an error occurred")
        return sec


def epoch_to_string(sec, offset=0):
    return epoch_to_datetime(sec, offset).strftime('%Y-%m-%d %H:%M:%S')


def sec_to_time(sec):
    seconds = int(sec)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return time(hour=h, minute=m, second=s)


def sec_to_string(rawtime: int, offset: int = 0, hours=True, seconds=True):
    sec = int(rawtime + offset)
    m, s = divmod(sec, 60)
    if hours:
        h, m = divmod(m, 60)
        string = f"{h:02d}:{m:02d}:{s:02d}"
    else:
        string = f"{m:02d}:{s:02d}"
    return string if seconds else string[:-3]


def sec_to_duration(rawtime):
    sec = int(rawtime)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    string = ''
    if h > 0:
        string += f"{h:02d}h "
    if m > 0:
        string += f"{m:02d}m "
    if s > 0:
        string += f"{s:02d}s"
    return string


def get_isotime(d: datetime.date, t: int, offset=None):
    import datetime as dt
    from datetime import datetime as dd

    tz = dt.timedelta(seconds=offset)
    return dd.combine(d, sec_to_time(t + offset), tzinfo=dt.timezone(offset=tz)).isoformat()


def altitude_compensation(QNH: float):
    """calculates pressure altitude compensation given QNH value:
    FL0MSL[m]=[(QNH[in hPa] – 1013)/12] x 100 – 2
    """
    import math

    if math.isclose(QNH, 1013.25, abs_tol=100) and not math.isclose(QNH, 1013.25, abs_tol=0.01):
        return math.floor((QNH - 1013.25) / 12 * 100 - 2)
    else:
        return 0


def get_season_dates(ladder_id: int, season: int, date_from: datetime.date = None, date_to: datetime.date = None):
    from db.tables import TblLadder as L

    if not (date_from and date_to):
        lad = L.get_by_id(ladder_id)
        date_from, date_to = lad.date_from, lad.date_to
    '''create start and end dates'''
    s = season - 1 if date_from > date_to else season
    starts = datetime.strptime(f"{s}-{date_from.month}-{date_from.day}", '%Y-%m-%d').date()
    ends = datetime.strptime(f"{s+1}-{date_to.month}-{date_to.day}", '%Y-%m-%d').date()
    return starts, ends


''' This are functions used by FSComp to calculate exact pressure altitude.
    I think it is an overkill. Also, I don't think Flight Levels are calculated on ISA values.'''
def CalculateQnhAltitude(pressure: float, qnh: float):
    import math

    if not pressure or not qnh or qnh < 900.0 or qnh > 1100.0:
        return 0
    else:
        return 288.15 / 0.0065 * (1 - math.exp(math.log(pressure / qnh) * 0.190266669078492))


def CalculatePressure(baroAltitude: float):
    import math

    return 1013.25 * math.exp(5.25578129287301 * math.log(1 - 0.0065 * baroAltitude / 288.15))


''' ISA pressure calculation'''
def isa(alt: float):
    """return a 2-uplet (pressure, temperature) depending on provided altitude.
    Units are SI (m, PA, Kelvin)
    considering only altitudes under 11000 meters (troposphere)
    """
    return 1013.25 * (1 - 2.25569e-5 * alt) ** 5.25616


def toBase62(b10: int) -> str or None:
    # modified from Dr. Zhihua Lai's original on GitHub
    from math import floor

    b = 62
    base = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    r = b10 % b
    res = base[r]
    q = floor(b10 / b)
    while q:
        r = q % b
        q = floor(q / b)
        res = base[int(r)] + res
    return res
