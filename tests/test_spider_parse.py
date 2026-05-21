"""Parser-drift detection: feed recorded fixtures to each spider's parse path.

If a court portal redesigns its markup, these tests start yielding zero items
or items missing keys — which is exactly the symptom that's silent today.

Fixtures live in tests/fixtures/:

  * <state>_search.{html,xml,json} — discovery response (every state). Refresh
    via `python tests/refresh_fixtures.py`.
  * <state>_detail.html — one decision's detail page (only bb, ni, whose
    parse() makes a synchronous requests.get() per result row). Refreshed
    manually; see tests/fixtures/README.md.

Missing fixtures cause the corresponding state's test to skip (not fail), so
the suite stays green on a fresh checkout before the cron has run.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import scrapy
from scrapy.http import HtmlResponse, TextResponse, XmlResponse

from gesp.__main__ import STATE_SPIDERS
from gesp.probe import all_states, fixture_filename, is_jportal

FIXTURES = Path(__file__).parent / "fixtures"

REQUIRED_KEYS = {"court", "date", "az", "link"}

# Spiders whose parse() makes a synchronous requests.get() per result row to
# pull metadata off the detail page. The drift test would otherwise hit those
# portals live on every CI run; stub the spider module's `requests` binding to
# replay a recorded detail-page response instead.
_DETAIL_FETCH_STATES = {"bb", "ni"}

# State → discovery URL used to construct the scrapy.http.Response object.
# Doesn't matter exactly which URL; only used for response.url-based logic.
_PROBE_URLS = {
    "bund": "http://www.rechtsprechung-im-internet.de/jportal/docs/bsjrs/",
    "by": "https://www.gesetze-bayern.de/Search/Filter/DOKTYP/rspr",
    "bb": "https://gerichtsentscheidungen.brandenburg.de/suche?&select_source=0",
    "hb": "https://www.landesarbeitsgericht.bremen.de/entscheidungen/entscheidungsuebersicht-11508?max=10&skip=0",
    "ni": "https://voris.wolterskluwer-online.de/search",
    "nw": "https://nrwesuche.justiz.nrw.de/index.php",
    "sn": "https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx",
}

# response.meta required by some spiders' parse() methods.
_RESPONSE_META = {
    "nw": {"body": "", "page": 1},
    "hb": {"c": "lag"},
    "by": {"cookiejar": 0},
    "ni": {"cookiejar": 0},
}

# Spiders whose parse() is a discovery step (yields scrapy.Requests, no items).
# For these, drift-detection means "parse() produces at least one follow-up request",
# not "yields items" — the items come from a downstream callback.
_DISCOVERY_ONLY = {"sn"}


def _make_spider(state: str, tmp_path):
    cls = STATE_SPIDERS[state]
    kwargs = dict(
        path=str(tmp_path),
        courts=[],
        states=[],
        fp=False,
        domains=[],
        store_docId=False,
        postprocess=False,
    )
    # Some spiders take an extra `wait` kwarg; pass it conditionally.
    if "wait" in cls.__init__.__code__.co_varnames:
        kwargs["wait"] = 0
    spider = cls(**kwargs)
    # Many spiders set `self.headers` in start(); seed it for tests that bypass start().
    if not hasattr(spider, "headers") or not spider.headers:
        spider.headers = {"x-csrf-token": "test-token"}
    elif "x-csrf-token" not in spider.headers:
        spider.headers["x-csrf-token"] = "test-token"
    return spider


def _load_or_skip(state: str) -> bytes:
    fp = FIXTURES / fixture_filename(state)
    if not fp.exists():
        pytest.skip(f"fixture {fp.name} not present — run `python tests/refresh_fixtures.py {state}`")
    return fp.read_bytes()


def _stub_detail_fetch(state: str, monkeypatch) -> None:
    """Replay a recorded detail-page response for spiders that call requests.get inside parse().

    Patches `gesp.spiders.<state>.requests` (the module-level binding, not the
    shared requests module's `.get` attribute) so the stub is scoped to this
    spider only. Skips when the static `<state>_detail.html` fixture isn't
    present — mirrors `_load_or_skip` for the discovery fixture.
    """
    if state not in _DETAIL_FETCH_STATES:
        return
    fp = FIXTURES / f"{state}_detail.html"
    if not fp.exists():
        pytest.skip(f"detail fixture {fp.name} not present — capture one detail page manually")
    body = fp.read_bytes()

    class _StubRequests:
        @staticmethod
        def get(*_args, **_kwargs):
            return SimpleNamespace(text=body.decode("utf-8"))

    monkeypatch.setattr(f"gesp.spiders.{state}.requests", _StubRequests)


def _items_and_requests(parse_results):
    items, requests = [], []
    for r in parse_results:
        if isinstance(r, scrapy.Request):
            requests.append(r)
        else:
            items.append(r)
    return items, requests


def _parse(state: str, spider, body: bytes):
    """Drive the spider down the parse path for `state`, return (items, requests)."""
    url = _PROBE_URLS.get(state, f"https://{state}.example/")

    if is_jportal(state):
        # jportal spiders parse JSON via extract_data(); the response just needs
        # to be a TextResponse with the JSON in its body.
        response = TextResponse(url=url, body=body, encoding="utf-8")
        return list(spider.extract_data(response)), []

    response_kwargs = dict(url=url, body=body, encoding="utf-8")
    if state in _RESPONSE_META:
        response_kwargs["request"] = scrapy.Request(url=url, meta=_RESPONSE_META[state])
    response_cls = XmlResponse if state == "bund" else HtmlResponse
    response = response_cls(**response_kwargs)

    return _items_and_requests(spider.parse(response))


# ─── Parametrized over every supported state ──────────────────────────────────
@pytest.mark.parametrize("state", all_states())
def test_spider_parses_fixture(state, tmp_path, monkeypatch):
    body = _load_or_skip(state)
    _stub_detail_fetch(state, monkeypatch)
    spider = _make_spider(state, tmp_path)
    items, requests = _parse(state, spider, body)
    if state in _DISCOVERY_ONLY:
        assert requests, (
            f"{state}: parse() yielded zero follow-up requests from {fixture_filename(state)}. "
            "The discovery page's form / viewstate XPath likely changed."
        )
    else:
        assert items, (
            f"{state}: parse() yielded zero items from {fixture_filename(state)}. "
            "Likely the portal's markup changed — inspect the fixture diff and update the spider."
        )


@pytest.mark.parametrize("state", sorted(set(all_states()) - _DISCOVERY_ONLY))
def test_items_have_required_keys(state, tmp_path, monkeypatch):
    body = _load_or_skip(state)
    _stub_detail_fetch(state, monkeypatch)
    spider = _make_spider(state, tmp_path)
    items, _ = _parse(state, spider, body)
    for item in items:
        missing = REQUIRED_KEYS - set(item.keys())
        assert not missing, f"{state}: item missing keys {missing}: {item!r}"


# ─── Sanity checks on the probe registry itself ───────────────────────────────
def test_every_state_in_probe_registry():
    assert set(all_states()) == set(STATE_SPIDERS.keys())


def test_jportal_fixtures_are_valid_json():
    """If a jportal fixture exists, it must be syntactically valid JSON."""
    for state in all_states():
        if not is_jportal(state):
            continue
        fp = FIXTURES / fixture_filename(state)
        if not fp.exists():
            continue
        try:
            json.loads(fp.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            pytest.fail(f"{state}: fixture is not valid JSON: {e}")


# ─── bb: detail-fetch failure paths ───────────────────────────────────────────
# parse() does a synchronous requests.get per result row to pull the AZ off
# the detail page. Each failure mode (network error, missing metadata, missing
# anchor) must skip the row rather than crash the spider.
def _bb_response(tmp_path, body_bytes):
    spider = _make_spider("bb", tmp_path)
    response = HtmlResponse(url=_PROBE_URLS["bb"], body=body_bytes, encoding="utf-8")
    return spider, response


def test_bb_skips_row_on_detail_fetch_failure(tmp_path, monkeypatch):
    import requests as _requests

    body = _load_or_skip("bb")

    # `RequestException` must be reachable through the stub — the spider's except
    # clause resolves it via the same module binding we're replacing here.
    class _Boom:
        RequestException = _requests.RequestException

        @staticmethod
        def get(*_args, **_kwargs):
            raise _requests.RequestException("network down")

    monkeypatch.setattr("gesp.spiders.bb.requests", _Boom)
    monkeypatch.setattr("gesp.spiders.bb.timelib.sleep", lambda _s: None)
    spider, response = _bb_response(tmp_path, body)
    items, _ = _items_and_requests(spider.parse(response))
    assert items == []  # every row's detail fetch failed → no items, but no crash


def test_bb_skips_row_when_detail_lacks_az(tmp_path, monkeypatch):
    import requests as _requests

    body = _load_or_skip("bb")
    # Detail page without the //div[@id='metadata'] block the spider looks for.
    detail_html = "<html><body><h1>no metadata table here</h1></body></html>"

    class _NoAz:
        RequestException = _requests.RequestException

        @staticmethod
        def get(*_args, **_kwargs):
            return SimpleNamespace(text=detail_html)

    monkeypatch.setattr("gesp.spiders.bb.requests", _NoAz)
    monkeypatch.setattr("gesp.spiders.bb.timelib.sleep", lambda _s: None)
    spider, response = _bb_response(tmp_path, body)
    items, _ = _items_and_requests(spider.parse(response))
    assert items == []


def test_bb_skips_row_when_docid_missing(tmp_path, monkeypatch):
    # Synthetic search page with one row that has no <a href> at all.
    # Before the guard, `self.base_url + None` raised TypeError.
    body = (
        b"<html><body>"
        b"<table id='resultlist'><tbody>"
        b"<tr><td>1</td><td>2</td><td>2024-01-01</td><td>4</td><td>OLG</td></tr>"
        b"</tbody></table>"
        b"</body></html>"
    )
    monkeypatch.setattr("gesp.spiders.bb.timelib.sleep", lambda _s: None)
    spider, response = _bb_response(tmp_path, body)
    items, _ = _items_and_requests(spider.parse(response))
    assert items == []
