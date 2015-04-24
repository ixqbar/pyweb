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

class mock_zip(object):

    _root_node  = ''
    _zookeeper  = None
    _shell_path = ''

    def __init__(self, host = '127.0.0.1', port = 2181, root_node = '/test', shell_path = './'):
        self._zookeeper  = KazooClient('%s:%s' % (host, port,))
        self._root_node  = root_node
        self._shell_path = shell_path

    def run(self):
        self._zookeeper.start()
        self.init()

    def init(self):
        zip_node = '%s/to_zip_notice' % self._root_node
        default_node_value = json.dumps({'update_time' : time.time()})

        try:
            if self._zookeeper.exists(zip_node) is None:
                self._zookeeper.create(zip_node, default_node_value, makepath = True)
        except kazoo.exceptions.NodeExistsError:
            pass

        @self._zookeeper.ChildrenWatch('%s/to_zip_notice' % (self._root_node, ))
        def to_zip_node(zip_node_list):
            for zip_node_id in zip_node_list:
                LOG.info('watch_zip children %s/to_zip_notice/%s' % (self._root_node, zip_node_id, ))
                self.to_zip(zip_node_id)

        return self

    def to_zip(self, zip_node_id):

        @self._zookeeper.DataWatch('%s/to_zip_notice/%s' % (self._root_node, zip_node_id, ))
        def to_zip_execute(data, stat, event):
            if event is not None and event.type == 'DELETED':
                return

            if 0 == len(data):
                return

            LOG.info('watch_zip execute %s/to_zip_notice/%s %s' % (self._root_node, zip_node_id, data, ))

            node_detail = json.loads(data)
            if node_detail.get('config_version', None) is None or \
                    node_detail.get('game_version', None) is None or \
                    node_detail.get('status', None) == 'ok' or  \
                    node_detail.get('status', None) == 'failed':
                return

            if self.zip_execute(node_detail['config_version'], node_detail['game_version']) is True:
                LOG.info('zip node %s/to_zip_notice/%s zip success' % (self._root_node, zip_node_id, ))
                node_detail['status']      = 'ok'
                node_detail['finish_time'] = time.time()
                self._zookeeper.set('%s/to_zip_notice/%s' % (self._root_node, zip_node_id, ), json.dumps(node_detail))
                self._zookeeper.set('%s/to_zip_result/%s' % (self._root_node, zip_node_id, ), json.dumps({
                    'update_time' : time.time(),
                    'status'      : 'ok'
                }))
            else:
                LOG.info('zip node %s/to_zip_notice/%s zip failed' % (self._root_node, zip_node_id, ))
                self._zookeeper.set('%s/to_zip_result/%s' % (self._root_node, zip_node_id, ), json.dumps({
                    'update_time' : time.time(),
                    'status'      : 'failed'
                }))

    def zip_execute(self, config_version, game_version):
        '''
        to execute shell to zip resource
        '''
        LOG.info('start to execute shell %s/zip.sh %s %s' % (self._shell_path, config_version, game_version, ))
        result = subprocess.call('%s/zip.sh %s %s > /dev/null 2>&1' % (self._shell_path, config_version, game_version, ), shell = True)

        return True if result == 0 else False

if __name__ == '__main__':
    os.environ['TZ'] = 'Asia/Shanghai'
    time.tzset()

    m = mock_zip(
        sys.argv[1] if len(sys.argv) >= 2 else '127.0.0.1',
        sys.argv[2] if len(sys.argv) >= 3 else '2181',
        sys.argv[2] if len(sys.argv) >= 4 else '/test',
        os.path.realpath(os.getcwd())
    )
    m.run()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass