'''
Created on 2012-04-07

@author: Mat
'''

import socket


class DynaSocket(socket.socket):
    '''
    This is essentially the same as a regular socket, but it sends messages in
    a dynamic manner. Receive length is no longer required and is calculated
    dynamically by the send and recv functions.
    '''

    _defaultRecvLength = 12

    def send(self, message):
        '''
        Sends the message's length, then sends the message.
        '''

        # Send the length of the message first, so the receiver knows how big it will be.
        socket.socket.send(self, str(len(message)))
        # Wait for confirmation that the message has been received.
        socket.socket.recv(self, self._defaultRecvLength)
        # Send the actual message.
        socket.socket.send(self, str(message))

    def recv(self):
        '''
        Receives the message length first, then receives the actual message.
        '''

        # Receive the message using the default receive length.
        messageLength = int(socket.socket.recv(self, self._defaultRecvLength))
        # Send back confirmation that the message was received.
        socket.socket.send(self, str(messageLength))
        # Receive and return the actual message, using the proper length.
        return socket.socket.recv(self, messageLength)
