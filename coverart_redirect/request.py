# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2011 Robert Kaye
# Distributed under the MIT license, see the LICENSE file for details.

import re
import os
import logging
import coverart_redirect
from wsgiref.util import shift_path_info, request_uri

logger = logging.getLogger(__name__)


class CoverArtRedirect(object):

    EOL = "\r\n"

    def __init__(self, config, conn):
        self.config = config
        self.conn = conn
        self.cmd = None
        self.proto = None

    def handle_index(self):
        try:
	    f = open(os.path.join(os.environ['STATIC_DIR'], "index"))
        except IOError:
            return ['500 Internal Server Error', ""]

        txt = f.read()
        f.close()

        return ['200 OK', txt]

    def handle_redirect(self, entity, mbid, filename):
        if not entity or entity != 'release':
            return ["400 Only release entities are supported currently", ""]
        if not mbid:
            return ["400 no MBID specified.", ""]
        if not re.match('[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{8}', mbid):
            return ["400 invalid MBID specified.", ""]
        if not filename:
            return ["400 no filename specified.", ""]

        query = """
            SELECT release.gid 
              FROM release, release_gid_redirect 
             WHERE release_gid_redirect.gid = %(mbid)s
               AND new_id = release.id
        """
        rows = self.conn.execute(query, dict(mbid=mbid)).fetchall()
        if rows:
            mbid = rows[0][0];

        # REMOVE ME for testing only!
        filename = filename.replace("-250", "")
        filename = filename.replace("-500", "")

        # This hack is for testing only
        #return ["307 Temporary Redirect", "http://archive.org/download/mbid-%s/mbid-%s-%s" % (mbid, mbid, filename)]
        return ["307 Temporary Redirect", "http://s3.amazonaws.com/mbid-%s/mbid-%s-%s" % (mbid, mbid, filename)]

    def handle(self, environ):
        entity = shift_path_info(environ)
	if not entity:
            return self.handle_index()
        mbid = shift_path_info(environ)
	if not mbid:
            return ["400 invalid request.", ""]
        filename = shift_path_info(environ)
        (code, response) = self.handle_redirect(entity, mbid.lower(), filename.encode('utf8')) 
        logger.debug("Request %s %s %s:\n%s\n", entity, mbid, filename, response)
        return code, response

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8051, application)
    httpd.serve_forever()
