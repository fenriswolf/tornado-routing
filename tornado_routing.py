'''
Created on May 31, 2014

@author: Fenriswolf
'''
import logging
import inspect
import re
from collections import OrderedDict

from tornado.web import Application, RequestHandler, HTTPError

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
            
    def _execute_method(self):
        if not self._finished:
            func_name = self._get_func_name()
            method = getattr(self, func_name)
            self._when_complete(method(*self.path_args, **self.path_kwargs),
                                self._execute_finish)
            