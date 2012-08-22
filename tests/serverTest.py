'''
Created on Mar 21, 2012

@author: mat.facer
'''
import os
from doubleBarrel import DoubleBarrelServer


if __name__ == '__main__':
    dirPath = os.path.dirname(__file__)
    sgFile = os.path.join(dirPath, 'myShotgunScript.sg')
    sg = DoubleBarrelServer(sgFile).run()
