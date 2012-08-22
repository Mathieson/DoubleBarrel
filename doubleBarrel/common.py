'''
Created on Mar 15, 2012

@author: mat.facer
'''
import os
import sys
import socket
import string
import logging.handlers


# -----------------------------------------------------------------------------
# Set our global variables
# -----------------------------------------------------------------------------
BUFFER_SIZE = 1024

CONNECT_SUCCESS_MSG = "Connection successful."
CONNECT_FAIL_MSG = "Connection failed."

AUTH_SERVER = 'base_url'
AUTH_SCRIPT = 'script_name'
AUTH_KEY = 'api_key'

FUNC_NAME = 'funcName'
ARGS = 'args'
KWARGS = 'kwargs'

LOGGER_MSG = '%-20s - Host: %-24s - Port: %-8s'

SOCKET_TIMEOUT = 3


# -----------------------------------------------------------------------------
# Common functions shared between the server and client modules.
# -----------------------------------------------------------------------------
def appKeyToPort(appKey):
    '''
    Translates the application key to a port number.
    '''
    minPort = 10000
    maxPort = 65535

    nonHexDigits = ''.join(list(set(string.printable) - set(string.hexdigits)))
    hexAppKey = appKey.translate(None, nonHexDigits)
    appKeyNum = str(int(hexAppKey, 16))

    for index, value in enumerate(appKeyNum): #@UnusedVariable
        possiblePort = int(appKeyNum[index:index + 5])
        if minPort < possiblePort < maxPort:
            return possiblePort


def createUsingShotgunAuthFile(func):
    '''
    Allows a DoubleBarrel server to be started by passing a Shotgun (.sg) file
    instead of the usual args and kwargs. It will get the args and kwargs from
    this file and then call the function.
    '''
    def wrapper(self, *args, **kwargs):

        # If the first argument is not a file, just return the normal function.
        if not os.path.isfile(args[0]):
            return func(self, *args, **kwargs)

        # Store the first arg as our Shotgun file.
        shotgunFile = args[0]

        # Try popping off the keyToUse kwarg. If there are multiple auth keys
        # in the file, this will specify which to use.
        keyToUse = None
        if 'keyToUse' in kwargs:
            keyToUse = kwargs.pop('keyToUse')

        # Get the auth data from the Shotgun file.
        # Import here because importing at the top of the file would create
        # an infinite import loop.
        from monitor.config import ServerConfig
        serverConfig = ServerConfig(shotgunFile)
        authKey = serverConfig.authKey(keyToUse)

        # Override any settings from the file with what the user has provided
        # in kwargs.
        authKey.update(kwargs)

        # Pop the server's URL, script name, and script key from the authKey.
        # These need to be passed as args rather than kwargs.
        serverUrl = authKey.pop(AUTH_SERVER)
        scriptName = authKey.pop(AUTH_SCRIPT)
        scriptKey = authKey.pop(AUTH_KEY)

        return func(self, serverUrl, scriptName, scriptKey, **authKey)
    return wrapper


# -----------------------------------------------------------------------------
# Set up our loggers
# -----------------------------------------------------------------------------
def getLogMessage(header, sock, **kwargs):
    '''
    This will be our main function for generating a log message. Requires a
    message header, a socket, and any additional log messages as keyword
    arguments.
    '''
    if type(sock) == socket.socket:
        host, port = sock.getpeername()
    elif type(sock) == tuple:
        host, port = sock
    else:
        msg = "sock must be a socket or tuple with host and port information"
        raise ValueError(msg)

    host = socket.gethostbyname_ex(host)[0]

    kwargMessages = ['%-10s: %s' % item for item in kwargs.items()]
    return ' - '.join([LOGGER_MSG] + kwargMessages) % (header, host, port)


def _screenFormatter():
    return logging.Formatter("%(name)-8s - %(levelname)-12s - %(message)s")


def _fileFormatter():
    return logging.Formatter("%(asctime)-6s - %(name)-10s - %(levelname)-12s - %(message)s")


def _createDir(path):
    '''
    This creates the directories for where our logs will exist.
    '''
    # If the current directory already exists, our work is done.
    if os.path.exists(path):
        return path

    # If the parent directory does not exist, we must create it.
    parentDir = os.path.dirname(path)
    if not os.path.exists(parentDir):
        os.mkdir(parentDir)

    # Now that the parent directory exists, we can make our current directory.
    os.mkdir(path)


def _configureRootLogger():
    '''
    This sets up the configuration for our root logger. It should log to the
    screen any messages at INFO level, and then any errors to a log file.
    '''
    # Get the logger object to work with.
    logger = logging.getLogger('')
    logger.setLevel(logging.NOTSET)

    # Create a file handler that will record all of our errors.
    errorFile = os.path.join(os.path.dirname(__file__), "logs", "errors.log")
    _createDir(os.path.dirname(errorFile))
    fileHandler = logging.FileHandler(errorFile)
    fileHandler.setLevel(logging.WARNING)

    # Create a stream handler for our console that will show errors.
    screenHandler = logging.StreamHandler()
    screenHandler.setLevel(logging.INFO)

    # Set our formatters for our handlers.
    fileHandler.setFormatter(_fileFormatter())
    screenHandler.setFormatter(_screenFormatter())

    # Add our handlers to our logger.
    logger.addHandler(fileHandler)
    logger.addHandler(screenHandler)


def _configureServerLogger():
    '''
    This sets up the configuration for our server logger. It should log all
    INFO level messages to the screen and also to a log file. The log file is
    named the same as the __main__ module. This will allow us to have
    multiple servers running at the same time, providing a log for each.
    '''
    # Configure our server logger.
    logger = logging.getLogger('server')
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Create a stream handler for our console that will show errors.
    screenHandler = logging.StreamHandler()
    screenHandler.setLevel(logging.INFO)

    # Set the formatter.
    screenHandler.setFormatter(_screenFormatter())

    # Add our handlers to our logger.
    logger.addHandler(screenHandler)


_configureRootLogger()
_configureServerLogger()
