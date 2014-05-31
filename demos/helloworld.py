'''
Created on May 31, 2014

@author: Fenriswolf
'''
import logging

import tornado.httpserver
import tornado.ioloop
import tornado.options

from tornado.options import define, options
from tornado_routing import RoutingApplication, RequestRoutingHandler

define("port", default=8080, help="run on the given port", type=int)

logging.basicConfig(level=logging.DEBUG)
app = RoutingApplication()

class HomeHandler(RequestRoutingHandler):
    @app.route('/')
    def get_home(self):
        self.write("Hello home")

class HelloWorldHandler(RequestRoutingHandler):
    @app.route('/hello/(.*)', methods = ['GET', 'POST'])
    def say_hello(self, user_name):
        self.write("Hello " + user_name)
        
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(app.get_application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
