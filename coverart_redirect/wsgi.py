# Copyright (C) 2011 Lukas Lalinsky
# Distributed under the MIT license, see the LICENSE file for details.

# Simple WSGI module intended to be used by uWSGI, e.g.:
# uwsgi -w acoustid.wsgi --pythonpath ~/acoustid/ --env COVERART_REDIRECT_CONFIG=~/acoustid/acoustid.conf --http :9090
# uwsgi -w acoustid.wsgi --pythonpath ~/acoustid/ --env COVERART_REDITECT_CONFIG=~/acoustid/acoustid.conf -M -L --socket 127.0.0.1:1717

import os
from coverart_redirect.server import make_application

application = make_application(os.environ['COVERART_REDIRECT_CONFIG'])
