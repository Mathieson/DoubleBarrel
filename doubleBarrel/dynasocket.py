'''
Created on 2012-04-07

@author: Mat
'''

DEFAULT_RECV_LENGTH = 2048


def send(sock, message):
    '''
    Sends the message's length, then sends the message.
    '''

    # Send the length of the message first, so the receiver knows how big it will be.
    sock.send(str(len(message)))
    # Wait for confirmation that the message has been received.
    sock.recv(DEFAULT_RECV_LENGTH)
    # Send the actual message.
    sock.send(str(message))


def recv(sock):
    '''
    Receives the message length first, then receives the actual message.
    '''

    # Receive the message using the default receive length.
    messageLength = int(sock.recv(DEFAULT_RECV_LENGTH))
    # Send back confirmation that the message was received.
    sock.send(str(messageLength))
    # Receive and return the actual message, using the proper length.
    return sock.recv(messageLength)
