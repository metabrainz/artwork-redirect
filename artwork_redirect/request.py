# Copyright (C) 2007 Pallets
# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2011 Robert Kaye
# Copyright (C) 2012, 2015 MetaBrainz Foundation Inc.
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

import os
import re
import uuid
from os.path import splitext
from wsgiref.util import shift_path_info

import sentry_sdk
from sqlalchemy import text
from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.exceptions import NotImplemented as HTTPNotImplemented
from werkzeug.wrappers import Response

CAA_ENTITY_TYPES = ["release", "release-group"]
EAA_ENTITY_TYPES = ["event"]
ALL_ENTITY_TYPES = CAA_ENTITY_TYPES + EAA_ENTITY_TYPES

_THUMB_RE = re.compile(r"-(250|500|1200).(jpg|gif|png|pdf)")


# Copied from https://github.com/pgjones/werkzeug/blob/a34d1f7/src/werkzeug/wsgi.py#L240
def pop_path_info(environ):
    path = environ.get("PATH_INFO")
    if not path:
        return None
    script_name = environ.get("SCRIPT_NAME", "")
    # shift multiple leading slashes over
    old_path = path
    path = path.lstrip("/")
    if path != old_path:
        script_name += "/" * (len(old_path) - len(path))
    if "/" not in path:
        environ["PATH_INFO"] = ""
        environ["SCRIPT_NAME"] = script_name + path
        rv = path.encode("latin1")
    else:
        segment, path = path.split("/", 1)
        environ["PATH_INFO"] = f"/{path}"
        environ["SCRIPT_NAME"] = script_name + segment
        rv = segment.encode("latin1")
    return rv.decode("utf-8", "replace")


_SERVICE_RE = re.compile(r"^(?:(beta)\.)?(cover|event)artarchive.org$")
_IMAGE_ID_RE = re.compile(r"[^0-9]")
_MBID_RE = re.compile(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}")


def get_service_name(request):
    match = _SERVICE_RE.match(request.host)
    if match:
        return match.groups()
    return ("", "")


