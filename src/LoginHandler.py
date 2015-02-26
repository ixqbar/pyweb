#!/usr/bin/env python

import time
import logging

import BaseHandler


LOG = logging.getLogger(__name__)

class LoginHandler(BaseHandler.BaseHandler):

    check_session = False
    use_session   = True

    def get(self):
        if self.session.get('name') is not None:
            self.redirect('/page?action=index')
        else:
            self.render('login.html')

    def post(self):
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        LOG.info('login page post %s-%s' % (username, password,))

        if username == 'admin' and password == 'todo':
            self.session.init({'name':username,'time':time.time()})
            self.redirect('/')