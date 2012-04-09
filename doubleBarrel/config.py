'''
Created on Mar 15, 2012

@author: mat.facer
'''

import os
import sys
import logging.handlers


# -----------------------------------------------------------------------------
# Set our global variables
# -----------------------------------------------------------------------------

BUFFER_SIZE = 1024

CONNECT_SUCCESS_MSG = "Connection successful."
CONNECT_FAIL_MSG = "Connection failed."

AUTH_SERVER = 'server'
AUTH_SCRIPT = 'script_name'
AUTH_KEY = 'api_key'

FUNC_NAME = 'funcName'
ARGS = 'args'
KWARGS = 'kwargs'


# -----------------------------------------------------------------------------
# Set up our loggers
# -----------------------------------------------------------------------------
def _screenFormatter():
    return logging.Formatter("%(name)-8s - %(levelname)-12s - %(message)s")


def _fileFormatter():
    return logging.Formatter("%(asctime)-6s - %(name)-10s - %(levelname)-12s - %(message)s")


def _configureRootLogger():
    '''
    This sets up the configuration for our root logger. It should log to the
    screen any messages at INFO level, and then any errors to a log file.
    '''

    # Get the logger object to work with.
    logger = logging.getLogger('')
    logger.setLevel(logging.NOTSET)

    # Create a file handler that will record all of our errors.
    errorFile = os.path.join(os.path.dirname(__file__), "logs/errors.log")
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
    This sets up the configuration for our server logger. It should log all INFO
    level messages to the screen and also to a log file. The log file is named
    the same as the __main__ module. This will allow us to have multiple servers
    running at the same time, providing a log for each.
    '''

    # Configure our server logger.
    logger = logging.getLogger('server')
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Get the name of our main module, as it will be used in the log file name.
    mainModule = sys.modules['__main__']
    baseName = os.path.basename(mainModule.__file__)
    moduleName, ext = os.path.splitext(baseName) #@UnusedVariable

    # Create a file handler that will track everything.
    serverFile = os.path.join(os.path.dirname(__file__),
                              "logs/server/%s.log" % moduleName)
    fileHandler = logging.handlers.RotatingFileHandler(serverFile)
    fileHandler.setLevel(logging.INFO)

    # Create a stream handler for our console that will show errors.
    screenHandler = logging.StreamHandler()
    screenHandler.setLevel(logging.INFO)

    # Set the formatter.
    fileHandler.setFormatter(_fileFormatter())
    screenHandler.setFormatter(_screenFormatter())

    # Add our handlers to our logger.
    logger.addHandler(fileHandler)
    logger.addHandler(screenHandler)


_configureRootLogger()
_configureServerLogger()
