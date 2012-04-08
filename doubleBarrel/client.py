'''
Created on Mar 9, 2012

@author: mat.facer
'''

import ast
import socket
import config
import logging
import dynasocket

from shotgun_api3 import Shotgun


logger = logging.getLogger('')


class ConnectionError(IOError):pass


class SGClient(object):
    '''
    Attempts to connect to an existing socket using the host and port information.
    It will pass commands through the socket, if the connection is successful. A
    Shotgun object is also required upon initialization so that the security can
    be double checked with the server.
    '''

    def __init__(self, sg, host, port):

        if not isinstance(sg, Shotgun):
            raise ValueError("sg must be a Shotgun object")

        if not isinstance(host, str):
            raise ValueError("host must be a string")

        portThresh = 2000
        if not isinstance(port, int) or port < portThresh:
            raise ValueError("port must be an integer larger than %i" % portThresh)

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
            authData = {config.AUTH_SERVER:self._sg.config.server,
                        config.AUTH_SCRIPT:self._sg.config.script_name,
                        config.AUTH_KEY:self._sg.config.api_key}
            dynasocket.send(self._socket, str(authData))
            # Get back a message as to whether or not we have succeeded.
            msg = dynasocket.recv(self._socket)
            if msg == config.SUCCESS_MSG:
                self._connected = True
            elif msg == config.FAIL_MSG:
                self._connected = False
        except socket.error:
            logger.warning("Could not connect to server -> Host: %s Port: %s" % (self._host, self._port))

        return self._connected

    def sendCommand(self, func, *args, **kwargs):
        '''
        Sends the Shotgun call over to the server to be performed.
        '''

        if not self._connected:
            errorMsg = "client is not connected to a server"
            logger.error(errorMsg)
            raise ConnectionError(errorMsg)
        
        # Assemble our function data and send through the socket.
        funcData = {config.FUNC_NAME:func.__name__,
                    config.ARGS:args,
                    config.KWARGS:kwargs}
        dynasocket.send(self._socket, str(funcData))
        # Receive back the results that the server got from Shotgun
        msg = dynasocket.recv(self._socket)
        return ast.literal_eval(msg)
