"""Guards on Sachsen's OVG sub-portal parser: each row in the results table has
multiple unprotected xpath/.get() accesses; a malformed row must be skipped
instead of crashing the discovery loop."""

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

from scrapy.http import HtmlResponse

from gesp.spiders.sn import SpdrSN
from tests._async_helpers import adrain, stub_async_machinery


def _make_spider(tmp_path):
    return SpdrSN(
        path=str(tmp_path),
        courts=[],
        states=[],
        fp=False,
        domains=[],
        store_docId=False,
        postprocess=False,
        wait=0,
    )


def _response(body_html):
    return HtmlResponse(
        url="https://www.justiz.sachsen.de/ovgentschweb/searchlist.phtml",
        body=body_html.encode("utf-8"),
        encoding="utf-8",
    )


def test_ovg_skips_row_without_href(tmp_path, monkeypatch):
    stub_async_machinery("sn", monkeypatch)
    body = "<html><body><table><tr><td>x</td><td><a>no href</a></td></tr></table></body></html>"
    spider = _make_spider(tmp_path)
    assert asyncio.run(adrain(spider.parse_results_ovg(_response(body)))) == []


def test_ovg_skips_row_when_href_lacks_quoted_id(tmp_path, monkeypatch):
    stub_async_machinery("sn", monkeypatch)
    # The id-extraction regex looks for a single-quoted substring; if absent, skip.
    body = (
        "<html><body><table><tr>"
        "<td>x</td>"
        '<td><a href="plain-href-without-quotes">Entscheidung vomXYZ</a></td>'
        "</tr></table></body></html>"
    )
    spider = _make_spider(tmp_path)
    assert asyncio.run(adrain(spider.parse_results_ovg(_response(body)))) == []


def test_ovg_skips_row_when_text_missing(tmp_path, monkeypatch):
    stub_async_machinery("sn", monkeypatch)
    body = "<html><body><table><tr><td>x</td><td><a href=\"openDoc('42')\"></a></td></tr></table></body></html>"
    spider = _make_spider(tmp_path)
    assert asyncio.run(adrain(spider.parse_results_ovg(_response(body)))) == []


def test_ovg_skips_row_when_text_too_short_for_slice(tmp_path, monkeypatch):
    stub_async_machinery("sn", monkeypatch)
    # The existing code does raw_data[15:] — anything shorter than 16 chars
    # used to silently produce empty strings that broke downstream parsing.
    body = (
        "<html><body><table><tr><td>x</td><td><a href=\"openDoc('42')\">too short</a></td></tr></table></body></html>"
    )
    spider = _make_spider(tmp_path)
    assert asyncio.run(adrain(spider.parse_results_ovg(_response(body)))) == []


def test_ovg_skips_detail_link_without_href(tmp_path, monkeypatch):
    """A valid row reaches the detail-page fetch; the inner loop now guards
    `link.xpath('./@href')` before indexing. Synthesize a detail page where
    the only target='_blank' anchor has no href — the row must drop without
    raising."""
    search_body = (
        "<html><body><table><tr>"
        "<td>x</td>"
        "<td><a href=\"openDoc('42')\">Entscheidung vom 01.01.2024 (1 A 1/24)</a></td>"
        "</tr></table></body></html>"
    )
    detail_body = "<html><body><a target='_blank'>anchor without href</a></body></html>"

    monkeypatch.setattr("gesp.spiders.sn.timelib.sleep", lambda _s: None)
    stub_async_machinery("sn", monkeypatch)
    with patch(
        "gesp.spiders.sn.requests.get",
        return_value=SimpleNamespace(text=detail_body),
    ):
        spider = _make_spider(tmp_path)
        assert asyncio.run(adrain(spider.parse_results_ovg(_response(search_body)))) == []


def test_ovg_yields_item_through_detail_fetch(tmp_path, monkeypatch):
    """Happy path through parse_results_ovg after the async conversion: a valid
    search row, a stubbed intermediate detail page with one target='_blank' anchor
    pointing at a pdf, must yield exactly one item with the expected fields."""
    # 15-char prefix matches the parser's raw_data[15:] slice; the parenthesised
    # date is what data[-11:-1] picks up; the text before "(" is the AZ.
    raw_text = ("x" * 15) + "1 A 1/24 (01.01.2024)"
    search_body = (
        "<html><body><table><tr>"
        "<td>x</td>"
        f"<td><a href=\"openWindow('abc123')\">{raw_text}</a></td>"
        "</tr></table></body></html>"
    )
    detail_body = (
        "<html><body>"
        "<a target='_blank' href='documents/x.pdf'>file</a>"
        "</body></html>"
    )

    monkeypatch.setattr("gesp.spiders.sn.timelib.sleep", lambda _s: None)
    stub_async_machinery("sn", monkeypatch)
    with patch(
        "gesp.spiders.sn.requests.get",
        return_value=SimpleNamespace(text=detail_body),
    ):
        spider = _make_spider(tmp_path)
        items = asyncio.run(adrain(spider.parse_results_ovg(_response(search_body))))

    assert len(items) == 1
    assert items[0]["court"] == "ovg"
    assert items[0]["az"] == "1 A 1/24"
    assert items[0]["date"] == "01.01.2024"
    assert items[0]["link"].endswith("documents/x.pdf")
