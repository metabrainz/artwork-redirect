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
from werkzeug.wrappers import Response
from werkzeug.utils import pop_path_info
from coverart_redirect.utils import statuscode
from wsgiref.util import request_uri

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


    def thumbnail (self, filename):
        if not '-' in filename:
            return ""

        (id, size) = filename.split ('-')

        if size.startswith ('250'):
            return "-250"
        elif size.startswith ('500'):
            return "-500"
        else:
            return ""


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


    def resolve_cover(self, entity, mbid, type, thumbnail):
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
            return unicode(row[0]) + thumbnail + u".jpg"

        return None


    def handle_index(self):
        '''Serve up the one static index page'''

        try:
            f = open(os.path.join(self.config.static_path, "index"))
        except IOError:
            return Response(status=500, response="Internal Server Error")

        txt = f.read()
        f.close()

        return Response (response=txt)


    def handle_dir(self, request, entity, mbid, environ):
        '''When the user requests no file, redirect to the root of the bucket to give the user an
           index of what is in the bucket'''

        index_url = "%s/mbid-%s/index.json" % (self.config.s3.prefix, mbid)
        return request.redirect (code=307, location=index_url)


    def handle_redirect(self, request, entity, mbid, filename):
        """ Handle the 307 redirect. """

        if not filename:
            return [statuscode (400), "no filename specified"]

        filename = filename.replace("-250.jpg", "_thumb250.jpg")
        filename = filename.replace("-500.jpg", "_thumb500.jpg")

        url = "%s/mbid-%s/mbid-%s-%s" % (self.config.s3.prefix, mbid, mbid, filename)
        return request.redirect (code=307, location=url)


    def handle(self, request):
        '''Handle a request, parse and validate arguments and dispatch the request'''

        entity = pop_path_info(environ)
        if not entity:
            return self.handle_index()

        if entity != 'release':
            return Response (status=400, response=
                             "Only release entities are currently supported")

        req_mbid = shift_path_info(environ)
        if not req_mbid:
            return Response (status=400, response="no MBID specified.")
        if not re.match('[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', req_mbid):
            return Response (status=400, response="invalid MBID specified.")

        mbid = self.resolve_mbid (entity, req_mbid)
        if not mbid:
            return Response (status=404, response=
                             "No %s found with identifier %s" % (entity, req_mbid))

        filename = pop_path_info(environ)
        if not filename:
            return self.handle_dir(entity, mbid, environ)

        if filename.startswith ('front'):
            filename = self.resolve_cover (entity, mbid, 'Front', self.thumbnail (filename))
            if not filename:
                return Response(status=404, response=
                                "No front cover image found for %s with identifier %s" % (entity, req_mbid))
        elif filename.startswith ('back'):
            filename = self.resolve_cover (entity, mbid, 'Back', self.thumbnail (filename))
            if not filename:
                return Response(status=404, response=
                                "No back cover image found for %s with identifier %s" % (entity, req_mbid))

        return self.handle_redirect(request, entity, mbid, filename.encode('utf8'))
