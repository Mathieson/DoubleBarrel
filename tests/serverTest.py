'''
Created on Mar 21, 2012

@author: mat.facer
'''

import config
import socket
from doubleBarrel import DoubleBarrelServer
from doubleBarrel import DoubleBarrel


if __name__ == '__main__':
    sg = DoubleBarrel(config.SERVER_PATH, config.SCRIPT_NAME, config.SCRIPT_KEY)
    DoubleBarrelServer(sg, socket.gethostname(), 2626).start()
