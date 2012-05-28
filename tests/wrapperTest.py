'''
Created on Mar 21, 2012

@author: mat.facer
'''

import socket
import config

from doubleBarrel import DoubleBarrel


def viaServer():
    sg = DoubleBarrel(config.SERVER_PATH, config.SCRIPT_NAME, config.SCRIPT_KEY,
                      host=socket.gethostname(), port=2626)
    results = sg.find('Project', [])
    print results
    return results


def viaDirect():
    sg = DoubleBarrel(config.SERVER_PATH, config.SCRIPT_NAME, config.SCRIPT_KEY)
    results = sg.find('Project', [])
    print results
    return results


if __name__ == '__main__':
    from timeit import Timer

    loops = 100

    t = Timer(viaServer)
    timeTotal = t.timeit(loops)
    print "Time total 1: %s" % str(timeTotal)

    t = Timer(viaDirect)
    timeTotal = t.timeit(loops)
    print "Time total 2: %s" % str(timeTotal)
