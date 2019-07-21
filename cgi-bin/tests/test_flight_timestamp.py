import datetime
import math
import re


def _strip_non_printable_chars(string):
    """Filters a string removing non-printable characters.

    Args:
        string: A string to be filtered.

    Returns:
        A string, where non-printable characters are removed.
    """
    printable = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKL"
                    "MNOPQRSTUVWXYZ!\"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ ")

    printable_string = [x for x in string if x in printable]
    return ''.join(printable_string)

def main():
    records = ['HFDTEDATE:090319,01', 'HFDTE120316']
    for record in records:
        date_timestamp = 0.0
        if record[0:5] == 'HFDTE':
            match = re.match(
                '(?:HFDTE|HFDTEDATE:)(\d\d)(\d\d)(\d\d)',
                record, flags=re.IGNORECASE)
            if match:
                dd, mm, yy = [_strip_non_printable_chars(group) for group in match.groups()]
                year = int(2000 + int(yy))
                month = int(mm)
                day = int(dd)
                if 1 <= month <= 12 and 1 <= day <= 31:
                    epoch = datetime.datetime(year=1970, month=1, day=1)
                    date = datetime.datetime(year=year, month=month, day=day)
                    date_timestamp = (date - epoch).total_seconds()
        print(date_timestamp)

if __name__== "__main__":
    main()