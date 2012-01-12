#!/usr/bin/env python

import os
import cherrypy
from cherrypy import wsgiserver
from coverart_redirect.server import make_application
from coverart_redirect.config import Config

config_path = os.path.dirname(os.path.abspath(__file__)) + '/coverart_redirect.conf'
static_path = os.path.dirname(os.path.abspath(__file__)) + '/static'

config = Config(config_path, static_path)
application = make_application(config)

server = wsgiserver.CherryPyWSGIServer((config.listen.addr, int(config.listen.port)), 
                                       application)
cherrypy.config.update({ 
    'log.screen': True,
    "server.thread_pool" : 10
})
cherrypy.log("server starting")
try:
    server.start()
except KeyboardInterrupt:
    server.stop()
