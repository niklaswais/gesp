"""Failure-path tests for the ten copy-pasted jportal extractors in get_text.py.

The implementation is duplicated rather than shared through a helper (see the
plan note), so each state's hardening must be verified independently. The four
parametrized cases below exercise the four exception classes the except tuple
now catches: RequestException, ValueError (incl. JSONDecodeError),
KeyError (missing `head`/`text`), and LxmlError.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests
from lxml import etree

from gesp.src import get_text

JPORTAL = [
    (get_text.be, "be"),
    (get_text.bw, "bw"),
    (get_text.he, "he"),
    (get_text.hh, "hh"),
    (get_text.mv, "mv"),
    (get_text.rp, "rp"),
    (get_text.sh, "sh"),
    (get_text.sl, "sl"),
    (get_text.st, "st"),
    (get_text.th, "th"),
]


def _make_item():
    return {
        "docId": "TEST-DOC-1",
        "link": "https://example.test/doc",
        "az": "1-A-1",
        "wait": 0,
    }


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    # Defensive: every function gates the sleep behind `if item["wait"]`,
    # but stub it anyway so a regression here can't slow the suite.
    monkeypatch.setattr("gesp.src.get_text.timelib.sleep", lambda _s: None)


@pytest.mark.parametrize("fn, name", JPORTAL)
def test_jportal_swallows_request_exception(fn, name):
    item = _make_item()
    with patch("gesp.src.get_text.requests.post", side_effect=requests.RequestException("boom")):
        result = fn(item, {}, {})
    assert result is None, f"{name}: expected None on RequestException"
    assert "text" not in item and "filetype" not in item


@pytest.mark.parametrize("fn, name", JPORTAL)
def test_jportal_swallows_json_decode_error(fn, name):
    item = _make_item()
    response = MagicMock()
    response.json.side_effect = ValueError("not json")  # mirrors how JSONDecodeError surfaces
    with patch("gesp.src.get_text.requests.post", MagicMock(return_value=response)):
        result = fn(item, {}, {})
    assert result is None, f"{name}: expected None on JSON decode error"
    assert "text" not in item and "filetype" not in item


@pytest.mark.parametrize("fn, name", JPORTAL)
def test_jportal_swallows_missing_head_key(fn, name):
    item = _make_item()
    response = MagicMock()
    response.json.return_value = {"text": "<p>body</p>"}  # no "head"
    with patch("gesp.src.get_text.requests.post", MagicMock(return_value=response)):
        result = fn(item, {}, {})
    assert result is None, f"{name}: expected None on missing 'head' key"
    assert "text" not in item and "filetype" not in item


@pytest.mark.parametrize("fn, name", JPORTAL)
def test_jportal_swallows_lxml_error(fn, name):
    item = _make_item()
    response = MagicMock()
    response.json.return_value = {"head": "<h1>ok</h1>", "text": "<p>body</p>"}
    with (
        patch("gesp.src.get_text.requests.post", MagicMock(return_value=response)),
        patch("gesp.src.get_text.html.fromstring", side_effect=etree.LxmlError("parse failed")),
    ):
        result = fn(item, {}, {})
    assert result is None, f"{name}: expected None on LxmlError"
    assert "text" not in item and "filetype" not in item


@pytest.mark.parametrize("fn, name", JPORTAL)
def test_jportal_success_returns_item(fn, name):
    """Sanity: the happy path still works after the try-block enlargement."""
    item = _make_item()
    response = MagicMock()
    response.json.return_value = {"head": "<h1>ok</h1>", "text": "<p>body</p>"}
    with patch("gesp.src.get_text.requests.post", MagicMock(return_value=response)):
        result = fn(item, {}, {})
    assert result is item, f"{name}: expected the populated item on success"
    assert item["filetype"] == "html"
    assert "<p>body</p>" in item["text"]
