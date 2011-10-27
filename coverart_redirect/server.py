# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2011 MetaBrainz Foundation
# Distributed under the MIT license, see the LICENSE file for details.

import logging
import sqlalchemy
from cgi import parse_qs
from contextlib import closing
from wsgiref.util import shift_path_info
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
        entity = shift_path_info(environ)
        mbid = shift_path_info(environ)
        filename = shift_path_info(environ)
        with closing(self.engine.connect()) as conn:
            conn.execute("SET search_path TO musicbrainz")
            status, location = CoverArtRedirect(self.config, conn).handle(entity, mbid, filename)
        start_response(status, [('Location', location)])
        return ""

def make_application(config_path):
    app = Server(config_path)
    return app

