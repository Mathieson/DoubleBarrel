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
    
    def send(self, message):
        '''
        Sends the message's length, then sends the message.
        '''
        
        
    
    def recv(self):
        '''
        Receives the message length, 
        '''