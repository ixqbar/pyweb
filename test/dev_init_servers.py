#!/usr/bin/env python

import os
import sys
import time
import json

import kazoo
from kazoo.client import KazooClient

def test_init_servers(server_id, host = '127.0.0.1', port = 2181):
    zookeeper = KazooClient('%s:%s' % (host, port,))
    zookeeper.start()

    try:
        node = '/test/server_list'
        if zookeeper.exists(node) is None:
            zookeeper.create(node, json.dumps({'update_time' : time.time()}), makepath = True)
    except kazoo.exceptions.NodeExistsError:
        pass

    try:
        node = '/test/server_list/s%s' % server_id
        zookeeper.delete(node)
        zookeeper.create(node, json.dumps({
            'update_time' : time.time(),
            'server_name' : 's%s' % server_id,
            'server_id'   : server_id,
        }), makepath = True)
    except kazoo.exceptions.NodeExistsError:
        pass

if __name__ == '__main__':
    os.environ['TZ'] = 'Asia/Shanghai'
    time.tzset()

    if len(sys.argv) >= 2:
        test_init_servers(str(sys.argv[1]))
    else:
        print 'You must usage like %s name' % (sys.argv[0], )