#!/usr/bin/env python

import os
import sys
import time
import json

import kazoo
from kazoo.client import KazooClient

def test_syc_response(pub_node, server_list, host = '127.0.0.1', port = 2181):
    zookeeper = KazooClient('%s:%s' % (host, port,))
    zookeeper.start()

    for s in server_list:
        if isinstance(s, int) is True:
            continue

        try:
            node = '/test/to_syc_result/%s/%s' % (pub_node, s, )
            if zookeeper.exists(node) is None:
                zookeeper.create(node, json.dumps({
                    'update_time' : time.time(),
                    'status'      : 'ok'
                }), makepath = True)
        except kazoo.exceptions.NodeExistsError:
            pass

if __name__ == '__main__':
    os.environ['TZ'] = 'Asia/Shanghai'
    time.tzset()

    if len(sys.argv) > 2:
        test_syc_response(sys.argv[1], sys.argv[2:])
    else:
        print 'You must usage like %s v{pub_id} s{server_id}' % (sys.argv[0], )