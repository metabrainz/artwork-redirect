# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2011 Robert Kaye
# Distributed under the MIT license, see the LICENSE file for details.

import re
import os
import sys
import coverart_redirect
from coverart_redirect.utils import statuscode
from wsgiref.util import shift_path_info, request_uri

# FIXME: fix http status codes.

class CoverArtRedirect(object):
    ''' Handles index and redirect requests '''

    def __init__(self, config, conn):
        self.config = config
        self.conn = conn
        self.cmd = None
        self.proto = None

        if not self.config.database.musicbrainz_schema:
            print "please configure musicbrainz database schema"
            sys.exit (1)

        if not self.config.database.coverart_schema:
            print "please configure cover art archive database schema"
            sys.exit (1)


    def resolve_mbid (self, entity, mbid):
        """Handle the GID redirect. Query the database to see if the given release has been
           merged into another release. If so, return the redirected MBID, otherwise return
           the original MBID. """

        schema = self.config.database.musicbrainz_schema

        mbid = mbid.lower ()
        query = """
            SELECT release.gid
              FROM """ + schema + """.release
              JOIN """ + schema + """.release_gid_redirect
                ON release_gid_redirect.new_id = release.id
             WHERE release_gid_redirect.gid = %(mbid)s;
        """

        row = self.conn.execute (query, { "mbid": mbid }).first ()
        if row:
            return row[0];

        return mbid


    def resolve_cover(self, entity, mbid, type):
        '''Get the frontiest or backiest cover image.'''

        mbz = self.config.database.musicbrainz_schema
        caa = self.config.database.coverart_schema

        query = """
            SELECT cover_art.id
              FROM """ + caa + """.cover_art
              JOIN """ + mbz + """.release ON release = release.id
             WHERE release.gid = %(mbid)s
               AND is_""" + type + """ = true;
        """
        row = self.conn.execute (query, { "mbid": mbid }).first ()
        if row:
            return unicode(row[0]) + u".jpg"

        return None


    def handle_index(self):
        '''Serve up the one static index page'''

        try:
            f = open(os.path.join(self.config.static_path, "index"))
        except IOError:
            return [statuscode (500), "Internal Server Error"]

        txt = f.read()
        f.close()

        return [statuscode (200), txt]


    def handle_dir(self, entity, mbid):
        '''When the user requests no file, redirect to the root of the bucket to give the user an
           index of what is in the bucked'''
        return [statuscode (307), "%s/mbid-%s/index.json" % (self.config.s3.prefix, mbid)]


    def handle_redirect(self, entity, mbid, filename):
        """ Handle the 307 redirect. """

        if not filename:
            return [statuscode (400), "no filename specified"]

        filename = filename.replace("-250.jpg", "_thumb250.jpg")
        filename = filename.replace("-500.jpg", "_thumb500.jpg")

        return [statuscode (307), "%s/mbid-%s/mbid-%s-%s" % (
                self.config.s3.prefix, mbid, mbid, filename)]


    def handle(self, environ):
        '''Handle a request, parse and validate arguments and dispatch the request'''

        entity = shift_path_info(environ)
        if not entity:
            return self.handle_index()

        if entity != 'release':
            return [statuscode (400), "Only release entities are currently supported"]

        req_mbid = shift_path_info(environ)
        if not req_mbid:
            return [statuscode (400), "no MBID specified."]
        if not re.match('[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', req_mbid):
            return [statuscode (400), "invalid MBID specified."]

        mbid = self.resolve_mbid (entity, req_mbid)
        if not mbid:
            return [statuscode (404), "No %s found with identifier %s" % (entity, req_mbid)]

        filename = shift_path_info(environ)
        if not filename:
            return self.handle_dir(entity, mbid)

        if filename.startswith ('front'):
            filename = self.resolve_cover (entity, mbid, 'front')
            if not filename:
                return [statuscode (404),
                        "No front cover image found for %s with identifier %s" % (entity, req_mbid)]
        elif filename.startswith ('back'):
            filename = self.resolve_cover (entity, mbid, 'back')
            if not filename:
                return [statuscode (404),
                        "No back cover image found for %s with identifier %s" % (entity, req_mbid)]

        (code, response) = self.handle_redirect(entity, mbid, filename.encode('utf8'))
        return code, response


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8051, application)
    httpd.serve_forever()
