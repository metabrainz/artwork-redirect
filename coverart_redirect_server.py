#!/usr/bin/env python

import os
import cherrypy
from cherrypy import wsgiserver
from coverart_redirect.server import make_application

config_path = os.path.dirname(os.path.abspath(__file__)) + '/coverart_redirect.conf'
static_path = os.path.dirname(os.path.abspath(__file__)) + '/static'
application = make_application(config_path, static_path)

# TODO: Move this config file
host = '0.0.0.0'
port = 8080

server = wsgiserver.CherryPyWSGIServer((host, port), application, server_name='coverartarchive.org')
cherrypy.config.update({ 
    'log.screen': True,
    "server.thread_pool" : 10
})
cherrypy.log("server starting")
try:
    server.start()
except KeyboardInterrupt:
    server.stop()
