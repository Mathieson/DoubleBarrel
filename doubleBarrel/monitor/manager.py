'''
Created on 2012-06-17

@author: Mat
'''

import config
from doubleBarrel.server import DoubleBarrelServer


class ServerManager(object):

    def __init__(self):
        self._servers = []
        self._config = config.MonitorConfig()
        self._serverThreads = {}

        # Create a server from each authKey.
        for serverConfig in self._config.serverConfigs():
            self.addServersFromFile(serverConfig.filepath(), skipAppend=True)

    def servers(self):
        return self._servers

    def addServer(self, filepath, keyName, start=True):
        '''
        This will create a DoubleBarrelServer from the serverConfig object it is
        passed. The server will also be started. The server is run in a different
        thread so that we can have multiple servers running at the same time.
        '''

        #TODO: Add some checks here before creating duplicate servers. If we create a server that has the same port already in use, it will just result in a crash.
        # Check to make sure that an instance of the server doesn't already exist.
            # If it does already exist, just return None.

        newServer = DoubleBarrelServer(filepath, keyName)
        newServer.daemon = True
        self.servers().append(newServer)

        if start:
            newServer.start()

        return newServer

    def addServersFromFile(self, filepath, skipAppend=False):
        '''
        Provided a filepath to a Shotgun authentication file, this will create
        a ServerConfig object and the pass it off to the addServer function.
        '''

        serverConfig = config.ServerConfig(filepath)
        if not skipAppend:
            self._config.addServerConfig(serverConfig)
        newServers = []
        for keyName in serverConfig.keyNames():
            newServer = self.addServer(filepath, keyName)
            newServers.append(newServer)
        return newServers

    def removeServer(self, server):
        '''
        This will remove the server config from the monitor's config and also
        stop any servers that are currently running using its credentials.
        '''

        self.stopServer(server)

        # Remove the server from the manager.
        serverIndex = self.servers().index(server)
        self.servers().remove(server)

        # Remove the server from the manager's config file so will not show up again in the future.
        serverConfig = self._config.serverConfigs()[serverIndex]
        self._config.removeServer(serverConfig)
