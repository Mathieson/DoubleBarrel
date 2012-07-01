'''
Created on 2012-06-17

@author: Mat
'''

import config
import common
from server import DoubleBarrelServer
from threading import Thread


class ServerThread(Thread):
    pass


class ServerManager(object):

    def __init__(self):
        self._servers = []
        self._config = config.MonitorConfig()

        # Create a server from each authKey.
        for serverConfig in self._config.serverConfigs():
            self.addServersFromFile(serverConfig.filepath(), skipAppend=True)

    def servers(self):
        return self._servers

    def addServer(self, filepath, keyName):
        '''
        This will create a DoubleBarrelServer from the serverConfig object it is
        passed. The server will also be started. The server is run in a different
        thread so that we can have multiple servers running at the same time.
        '''

        newServer = DoubleBarrelServer(filepath, keyName)
        self.servers().append(newServer)
        return newServer

    def addServersFromFile(self, filepath, skipAppend=False):
        '''
        Provided a filepath to a Shotgun authentication file, this will create
        a ServerConfig object and the pass it off to the addServer function.
        '''

        serverConfig = config.ServerConfig(filepath)
        if not skipAppend:
            self._config.addServerConfig(serverConfig)
        for keyName in serverConfig.keyNames():
            self.addServer(filepath, keyName)

    def removeServer(self, server):
        '''
        This will remove the server config from the monitor's config and also
        stop any servers that are currently running using its credentials.
        '''

        server.stop()
        serverIndex = self.servers().index(server)
        self.servers().remove(server)
        serverConfig = self._config.serverConfigs()[serverIndex]
        self._config.removeServer(serverConfig)
