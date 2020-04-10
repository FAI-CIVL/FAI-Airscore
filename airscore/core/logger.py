"""
Defines the log file in which all output are deviated.

Use: logger [mode] [file]

    mode:   ON Filename     stdout deviated to filename
            OFF             stdout back to normal

Antonio Golfari - 2019
"""

import io
import logging
import sys
from os import path as p

import Defines as d


def Logger(mode='ON', name='log.txt'):
    """Main module"""
    if mode == 'ON':
        f = io.StringIO()
        sys.stdout = f
        sys.stderr = f
        log_dir = d.LOGDIR
        file = p.join(log_dir, name)
        logging.basicConfig(filename=file, level=logging.INFO, format='%(asctime)s %(message)s')
        mylogger = logging.getLogger()
        sys.stderr.write = mylogger.error
        sys.stdout.write = mylogger.info
        print(f'LOGGER ON | Filename = {file}')

    elif mode == 'OFF':
        print('LOGGER OFF')
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
