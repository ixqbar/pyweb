import uuid
import logging

import Tools

LOG = logging.getLogger(__name__)

class Session(object):

    _sessionName        = 'jzps'
    _sessionValue       = {}
    _sessionID          = None
    _sessionDataHandler = None
    _webApplication     = None
    _webRequestHandler  = None

    def __init__(self, webRequestHandler):
        self._sessionDataHandler = webRequestHandler.application.get_redis_server()
        self._webApplication     = webRequestHandler.application
        self._webRequestHandler  = webRequestHandler

    def load(self):
        if self._sessionID is None:
            self.get_session_id()

        if self._sessionID is not None:
            self._sessionValue = self._sessionDataHandler.hgetall(self._sessionID)

    def get_session_id(self):
        if self._sessionID is None:
            sessionID = self._webRequestHandler.get_secure_cookie(self._sessionName, None)
            if sessionID is not None:
                flag = sessionID.split('-')[1] if sessionID.count('-') else None
                if flag is None or flag != Tools.md5(self._webRequestHandler.request.remote_ip + self._webApplication.settings.get('cookie_secret', '')):
                    LOG.warn('session %s invalid' % sessionID)
                    sessionID = None

            if sessionID is None:
                sessionID = '%s-%s' % (str(uuid.uuid4()).split('-')[0], Tools.md5(self._webRequestHandler.request.remote_ip + self._webApplication.settings.get('cookie_secret', '')), )
                self._webRequestHandler.set_secure_cookie(self._sessionName, sessionID, expires_days = 1, httponly = True)
                LOG.info('gen session id %s %s' % (self._webRequestHandler.request.remote_ip, sessionID,))

            self._sessionID = 'session_' + sessionID

        return self._sessionID

    def init(self, value):
        if type(value) is dict:
            self._sessionValue = value
        else:
            raise 'Error session data type to init'

    def get(self, key, default_value=None):
        return self._sessionValue.get(key, default_value)

    def set(self, key, value):
        self._sessionValue[key] = value

    def clear(self):
        if self._sessionID is not None:
            self._sessionDataHandler.delete(self._sessionID)
            self._sessionValue = {}
            self._webRequestHandler.set_secure_cookie(self._sessionName, '')

    def save(self):
        if self._sessionID is not None and len(self._sessionValue):
            self._sessionDataHandler.hmset(self._sessionID, self._sessionValue)
            self._sessionDataHandler.expire(self._sessionID, 3600)
