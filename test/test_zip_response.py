#!/usr/bin/env python

import os
import sys
import time
import json

from kazoo.client import KazooClient

def test_zip_response(pub_node, host = '127.0.0.1', port = 2181):
    zookeeper = KazooClient('%s:%s' % (host, port,))
    zookeeper.start()

    node_value = {
        'status'      : 'ok',
        'create_time' : time.time(),
    }

    if zookeeper.exists('/test/to_zip_result/%s' % pub_node) is not None:
        zookeeper.set('/test/to_zip_result/%s' % pub_node, json.dumps(node_value))
    else:
        print 'Not found node `/test/to_zip_result/%s`' % pub_node

if __name__ == '__main__':
    os.environ['TZ'] = 'Asia/Shanghai'
    time.tzset()

    if len(sys.argv) >= 2:
        test_zip_response(sys.argv[1])
    else:
        print 'You must usage like %s v{pub_id}' % (sys.argv[0], )