# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2012 Kuno Woudt
# Copyright (C) 2011-2012 MetaBrainz Foundation
# Distributed under the MIT license, see the LICENSE file for details.

import sys
import traceback
import cherrypy
import sqlalchemy
import werkzeug.wrappers
import werkzeug.exceptions
from cgi import parse_qs
from contextlib import closing
from coverart_redirect.config import Config
from coverart_redirect.utils import LocalSysLogHandler, statuscode
from coverart_redirect.request import CoverArtRedirect

class Request (werkzeug.wrappers.Request):

    def redirect (self, location, code=302):
        if location.startswith ("/"):
            location = self.host_url + location[1:]

        response = werkzeug.wrappers.BaseResponse (
            "see: %s\n" % location, code, mimetype='text/plain')
        response.headers['Location'] = werkzeug.urls.iri_to_uri (location)
        return response


class Server(object):

    def __init__(self, config):
        self.config = config
        self.engine = sqlalchemy.create_engine(self.config.database.create_url())

    @Request.application
    def __call__(self, request):
        try:
            with closing(self.engine.connect()) as conn:
                response = CoverArtRedirect(self.config, conn).handle(request)

            response.headers['Access-Control-Allow-Origin', '*']
            return response
        except werkzeug.exceptions.HTTPException, e:
            return e
        except:
            cherrypy.log("Caught exception\n" + traceback.format_exc())
            return werkzeug.wrappers.Response (status=500, response=
                                               ["Whoops. Our bad.\n"])

def make_application(config):
    app = Server(config)
    return app

