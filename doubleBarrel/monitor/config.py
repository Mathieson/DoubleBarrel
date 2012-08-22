'''
Created on 2012-06-20

@author: Mat
'''
import os
from doubleBarrel import common
from ConfigParser import ConfigParser


class MonitorConfig(object):

    SERVER_FILES_SECTION = 'ServerFiles'
    REGISTERED_PORTS_SECTION = 'RegisteredPorts'

    def __init__(self):

        self._configFile = os.path.join(os.path.dirname(__file__), 'config.ini')
        self._config = ConfigParser()
        self._serverConfigs = []
        self.read()
        self._getServerConfigs()

    def read(self):
        '''
        Reads the data in from the config file.
        '''
        if os.path.exists(self._configFile):
            self._config.read(self._configFile)

    def write(self):
        '''
        Writes out the settings to the file.
        '''
        with open(self._configFile, 'wb') as configfile:
            self._config.write(configfile)

    def serverFiles(self):
        '''
        Returns the server names and files in a dictionary.
        '''
        serverFiles = {}
        if self._config.has_section(self.SERVER_FILES_SECTION):
            serverFiles.update((self._config.items(self.SERVER_FILES_SECTION)))
        return serverFiles

    def _getServerConfigs(self):
        '''
        Turns the stored server files into server configs.
        '''
        self._serverConfigs = [ServerConfig(serverFile)
                               for serverFile in self.serverFiles().values()]

    def _addServerConfig(self, serverConfig):
        '''
        Adds a server config object to the stored list.
        '''
        self.serverConfigs().append(serverConfig)

    def serverConfigs(self):
        '''
        Returns the server config this monitor is using.
        '''
        return self._serverConfigs

    def addServerConfig(self, serverConfig):
        '''
        This will add a server file's filepath to the config file.
        '''
        if not self._config.has_section(self.SERVER_FILES_SECTION):
            self._config.add_section(self.SERVER_FILES_SECTION)

        # Collect the script names that exist in the file.
        scriptNames = [authKey.get('script_name')
                       for authKey in serverConfig.authKeys()]

        # Add the file to the list.
        #    The key will be the script name and host url.
        #    The value will be the file path for the auth data.
        self._config.set(self.SERVER_FILES_SECTION,
                         ', '.join(scriptNames),
                         serverConfig.filepath())

        # Write out to the file so the changes are saved.
        self.write()

        # Add the server config to the stored list for the monitor.
        self._addServerConfig(serverConfig)

    def removeServer(self, serverConfig):
        '''
        Removes the serverConfig from the list of servers. This can remove more
        than one server if there have been multiple authKeys set up in a single
        sg file.
        '''
        if not self._config.has_section(self.SERVER_FILES_SECTION):
            return True

        for scriptNames, filepath in self._config.items(self.SERVER_FILES_SECTION):
            if filepath == serverConfig.filepath():
                self._config.remove_option(self.SERVER_FILES_SECTION, scriptNames)

        self.write()

    def addPort(self, port, script):
        pass


class ServerConfig(object):

    #TODO: Override the __eq__ function to make it so the ServerConfigs will match as long as the authKeys match.

    FILE_EXTENSION = '.sg'

    def __init__(self, filepath):

        if not os.path.exists(filepath):
            raise ValueError("Path does not exist.")

        if not os.path.isfile(filepath):
            raise ValueError("Path provided is not a file.")

        if not filepath.endswith(self.FILE_EXTENSION):
            raise ValueError("File is not a valid Shotgun authorization file.")

        self._config = ConfigParser()
        self._configFile = filepath
        self._authKeys = {}

        self.read()

    def filepath(self):
        return self._configFile

    def authKeys(self):
        return self._authKeys.values()

    def authKey(self, keyName):
        '''
        If a keyName is provided, this will return the key from the file stored in that section. If there is only one
        key in the Shotgun file no keyName is necessary and this will return that one and only key. If neither of these
        cases are met a value of None will be returned.
        '''
        # If there is only one authKey, return it.
        if len(self.authKeys()) == 1:
            return self.authKeys()[0]
        else:
            return self._authKeys.get(keyName)

    def keyNames(self):
        '''
        Returns the section names for each key from the INI file.
        '''
        return self._authKeys.keys()

    def read(self):
        '''
        This will read the data in from the file and then return a list of
        ShotgunAuthKey dictionaries with the login data for servers.
        '''
        self._config.read(self._configFile)
        self._authKeys = dict([(key, ShotgunAuthKey(self._config.items(key)))
                          for key in self._config.sections()])


class ShotgunAuthKey(dict):

    def __init__(self, *args, **kwargs):
        '''
        Initializes the dictionary as normal and then performs some sanity checks immediately afterwards.
        '''
        dict.__init__(self, *args, **kwargs)
        self._isValid()

    def _isValid(self):
        '''
        Runs sanity checks to ensure the auth key is valid for Shotgun server generation.
        '''
        for key in (common.AUTH_SERVER, common.AUTH_SCRIPT, common.AUTH_KEY):
            if not self.has_key(key):
                raise ValueError("Required key missing from Shotgun file: %s" % key)
