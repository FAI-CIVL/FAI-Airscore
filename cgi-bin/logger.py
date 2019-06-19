"""
Defines the log file in which all output are deviated.

Use: logger [mode] [file]

    mode:   ON Filename     stdout deviated to filename
            OFF             stdout back to normal

Antonio Golfari - 2019
"""

import io, sys, logging, contextlib
from os import path as p
import Defines as d

# def Logger(mode='ON', name='log.txt'):
#     """Main module"""
#     if mode == 'ON':
#         log_dir = d.LOGDIR
#         file    = p.join(log_dir, name)
#         logging.basicConfig(filename=file,level=logging.INFO,format='%(asctime)s %(message)s')
#         mylogger = logging.getLogger()
#         sys.stderr.write = mylogger.error
#         sys.stdout.write = mylogger.info
#         print('LOGGER ON | Filename = {}'.format(file))
#
#     elif mode == 'OFF':
#         print('LOGGER OFF')
#         sys.stdout.close()
#         sys.stderr.close()
#         sys.stdout = sys.__stdout__
#         sys.stderr = sys.__stderr__


class myLogger:
    def __init__(self, name='root', file='log.txt', level='INFO'):
        self.logger = logging.getLogger(name)
        self.name = self.logger.name
        self.level = getattr(logging, level)
        self.path = d.LOGDIR

        fileHandler = logging.FileHandler(p.join(self.path, file), mode='w')
        fileHandler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s  %(levelname)s: %(message)s')
        fileHandler.setFormatter(formatter)
        self.logger.addHandler(fileHandler)
        self._redirector = contextlib.redirect_stdout(self)


    def write(self, msg):
        if msg and not msg.isspace():
            self.logger.log(self.level, msg)

    def flush(self): pass

    def __enter__(self):
        self._redirector.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # let contextlib do any exception handling here
        self._redirector.__exit__(exc_type, exc_value, traceback)
