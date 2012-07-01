'''
Created on Mar 9, 2012

@author: mat.facer
'''

import ast
import socket
import common
import logging
import dynasocket

from shotgun_api3 import Shotgun


logger = logging.getLogger('')
socket.setdefaulttimeout(common.SOCKET_TIMEOUT)


class ConnectionError(IOError):pass


class DoubleBarrelClient(object):
    '''
    Attempts to connect to an existing socket using the host and port information.
    It will pass commands through the socket, if the connection is successful. A
    Shotgun object is also required upon initialization so that the security can
    be double checked with the server.
    '''

    def __init__(self, sg, host, port):

        if not isinstance(sg, Shotgun):
            logMsg = "sg must be a Shotgun object"
            logger.critical(logMsg)
            raise ValueError(logMsg)

        if not isinstance(host, str):
            logMsg = "host must be a string"
            logger.critical(logMsg)
            raise ValueError(logMsg)

        portThresh = 2000
        if not isinstance(port, int) or port < portThresh:
            logMsg = "port must be an integer larger than %i" % portThresh
            logger.critical(logMsg)
            raise ValueError(logMsg)

        self._sg = sg
        self._host = host
        self._port = port

        self._connected = False

    def connect(self):
        '''
        Attempts to connect to the server. Returns whether the connection
        succeeded or not.
        '''

        try:
            # Create a socket and try to connect to a server.
            self._socket = socket.socket()
            self._socket.connect((self._host, self._port))
            # Package our Shotgun auth data to then send to the server.
            authData = {common.AUTH_SERVER:self._sg.config.server,
                        common.AUTH_SCRIPT:self._sg.config.script_name,
                        common.AUTH_KEY:self._sg.config.api_key}
            dynasocket.send(self._socket, str(authData))
            # Get back a message as to whether or not we have succeeded.
            msg = dynasocket.recv(self._socket)
            if msg == common.CONNECT_SUCCESS_MSG:
                self._connected = True
            elif msg == common.CONNECT_FAIL_MSG:
                self._connected = False
        except socket.error:
            logMsg = common.getLogMessage("Could not connect to server", (self._host, self._port))
            logger.warning(logMsg)

        return self._connected

    def sendCommand(self, func, *args, **kwargs):
        '''
        Sends the Shotgun call over to the server to be performed.
        '''

        if not self._connected:
            logMsg = "client is not connected to a server"
            logger.critical(logMsg)
            raise ConnectionError(logMsg)

        # Assemble our function data and send through the socket.
        funcData = {common.FUNC_NAME:func.__name__,
                    common.ARGS:args,
                    common.KWARGS:kwargs}
        dynasocket.send(self._socket, str(funcData))
        # Receive back the results that the server got from Shotgun
        msg = dynasocket.recv(self._socket)
        return ast.literal_eval(msg)
