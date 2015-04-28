import logging

import tornado.web
import tornado.template

import Session

LOG = logging.getLogger(__name__)

class BaseHandler(tornado.web.RequestHandler):

    check_session = False
    use_session   = False
    session       = None

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        LOG.info('web request init')

        if self.use_session:
            self.session = Session.Session(self)
            self.session.load()

    def check_login(self):
        if self.use_session \
                and self.check_session \
                and self.session.get('name') is None:
            self.redirect('/login')

    def prepare(self):
        LOG.info('web request prepare')
        self.check_login()

    def on_finish(self):
        LOG.info('web request finish')
        if self.use_session:
            self.session.save()

    def write_error(self, status_code, **kwargs):
        self.write('Error:%d' % status_code)