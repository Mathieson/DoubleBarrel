'''
Created on Mar 9, 2012

@author: mat.facer
'''
#TODO: Implement some sort of maximum number of connections check. If we have reached the maximum number of connections, close the ones that have not been accessed in a long time.
#TODO: Implement a switch for the log. Suspect writing everything to the console and file may slow things down a bit. Is it really necessary? Maybe default to file only and give an option to enable console.

import os
import ast
import socket
import select
import threading
import common
import logging
import dynasocket
from StringIO import StringIO
from shotgun_api3 import Shotgun
from threading import Thread
from copy import copy


socket.setdefaulttimeout(common.SOCKET_TIMEOUT)


def _funcToString(funcName, *args, **kwargs):
    '''
    Provided a function name, arguments, and keyword arguments, this will output
    a string that looks like this function call. This is intended for logging
    purposes only.
    '''
    allArgs = str(args)[1:-1].replace(' ', '').split(',')
    allArgs.extend(['%s=%s' % item for item in kwargs])
    return '%s(%s)' % (funcName, ', '.join(allArgs))


class ShotgunCommandThread(Thread):
    '''
    Allows threaded Shotgun interaction. We are having a queue of transaction
    requests come into the server. It is not efficient to have the queue wait
    on the requests to finish their Shotgun queries before moving on to the next
    item. We need to split the transactions up as soon as they come in so that
    we are not waiting as long.
    '''
    def __init__(self, sg, funcData, sock):

        if not isinstance(sg, Shotgun):
            raise ValueError("sg must be a Shotgun object")

        if not isinstance(funcData, dict):
            raise ValueError("funcData must be a dictionary")

        if not isinstance(sock, socket.socket):
            raise ValueError("sock must be a socket")

        self._logger = logging.getLogger('server.%s' % sg.config.script_name)

        Thread.__init__(self)
        self._sg = copy(sg)  # Make a copy. Risk crashing otherwise.
        self._funcData = funcData
        self._socket = sock

    def run(self):
        '''
        Performs the Shotgun transaction and then sends the results back
        through the socket.
        '''
        # Get our function data from the funcdata dict.
        funcName = self._funcData.get(common.FUNC_NAME)
        args = self._funcData.get(common.ARGS)
        kwargs = self._funcData.get(common.KWARGS)

        results = None
        # Ensure we have a function name and it exists on the Shotgun object.
        if funcName and hasattr(self._sg, funcName):
            queryString = _funcToString(funcName, *args, **kwargs)
            logMsg = common.getLogMessage("Querying Shotgun", self._socket, Query=queryString)
            self._logger.info(logMsg)

            func = getattr(self._sg, funcName)
            results = func(*args, **kwargs)

        logMsg = common.getLogMessage("Sending results", self._socket, Results=results)
        self._logger.info(logMsg)

        dynasocket.send(self._socket, str(results))


