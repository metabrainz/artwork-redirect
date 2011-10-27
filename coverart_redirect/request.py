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

    def handle_cmd_cddb_query(self):
        """Perform a CD search based on either the FreeDB DiscID or the CD TOC."""
        if len(self.cmd) < 3:
            return ["500 Command syntax error."]

        discid = self.cmd[0]
        try:
            int(discid, 16)
        except ValueError:
            return ["500 ID not hex."]

        try:
            num_tracks = int(self.cmd[1])
        except ValueError:
            return ["500 Command syntax error."]

        if len(self.cmd) < 3 + num_tracks:
            return ["500 Command syntax error."]

        offsets = []
        for i in xrange(2, 2 + num_tracks):
            offsets.append(int(self.cmd[i]))
        offsets.append(int(self.cmd[2 + num_tracks]) * 75)

        durations = []
        for i in xrange(num_tracks):
            durations.append((offsets[i + 1] - offsets[i]) * 1000 / 75)

        toc_query = """
            SELECT DISTINCT
                m.id,
                CASE
                    WHEN (SELECT count(*) FROM medium WHERE release = r.id) > 1 THEN
                        rn.name || ' (disc ' || m.position::text || ')'
                    ELSE
                        rn.name
                END AS title,
                CASE
                    WHEN artist_name.name = 'Various Artists' THEN
                        'Various'
                    ELSE
                        artist_name.name
                END AS artist
            FROM
                medium m
                JOIN tracklist t ON t.id = m.tracklist
                JOIN tracklist_index ti ON ti.tracklist = t.id
                JOIN release r ON m.release = r.id
                JOIN release_name rn ON r.name = rn.id
                JOIN artist_credit ON r.artist_credit = artist_credit.id
                JOIN artist_name ON artist_credit.name = artist_name.id
            WHERE
                toc <@ create_bounding_cube(%(durations)s, %(fuzzy)s::int) AND
                track_count = %(num_tracks)s
        """

        discid_query = """
            SELECT DISTINCT
                m.id,
                CASE
                    WHEN (SELECT count(*) FROM medium WHERE release = r.id) > 1 THEN
                        rn.name || ' (disc ' || m.position::text || ')'
                    ELSE
                        rn.name
                END AS title,
                CASE
                    WHEN artist_name.name = 'Various Artists' THEN
                        'Various'
                    ELSE
                        artist_name.name
                END AS artist
            FROM
                medium m
                JOIN medium_cdtoc mc ON m.id = mc.medium
                JOIN cdtoc c ON c.id = mc.cdtoc
                JOIN tracklist t ON t.id = m.tracklist
                JOIN release r ON m.release = r.id
                JOIN release_name rn ON r.name = rn.id
                JOIN artist_credit ON r.artist_credit = artist_credit.id
                JOIN artist_name ON artist_credit.name = artist_name.id
            WHERE
                c.freedb_id = %(discid)s AND
                t.track_count = %(num_tracks)s
        """

        #used_toc = False
        #rows = self.conn.execute(discid_query, dict(discid=discid, num_tracks=num_tracks)).fetchall()
        #if not rows:
        used_toc = True
        rows = self.conn.execute(toc_query, dict(durations=durations, num_tracks=num_tracks, fuzzy=10000)).fetchall()

        if not rows:
            return ["202 No match found."]

        # Only one match and we didn't use the TOC
        if len(rows) == 1 and not used_toc:
            id, title, artist = rows[0]
            return ["200 rock %08x %s / %s" % (id, artist, title)]

        # Found multiple matches
        res = ["211 Found inexact matches, list follows (until terminating `.')"]
        for id, title, artist in rows:
            res.append("rock %08x %s / %s" % (id, artist, title))
        res.append(".")
        return res

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

        return ["307 Temporary Redirect", "http://archive.org/download/mbid-%s/mbid-%s-%s" % (mbid, mbid, filename)]

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
