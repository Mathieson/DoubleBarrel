'''
Created on Mar 21, 2012

@author: mat.facer
'''

import config
import socket
from doubleBarrel.server import SGServer
from doubleBarrel.wrapper import DoubleBarrel


if __name__ == '__main__':
    sg = DoubleBarrel(config.SERVER_PATH, config.SCRIPT_NAME, config.SCRIPT_KEY)
    SGServer(sg, socket.gethostname(), 2626).start()
