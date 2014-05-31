'''
Created on May 31, 2014

@author: Fenriswolf
'''
import logging
import inspect
import re
from collections import OrderedDict

from tornado.web import Application, RequestHandler, HTTPError, _has_stream_request_body
from tornado import gen
from tornado.concurrent import is_future
from tornado import iostream

app_routing_log = logging.getLogger("tornado.application.routing")

class RoutingApplication():
    def __init__(self, app = None):
        self.app = app or Application()
        self.handler_map = OrderedDict()
        
    def route(self, rule, methods = ['GET'], kwargs=None, name=None):
        """
        A decorator that is used to register a given URL rule.
        """
        def decorator(func, *args, **kwargs):
            func_name = func.__name__
            frm = inspect.stack()[1]
            class_name = frm[3]
            module_name = frm[0].f_back.f_globals["__name__"]
            full_class_name = module_name + '.' + class_name
  
            for method in methods:
                self.handler_map.setdefault(full_class_name, {})[method] = (rule, func_name)
                app_routing_log.info("register %s %s to %s.%s" % (method, rule, full_class_name, func_name))
                
            return func
        return decorator

    def get_application(self):
        handlers = [(rule[0], full_class_name) 
                    for full_class_name, rules in self.handler_map.items()
                    for rule in rules.values()]
        self.app.add_handlers(".*$", handlers)
        self.app.handler_map = self.handler_map
        
        return self.app
    
class RequestRoutingHandler(RequestHandler):
    def _get_func_name(self):
        full_class_name = self.__module__ + '.' + self.__class__.__name__
        rule, func_name = self.application.handler_map.get(full_class_name, {}).get(self.request.method, (None, None))
        
        if not rule or not func_name:
            raise HTTPError(404, "")
        
        match = re.match(rule, self.request.path)
        if match:
            return func_name
        else:
            raise HTTPError(404, "")
            
    @gen.coroutine
    def _execute(self, transforms, *args, **kwargs):
        """Executes this request with the given output transforms."""
        self._transforms = transforms
        try:
            if self.request.method not in self.SUPPORTED_METHODS:
                raise HTTPError(405)
            self.path_args = [self.decode_argument(arg) for arg in args]
            self.path_kwargs = dict((k, self.decode_argument(v, name=k))
                                    for (k, v) in kwargs.items())
            # If XSRF cookies are turned on, reject form submissions without
            # the proper cookie
            if self.request.method not in ("GET", "HEAD", "OPTIONS") and \
                    self.application.settings.get("xsrf_cookies"):
                self.check_xsrf_cookie()

            result = self.prepare()
            if is_future(result):
                result = yield result
            if result is not None:
                raise TypeError("Expected None, got %r" % result)
            if self._prepared_future is not None:
                # Tell the Application we've finished with prepare()
                # and are ready for the body to arrive.
                self._prepared_future.set_result(None)
            if self._finished:
                return

            if _has_stream_request_body(self.__class__):
                # In streaming mode request.body is a Future that signals
                # the body has been completely received.  The Future has no
                # result; the data has been passed to self.data_received
                # instead.
                try:
                    yield self.request.body
                except iostream.StreamClosedError:
                    return

            method = getattr(self, self._get_func_name())
            result = method(*self.path_args, **self.path_kwargs)
            if is_future(result):
                result = yield result
            if result is not None:
                raise TypeError("Expected None, got %r" % result)
            if self._auto_finish and not self._finished:
                self.finish()
        except Exception as e:
            self._handle_request_exception(e)
            if (self._prepared_future is not None and
                    not self._prepared_future.done()):
                # In case we failed before setting _prepared_future, do it
                # now (to unblock the HTTP server).  Note that this is not
                # in a finally block to avoid GC issues prior to Python 3.4.
                self._prepared_future.set_result(None)
            