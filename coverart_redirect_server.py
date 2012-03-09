#!/usr/bin/env python

import os
import sys
from coverart_redirect.server import make_application
from coverart_redirect.config import Config


def production (addr, port, application):
    import cherrypy
    from cherrypy import wsgiserver

    server = wsgiserver.CherryPyWSGIServer((addr, port), application)

    cherrypy.config.update({
            'log.screen': True,
            "server.thread_pool" : 10
    })
    cherrypy.log("server starting")

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


def development (addr, port, application):
    from werkzeug import run_simple

    run_simple (addr, port, application, use_reloader=True,
                extra_files=None, reloader_interval=1, threaded=False,
                processes=1, request_handler=None)


def help ():
    print """
syntax: python coverart_redirect_server.py [options]

options:

    --help               This message
    -r, --development    Use werkzeug development server (restarts on source code changes)

"""
    sys.exit (0)


if __name__ == '__main__':
    config_path = os.path.dirname(os.path.abspath(__file__)) + '/coverart_redirect.conf'
    static_path = os.path.dirname(os.path.abspath(__file__)) + '/static'

    config = Config(config_path, static_path)
    application = make_application(config)

    addr = config.listen.addr
    port = int(config.listen.port)

    option = None
    if len (sys.argv) > 1:
        option = sys.argv.pop ()

    if option == '--help':
        help ()
    elif option == '-r' or option == '--development':
        development (addr, port, application)
    else:
        production (addr, port, application)

