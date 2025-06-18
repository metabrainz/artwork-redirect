# Copyright (C) 2017 MetaBrainz Foundation
# Distributed under the MIT license, see the LICENSE file for details.

# Simple WSGI module intended to be used by uWSGI.

import sentry_sdk
from werkzeug.exceptions import HTTPException
from artwork_redirect.server import Server
from artwork_redirect.config import load_config


config = load_config()

sentry_dsn = config.sentry.dsn
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        ignore_errors=[KeyboardInterrupt, HTTPException],
    )


application = Server(config)
