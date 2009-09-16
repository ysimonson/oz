from tornado.web import *
from oz import error

import base64

class ArgumentPatchMixin(RequestHandler):
    def get_argument(self, name, default=RequestHandler._ARG_DEFAULT, strip=True):
        """Returns the value of the argument with the given name.
 
        If default is not provided, the argument is considered to be
        required, and we throw an HTTP 404 exception if it is missing.
 
        The returned value is always unicode.
        
        This method is a replacement of Tornado's default implementation to
        throw an HTTP status code of 400 (bad request) rather than 404 (not
        found)
        """
        
        try:
            return RequestHandler.get_argument(self, name, default, strip)
        except HTTPError:
            raise HTTPError(400, "Missing argument %s" % name)
            
class BasicAuthMixin(object):
    def _request_auth(self, realm):
        if self._headers_written: return Exception('headers have already been written')
        
        self.set_status(401)
        self.set_header('WWW-Authenticate', 'Basic realm="%s"' % realm)
        self.finish()
        
    def get_authenticated_user(self, auth_func, realm):
        """Requests HTTP basic authentication credentials from the client, or
        authenticates the user if credentials are provided."""
        try:
            auth = self.request.headers.get('Authorization')
            
            if auth == None: return self._request_auth(realm)
            if not auth.startswith('Basic '): return self._request_auth(realm)
            
            auth_decoded = base64.decodestring(auth[6:])
            username, password = auth_decoded.split(':', 1)
            
            if auth_func(self, realm, username, password):
                self._current_user = username
            else:
                return self._request_auth(realm)
        except Exception, e:
            return self._request_auth(realm)

class DjangoErrorMixin(RequestHandler):
    def get_error_html(self, status_code):
        self.require_setting('debug')
        debug = self.application.settings['debug']
        
        if debug:
            error.render_error(self)
        else:
            return "<html><title>%(code)d: %(message)s</title>" \
                   "<body>%(code)d: %(message)s</body></html>" % {
                "code": status_code,
                "message": httplib.responses[status_code],
            }