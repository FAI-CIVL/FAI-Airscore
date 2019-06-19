from logger import myLogger
logfile = 'log.txt'
with myLogger('log', logfile) as redirector:
    print('ciao')

print('ciao mario')
