"""Unit tests that don't require a database."""

import pytest
from werkzeug.exceptions import BadRequest
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Response

from artwork_redirect.request import (
    ArtworkRedirect,
    get_service_name,
    pop_path_info,
)
from artwork_redirect.utils import statuscode


class TestPopPathInfo:
    def test_basic(self):
        environ = {"PATH_INFO": "/release/abc", "SCRIPT_NAME": ""}
        assert pop_path_info(environ) == "release"
        assert environ["PATH_INFO"] == "/abc"

    def test_empty(self):
        environ = {"PATH_INFO": "", "SCRIPT_NAME": ""}
        assert pop_path_info(environ) is None

    def test_single_segment(self):
        environ = {"PATH_INFO": "/front.jpg", "SCRIPT_NAME": ""}
        assert pop_path_info(environ) == "front.jpg"
        assert environ["PATH_INFO"] == ""

    def test_leading_slashes(self):
        environ = {"PATH_INFO": "///foo/bar", "SCRIPT_NAME": ""}
        assert pop_path_info(environ) == "foo"


class TestGetServiceName:
    def test_coverartarchive(self):
        builder = EnvironBuilder(method="GET")
        request = builder.get_request()
        request.host = "coverartarchive.org"
        assert get_service_name(request) == (None, "cover")

    def test_eventartarchive(self):
        builder = EnvironBuilder(method="GET")
        request = builder.get_request()
        request.host = "eventartarchive.org"
        assert get_service_name(request) == (None, "event")

    def test_beta_coverartarchive(self):
        builder = EnvironBuilder(method="GET")
        request = builder.get_request()
        request.host = "beta.coverartarchive.org"
        assert get_service_name(request) == ("beta", "cover")

    def test_unknown_host(self):
        builder = EnvironBuilder(method="GET")
        request = builder.get_request()
        request.host = "example.com"
        assert get_service_name(request) == ("", "")


class TestValidateMbid:
    def setup_method(self):
        self.redirect = ArtworkRedirect(config=None, conn=None)

    def test_valid_mbid(self):
        # Should not raise
        self.redirect.validate_mbid("ab5245f6-ae8d-49a5-be42-6347f6c0330e")

    def test_empty_mbid(self):
        with pytest.raises(BadRequest):
            self.redirect.validate_mbid("")

    def test_none_mbid(self):
        with pytest.raises(BadRequest):
            self.redirect.validate_mbid(None)

    def test_invalid_mbid(self):
        with pytest.raises(BadRequest):
            self.redirect.validate_mbid("not-a-valid-mbid")

    def test_uppercase_mbid(self):
        with pytest.raises(BadRequest):
            self.redirect.validate_mbid("AB5245F6-AE8D-49A5-BE42-6347F6C0330E")


class TestThumbnail:
    def setup_method(self):
        self.redirect = ArtworkRedirect(config=None, conn=None)

    def test_250(self):
        assert self.redirect.thumbnail("12345-250.jpg") == "-250"

    def test_500(self):
        assert self.redirect.thumbnail("12345-500.jpg") == "-500"

    def test_1200(self):
        assert self.redirect.thumbnail("12345-1200.jpg") == "-1200"

    def test_no_thumbnail(self):
        assert self.redirect.thumbnail("12345.jpg") == ""

    def test_unknown_size(self):
        assert self.redirect.thumbnail("12345-999.jpg") == ""


class TestHandleOptions:
    def setup_method(self):
        self.redirect = ArtworkRedirect(config=None, conn=None)

    def _options_request(self, path_info):
        """Simulate environ after entity has been popped by handle()."""
        from artwork_redirect.server import Request

        builder = EnvironBuilder(method="OPTIONS")
        env = builder.get_environ()
        env["SERVER_PROTOCOL"] = "HTTP/1.1"
        env["PATH_INFO"] = path_info
        return Request(env)

    def test_image_id_with_size(self):
        # PATH_INFO after "release" has been popped: /mbid/12345-250.jpg
        request = self._options_request("/ab5245f6-ae8d-49a5-be42-6347f6c0330e/12345-250.jpg")
        result = self.redirect.handle_options(request, "release")
        assert isinstance(result, Response)
        assert result.status_code == 200

    def test_image_id_invalid_size(self):
        request = self._options_request("/ab5245f6-ae8d-49a5-be42-6347f6c0330e/12345-999.jpg")
        with pytest.raises(BadRequest):
            self.redirect.handle_options(request, "release")

    def test_front(self):
        request = self._options_request("/ab5245f6-ae8d-49a5-be42-6347f6c0330e/front")
        result = self.redirect.handle_options(request, "release")
        assert result.status_code == 200


class TestHandleRedirect:
    def setup_method(self):
        self.redirect = ArtworkRedirect(config=None, conn=None)

    def test_empty_filename_returns_response(self):
        from artwork_redirect.server import Request

        builder = EnvironBuilder(method="GET")
        request = Request(builder.get_environ())
        result = self.redirect.handle_redirect(request, "some-mbid", "")
        assert isinstance(result, Response)
        assert result.status_code == 400

    def test_thumb_substitution_250(self):
        assert self.redirect._apply_thumb_subs("100000001-250.jpg") == "100000001_thumb250.jpg"

    def test_thumb_substitution_500(self):
        assert self.redirect._apply_thumb_subs("100000001-500.jpg") == "100000001_thumb500.jpg"

    def test_thumb_substitution_1200(self):
        assert self.redirect._apply_thumb_subs("100000001-1200.jpg") == "100000001_thumb1200.jpg"

    def test_thumb_substitution_no_match(self):
        assert self.redirect._apply_thumb_subs("100000001.jpg") == "100000001.jpg"


class TestStatusCode:
    def test_200(self):
        assert statuscode(200) == "200 OK"

    def test_404(self):
        assert statuscode(404) == "404 Not Found"

    def test_501(self):
        assert statuscode(501) == "501 Not Implemented"