class ArtworkRedirect(object):
    """Handles index and redirect requests."""

    def __init__(self, config, conn, static_cache=None):
        self.config = config
        self.conn = conn
        self.static_cache = static_cache

    def validate_entity(self, request, entity):
        supported_entities = ALL_ENTITY_TYPES

        is_beta, service_name = get_service_name(request)
        # Support requesting any entity type from a beta service.
        # This allows us to support fetching event artwork on the
        # test server (as there is currently only a beta CAA
        # subdomain, not a beta EAA one).
        if not is_beta:
            if service_name == "cover":
                supported_entities = CAA_ENTITY_TYPES
            elif service_name == "event":
                supported_entities = EAA_ENTITY_TYPES

        if entity not in supported_entities:
            raise BadRequest("Only the following entities are supported: " + ", ".join(supported_entities))

    def validate_mbid(self, mbid):
        """Check if an MBID is syntactically valid. If not, raise a BadRequest."""
        if not mbid:
            raise BadRequest("no MBID specified")
        if not _MBID_RE.fullmatch(mbid):
            raise BadRequest("invalid MBID specified")

    def thumbnail(self, filename):
        if "-" not in filename:
            return ""

        _, size = filename.rsplit("-", 1)

        if size.startswith("250"):
            return "-250"
        elif size.startswith("500"):
            return "-500"
        elif size.startswith("1200"):
            return "-1200"
        else:
            return ""

    def _resolve_entity_id_sql(self, entity):
        """Return a SQL subquery that resolves an MBID to an entity id,
        following GID redirects. Use as: WHERE entity.id = ({this})"""
        entity = entity.replace("-", "_")
        quote = self.conn.dialect.identifier_preparer.quote
        t = quote(entity)
        t_redir = quote(f"{entity}_gid_redirect")
        return f"""SELECT COALESCE(
            (SELECT r.id FROM musicbrainz.{t} r
             JOIN musicbrainz.{t_redir} redir ON redir.new_id = r.id
             WHERE redir.gid = :mbid),
            (SELECT r.id FROM musicbrainz.{t} r WHERE r.gid = :mbid)
        )"""

    def resolve_release_cover_index(self, mbid):
        """Query the database to see if the given release has any
        cover art entries, if not respond with a 404 to the request.
        """

        query = text(f"""
            SELECT release.gid
              FROM musicbrainz.release
              JOIN cover_art_archive.cover_art ON release = release.id
             WHERE release.id = ({self._resolve_entity_id_sql("release")})
        """).bindparams(mbid=mbid)

        resultproxy = self.conn.execute(query)
        row = resultproxy.fetchone()
        resultproxy.close()
        if row:
            return row[0]

        raise NotFound("No cover art found for release %s" % (mbid))

    def resolve_event_art_index(self, mbid):
        """Query the database to see if the given event has any
        artwork entries. If not, respond with a 404 to the request.
        """

        query = text(f"""
            SELECT event.gid
              FROM musicbrainz.event
              JOIN event_art_archive.event_art ON event = event.id
             WHERE event.id = ({self._resolve_entity_id_sql("event")})
        """).bindparams(mbid=mbid)

        resultproxy = self.conn.execute(query)
        row = resultproxy.fetchone()
        resultproxy.close()
        if row:
            return row[0]

        raise NotFound("No artwork found for event %s" % (mbid))

    def resolve_release_group_cover_art(self, mbid):
        """This gets the selected front cover art for a release
        group, or picks the earliest front cover art available.  It
        takes a release group GID and returns a release GID -- if the
        release has front cover art. Otherwise it raises a 404
        NotFound exception.
        """

        query = text(f"""
        SELECT DISTINCT ON (release.release_group)
          release.gid AS mbid
        FROM cover_art_archive.index_listing
        JOIN musicbrainz.release
          ON musicbrainz.release.id = cover_art_archive.index_listing.release
        JOIN musicbrainz.release_group
          ON release_group.id = release.release_group
        LEFT JOIN (
          SELECT release, date_year, date_month, date_day
          FROM musicbrainz.release_country
          UNION ALL
          SELECT release, date_year, date_month, date_day
          FROM musicbrainz.release_unknown_country
        ) release_event ON (release_event.release = release.id)
        FULL OUTER JOIN cover_art_archive.release_group_cover_art
        ON release_group_cover_art.release = musicbrainz.release.id
        WHERE release_group.id = ({self._resolve_entity_id_sql("release_group")})
        AND is_front = true
        ORDER BY release.release_group, release_group_cover_art.release,
          (CASE WHEN 'Raw/Unedited' = any(cover_art_archive.index_listing.types)
           THEN 1 ELSE 0 END),
          release_event.date_year, release_event.date_month,
          release_event.date_day
        """).bindparams(mbid=mbid)

        resultproxy = self.conn.execute(query)
        row = resultproxy.fetchone()
        resultproxy.close()
        if row:
            return row[0]

        raise NotFound("No cover art found for release group %s" % (mbid))

    def resolve_release_cover(self, mbid, cover_type, thumbnail):
        """Get the frontiest or backiest cover image."""

        if cover_type == "Front":
            type_filter = "is_front = true"
        elif cover_type == "Back":
            type_filter = "is_back = true"
        else:
            raise NotFound("No %s cover image found for release with identifier %s" % (cover_type.lower(), mbid))

        query = text(
            f"""
            SELECT index_listing.id, image_type.suffix
              FROM cover_art_archive.index_listing
              JOIN musicbrainz.release
                ON cover_art_archive.index_listing.release = musicbrainz.release.id
              JOIN cover_art_archive.image_type
                ON cover_art_archive.index_listing.mime_type = cover_art_archive.image_type.mime_type
             WHERE musicbrainz.release.id = ({self._resolve_entity_id_sql("release")})
               AND """
            + type_filter
            + """
          ORDER BY ordering ASC LIMIT 1;
        """
        ).bindparams(mbid=mbid)

        resultproxy = self.conn.execute(query)
        row = resultproxy.fetchone()
        resultproxy.close()
        if row:
            return "%s%s.%s" % (str(row[0]), thumbnail, row[1])

        raise NotFound("No %s cover image found for release with identifier %s" % (cover_type.lower(), mbid))

    def resolve_event_art(self, mbid, cover_type, thumbnail):
        """Get the frontiest artwork image."""

        if cover_type == "Front":
            type_filter = "is_front = true"
        else:
            raise NotFound("No %s image found for event with identifier %s" % (cover_type.lower(), mbid))

        query = text(
            f"""
            SELECT index_listing.id, image_type.suffix
              FROM event_art_archive.index_listing
              JOIN musicbrainz.event
                ON event_art_archive.index_listing.event = musicbrainz.event.id
              JOIN cover_art_archive.image_type
                ON event_art_archive.index_listing.mime_type = cover_art_archive.image_type.mime_type
             WHERE musicbrainz.event.id = ({self._resolve_entity_id_sql("event")})
               AND """
            + type_filter
            + """
          ORDER BY ordering ASC LIMIT 1;
        """
        ).bindparams(mbid=mbid)

        resultproxy = self.conn.execute(query)
        row = resultproxy.fetchone()
        resultproxy.close()
        if row:
            return "%s%s.%s" % (str(row[0]), thumbnail, row[1])

        raise NotFound("No %s image found for event with identifier %s" % (cover_type.lower(), mbid))

    def resolve_release_image_id(self, mbid, filename, thumbnail):
        """Get a cover image by image id."""

        m = _IMAGE_ID_RE.search(filename)
        possible_id = filename[: m.start()] if m else filename

        try:
            image_id = int(possible_id)
        except ValueError:
            raise BadRequest("%s does not not contain a valid cover image id" % (filename))

        query = text(f"""
            SELECT cover_art.id, suffix
              FROM cover_art_archive.cover_art
              JOIN musicbrainz.release
                ON release = release.id
              JOIN cover_art_archive.image_type
                ON cover_art.mime_type = image_type.mime_type
             WHERE release.id = ({self._resolve_entity_id_sql("release")})
               AND cover_art.id = :image_id
          ORDER BY ordering ASC LIMIT 1;
        """).bindparams(mbid=mbid, image_id=image_id)

        resultproxy = self.conn.execute(query)
        row = resultproxy.fetchone()
        resultproxy.close()
        if row:
            return "%s%s.%s" % (str(row[0]), thumbnail, row[1])

        raise NotFound("cover image with id %s not found" % (image_id))

    def resolve_event_image_id(self, mbid, filename, thumbnail):
        """Get an event image by image id."""

        m = _IMAGE_ID_RE.search(filename)
        possible_id = filename[: m.start()] if m else filename

        try:
            image_id = int(possible_id)
        except ValueError:
            raise BadRequest("%s does not not contain a valid event image id" % (filename))

        query = text(f"""
            SELECT event_art.id, suffix
              FROM event_art_archive.event_art
              JOIN musicbrainz.event
                ON event = event.id
              JOIN cover_art_archive.image_type
                ON event_art.mime_type = image_type.mime_type
             WHERE event.id = ({self._resolve_entity_id_sql("event")})
               AND event_art.id = :image_id
          ORDER BY ordering ASC LIMIT 1;
        """).bindparams(mbid=mbid, image_id=image_id)

        resultproxy = self.conn.execute(query)
        row = resultproxy.fetchone()
        resultproxy.close()
        if row:
            return "%s%s.%s" % (str(row[0]), thumbnail, row[1])

        raise NotFound("event image with id %s not found" % (image_id))

    def _serve_static(self, path, mimetype):
        """Serve a static file from cache or disk."""
        content = self.static_cache and self.static_cache.get(path)
        if content is None:
            if not os.path.isfile(path):
                raise NotFound
            try:
                with open(path, "rb") as f:
                    content = f.read()
            except Exception as e:
                sentry_sdk.capture_exception(e)
                return Response(status=500, response="Internal Server Error")
        return Response(response=content, mimetype=mimetype)

    def handle_index(self, request, index_page=None):
        """Serve up the one static index page."""
        if index_page is None:
            index_page = "index.html"
            _, service_name = get_service_name(request)
            if service_name == "cover":
                index_page = "coverartarchive.html"
            elif service_name == "event":
                index_page = "eventartarchive.html"
        return self._serve_static(os.path.join(self.config.static_path, index_page), "text/html")

    def handle_svg_img(self, name):
        return self._serve_static(os.path.join(self.config.static_path, "img", name), "image/svg+xml")

    def handle_robots(self):
        """Serve up a permissive robots.txt."""
        return Response(response="User-agent: *\nAllow: /", mimetype="text/plain")

    def handle_api(self, request):
        """Redirect to API docs at musicbrainz.org."""
        return request.redirect(code=301, location="https://musicbrainz.org/doc/Cover_Art_Archive/API")

    def handle_dir(self, request, mbid):
        """When the user requests no file, redirect to the root of the bucket
        to give the user an index of what is in the bucket.
        """

        index_url = "%s/mbid-%s/index.json" % (self.config.ia.download_prefix, mbid)
        return request.redirect(code=307, location=index_url)

    def handle_options(self, request, entity):
        """Repond to OPTIONS requests with a status code of 200 and the allowed
        request methods.
        """
        if request.environ["SERVER_PROTOCOL"] != "HTTP/1.1":
            # OPTIONS does not exist in HTTP/1.0
            raise HTTPNotImplemented()
        if entity:
            if not entity == "*":
                self.validate_entity(request, entity)
            elif pop_path_info(request.environ) is not None:
                # There's more than a single asterisk in the request uri
                raise BadRequest()
            else:
                return Response(status=200, headers=[("Allow", "GET, HEAD, OPTIONS")])

            req_mbid = shift_path_info(request.environ)
            self.validate_mbid(req_mbid)

            image_id = shift_path_info(request.environ)

            if image_id:
                image_id = splitext(image_id)[0]
                _split = image_id.split("-", 1)
                id_text = _split[0]

                try:
                    int(id_text)
                except ValueError:
                    if id_text not in ("front", "back"):
                        raise BadRequest()

                if len(_split) > 1:
                    size = _split[1]
                    if size not in ("250", "500", "1200"):
                        raise BadRequest()

        return Response(status=200, headers=[("Allow", "GET, HEAD, OPTIONS")])

    def handle_release(self, request, mbid, filename):
        if not filename:
            mbid = self.resolve_release_cover_index(mbid)
            return self.handle_dir(request, mbid)

        if filename.startswith("front"):
            filename = self.resolve_release_cover(mbid, "Front", self.thumbnail(filename))
        elif filename.startswith("back"):
            filename = self.resolve_release_cover(mbid, "Back", self.thumbnail(filename))
        else:
            filename = self.resolve_release_image_id(mbid, filename, self.thumbnail(filename))

        return self.handle_redirect(request, mbid, filename)

    def handle_release_group(self, request, mbid, filename):
        release_mbid = self.resolve_release_group_cover_art(mbid)
        if not filename:
            return self.handle_dir(request, release_mbid)
        elif filename.startswith("front"):
            filename = self.resolve_release_cover(release_mbid, "Front", self.thumbnail(filename))
            return self.handle_redirect(request, release_mbid, filename)
        else:
            return Response(
                status=400,
                response="%s not supported for release groups." % filename,
            )

    def handle_event(self, request, mbid, filename):
        if not filename:
            mbid = self.resolve_event_art_index(mbid)
            return self.handle_dir(request, mbid)

        if filename.startswith("front"):
            filename = self.resolve_event_art(mbid, "Front", self.thumbnail(filename))
        else:
            filename = self.resolve_event_image_id(mbid, filename, self.thumbnail(filename))

        return self.handle_redirect(request, mbid, filename)

    def _apply_thumb_subs(self, filename):
        m = _THUMB_RE.search(filename)
        if m:
            return filename[: m.start()] + "_thumb" + m.group(1) + ".jpg"
        return filename

    def handle_redirect(self, request, mbid, filename):
        """Handle the 307 redirect."""

        if not filename:
            return Response(status=400, response="no filename specified")

        filename = self._apply_thumb_subs(filename)

        url = "%s/mbid-%s/mbid-%s-%s" % (self.config.ia.download_prefix, mbid, mbid, filename)
        return request.redirect(code=307, location=url)

    def handle(self, request):
        """Handle a request, parse and validate arguments and dispatch the request."""
        entity = pop_path_info(request.environ)

        if request.method == "OPTIONS":
            return self.handle_options(request, entity)

        if not entity:
            return self.handle_index(request)
        elif entity == "coverartarchive.html":
            return self.handle_index(request, "coverartarchive.html")
        elif entity == "eventartarchive.html":
            return self.handle_index(request, "eventartarchive.html")
        elif entity == "robots.txt":
            return self.handle_robots()
        elif entity == "img":
            return self.handle_svg_img(pop_path_info(request.environ))
        elif entity == "api":
            return self.handle_api(request)

        self.validate_entity(request, entity)

        req_mbid = shift_path_info(request.environ)
        self.validate_mbid(req_mbid)
        mbid = uuid.UUID(req_mbid)

        filename = pop_path_info(request.environ)

        if entity == "release-group":
            return self.handle_release_group(request, mbid, filename)
        elif entity == "release":
            return self.handle_release(request, mbid, filename)
        elif entity == "event":
            return self.handle_event(request, mbid, filename)
