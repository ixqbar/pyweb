#!/usr/bin/env python

import logging
import urlparse

import tornado.websocket

LOG = logging.getLogger(__name__)

class SocketHandler(tornado.websocket.WebSocketHandler):

    client = ''

    def open(self):
        LOG.info('client connected')
        self.write_message('welcome')

    def on_close(self):
        LOG.info('client disconnected')

    def on_message(self, message):
        LOG.info('client post %s' % message)
        self.write_message('reply:' + message)
        if self.client:
            print self.client
        else:
            self.client = message

    def check_origin(self, origin):
        return urlparse.urlparse(origin).netloc.lower() == '127.0.0.1:8888'
