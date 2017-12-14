# Copyright (C) 2017 MetaBrainz Foundation
# Distributed under the MIT license, see the LICENSE file for details.

# Simple WSGI module intended to be used by uWSGI.

from coverart_redirect.server import Server
from coverart_redirect.config import load_config
from coverart_redirect.loggers import init_raven_client


config = load_config()

sentry_dsn = config.sentry.dsn
if sentry_dsn:
    init_raven_client(sentry_dsn)

application = Server(config)
