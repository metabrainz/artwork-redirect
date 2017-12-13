#!/usr/bin/env python3

# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2011, 2012 MetaBrainz Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import sys
from coverart_redirect.server import Server
from coverart_redirect.config import Config
from coverart_redirect.loggers import init_raven_client


def production(addr, port, application, sentry_dsn=None):
    import cherrypy
    from cherrypy import wsgiserver

    if sentry_dsn:
        init_raven_client(sentry_dsn)

    server = wsgiserver.CherryPyWSGIServer((addr, port), application)

    cherrypy.config.update({
        'log.screen': True,
        "server.thread_pool": 10
    })
    cherrypy.log("server starting")

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


def development(addr, port, application):
    from werkzeug import run_simple

    run_simple(addr, port, application, use_reloader=True,
               extra_files=None, reloader_interval=1, threaded=False,
               processes=1, request_handler=None)


def print_help():
    print("""
syntax: python coverart_redirect_server.py [options]

options:

    --help               This message
    -r, --development    Use werkzeug development server (restarts on source code changes)

""")
    sys.exit(0)


def load_config(test=False):
    """Load configuration from coverart_redirect.conf.

    If test=True will take the database configuration from the
    [testdatabase] section instead of the [database] section.
    """

    config_path = os.path.dirname(os.path.abspath(__file__)) + '/coverart_redirect.conf'
    static_path = os.path.dirname(os.path.abspath(__file__)) + '/static'

    return Config(config_path, static_path, test)


if __name__ == '__main__':
    config = load_config()
    application = Server(config)

    addr = config.listen.addr
    port = int(config.listen.port)

    option = None
    if len(sys.argv) > 1:
        option = sys.argv.pop()

    if option == '--help':
        print_help()
    elif option == '-r' or option == '--development':
        development(addr, port, application)
    else:
        production(addr, port, application, sentry_dsn=config.sentry.dsn)
