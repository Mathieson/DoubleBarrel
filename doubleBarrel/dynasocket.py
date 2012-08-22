'''
Created on 2012-04-07

@author: Mat
'''
import common
import ast
import logging


logger = logging.getLogger('')


MESSAGE_LENGTH_STRING = "msgLen="
CONFIRM_MESSAGE = "Message length received."


def send(sock, message):
    '''
    Sends the message's length, then sends the message.
    '''
    try:
        # Get the message's length.
        msgLen = len(message)

        if msgLen > common.BUFFER_SIZE:
            # Send the message size.
            sock.send(''.join([MESSAGE_LENGTH_STRING, str(msgLen)]))
            # Wait for confirmation that the message was received.
            sock.recv(len(CONFIRM_MESSAGE))

        # Send the actual message.
        sock.send(message)
    except:
        logMsg = common.getLogMessage("Socket is no longer connected", sock)
        logger.error(logMsg)


def recv(sock):
    '''
    Receives the message length first, then receives the actual message.
    '''
    # Receive the message.
    msg = sock.recv(common.BUFFER_SIZE)
    # If it is not a message length, return the message.
    if not msg.startswith(MESSAGE_LENGTH_STRING):
        return msg
    else:
        # Get the proper message length.
        msgLen = ast.literal_eval(msg.split('=')[-1])
        # Send confirmation back.
        sock.send(CONFIRM_MESSAGE)
        # Receive a new message
        return sock.recv(msgLen)
