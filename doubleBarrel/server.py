'''
Created on Mar 9, 2012

@author: mat.facer
'''

import ast
import socket
import select
import threading
import config
import logging
import dynasocket

from shotgun_api3 import Shotgun
from threading import Thread
from copy import copy


logger = logging.getLogger('server')


class SGThread(Thread):
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
        funcName = self._funcData.get(config.FUNC_NAME)
        args = self._funcData.get(config.ARGS)
        kwargs = self._funcData.get(config.KWARGS)

        # Ensure we have a function name and it exists on the Shotgun object.
        if funcName and hasattr(self._sg, funcName):
            func = getattr(self._sg, funcName)
            results = func(*args, **kwargs)
            dynasocket.send(self._socket, str(results))
        else:
            dynasocket.send(self._socket, "None")


class SGServer(object):
    '''
    Opens a socket using the host and port provided. Intended to be used as a
    daemon process. Requires a Shotgun object as well.
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

        self.setMaxThreads(25)

        self._socket = socket.socket()
        self._socket.bind((host, port))
        self._socket.listen(5)

        self._clients = [self._socket]

    def setMaxThreads(self, maxthreads):
        '''
        Sets the maximum number of threads that can run at one time.
        '''

        if not isinstance(maxthreads, int) or maxthreads < 0:
            raise ValueError("maxthreads must be a positive integer")

        self._maxThreads = maxthreads

    def start(self):
        '''
        Starts the server watching for messages. This will receive messages and
        handle them appropriately. Messages are either clients connecting or
        disconnecting, or a Shotgun transaction request coming in from a client.
        '''

        logger.info("Shotgun Server started -> Host: %s Port: %s" % (self._host, self._port))

        while 1:
            # Get all of our sockets that have communications occurring.
            sread, swrite, sexc = select.select(self._clients, [], []) #@UnusedVariable

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
                            logger.info("Message received: %s" % msg)
                            # Convert our message into a dictionary we can use.
                            funcData = ast.literal_eval(msg)
                            while 1:
                                # Loop until we have a free thread available.
                                if threading.activeCount() < self._maxThreads:
                                    SGThread(self._sg, funcData, sock).start()
                                    break
                        else:
                            # If there is no message, our client has disconnected.
                            self.disconnectClient(sock)
                    except:
                        self.disconnectClient(sock)

    def disconnectClient(self, client):
        '''
        Disconnects the client by closing the socket connection and then
        removing it from the list of active clients.
        '''

        remhost, remport = client.getpeername()
        logger.info("Client disconnected -> Host: %s Port: %s" % (remhost, remport))
        client.close()
        self._clients.remove(client)

    def acceptNewClient(self):
        '''
        Connects a new client by accepting its request and then authorizes it.
        If it passes authorization, it will add it to the active clients list so
        we start receiving messages from it.
        '''

        newsock, (remhost, remport) = self._socket.accept() #@UnusedVariable

        # Get our authorization data.
        msg = dynasocket.recv(newsock)
        authData = ast.literal_eval(msg)
        server = authData.get(config.AUTH_SERVER)
        script_name = authData.get(config.AUTH_SCRIPT)
        api_key = authData.get(config.AUTH_KEY)

        # Check that our auth data matches our current Shotgun object.
        if server == self._sg.config.server \
        and script_name == self._sg.config.script_name \
        and api_key == self._sg.config.api_key:
            self._clients.append(newsock)
            logger.info("Client connected -> Host: %s Port: %s" % (remhost, remport))
            dynasocket.send(newsock, config.SUCCESS_MSG)
            return True
        else:
            dynasocket.send(newsock, config.FAIL_MSG)
            newsock.close()
            return False
