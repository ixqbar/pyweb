#!/usr/bin/env python

import os
import sys
import json
import time
import logging
import subprocess

import kazoo
from kazoo.client import KazooClient

logging.basicConfig(
    level   = logging.INFO,
    stream  = sys.stdout,
    datefmt = "%Y-%m-%d %H:%M:%S",
    format  = "[%(levelname)s %(asctime)s %(filename)s %(lineno)s] %(message)s"
)

LOG = logging.getLogger(__name__)

class mock_syc(object):

    _server_id   = ''
    _root_node   = ''
    _server_list = {}
    _zookeeper   = None
    _shell_path  = ''

    def __init__(self, host = '127.0.0.1', port = 2181, root_node = '/test', shell_path = './'):
        self._zookeeper  = KazooClient('%s:%s' % (host, port,))
        self._root_node  = root_node
        self._shell_path = shell_path

    def run(self):
        self._zookeeper.start()
        self.init()

    def init(self):
        syc_node = '%s/to_syc_notice' % self._root_node
        default_node_value = json.dumps({'update_time' : time.time()})

        try:
            if self._zookeeper.exists(syc_node) is None:
                self._zookeeper.create(syc_node, default_node_value, makepath = True)
        except kazoo.exceptions.NodeExistsError:
            pass

        @self._zookeeper.ChildrenWatch('%s/server_list' % (self._root_node, ))
        def server(server_list):
            for server_node in server_list:
                result = self.init_server(server_node)
                LOG.info('refresh server list %s' % json.dumps(result))

        @self._zookeeper.ChildrenWatch('%s/to_syc_notice' % (self._root_node, ))
        def to_syc_node(syc_node_list):
            for syc_node_id in syc_node_list:
                LOG.info('watch_syc children %s/to_syc_notice/%s' % (self._root_node, syc_node_id, ))
                self.to_syc(syc_node_id)

        return self

    def init_server(self, server_node):
        server_detail = self._zookeeper.get('%s/server_list/%s' % (self._root_node, server_node, ))
        if 0 == len(server_detail[0]):
            self._server_list[server_node] = {'server_id' : 0, 'server_name':'', 'update_time' : 0}
        else:
            self._server_list[server_node] = json.loads(server_detail[0])

        return self._server_list[server_node]

    def to_syc(self, syc_node_id):

        @self._zookeeper.DataWatch('%s/to_syc_notice/%s' % (self._root_node, syc_node_id, ))
        def to_zip_execute(data, stat, event):
            if event is not None and event.type == 'DELETED':
                return

            if 0 == len(data):
                return

            LOG.info('watch_syc execute %s/to_syc_notice/%s %s' % (self._root_node, syc_node_id, data, ))

            node_detail = json.loads(data)
            if node_detail.get('status', None) == 'ok' or \
                            node_detail.get('status', None) == 'failed' or \
                            node_detail.get('servers', None) is None:
                return

            if 0 == len(self._server_id) or \
                        str(self._server_id) not in node_detail['servers']:
                return

            node_value = {
                'update_time' : time.time()
            }

            if self.syc_execute(node_detail['config_version'], node_detail['game_version']) is True:
                LOG.info('syc node %s/to_syc_result/%s/s%s syc success' % (self._root_node, syc_node_id, self._server_id, ))
                node_value['status'] = 'ok'
            else:
                LOG.info('syc node %s/to_syc_result/%s/s%s syc failed' % (self._root_node, syc_node_id, self._server_id, ))
                node_value['status'] = 'failed'

            syc_server_node = '%s/to_syc_result/%s/s%s' % (self._root_node, syc_node_id, self._server_id, )

            try:
                if self._zookeeper.exists(syc_server_node) is None:
                    self._zookeeper.create(syc_server_node, json.dumps(node_value), makepath = True)
                else:
                    self._zookeeper.set(syc_server_node, json.dumps(node_value))
            except kazoo.exceptions.NodeExistsError:
                pass


    def syc_execute(self, config_version, game_version):
        '''
        to execute shell to zip resource
        '''

        LOG.info('start to execute shell %s/syc.sh %s %s %s' % (self._shell_path, config_version, game_version, self._server_id, ))
        result = subprocess.call('%s/syc.sh %s %s %s > /dev/null 2>&1' % (self._shell_path, config_version, game_version, self._server_id, ), shell = True)

        return True if result == 0 else False

if __name__ == '__main__':
    os.environ['TZ'] = 'Asia/Shanghai'
    time.tzset()

    m = mock_syc(
        sys.argv[1] if len(sys.argv) >= 2 else '127.0.0.1',
        sys.argv[2] if len(sys.argv) >= 3 else '2181',
        sys.argv[3] if len(sys.argv) >= 4 else '/test',
        os.path.dirname(sys.argv[0])
    )
    m.run()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass