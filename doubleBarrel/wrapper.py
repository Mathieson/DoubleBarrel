'''
Created on Mar 12, 2012

@author: mat.facer
'''

import config #@UnusedImport
import logging

from shotgun_api3 import Shotgun
from client import DoubleBarrelClient


logger = logging.getLogger('')


def shotgunInteraction(func):
    '''
    A decorator function that handles whether the command should be sent through
    a socket connection or called on our Shotgun object. It will call the methods
    dynamically.
    '''

    def wrapper(self, *args, **kwargs):

        if self._sgclient:
            # If we have a socket connection, send the command through it.
            return self._sgclient.sendCommand(func, *args, **kwargs)
        else:
            # Otherwise, dynamically get the function from the Shotgun object and then call it.
            funcname = func.__name__
            sgfunc = getattr(Shotgun, funcname)
            return sgfunc(self, *args, **kwargs)

    return wrapper


class DoubleBarrel(Shotgun):
    '''
    This entire class is just a wrapper of the Shotgun API. Each method that
    communicates to the server is decorated with a method that will first check
    to see if we already have a connection available elsewhere on our local
    network. If it finds one, it will create a socket connection and make
    database transactions through that channel instead.
    '''

    def __init__(self, base_url, script_name, api_key, convert_datetimes_to_utc=True,
        http_proxy=None, ensure_ascii=True, connect=True, host=None, port=None):
        '''
        We will initialize the Shotgun object, but will not connect right away.
        Instead, if we have a host and port specified, we will attempt to create
        a socket connection using that data and the Shotgun object. If we do not
        have a host and port specified, or do not find a connection, we will fall
        back and connect to the actual Shotgun server instead.
        '''

        Shotgun.__init__(self, base_url, script_name, api_key,
            convert_datetimes_to_utc=convert_datetimes_to_utc,
            http_proxy=http_proxy, ensure_ascii=ensure_ascii,
            connect=False)

        self._sgclient = None
        # Attempt to open a socket at the host and port.
        if host and port and connect:
            sgclient = DoubleBarrelClient(self, host, port)
            if sgclient.connect():
                self._sgclient = sgclient

        if connect and not self._sgclient:
            self.connect()

    @shotgunInteraction
    def find(self, entity_type, filters, fields=None, order=None,
             filter_operator=None, limit=0, retired_only=False, page=0):pass

    @shotgunInteraction
    def find_one(self, entity_type, filters, fields=None, order=None,
        filter_operator=None, retired_only=False):pass

    @shotgunInteraction
    def create(self, entity_type, data, return_fields=None):pass

    @shotgunInteraction
    def update(self, entity_type, entity_id, data):pass

    @shotgunInteraction
    def delete(self, entity_type, entity_id):pass

    @shotgunInteraction
    def revive(self, entity_type, entity_id):pass

    @shotgunInteraction
    def batch(self, requests):pass

    @shotgunInteraction
    def upload(self, entity_type, entity_id, path, field_name=None,
        display_name=None, tag_list=None):pass

    @shotgunInteraction
    def upload_thumbnail(self, entity_type, entity_id, path, **kwargs):pass

    @shotgunInteraction
    def upload_filmstrip_thumbnail(self, entity_type, entity_id, path, **kwargs):pass

    @shotgunInteraction
    def download_attachment(self, attachment_id):pass

    @shotgunInteraction
    def work_schedule_read(self, start_date, end_date, project=None, user=None):pass

    @shotgunInteraction
    def work_schedule_update(self, date, working, description=None, project=None,
                             user=None, recalculate_field=None):pass

    @shotgunInteraction
    def schema_entity_read(self):pass

    @shotgunInteraction
    def schema_field_create(self, entity_type, data_type,
                            display_name, properties=None):pass

    @shotgunInteraction
    def schema_field_delete(self, entity_type, field_name):pass

    @shotgunInteraction
    def schema_field_read(self, entity_type, field_name=None):pass

    @shotgunInteraction
    def schema_field_update(self, entity_type, field_name, properties):pass

    @shotgunInteraction
    def set_session_uuid(self, session_uuid):pass
