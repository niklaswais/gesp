from unittest.mock import MagicMock, patch

import requests

from gesp.src.fingerprint import _csrf_headers


def _mock_post_returning(token):
    response = MagicMock()
    response.json.return_value = {"csrfToken": token}
    return MagicMock(return_value=response)


def test_csrf_headers_injects_token_on_success():
    with patch("gesp.src.fingerprint.requests.post", _mock_post_returning("abc-123")):
        headers = _csrf_headers("be", "https://example/init", {"User-Agent": "x"}, {}, "body")
    assert headers["x-csrf-token"] == "abc-123"
    assert headers["User-Agent"] == "x"  # Existing headers preserved.


def test_csrf_headers_swallows_network_error():
    with patch("gesp.src.fingerprint.requests.post", side_effect=requests.RequestException("boom")):
        headers = _csrf_headers("be", "https://example/init", {"User-Agent": "x"}, {}, "body")
    assert "x-csrf-token" not in headers
    assert headers["User-Agent"] == "x"


def test_csrf_headers_swallows_malformed_json():
    bad_response = MagicMock()
    bad_response.json.side_effect = ValueError("not json")
    with patch("gesp.src.fingerprint.requests.post", MagicMock(return_value=bad_response)):
        headers = _csrf_headers("be", "https://example/init", {}, {}, "body")
    assert "x-csrf-token" not in headers
