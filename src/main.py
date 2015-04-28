#!/usr/bin/env python
#coding=utf-8

import os
import sys
import time
import logging

import redis
import tornado.web
import tornado.ioloop
import tornado.options

import Mongo
import Publish

import PageHandler
import IndexHandler
import LoginHandler
import SocketHandler

logging.basicConfig(
    level   = logging.INFO,
    stream  = sys.stdout,
    datefmt = "%Y-%m-%d %H:%M:%S",
    format  = "[%(levelname)s %(asctime)s %(filename)s %(lineno)s] %(message)s"
)

LOG = logging.getLogger(__name__)

tornado.options.define('port', default=8888, help='run on the given port', type=int)

class Application(tornado.web.Application):

    _redis   = None
    _mongo   = None
    _publish = None

    def __init__(self):
        handlers = [
            (r'/',       IndexHandler.IndexHandler),
            (r'/page',   PageHandler.PageHandler),
            (r'/login',  LoginHandler.LoginHandler),
            (r'/socket', SocketHandler.SocketHandler),
        ]

        settings = {
            'debug'            : True,
            'cookie_secret'    : 'ZyVB9oXwQt8S0R0kRvJ5/bZJc2sWuQLTos6GkHn/todo=',
            'static_path'      : os.path.dirname(__file__) + '/static',
            'template_path'    : os.path.dirname(__file__) + '/tpl',
            'ui_modules'       : {},
            'redis_server'     : {'host' : '127.0.0.1', 'port' : 6379, 'db' : 1},
            'mongo_server'     : {'host' : '127.0.0.1', 'port' : 27017},
            'zookeeper_server' : {'host' : '127.0.0.1', 'port' : 2181, 'root_node' : '/test'},
        }

        self._redis   = redis.Redis(connection_pool=redis.ConnectionPool(**settings['redis_server']))
        self._mongo   = Mongo.Mongo(**settings['mongo_server'])
        self._publish = Publish.Publish(**settings['zookeeper_server'])

        tornado.web.Application.__init__(self, handlers, **settings)

    def get_redis(self):
        return self._redis

    def get_mongo(self):
        return self._mongo

    def get_publish(self):
        return self._publish

if __name__ == '__main__':
    #fixed codec can’t encode
    reload(sys)
    sys.setdefaultencoding('utf-8')

    try:
        os.environ['TZ'] = 'Asia/Shanghai'
        time.tzset()

        tornado.options.parse_command_line()
        Application().listen(tornado.options.options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print 'Interrupt'
    else:
        print 'Exit'
