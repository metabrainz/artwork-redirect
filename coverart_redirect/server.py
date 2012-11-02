#!/usr/bin/env python2

# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2011 Robert Kaye
# Copyright (C) 2012 MetaBrainz Foundation Inc.
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


import sys
import traceback
import cherrypy
import sqlalchemy
from cgi import parse_qs
from contextlib import closing
from coverart_redirect.config import Config
from coverart_redirect.utils import LocalSysLogHandler, statuscode
from coverart_redirect.request import CoverArtRedirect

class Server(object):

    def __init__(self, config):
        self.config = config
        self.engine = sqlalchemy.create_engine(self.config.database.create_url())

    def __call__(self, environ, start_response):
        try:
            with closing(self.engine.connect()) as conn:
                (status, txt) = CoverArtRedirect(self.config, conn).handle(environ)

            if status.startswith("307"):
                start_response(status, [
                        ('Location', txt),
                        ('Access-Control-Allow-Origin', '*')
                        ])
                return ["See: ", txt, "\n"]
            elif status.startswith("200"):
                start_response(statuscode (200), [
                ('Content-Type', 'text/html; charset=UTF-8'),
                ('Content-Length', str(len(txt)))])
                return [txt]
            else:
                start_response(status, [])
                return [txt, "\n"]
        except:
            cherrypy.log("Caught exception\n" + traceback.format_exc())
            start_response(statuscode (500), [])
            return ["Whoops. Our bad.\n"]
