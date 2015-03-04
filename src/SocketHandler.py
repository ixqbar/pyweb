#!/usr/bin/env python

import time
import json
import logging
import urlparse

import tornado.websocket

import R
import Session
import Tools

LOG = logging.getLogger(__name__)

class SocketHandler(tornado.websocket.WebSocketHandler):

    _mongo     = None
    _mongo_col = None
    _publish   = None
    _connected = False

    def check_origin(self, origin):
        return urlparse.urlparse(origin).netloc.lower() == '127.0.0.1:8888'

    def open(self):
        LOG.info('client connected %s' % self.request.remote_ip)
        self.session = Session.Session(self)
        self.session.load()
        if self.session.get('name') is None:
            self.close(500, 'not login')
            return

        self._mongo     = self.application.get_mongo()
        self._mongo_col = self._mongo.get().use_collection(R.collection_publish)
        self._publish   = self.application.get_publish()
        self._connected = True

    def on_close(self):
        LOG.info('client disconnected')
        self._connected = False

    def client_response(self, message, executor):
        if self._connected:
            self.write_message(json.dumps({'executor':executor, 'params':message}))
            return True

        LOG.error('client already closed')
        return False

    def client_debug(self, message):
        return self.client_response(message, 'debug')

    def get_server_list(self, executor):
        return self.client_response(self._publish.get_server_list(), executor)

    def on_message(self, message):
        if isinstance(message, str) is False \
                and isinstance(message, unicode) is False:
            self.close(500, 'error message type')
            return

        LOG.info('client post %s' % message)
        self.client_debug(message)

        client_message = json.loads(message)
        client_action  = client_message.get('action', None)
        client_params  = client_message.get('params', dict())
        target_servers = client_params.get('servers').split(',') if len(client_params.get('servers', '')) > 0 else []

        if client_action == 'to_zip':
            self.to_zip(client_params.get('pub_id', 0),\
                        client_params.get('config_version', 0),\
                        client_params.get('game_version', 0), \
                        client_params.get('desc', ''), \
                        client_message.get('callback', ''))
        elif client_action == 'to_syc':
            self.to_syc(client_params.get('pub_id', 0), target_servers, client_message.get('callback', ''))
        elif client_action == 'to_pub':
            self.to_pub(client_params.get('pub_id', 0), target_servers, client_message.get('callback', ''))
        elif client_action == 'servers':
            self.get_server_list(client_message.get('callback', ''))
        else:
            self.client_debug('error action or params')

    def to_zip(self, pub_id, config_version, game_version, desc, executor):
        if pub_id <= 0:
            pub_id = self._mongo.gen_uuid(R.collection_publish)
            self._mongo_col.insert({
                R.mongo_id           : int(pub_id),
                R.pub_config_version : str(config_version),
                R.pub_game_version   : str(game_version),
                R.pub_description    : str(desc),
                R.pub_status         : 'zip',
                R.pub_servers        : [],
                R.pub_time           : Tools.g_time()
            })
            LOG.info('new zip_id=%s' % pub_id)

        self.client_response({'code' : 'ok', 'pub_id' : pub_id, 'status' : 'zip'}, executor)

        def zip_callback(zip_response):
            LOG.info('zip return %s' % zip_response)
            zip_result = json.loads(zip_response)
            if zip_result.get('status', None) == 'ok':
                self._mongo_col.update({
                    R.mongo_id   : int(pub_id),
                    R.pub_status : 'zip'
                }, {'$set' : {R.pub_status : 'zip_success'}})
                self.client_response({'code' : 'ok', 'pub_id' : pub_id, 'status' : 'zip_success'}, executor)
            else:
                self.client_response({'code' : 'ok', 'pub_id' : pub_id, 'status' : 'zip_failed'}, executor)

        ext_data = {
            'config_version' : str(config_version),
            'game_version'   : str(game_version)
        }

        self._publish.to_zip(pub_id, zip_callback, **ext_data)


    def to_syc(self, pub_id, target_servers, executor):
        pub_col_data = self._mongo_col.find_one({R.mongo_id : int(pub_id)})
        if pub_col_data is None:
            self.client_response({'code' : 'err', 'msg' : 'not found pub %s' % pub_id}, executor)
            return

        self._mongo_col.update({
            R.mongo_id : int(pub_id),
        }, {'$set' : {R.pub_status : 'syc', R.pub_servers : target_servers}})

        self.client_response({'code' : 'ok', 'pub_id' : pub_id, 'status' : 'syc'}, executor)

        def syc_process(server_id, syc_response):
            LOG.info('server %s syc finished %s' % (server_id, syc_response, ))
            syc_result = json.loads(syc_response)
            if syc_result.get('status', None) == 'ok':
                self.client_response({'code' : 'ok', 'pub_id' : pub_id, 'status' : 'syc_process', 'server' : server_id}, executor)
            else:
                self.client_response({'code' : 'ok', 'pub_id' : pub_id, 'status' : 'syc_failed', 'server' : server_id}, executor)

        def syc_success():
            LOG.info('syc success')
            self._mongo_col.update({
                R.mongo_id   : int(pub_id),
                R.pub_status : 'syc'
            }, {'$set' : {R.pub_status : 'syc_success'}})
            return self.client_response({'code' : 'ok', 'pub_id' : pub_id, 'status' : 'syc_success'}, executor)

        ext_data = {
            'config_version' : str(pub_col_data[R.pub_config_version]),
            'game_version'   : str(pub_col_data[R.pub_game_version])
        }

        self._publish.to_syc(pub_id, target_servers, syc_process, syc_success, **ext_data)

    def to_pub(self, pub_id, target_servers, executor):
        pub_col_data = self._mongo_col.find_one({R.mongo_id : int(pub_id)})
        if pub_col_data is None:
            self.client_response({'code' : 'err', 'msg' : 'not found pub %s' % pub_id}, executor)
            return

        self.client_response({'code' : 'ok', 'pub_id' : pub_id, 'status' : 'pub'}, executor)

        def pub_process(server_id, pub_response):
            LOG.info('server %s pub finished %s' % (server_id, pub_response, ))
            pub_result = json.loads(pub_response)
            if pub_result.get('status', None) == 'ok':
                self.client_response({'code' : 'ok', 'pub_id' : pub_id, 'status' : 'pub_process', 'server' : server_id}, executor)
            else:
                self.client_response({'code' : 'ok', 'pub_id' : pub_id, 'status' : 'pub_failed', 'server' : server_id}, executor)

        def pub_success():
            LOG.info('syc success')
            self._mongo_col.update({
                R.mongo_id   : int(pub_id),
                R.pub_status : 'syc_success'
            }, {'$set' : {R.pub_status : 'pub_success'}})
            return self.client_response({'code' : 'ok', 'pub_id' : pub_id, 'status' : 'pub_success'}, executor)

        ext_data = {
            'config_version' : str(pub_col_data[R.pub_config_version]),
            'game_version'   : str(pub_col_data[R.pub_game_version])
        }

        self._publish.to_pub(pub_id, target_servers, pub_process, pub_success, **ext_data)