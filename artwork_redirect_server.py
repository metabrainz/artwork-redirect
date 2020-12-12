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
from artwork_redirect.server import Server
from artwork_redirect.config import load_config


def development():
    from werkzeug import run_simple

    config = load_config()
    application = Server(config)

    addr = config.listen.addr
    port = int(config.listen.port)

    run_simple(addr, port, application, use_reloader=True,
               extra_files=None, reloader_interval=1, threaded=False,
               processes=1, request_handler=None)


def print_help():
    print("""
syntax: python artwork_redirect_server.py [options]

options:

    --help               This message

""")
    sys.exit(0)


if __name__ == '__main__':
    option = None
    if len(sys.argv) > 1:
        option = sys.argv.pop()

    if option == '--help':
        print_help()
    else:
        development()
