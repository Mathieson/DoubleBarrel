'''
Created on Mar 21, 2012

@author: mat.facer
'''

import config
import socket
from doubleBarrel import DoubleBarrelServer


if __name__ == '__main__':
    sg = DoubleBarrelServer(config.SERVER_PATH, config.SCRIPT_NAME, config.SCRIPT_KEY).start()
