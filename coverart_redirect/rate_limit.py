#!/usr/bin/env python2

# Copyright (C) 2015 MetaBrainz Foundation
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
import re
import socket
import select
from werkzeug.wrappers import Response

HTTP_SERVICE_UNAVAILABLE = 503

class RateLimiter(object):

    def __init__(self, config):
        self.config = config
        self.socket = None
        self.id = 0

    def get_socket(self):
        if self.socket:
            return self.socket

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.getprotobyname('udp'))
        config = self.config.rate_limit_server

        try:
            self.socket.connect((config.host, int(config.port)))
        except socket.error as e:
            print >> sys.stderr, ('socket.connect error: %s' % e)
            return None

        return self.socket

    def reset_socket(self):
        if self.socket:
            self.socket.close()
            self.socket = None

    def check_rate_limit(self, key):
        s = self.get_socket()

        if not s:
            return None

        self.id += 1
        self.id &= 0xFFFF

        bytes_sent = s.send('%s over_limit %s' % (self.id, key))
        if bytes_sent == 0:
            return None

        ready = select.select([s], [], [], 0.1)
        if s not in ready[0]:
            return None

        # Note: recv is blocking.
        data = s.recv(1000)

        if not re.search(r'\A(%s) /' % (self.id,), data):
            self.reset_socket()
            return None

        match = re.match(r'^ok ([YN]) ([\d.]+) ([\d.]+) (\d+)$', data)
        if match:
            is_over_limit = match.group(1) == 'Y'
            if is_over_limit:
                return Response(
                    status=HTTP_SERVICE_UNAVAILABLE,
                    headers=[('X-Rate-Limited', '%.1f %.1f %d' % match.group(2, 3, 4))]
                )
