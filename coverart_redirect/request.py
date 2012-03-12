#!/usr/bin/env python

# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2011 Robert Kaye
# Copyright (C) 2012 MetaBrainz Foundation Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import re
import os
import sys
import cgi
import urllib2
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
              JOIN """ + caa + """.cover_art_type ON cover_art.id = cover_art_type.id
              JOIN """ + caa + """.art_type ON cover_art_type.type_id = art_type.id
             WHERE release.gid = %(mbid)s
               AND art_type.name = %(type)s
          ORDER BY ordering ASC LIMIT 1;
        """
        row = self.conn.execute (query, { "mbid": mbid, "type": type }).first ()
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


    def handle_dir(self, entity, mbid, environ):
        '''When the user requests no file, redirect to the root of the bucket to give the user an
           index of what is in the bucket'''

        index_url = "%s/mbid-%s/index.json" % (self.config.s3.prefix, mbid)

        qs = cgi.parse_qs (environ['QUERY_STRING'])
        if not 'jsonp' in qs:
            return [statuscode (307), index_url]

        jsonp = qs['jsonp'].pop ()
        data = None
        try:
            data = urllib2.urlopen (index_url).read()
        except urllib2.HTTPError as e:
            if (e.getcode () == 404):
                data = '{ "images": [], "release": null }'
            else:
                raise e

        return [statuscode (200), "%s(%s);" % (jsonp, data)]



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
            return self.handle_dir(entity, mbid, environ)

        if filename.startswith ('front'):
            filename = self.resolve_cover (entity, mbid, 'Front')
            if not filename:
                return [statuscode (404),
                        "No front cover image found for %s with identifier %s" % (entity, req_mbid)]
        elif filename.startswith ('back'):
            filename = self.resolve_cover (entity, mbid, 'Back')
            if not filename:
                return [statuscode (404),
                        "No back cover image found for %s with identifier %s" % (entity, req_mbid)]

        (code, response) = self.handle_redirect(entity, mbid, filename.encode('utf8'))
        return code, response
