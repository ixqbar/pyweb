#!/usr/bin/env python

import os
import logging

import redis
import tornado.web
import tornado.ioloop
import tornado.options

import PageHandler
import IndexHandler
import LoginHandler
import SocketHandler


LOG = logging.getLogger(__name__)

tornado.options.define('port', default=8888, help='run on the given port', type=int)

class Application(tornado.web.Application):

    _redisServer = None

    def __init__(self):
        handlers = [
            (r'/',       IndexHandler.IndexHandler),
            (r'/page',   PageHandler.PageHandler),
            (r'/login',  LoginHandler.LoginHandler),
            (r'/socket', SocketHandler.SocketHandler),
        ]

        settings = {
            'debug'         : True,
            'cookie_secret' : 'ZyVB9oXwQt8S0R0kRvJ5/bZJc2sWuQLTos6GkHn/todo=',
            'static_path'   : os.path.dirname(__file__) + '/static',
            'template_path' : os.path.dirname(__file__) + '/tpl',
            'ui_modules'    : {},
            'redis_server'  : {'host':'127.0.0.1', 'port':6379, 'db':1}
        }

        self._redisServer = redis.Redis(connection_pool=redis.ConnectionPool(**settings['redis_server']))

        tornado.web.Application.__init__(self, handlers, **settings)

    def get_redis_server(self):
        return self._redisServer


if __name__ == '__main__':
    try:
        tornado.options.parse_command_line()
        Application().listen(tornado.options.options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print 'Interrupt'
    else:
        print 'Exit'
