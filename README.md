== DEPRECATION NOTICE ==

This version of Oz is deprecated. Please see the new Oz at:
[http://github.com/dailymuse/oz](http://github.com/dailymuse/oz)

== ABOUT ==
Oz is a set of classes for augmenting the functionality of the Tornado web
framework. I will give you an e-high-five if you understand the name's
reference.

== DJANGO-STYLE ERROR MESSAGES ==
DjangoErrorMixin provides pretty Django-like error messages when an exception
occurs. This is very useful when you're developing your web app, but not a good
idea to run in production. Consequently, this tool only runs when the setting
'debug' is set to True.

To use it, first enable debug in the settings:

    settings = {
        'debug': True,
    }
    
    app = tornado.web.Application([
        (r'/', HelloWorldHandler),
    ], **settings)
    
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
    
Then in your handler, add the mixin:

    class HelloWorldHandler(DjangoErrorMixin, RequestHandler):
        def get(self):
            #This will throw an AssertionError to display the pretty error page
            assert False
            
            self.write('hello, world!')

If your application also defines a 'output_type_override' setting, the setting's
value will be used as a parameter key that clients can use to change the error
output format. For example, if you set 'output_type_override' to 'error_output',
then a client upon making a request can set a GET or POST parameter error_output
to either 'txt', 'verbose_txt' or 'html' to change the error output formatting.
For example, a request to http://localhost:8080/?error_output=verbose_txt will
provide a textual version of the Django error page instead. This is useful if
you want the debugging richness of the Django error page, but your client cannot
view html appropriately. Setting the format to txt will provide a simple Python
stack trace. verbose_txt is roughly a textual equivalent of the Django error
page. html is the default Dango error page output.

== HTTP BASIC AUTHENTICATION ==
BasicAuthMixin enables HTTP basic authentication. The tool is very flexible,
as it uses a callback to check the credentials.

Add the mixin in your handler and call self.get_authenticated_user() (similar to
the auth mixins provided by Tornado) when you want to authenticate the request:

    class HelloWorldHandler(BasicAuthMixin, RequestHandler):
        def get(self):
            if not self.get_authenticated_user(auth_callback, 'realm'):
                return False
            
            self.write('hello, world!')
            
The first argument for get_authenticated_user() is the callback method you wish
to use for authentication. The second argument is the realm. An example callback
method:

    def auth_callback(request, realm, username, password):
        if username == 'foo' and password == 'bar':
            request.user_id = 1
            return True
        else:
            return False
            
The method must a boolean stating whether the authentication succeeded. It takes
in the RequestHandler object as the first argument in case you want to add some
useful attributes (in this case, we're adding user_id).

If authentication fails, the RequestHandler will finish() and no further code
will be executed. If it succeeds, the authenticated user will be available via
RequestHandler.get_current_user().

You can also use the basic_auth decorator for methods that you wish to protect
as an alternate use case for the mixin. Example:

    class HelloWorldHandler(BasicAuthMixin, RequestHandler):
        @basic_auth(auth_callback, 'realm')
        def get(self):
            self.write('hello, world!')

This is equivalent to the previous implementation example.

== ARGUMENT PATCH ==
ArgumentPatchMixin replaces the default implementation of
RequestHandler.get_argument(), which returns GET/POST parameters sent with the
request. If a required argument is missing, it throws an HTTP code 400 (bad
request) instead of a 404 (not found). I think this makes more sense.

To use it, all you have to do is add the mixin:

    class HelloWorldHandler(ArgumentPatchMixin, RequestHandler):
        def get(self):
            name = self.get_argument('name')
            self.write('hello, %s!' % name)
            
== NOTES ==
 * Always put the mixins before the RequestHandler on the inheritance list. This
   will work:
   
       class HelloWorldHandler(ArgumentPatchMixin, RequestHandler):
           ...
           
   Whereas this will *NOT* work:
   
       class HelloWorldHandler(RequestHandler, ArgumentPatchMixin):
           ...
           
 * You can mix and match multiple mixins. This will work fine:
 
       class HelloWorldHandler(BasicAuthMixin, DjangoErrorMixin,
           ArgumentPatchMixin, RequestHandler):
           ...