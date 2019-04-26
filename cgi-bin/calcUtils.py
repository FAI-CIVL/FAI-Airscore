"""
Module for operations on tracks
Use:    import trackUtils
        pilPk = compUtils.get_track_pilot(filename)

Antonio Golfari - 2018
"""

import json
from datetime import date, time, datetime, timedelta

class DateTimeEncoder(json.JSONEncoder):
    """Transfrom DateTme to string for JSON encoding"""
    def default(self, o):
        if isinstance(o, datetime) or isinstance(o, date) or isinstance(o, time):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)

def get_int(str):
    try:
        return int(str)
    except:
        lstr = str.replace('.', ' ').replace('_', ' ').replace('-', ' ').split()
        for i in lstr:
            if i.isdigit():
                return int(i)
        return None

def decimal_to_seconds(time):
    return int(time * 3600)

def time_to_seconds(t):
    h, m, s = [int(i) for i in t.strftime("%H:%M:%S").split(':')]
    return 3600*h + 60*m + s

def datetime_to_seconds(t):
    return (t - t.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()


def decimal_to_time(time):
    hours = int(time)
    minutes = (time*60) % 60
    seconds = (time*3600) % 60
    return ("{:02d}:{02d}:{02d}".format(hours, minutes, seconds))

def time_difference(t1, t2):
    # Create datetime objects for each time (a and b)
    dtA = datetime.combine(date.today(), t1)
    dtB = datetime.combine(date.today(), t2)
    # Get the difference between datetimes (as timedelta)
    diff = dtB - dtA

    return diff

def get_datetime(str, test = 0):
    """
        Transform string in datetime.datetime
    """
    if str is not None:
        return datetime.strptime((str)[:19], '%Y-%m-%dT%H:%M:%S')
    else:
        return str

def epoch_to_date(sec, offset = 0, test = 0):
    """
        Transform string in datetime.datetime
    """
    try:
        return datetime.fromtimestamp(sec).date()
    except TypeError:
        print("an error occurred")
        return sec

def epoch_to_datetime(sec, rawtime = 0, offset = 0, test = 0):
    """
        Transform string in datetime.datetime
    """
    try:
        return datetime.fromtimestamp(sec+rawtime).strftime('%Y-%m-%d %H:%M:%S')
    except TypeError:
        print("an error occurred")
        return sec
def sec_to_time(sec):
    seconds = int(sec)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return time(hour=h, minute=m, second=s)

def sec_to_str(sec, offset = 0, test = 0): #used in design_map.py
    """
        Transform string in datetime.datetime
    """
    try:
        return str(timedelta(seconds=sec+offset*3600))
    except TypeError:
        print ("an error occurred")
    else:
        return sec

# class time_diff(timedelta):
#   """Transfrom DateTme to string for JSON encoding"""
#   def default(self, t1, t2):
#       if isinstance(t1, time) and isinstance(t2, time):
#           return o.isoformat()
#
#       return json.JSONEncoder.default(self, o)
