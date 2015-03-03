#!/usr/bin/env python

import os
import sys
import time
import json

import kazoo
from kazoo.client import KazooClient

def test_init_servers(num, host = '127.0.0.1', port = 2181):
    zookeeper = KazooClient('%s:%s' % (host, port,))
    zookeeper.start()

    try:
        node = '/test/server_list'
        if zookeeper.exists(node) is None:
            zookeeper.create(node, json.dumps({'create_time' : time.time()}), makepath = True)
    except kazoo.exceptions.NodeExistsError:
        pass

    v = 1
    while v <= num:
        try:
            node = '/test/server_list/s%s' % v
            if zookeeper.exists(node) is None:
                zookeeper.create(node, json.dumps({
                    'create_time' : time.time(),
                    'server_name' : 's%s' % v,
                    'server_id'   : v,
                    'versions'    : {}
                }), makepath = True)
        except kazoo.exceptions.NodeExistsError:
            pass
        v += 1

if __name__ == '__main__':
    os.environ['TZ'] = 'Asia/Shanghai'
    time.tzset()

    if len(sys.argv) >= 2:
        test_init_servers(int(sys.argv[1]))
    else:
        print 'You must usage like %s num' % (sys.argv[0], )