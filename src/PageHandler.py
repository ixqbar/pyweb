#!/usr/bin/env python

import logging

import BaseHandler

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