class DoubleBarrelServer(Thread):
    '''
    Opens a socket using the host and port provided. Intended to be used as a
    daemon process. Requires a Shotgun object as well.
    '''
    @common.createUsingShotgunAuthFile
    def __init__(self, base_url, script_name, api_key, convert_datetimes_to_utc=True,
        http_proxy=None, ensure_ascii=True, connect=True, host=None, port=None):

        self._configureLogger(script_name)

        Thread.__init__(self)

        # Create the Shotgun object that will be used throughout the server.
        sg = Shotgun(base_url, script_name, api_key, convert_datetimes_to_utc, http_proxy, ensure_ascii, connect)

        host = host or socket.gethostname()
        port = port or common.appKeyToPort(sg.config.api_key)

        if not isinstance(host, str):
            logMsg = "host must be a string"
            self.logger().critical(logMsg)
            raise ValueError(logMsg)

        minPort = 2000
        if not isinstance(port, int) or port < minPort:
            logMsg = "port must be an integer larger than %i" % minPort
            self.logger().critical(logMsg)
            raise ValueError(logMsg)

        self._sg = sg
        self._host = host
        self._port = port

        self.setMaxThreads(25)

        self._socket = socket.socket()
        self._socket.bind((host, port))
        self._socket.listen(5)

        self._clients = [self._socket]

        self._isRunning = False
        self._hasErrored = False
        self._needsReInit = False

    def _configureLogger(self, serverName):
        '''
        Configures a logger for this server instance.
        '''
        # Create a logger specifically for this server name.
        logger = logging.getLogger('server.%s' % serverName)
        # Determine the path for where the log file should be saved.
        serverFile = os.path.join(os.path.dirname(__file__), 'logs', 'server', '%s.log' % serverName)
        # Make sure that directory exists.
        common._createDir(os.path.dirname(serverFile))
        # Create a rotating file handler and set it for the logger.
        fileHandler = logging.handlers.RotatingFileHandler(serverFile)
        fileHandler.setLevel(logging.INFO)
        fileHandler.setFormatter(common._fileFormatter())
        logger.addHandler(fileHandler)

        # Create a stream object and then use it to create a stream handler.
        logStream = StringIO()
        streamHandler = logging.StreamHandler(stream=logStream)
        logger.addHandler(streamHandler)

        # Set the logger object as the server's logger, and the stream as the server's log.
        self._logger = logger
        self._log = logStream

    def shotgunObject(self):
        return self._sg

    def setMaxThreads(self, maxthreads):
        '''
        Sets the maximum number of threads that can run at one time.
        '''
        if not isinstance(maxthreads, int) or maxthreads < 0:
            raise ValueError("maxthreads must be a positive integer")

        self._maxThreads = maxthreads

    def stop(self):
        '''
        Stops the server by setting the _isRunning variable to false. This will
        kill the infinite looping of the server.
        '''
        # Stop the loop
        self._isRunning = False

    def isRunning(self):
        return self._isRunning

    def hasErrored(self):
        return self._hasErrored

    def log(self):
        return self._log

    def logger(self):
        return self._logger

    def run(self):
        '''
        Starts the server watching for messages. This will receive messages and
        handle them appropriately. Messages are either clients connecting or
        disconnecting, or a Shotgun transaction request coming in from a client.
        '''
        self._isRunning = True
        self._needsReInit = True

        logMsg = common.getLogMessage("DoubleBarrel server started", (self._host, self._port))
        self.logger().info(logMsg)

        while self._isRunning:
            # Get all of our sockets that have communications occurring.
            sread, swrite, sexc = select.select(self._clients, [], [], 0.1)   #@UnusedVariable

            for sock in sread:
                # If the signal is coming from the server socket.
                if sock == self._socket:
                    # A client is trying to connect.
                    self.acceptNewClient()
                else:
                    try:
                        # Otherwise, we are receiving a message from the client.
                        msg = dynasocket.recv(sock)
                        if msg:
                            # If we have a message, it is a Shotgun transaction.
                            logMsg = common.getLogMessage("Message received", sock, Message=msg)
                            self.logger().info(logMsg)
                            # Convert our message into a dictionary we can use.
                            funcData = ast.literal_eval(msg)
                            while 1:
                                # Loop until we have a free thread available.
                                if threading.activeCount() < self._maxThreads:
                                    ShotgunCommandThread(self._sg, funcData, sock).start()
                                    break
                        else:
                            # If there is no message, our client has disconnected.
                            self.disconnectClient(sock)
                    except:
                        self._hasErrored = True
                        self.disconnectClient(sock)

        # Kill the socket since we are no longer in the loop.
        logMsg = common.getLogMessage("Stopping server", self._socket)
        self._socket.close()

    def disconnectClient(self, client):
        '''
        Disconnects the client by closing the socket connection and then
        removing it from the list of active clients.
        '''
        logMsg = common.getLogMessage("Client disconnected", client)
        self.logger().info(logMsg)
        client.close()
        self._clients.remove(client)

    def acceptNewClient(self):
        '''
        Connects a new client by accepting its request and then authorizes it.
        If it passes authorization, it will add it to the active clients list so
        we start receiving messages from it.
        '''
        newsock, (host, port) = self._socket.accept() #@UnusedVariable

        # Create a variable to keep track of if we have failed the connection.
        failed = False

        # Get our authorization data.
        msg = dynasocket.recv(newsock)
        if msg:
            authData = ast.literal_eval(msg)
            server = authData.get(common.AUTH_SERVER)
            script_name = authData.get(common.AUTH_SCRIPT)
            api_key = authData.get(common.AUTH_KEY)
        else:
            failed = True

        # Check that our auth data matches our current Shotgun object.
        if server == self._sg.config.server \
        and script_name == self._sg.config.script_name \
        and api_key == self._sg.config.api_key:
            self._clients.append(newsock)
            self.logger().info(common.getLogMessage("Client Connected", newsock))
            dynasocket.send(newsock, common.CONNECT_SUCCESS_MSG)
            return True
        else:
            failed = True

        if failed:
            dynasocket.send(newsock, common.CONNECT_FAIL_MSG)
            newsock.close()
            return False
