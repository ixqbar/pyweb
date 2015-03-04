
import json
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
                result = self.init_server(server_node)
                LOG.info('refresh server list %s' % json.dumps(result))

        return self

    def init_server(self, server_node):
        server_detail = self._zookeeper.get('%s/server_list/%s' % (self._root_node, server_node, ))
        if 0 == len(server_detail[0]):
            self._server_list[server_node] = {'server_id' : 0, 'server_name':'', 'create_time':0}
        else:
            self._server_list[server_node] = json.loads(server_detail[0])

        return self._server_list[server_node]

    def get_pub_node_id(self, pub_id):
        return 'v%s' % pub_id

    def get_server_list(self):
        server_list = []
        if len(self._server_list):
            for s in sorted(self._server_list):
                server_list.append(self._server_list[s])

        return server_list

    def to_zip(self, pub_id, zip_callback = None, **ext_data):
        pub_node_id = self.get_pub_node_id(pub_id)

        ext_data['pub_id']      = pub_id
        ext_data['pub_node_id'] = pub_node_id
        ext_data['create_time'] = Tools.g_time()

        try:
            if self._zookeeper.exists(self._root_node + '/to_zip_notice/' + pub_node_id) is None:
                self._zookeeper.create(self._root_node + '/to_zip_notice/' + pub_node_id, json.dumps(ext_data), makepath = True)
            else:
                self._zookeeper.set(self._root_node + '/to_zip_notice/' + pub_node_id, json.dumps(ext_data))

            if self._zookeeper.exists(self._root_node + '/to_zip_result/' + pub_node_id) is None:
                self._zookeeper.create(self._root_node + '/to_zip_result/' + pub_node_id, '', makepath = True)
            else:
                self._zookeeper.set(self._root_node + '/to_zip_result/' + pub_node_id, '')

        except kazoo.exceptions.NodeExistsError:
            pass

        if self._to_zip_node.get(pub_node_id, None) is None:
            self._to_zip_node[pub_node_id] = [zip_callback]
            self.zip_notice(pub_id, pub_node_id)
        else:
            self._to_zip_node[pub_node_id].append(zip_callback)

        return self

    def zip_notice(self, pub_id, pub_node_id):

        @self._zookeeper.DataWatch('%s/to_zip_result/%s' % (self._root_node, pub_node_id, ))
        def to_zip_notice(data, stat, event):
            if 0 == len(data) or \
                    event is None \
                    or event.type == 'CREATED' \
                    or event.type == 'DELETED':
                return

            LOG.info('%s/to_zip_result/%s changed %s' % (self._root_node, pub_node_id, data, ))

            for zip_callback in self._to_zip_node[pub_node_id]:
                zip_callback(data)
                self._to_zip_node[pub_node_id] = []

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
            else:
                self._zookeeper.set(self._root_node + '/to_syc_notice/' + pub_node_id, json.dumps(ext_data))

            if self._zookeeper.exists(self._root_node + '/to_syc_result/' + pub_node_id) is None:
                self._zookeeper.create(self._root_node + '/to_syc_result/' + pub_node_id, '', makepath = True)
            else:
                self._zookeeper.set(self._root_node + '/to_syc_result/' + pub_node_id, '')

            for target_server_id in target_servers:
                target_node = self._root_node + '/to_syc_result/' + pub_node_id + '/s' + str(target_server_id)
                if self._zookeeper.exists(target_node) is not None:
                    self._zookeeper.delete(target_node)

        except kazoo.exceptions.NodeExistsError:
            pass

        if self._to_syc_node.get(pub_node_id, None) is None:
            self._to_syc_node[pub_node_id] = {
                'callback' : [syc_process_callback, syc_success_callback],
                'servers'  : target_servers,
                'notices'  : [],
                'results'  : {}
            }
            self.syc_children_notice(pub_id, pub_node_id)
        else :
            self._to_syc_node[pub_node_id]['callback'] = [syc_process_callback, syc_success_callback]
            self._to_syc_node[pub_node_id]['servers']  = target_servers
            self._to_syc_node[pub_node_id]['results']  = {}

        return self

    def syc_children_notice(self, pub_id, pub_node_id):

        @self._zookeeper.ChildrenWatch('%s/to_syc_result/%s' % (self._root_node, pub_node_id, ))
        def to_syc_process(server_list):
            for server_node in server_list:
                if server_node not in self._to_syc_node[pub_node_id]['notices']:
                    self._to_syc_node[pub_node_id]['notices'].append(server_node)
                    self.syc_process_notice(pub_id, pub_node_id, server_node)

        return self

    def syc_process_notice(self, pub_id, pub_node_id, server_node):
        syc_server_node = '%s/to_syc_result/%s/%s' % (self._root_node, pub_node_id, server_node, )

        @self._zookeeper.DataWatch(syc_server_node)
        def to_syc_process(data, stat, event):
            if event is not None and event.type == 'DELETED':
                return

            if 0 == len(data):
                return

            LOG.info('syc children %s %s' % (syc_server_node, data, ))

            syc_detail = json.loads(data)
            if isinstance(syc_detail, dict) == False or \
                            syc_detail.get('create_time', None) is None or \
                            syc_detail.get('status', None) is None:
                return

            if syc_detail['status'] == 'ok':
                self._to_syc_node[pub_node_id]['results'][server_node] = True
            else:
                self._to_syc_node[pub_node_id]['results'][server_node] = False

            self._to_syc_node[pub_node_id]['callback'][0](server_node, data)

            all_syc_finished = True if len(self._to_syc_node[pub_node_id]['servers']) > 0 else False
            for server_id in self._to_syc_node[pub_node_id]['servers']:
                target_server_node = 's%s' % server_id
                if self._to_syc_node[pub_node_id]['results'].get(target_server_node, False) is False:
                    all_syc_finished = False
                    break

            if all_syc_finished:
                self._to_syc_node[pub_node_id]['callback'][1]()

                self._to_syc_node[pub_node_id]['callback'] = []
                self._to_syc_node[pub_node_id]['results']  = {}

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
            else:
                self._zookeeper.set(self._root_node + '/to_pub_notice/' + pub_node_id, json.dumps(ext_data))

            if self._zookeeper.exists(self._root_node + '/to_pub_result/' + pub_node_id) is None:
                self._zookeeper.create(self._root_node + '/to_pub_result/' + pub_node_id, '', makepath = True)
            else:
                self._zookeeper.set(self._root_node + '/to_pub_result/' + pub_node_id, '')

            for target_server_id in target_servers:
                target_node = self._root_node + '/to_pub_result/' + pub_node_id + '/s' + str(target_server_id)
                if self._zookeeper.exists(target_node) is not None:
                    self._zookeeper.delete(target_node)

        except kazoo.exceptions.NodeExistsError:
            pass

        if self._to_pub_node.get(pub_node_id, None) is None:
            self._to_pub_node[pub_node_id] = {
                'callback' : [pub_process_callback, pub_success_callback],
                'servers'  : target_servers,
                'notices'  : [],
                'results'  : {}
            }
            self.pub_children_notice(pub_id, pub_node_id)
        else :
            self._to_pub_node[pub_node_id]['callback'] = [pub_process_callback, pub_success_callback]
            self._to_pub_node[pub_node_id]['servers']  = target_servers
            self._to_pub_node[pub_node_id]['results']  = {}

        return self

    def pub_children_notice(self, pub_id, pub_node_id):

        @self._zookeeper.ChildrenWatch('%s/to_pub_result/%s' % (self._root_node, pub_node_id, ))
        def to_pub_process(server_list):
            for server_node in server_list:
                if server_node not in self._to_pub_node[pub_node_id]['notices']:
                    self._to_pub_node[pub_node_id]['notices'].append(server_node)
                    self.pub_process_notice(pub_id, pub_node_id, server_node)

        return self

    def pub_process_notice(self, pub_id, pub_node_id, server_node):
        pub_server_node = '%s/to_pub_result/%s/%s' % (self._root_node, pub_node_id, server_node, )

        @self._zookeeper.DataWatch(pub_server_node)
        def to_pub_process(data, stat, event):
            if event is not None and event.type == 'DELETED':
                return

            if 0 == len(data):
                return

            LOG.info('pub children %s %s' % (pub_server_node, data, ))

            pub_detail = json.loads(data)
            if isinstance(pub_detail, dict) == False or \
                            pub_detail.get('create_time', None) is None or \
                            pub_detail.get('status', None) is None:
                return

            if pub_detail['status'] == 'ok':
                self._to_pub_node[pub_node_id]['results'][server_node] = True
            else:
                self._to_pub_node[pub_node_id]['results'][server_node] = False

            self._to_pub_node[pub_node_id]['callback'][0](server_node, data)

            all_pub_finished = True if len(self._to_pub_node[pub_node_id]['servers']) > 0 else False
            for server_id in self._to_pub_node[pub_node_id]['servers']:
                target_server_node = 's%s' % server_id
                if self._to_pub_node[pub_node_id]['results'].get(target_server_node, False) is False:
                    all_pub_finished = False
                    break

            if all_pub_finished:
                self._to_pub_node[pub_node_id]['callback'][1]()

                self._to_pub_node[pub_node_id]['callback'] = []
                self._to_pub_node[pub_node_id]['results']  = {}

                self._zookeeper.set('%s/to_pub_result/%s' % (self._root_node, pub_node_id, ), json.dumps({
                    'create_time' : Tools.g_time(),
                    'status'      : 'ok'
                }))

        return self