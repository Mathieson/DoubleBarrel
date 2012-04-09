'''
Created on Mar 21, 2012

@author: mat.facer
'''

import socket
import config

from doubleBarrel.wrapper import DoubleBarrel


def throughServer():
    sg = DoubleBarrel(config.SERVER_PATH, config.SCRIPT_NAME, config.SCRIPT_KEY,
                      host=socket.gethostname(), port=2626)
    results = sg.find('Shot', [])
    print results
    return results


def throughDirect():
    sg = DoubleBarrel(config.SERVER_PATH, config.SCRIPT_NAME, config.SCRIPT_KEY)
    results = sg.find('Shot', [])
    print results
    return results


if __name__ == '__main__':
    from timeit import Timer

    loops = 1000

    t = Timer(throughServer)
    timeTotal = t.timeit(loops)
    print "Time total 1: %s" % str(timeTotal)

    t = Timer(throughDirect)
    timeTotal = t.timeit(loops)
    print "Time total 2: %s" % str(timeTotal)
