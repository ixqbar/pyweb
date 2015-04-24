#!/usr/bin/env python

import time
import json
import logging

import BaseHandler

import R
import pymongo

LOG = logging.getLogger(__name__)

class PageHandler(BaseHandler.BaseHandler):

    check_session = True
    use_session   = True

    def get(self):
        action_page = self.get_argument('action', '')

        if len(action_page):
            cls_method = getattr(self, action_page, None)
            if cls_method:
                cls_method()
            else:
                self.error('not found `%s`' % action_page)
        else:
            self.error('error action page')

    def about(self):
        self.render('about.html')

    def logout(self):
        self.session.clear()
        self.redirect('/login')

    def error(self, message = ''):
        page_val = {
            'message' : message
        }
        self.render('error.html', **page_val)

    def publish(self):
        page_val = {
            'pub_data' : {}
        }

        pub_id = self.get_argument('id', 0)
        if pub_id > 0:
            mongo_col_data = self.application.get_mongo().get().use_collection(R.collection_publish).find_one({R.mongo_id : int(pub_id)})
            if mongo_col_data:
                page_val['pub_data'] = json.dumps({
                    'pub_id'             : mongo_col_data[R.mongo_id],
                    'pub_config_version' : mongo_col_data[R.pub_config_version],
                    'pub_game_version'   : mongo_col_data[R.pub_game_version],
                    'pub_desc'           : mongo_col_data[R.pub_description],
                    'pub_status'         : mongo_col_data[R.pub_status],
                    'pub_servers'        : mongo_col_data[R.pub_servers],
                })

        self.render('publish.html', **page_val)

    def history(self):
        page_val = {
            'page'       : int(self.get_argument('page', 1)),
            'total_page' : 0,
            'total'      : 0,
            'prev'       : False,
            'next'       : False,
            'pub_list'   : []
        }

        page_num = 20
        skip_num = (page_val['page'] - 1) * page_num if page_val['page'] >= 1 else 1

        mongo_col_cursor = self.application.get_mongo().get().use_collection(R.collection_publish).find(sort=[('_id',pymongo.DESCENDING)])

        page_val['total']      = mongo_col_cursor.count()
        page_val['total_page'] = page_val['total'] / page_num if page_val['total'] % page_num == 0 else 1 + page_val['total'] / page_num
        page_val['prev']       = True if page_val['page'] > 1 else False
        page_val['next']       = True if page_val['page'] < page_val['total_page'] else False

        mongo_col_cursor.batch_size(page_num)
        mongo_col_cursor.limit(page_val['page'] * page_num)

        for mongo_col_data in mongo_col_cursor[skip_num:skip_num + page_num]:
            page_val['pub_list'].append({
                'id'             : mongo_col_data[R.mongo_id],
                'pub_node_id'    : 'v%s' % mongo_col_data[R.mongo_id],
                'config_version' : mongo_col_data[R.pub_config_version],
                'game_version'   : mongo_col_data[R.pub_game_version],
                'description'    : mongo_col_data[R.pub_description],
                'servers'        : ','.join(mongo_col_data[R.pub_servers]) if len(mongo_col_data[R.pub_servers]) > 0 else '',
                'status'         : mongo_col_data[R.pub_status],
                'pub_time'       : time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mongo_col_data[R.pub_time]))
            })

        mongo_col_cursor.close()

        self.render('history.html', **page_val)


