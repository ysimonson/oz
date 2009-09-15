from tornado.web import *
from oz import error

import base64

class ArgumentPatchMixin(object):
    def get_argument(self, name, default=RequestHandler._ARG_DEFAULT, strip=True):
        """Returns the value of the argument with the given name.
 
        If default is not provided, the argument is considered to be
        required, and we throw an HTTP 404 exception if it is missing.
 
        The returned value is always unicode.
        
        This method is a replacement of Tornado's default implementation to
        fix a couple of bugs;
        1) The full argument value is returned rather than the last character
        2) If an argument is missing, an HTTP status code of 400 is sent (bad request)
           rather than 404 (not found)
        """
        
        values = self.request.arguments.get(name, None)
        
        if values is None:
            if default is self._ARG_DEFAULT:
                raise HTTPError(400, "Missing argument %s" % name)
            return default
        
        # Get rid of any weird control chars
        if len(values) > 0:
            value = values[:-1] + re.sub(r"[\x00-\x08\x0e-\x1f]", " ", values[-1])
        else:
            value = ''
            
        value = _unicode(value)
        if strip: value = value.strip()
        return value
            
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