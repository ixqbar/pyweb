
import json
import types
import logging

import Tools

import kazoo
from kazoo.client import KazooClient

LOG = logging.getLogger(__name__)

class Publish(object):

    _to_zip_node = dict()
    _to_syc_node = dict()
    _to_pub_node = dict()
    _server_list = dict()
    _root_node   = ''
    _zookeeper   = None

    def __init__(self, host = '127.0.0.1', port = 2181, root_node = '/jzqps'):
        self._root_node = root_node if root_node[0] == '/' else '/jzgps'
        self._zookeeper = KazooClient('%s:%s' % (host, port,))
        self._zookeeper.start()

        default_node = [
            self._root_node,
            self._root_node + '/server_list',
            self._root_node + '/to_zip_notice',
            self._root_node + '/to_zip_result',
            self._root_node + '/to_syc_notice',
            self._root_node + '/to_syc_result',
            self._root_node + '/to_pub_notice',
            self._root_node + '/to_pub_result',
            self._root_node + '/to_rol_notice',
            self._root_node + '/to_rol_result',
        ]

        default_node_value = json.dumps({'create_time' : Tools.g_time()})

        try:
            for node in default_node:
                if self._zookeeper.exists(node) is None:
                    self._zookeeper.create(node, default_node_value, makepath = True)
        except kazoo.exceptions.NodeExistsError:
            pass

        self.init()

    def init(self):

        @self._zookeeper.ChildrenWatch('%s/server_list' % (self._root_node, ))
        def server(server_list):
            for server_node in server_list:
                if self._server_list.get(server_node, None) is None:
                    result = self.init_server(server_node)
                    LOG.info('refresh server list %s' % json.dumps(result))

        return self

    def init_server(self, server_node):
        server_detail = self._zookeeper.get('%s/server_list/%s' % (self._root_node, server_node, ))
        if len(server_detail[0]) == 0:
            self._server_list[server_node] = {'server_id' : 0, 'server_name':'', 'create_time':0, 'versions':{}}
        else:
            self._server_list[server_node] = json.loads(server_detail[0])

        return self._server_list[server_node]

    def get_pub_node_id(self, pub_id):
        return 'v%s' % pub_id

    def get_server_list(self):
        return self._server_list

    def to_zip(self, pub_id, zip_success_callback = None, **ext_data):
        pub_node_id = self.get_pub_node_id(pub_id)

        ext_data['pub_id']      = pub_id
        ext_data['pub_node_id'] = pub_node_id
        ext_data['create_time'] = Tools.g_time()

        try:
            if self._zookeeper.exists(self._root_node + '/to_zip_notice/' + pub_node_id) is None:
                self._zookeeper.create(self._root_node + '/to_zip_notice/' + pub_node_id, json.dumps(ext_data), makepath = True)

            if self._zookeeper.exists(self._root_node + '/to_zip_result/' + pub_node_id) is None:
                self._zookeeper.create(self._root_node + '/to_zip_result/' + pub_node_id, '{}', makepath = True)
        except kazoo.exceptions.NodeExistsError:
            pass


        if self._to_zip_node.get(pub_node_id, None) is None:
            self._to_zip_node[pub_node_id] = [zip_success_callback]
            self.zip_notice(pub_id, pub_node_id)
        else:
            self._to_zip_node[pub_node_id].append(zip_success_callback)

        return self

    def zip_notice(self, pub_id, pub_node_id):

        @self._zookeeper.DataWatch('%s/to_zip_result/%s' % (self._root_node, pub_node_id, ))
        def to_zip_notice(data, stat, event):
            if event is None \
                    or event.type == 'CREATED' \
                    or event.type == 'DELETED':
                return

            LOG.info('%s/to_zip_result/%s changed %s' % (self._root_node, pub_id, data, ))

            for zip_success_callback in self._to_zip_node[pub_node_id]:
                if hasattr(zip_success_callback, '__call__') \
                        or isinstance(zip_success_callback, types.FunctionType):
                    zip_success_callback(data)
                del self._to_zip_node[pub_node_id]

        return self

    def to_syc(self, pub_id, target_servers, syc_process_callback=None, syc_success_callback = None, **ext_data):
        pub_node_id = self.get_pub_node_id(pub_id)

        ext_data['pub_id']      = pub_id
        ext_data['pub_node_id'] = pub_node_id
        ext_data['create_time'] = Tools.g_time()
        ext_data['servers']     = target_servers

        try:
            if self._zookeeper.exists(self._root_node + '/to_syc_notice/' + pub_node_id) is None:
                self._zookeeper.create(self._root_node + '/to_syc_notice/' + pub_node_id, json.dumps(ext_data), makepath = True)

            if self._zookeeper.exists(self._root_node + '/to_syc_result/' + pub_node_id) is None:
                self._zookeeper.create(self._root_node + '/to_syc_result/' + pub_node_id, '{}', makepath = True)
        except kazoo.exceptions.NodeExistsError:
            pass

        if self._to_syc_node.get(pub_node_id, None) is None:
            self._to_syc_node[pub_node_id] = [[syc_process_callback, syc_success_callback]]
            self.syc_notice(pub_id, pub_node_id, target_servers)
        else:
            self._to_syc_node[pub_node_id].append([syc_process_callback, syc_success_callback])

        return self

    def syc_notice(self, pub_id, pub_node_id, target_servers):
        already_finished_syc_server_list = {}

        @self._zookeeper.ChildrenWatch('%s/to_syc_result/%s' % (self._root_node, pub_node_id, ))
        def to_syc_process(server_list):
            for server_node in server_list:
                if self._server_list.get(server_node, None) is None:
                    self.init_server(server_node)

                if self._server_list[server_node].get('versions', None) is None:
                    self._server_list[server_node]['versions'] = dict()

                if self._server_list[server_node]['versions'].get(pub_node_id, None) is None:
                    self._server_list[server_node]['versions'][pub_node_id] = ''

                if already_finished_syc_server_list.get(server_node, None) is not None:
                    continue

                syc_result = self._zookeeper.get('%s/to_syc_result/%s/%s' % (self._root_node, pub_node_id, server_node, ))
                if len(syc_result[0]) == 0:
                    LOG.error('syc children %s got zero response' % server_node)
                    continue

                LOG.info('syc children changed %s' % syc_result[0])

                syc_detail = json.loads(syc_result[0])
                if isinstance(syc_detail, dict) == False or \
                                syc_detail.get('create_time', None) is None:
                    continue

                already_finished_syc_server_list[server_node] = syc_result
                self._server_list[server_node]['versions'][pub_node_id] = True

                LOG.info('server list %s' % json.dumps(self._server_list))

                for callback in self._to_syc_node[pub_node_id]:
                    if hasattr(callback[0], '__call__') \
                            or isinstance(callback[0], types.FunctionType):
                        callback[0](server_node, syc_result[0])

            all_syc_finished = True if len(self._server_list) > 0 else False

            for server_id in target_servers:
                server_node = 's%s' % server_id
                if self._server_list.get(server_node, None) is None or \
                        self._server_list[server_node]['versions'].get(pub_node_id, None) is None:
                    all_syc_finished = False
                    break

            if all_syc_finished:
                for callback in self._to_syc_node[pub_node_id]:
                    if hasattr(callback[1], '__call__') \
                            or isinstance(callback[0], types.FunctionType):
                        callback[1]()

                for server_node in self._server_list:
                    if self._server_list[server_node]['versions'].get(pub_node_id, None) is not None:
                        del(self._server_list[server_node]['versions'][pub_node_id])

                del(self._to_syc_node[pub_node_id])

                already_finished_syc_server_list.clear()

                self._zookeeper.set('%s/to_syc_result/%s' % (self._root_node, pub_node_id, ), json.dumps({
                    'create_time' : Tools.g_time(),
                    'status'      : 'ok'
                }))

        return self

    def to_pub(self, pub_id, target_servers, pub_process_callback=None, pub_success_callback = None, **ext_data):
        pub_node_id = self.get_pub_node_id(pub_id)

        ext_data['pub_id']      = pub_id
        ext_data['pub_node_id'] = pub_node_id
        ext_data['create_time'] = Tools.g_time()
        ext_data['servers']     = target_servers

        try:
            if self._zookeeper.exists(self._root_node + '/to_pub_notice/' + pub_node_id) is None:
                self._zookeeper.create(self._root_node + '/to_pub_notice/' + pub_node_id, json.dumps(ext_data), makepath = True)

            if self._zookeeper.exists(self._root_node + '/to_pub_result/' + pub_node_id) is None:
                self._zookeeper.create(self._root_node + '/to_pub_result/' + pub_node_id, '{}', makepath = True)
        except kazoo.exceptions.NodeExistsError:
            pass

        if self._to_pub_node.get(pub_node_id, None) is None:
            self._to_pub_node[pub_node_id] = [[pub_process_callback, pub_success_callback]]
            self.pub_notice(pub_id, pub_node_id, target_servers)
        else:
            self._to_pub_node[pub_node_id].append([pub_process_callback, pub_success_callback])

        return self

    def pub_notice(self, pub_id, pub_node_id, target_servers):
        already_finished_pub_server_list = {}

        @self._zookeeper.ChildrenWatch('%s/to_pub_result/%s' % (self._root_node, pub_node_id, ))
        def to_syc_process(server_list):
            for server_node in server_list:
                if self._server_list.get(server_node, None) is None:
                    self.init_server(server_node)

                if self._server_list[server_node].get('versions', None) is None:
                    self._server_list[server_node]['versions'] = dict()

                if self._server_list[server_node]['versions'].get(pub_node_id, None) is None:
                    self._server_list[server_node]['versions'][pub_node_id] = ''

                if already_finished_pub_server_list.get(server_node, None) is not None:
                    continue

                pub_result = self._zookeeper.get('%s/to_pub_result/%s/%s' % (self._root_node, pub_node_id, server_node, ))
                if len(pub_result[0]) == 0:
                    LOG.error('pub children %s got zero response' % server_node)
                    continue

                LOG.info('pub children changed %s' % pub_result[0])

                pub_detail = json.loads(pub_result[0])
                if isinstance(pub_detail, dict) == False or \
                                pub_detail.get('create_time', None) is None:
                    continue

                already_finished_pub_server_list[server_node]           = pub_detail
                self._server_list[server_node]['versions'][pub_node_id] = True

                LOG.info('server list %s' % json.dumps(self._server_list))

                for callback in self._to_pub_node[pub_node_id]:
                    if hasattr(callback[0], '__call__') \
                            or isinstance(callback[0], types.FunctionType):
                        callback[0](server_node, pub_result[0])

            all_pub_finished = True if len(self._server_list) > 0 else False

            for server_id in target_servers:
                server_node = 's%s' % server_id
                if self._server_list.get(server_node, None) is None or \
                        self._server_list[server_node]['versions'].get(pub_node_id, None) is None:
                    all_pub_finished = False
                    break

            if all_pub_finished:
                for callback in self._to_pub_node[pub_node_id]:
                    if hasattr(callback[1], '__call__') \
                            or isinstance(callback[0], types.FunctionType):
                        callback[1]()

                for server_node in self._server_list:
                    if self._server_list[server_node]['versions'].get(pub_node_id, None) is not None:
                        del(self._server_list[server_node]['versions'][pub_node_id])

                del(self._to_pub_node[pub_node_id])

                already_finished_pub_server_list.clear()

                self._zookeeper.set('%s/to_pub_result/%s' % (self._root_node, pub_node_id, ), json.dumps({
                    'create_time' : Tools.g_time(),
                    'status'      : 'ok'
                }))

        return self