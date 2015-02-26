#!/usr/bin/env python

import logging

import BaseHandler

LOG = logging.getLogger(__name__)

class IndexHandler(BaseHandler.BaseHandler):

    check_session = True
    use_session   = True

    def get(self):
        page_val = {
            'manager_name' : self.session.get('name')
        }
        self.render('index.html', **page_val)
