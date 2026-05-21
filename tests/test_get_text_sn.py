"""Guards on the Sachsen OVG extractor: the intermediate page must contain a
target='_blank' link, but if the portal layout drops it, the function must log
and return None rather than IndexError."""

from types import SimpleNamespace
from unittest.mock import patch

from gesp.src.get_text import sn


def test_sn_ovg_missing_detail_link_returns_none(monkeypatch):
    monkeypatch.setattr("gesp.src.get_text.timelib.sleep", lambda _s: None)
    # HTML without any //a[@target='_blank'] anchors.
    response = SimpleNamespace(text="<html><body><p>no detail link here</p></body></html>")
    item = {
        "link": "https://www.justiz.sachsen.de/ovgentschweb/intermediate.phtml?id=42",
        "az": "1-A-1",
        "wait": 0,
    }
    original_link = item["link"]
    with patch("gesp.src.get_text.requests.get", return_value=response):
        result = sn(item, {})
    assert result is None
    assert item["link"] == original_link  # untouched
