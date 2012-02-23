# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2011 Robert Kaye
# Distributed under the MIT license, see the LICENSE file for details.

import re
import os
import coverart_redirect
from wsgiref.util import shift_path_info, request_uri
import cherrypy

class CoverArtRedirect(object):
    ''' Handles index and redirect requests '''

    def __init__(self, config, conn):
        self.config = config
        self.conn = conn
        self.cmd = None
        self.proto = None

    def handle_index(self):
        '''Serve up the one static index page'''

        try:
	    f = open(os.path.join(self.config.static_path, "index"))
        except IOError:
            return ['500 Internal Server Error', ""]

        txt = f.read()
        f.close()

        return ['200 OK', txt]

    def handle_dir(self, entity, mbid):
        '''When the user requests no file, redirect to the root of the bucket to give the user an
           index of what is in the bucked'''
        return ["307 Temporary Redirect", "http://archive.org/download/mbid-%s/index.json" % (mbid)]

    def handle_redirect(self, entity, mbid, filename):
        '''Handle the actual redirect. Query the database to see if the given release has been
           merged into another release. If so, return the redirected MBID, otherwise redirect
           to the given MBID.'''

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

        # ------------------------------------------------------------------------------------------------
        # Remove me for deploying this service for real. This code is for testing only!
        # ------------------------------------------------------------------------------------------------
        # REMOVE ME for testing only!
        filename = filename.replace("-250", "")
        filename = filename.replace("-500", "")

        return ["307 Temporary Redirect", "http://archive.org/download/mbid-%s/mbid-%s-%s" % (mbid, mbid, filename)]


    def handle(self, environ):
        '''Handle a request, parse and validate arguments and dispatch the request'''

        entity = shift_path_info(environ)
	if not entity:
            return self.handle_index()

        mbid = shift_path_info(environ)
        if not mbid:
            return ["400 no MBID specified.", ""]
        if not re.match('[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', mbid):
            return ["400 invalid MBID specified.", ""]

        filename = shift_path_info(environ)
        if not filename:
            return self.handle_dir(entity, mbid)

        if not entity or entity != 'release':
            return ["400 Only release entities are supported currently", ""]

        (code, response) = self.handle_redirect(entity, mbid.lower(), filename.encode('utf8')) 
        return code, response

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8051, application)
    httpd.serve_forever()
