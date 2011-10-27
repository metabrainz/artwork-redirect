# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2011 MetaBrainz Foundation
# Distributed under the MIT license, see the LICENSE file for details.

import logging
import sqlalchemy
from cgi import parse_qs
from contextlib import closing
from coverart_redirect.config import Config
from coverart_redirect.utils import LocalSysLogHandler
from coverart_redirect.request import CoverArtRedirect

logger = logging.getLogger(__name__)

class Server(object):

    def __init__(self, config_path):
        self.config = Config(config_path)
        self.engine = sqlalchemy.create_engine(self.config.database.create_url())
        self.setup_logging()

    def setup_logging(self):
        for logger_name, level in sorted(self.config.logging.levels.items()):
            logging.getLogger(logger_name).setLevel(level)
        if self.config.logging.syslog:
            handler = LocalSysLogHandler(ident='coverart_redirect',
                facility=self.config.logging.syslog_facility, log_pid=True)
            handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
            logging.getLogger().addHandler(handler)

    def __call__(self, environ, start_response):
        with closing(self.engine.connect()) as conn:
            conn.execute("SET search_path TO musicbrainz")
            status, txt = CoverArtRedirect(self.config, conn).handle(environ)
        if status.startswith("307"):
            start_response(status, [('Location', txt)])
            return ""
        elif status.startswith("200"):
            start_response('200 OK', [
                ('Content-Type', 'text/html; charset=UTF-8'),
                ('Content-Length', str(len(txt)))])
            return txt
        else:
            start_response('500 Oops', [])
            return ""


def make_application(config_path):
    app = Server(config_path)
    return app

