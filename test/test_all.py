# Copyright (C) 2012 MetaBrainz Foundation
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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys
import os
import os.path

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(_root)

import codecs
import unittest
from contextlib import closing
from artwork_redirect_server import load_config
from artwork_redirect.server import Server
from werkzeug.wrappers import Response
from werkzeug.test import Client, EnvironBuilder


class All(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = Server(load_config(test=True))

        sqlfile = os.path.join(_root, "test", "add_data.sql")
        with codecs.open(sqlfile, "rb", "utf-8") as c:
            with closing(cls.app.engine.connect()) as connection:
                connection.execute(c.read())

    def setUp(self):
        self.server = Client(self.app, Response)

    def verifyRedirect(self, src, dst, **kwargs):
        response = self.server.get(src, **kwargs)
        self.assertEqual(response.status, '307 TEMPORARY REDIRECT')
        self.assertEqual(response.headers['Location'], dst)
        self.assertEqual(response.data, b"See: %s\n" % (dst.encode('utf-8')))

    def test_caa_index(self):
        response = self.server.get('/')

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.mimetype, 'text/html')
        self.assertTrue(b'<title>Cover Art Archive</title>' in response.data)
        self.assertTrue(b'Images in the archive are curated' in response.data)

    def test_front(self):
        response = self.server.get('/release/98f08de3-c91c-4180-a961-06c205e63669/front')
        self.assertEqual(response.status, '404 NOT FOUND')
        self.assertTrue(b'No front cover image found for' in response.data)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        expected = 'http://archive.org/download/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80-100000001'
        req = '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80'

        self.verifyRedirect(req + '/front',         expected + '.jpg')
        self.verifyRedirect(req + '/front.jpg',     expected + '.jpg')
        self.verifyRedirect(req + '/front-250',     expected + '_thumb250.jpg')
        self.verifyRedirect(req + '/front-250.jpg', expected + '_thumb250.jpg')
        self.verifyRedirect(req + '/front-500',     expected + '_thumb500.jpg')
        self.verifyRedirect(req + '/front-500.jpg', expected + '_thumb500.jpg')
        self.verifyRedirect(req + '/front-1200',     expected + '_thumb1200.jpg')
        self.verifyRedirect(req + '/front-1200.jpg', expected + '_thumb1200.jpg')

    def test_back(self):
        response = self.server.get('/release/98f08de3-c91c-4180-a961-06c205e63669/back')
        self.assertEqual(response.status, '404 NOT FOUND')
        self.assertTrue(b'No back cover image found for' in response.data)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        expected = 'http://archive.org/download/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80-999999999'
        req = '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80'

        self.verifyRedirect(req + '/back',         expected + '.jpg')
        self.verifyRedirect(req + '/back.jpg',     expected + '.jpg')
        self.verifyRedirect(req + '/back-250',     expected + '_thumb250.jpg')
        self.verifyRedirect(req + '/back-250.jpg', expected + '_thumb250.jpg')
        self.verifyRedirect(req + '/back-500',     expected + '_thumb500.jpg')
        self.verifyRedirect(req + '/back-500.jpg', expected + '_thumb500.jpg')
        self.verifyRedirect(req + '/back-1200',     expected + '_thumb1200.jpg')
        self.verifyRedirect(req + '/back-1200.jpg', expected + '_thumb1200.jpg')

    def test_image(self):

        response = self.server.get('/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/444444444.jpg')
        self.assertEqual(response.status, '404 NOT FOUND')
        self.assertTrue(b'cover image with id 444444444 not found' in response.data)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        expected = 'http://archive.org/download/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80-999999999'
        req = '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/999999999'

        self.verifyRedirect(req + '.jpg',     expected + '.jpg')
        self.verifyRedirect(req + '-250.jpg', expected + '_thumb250.jpg')
        self.verifyRedirect(req + '-500.jpg', expected + '_thumb500.jpg')
        self.verifyRedirect(req + '-1200.jpg', expected + '_thumb1200.jpg')

    def test_resolve_image_id_with_invalid_cover_image_id(self):
        _id = "invalid"
        response = self.server.get("release/353710ec-1509-4df9-8ce2-9bd5011e3b80/" + _id)
        self.assertEqual(response.status, '400 BAD REQUEST')

    def test_release_index(self):
        response = self.server.get('/release/98f08de3-c91c-4180-a961-06c205e63669/')
        self.assertEqual(response.status, '404 NOT FOUND')
        self.assertTrue(b'No cover art found for' in response.data)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        expected = 'http://archive.org/download/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80'
        req = '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80'

        self.verifyRedirect(req + '/', expected + '/index.json')

    def test_direct_https(self):
        expected = 'https://archive.org/download/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80'
        expimg = expected + '/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80-'
        req = '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80'

        kw = {'base_url': 'https://coverartarchive.org'}

        self.verifyRedirect(req + '/', expected + '/index.json', **kw)
        self.verifyRedirect(req + '/front', expimg + '100000001.jpg', **kw)
        self.verifyRedirect(req + '/999999999.jpg', expimg + '999999999.jpg', **kw)

    def test_proxied_https(self):
        expected = 'https://archive.org/download/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80'
        expimg = expected + '/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80-'
        req = '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80'

        kw = {'headers': [('X-Forwarded-Proto', 'https')]}

        self.verifyRedirect(req + '/', expected + '/index.json', **kw)
        self.verifyRedirect(req + '/front', expimg + '100000001.jpg', **kw)
        self.verifyRedirect(req + '/999999999.jpg', expimg + '999999999.jpg', **kw)

    def test_release_group(self):

        response = self.server.get('/release-group/c9b6b442-38d5-11e2-a5e5-001cc0fde924')
        self.assertEqual(response.status, '404 NOT FOUND')
        self.assertTrue(b'No cover art found for release group' in response.data)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        response = self.server.get('/release-group/c9b6b442-38d5-11e2-a5e5-001cc0fde924/front')
        self.assertEqual(response.status, '404 NOT FOUND')
        self.assertTrue(b'No cover art found for release group' in response.data)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        expected = 'http://archive.org/download/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80-100000001'
        req = '/release-group/67a63246-0de4-4cd8-8ce2-35f70a17f92b'

        self.verifyRedirect(req + '/front',         expected + '.jpg')
        self.verifyRedirect(req + '/front.jpg',     expected + '.jpg')
        self.verifyRedirect(req + '/front-250',     expected + '_thumb250.jpg')
        self.verifyRedirect(req + '/front-250.jpg', expected + '_thumb250.jpg')
        self.verifyRedirect(req + '/front-500',     expected + '_thumb500.jpg')
        self.verifyRedirect(req + '/front-500.jpg', expected + '_thumb500.jpg')
        self.verifyRedirect(req + '/front-1200',     expected + '_thumb1200.jpg')
        self.verifyRedirect(req + '/front-1200.jpg', expected + '_thumb1200.jpg')

        expected = 'http://archive.org/download/mbid-353710ec-1509-4df9-8ce2-9bd5011e3b80'

        self.verifyRedirect(req,       expected + '/index.json')
        self.verifyRedirect(req + '/', expected + '/index.json')

    def test_options_method(self):
        for path in [
            '/',
            '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/999999999',
            '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/front',
            '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/back',
            '/release-group/67a63246-0de4-4cd8-8ce2-35f70a17f92b',
            '/release-group/67a63246-0de4-4cd8-8ce2-35f70a17f92b/front',
            # 404s
            '/release/98f08de3-c91c-4180-a961-06c205e63669/',
            '/release/98f08de3-c91c-4180-a961-06c205e63669/front',
            '/release/98f08de3-c91c-4180-a961-06c205e63669/back',
            '/release-group/c9b6b442-38d5-11e2-a5e5-001cc0fde924',
            '/release-group/c9b6b442-38d5-11e2-a5e5-001cc0fde924/front',
            '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/444444444.jpg',
        ]:
            response = self.server.open(path=path,
                                        method='OPTIONS')
            self.assertEqual(response.status, '200 OK')
            self.assertTrue('Allow' in response.headers)
            self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        for path in [
            '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/foo',
            '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/front-100',
            '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/-250',
            '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/front-back-500',
            '/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/1200-front',
        ]:
            response = self.server.open(path=path,
                                        method='OPTIONS')
            self.assertEqual(response.status, '400 BAD REQUEST')
            self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

    def test_options_method_asterisk(self):
        response = self.server.open(path='/*',
                                    method='OPTIONS')
        self.assertEqual(response.status, '200 OK')
        self.assertTrue('Allow' in response.headers)

        response = self.server.open(path='/*foo',
                                    method='OPTIONS')
        self.assertEqual(response.status, '400 BAD REQUEST')

    def test_options_501_on_http_10(self):
        env = EnvironBuilder(path='/*foo', method='OPTIONS')
        env.server_protocol = 'HTTP/1.0'
        response = self.server.open(env)
        self.assertEqual(response.status, '501 NOT IMPLEMENTED')

    def test_mbid_validation(self):
        # Missing digit
        response = self.server.get('/release/98f08de3-c91c-4180-a961-06c205e6366')
        self.assertEqual(response.status, '400 BAD REQUEST')
        self.assertTrue(b'invalid MBID specified' in response.data)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        # Percent-encoded newline at the end (%0A)
        response = self.server.get('/release/98f08de3-c91c-4180-a961-06c205e63669%0A')
        self.assertEqual(response.status, '400 BAD REQUEST')
        self.assertTrue(b'invalid MBID specified' in response.data)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        # Extra digits prefixed
        response = self.server.get('/release/000098f08de3-c91c-4180-a961-06c205e63669')
        self.assertEqual(response.status, '400 BAD REQUEST')
        self.assertTrue(b'invalid MBID specified' in response.data)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')
