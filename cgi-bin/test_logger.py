from logger import Logger
logfile = 'log.txt'
# with myLogger('log', logfile) as redirector:
#     print('ciao')

Logger('ON', 'test.txt')
print('Should be in file')

Logger('OFF')
print('ciao mario')
