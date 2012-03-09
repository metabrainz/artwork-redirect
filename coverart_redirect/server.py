# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2011 MetaBrainz Foundation
# Distributed under the MIT license, see the LICENSE file for details.

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

def make_application(config):
    app = Server(config)
    return app

