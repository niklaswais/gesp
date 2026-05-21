"""Guards on the Brandenburg extractor: every xpath result must be length-checked
before indexing, so a Brandenburg detail page with missing markup logs and
returns None instead of raising IndexError."""

from lxml import html

from gesp.src.get_text import bb


def _item_with_tree(html_str):
    return {
        "link": "https://gerichtsentscheidungen.brandenburg.de/gerichtsentscheidung/x",
        "az": "1-A-1",
        "wait": 0,
        "tree": html.fromstring(html_str),
    }


def test_bb_returns_none_when_header_missing():
    item = _item_with_tree("<html><body><p>no h1#header here</p></body></html>")
    assert bb(item) is None
    assert "text" not in item and "filetype" not in item


def test_bb_returns_none_for_empty_placeholder_page():
    # Header text "Entscheidung" is the portal's placeholder for an empty page.
    item = _item_with_tree("<html><body><h1 id='header'>Entscheidung</h1></body></html>")
    assert bb(item) is None
    assert "text" not in item and "filetype" not in item


def test_bb_returns_none_when_metadata_block_missing():
    # Header is fine but the metadata div the function tostring()s is absent.
    item = _item_with_tree(
        "<html><body><h1 id='header'>Urteil vom 1.1.2024</h1><p>no metadata div anywhere on this page</p></body></html>"
    )
    assert bb(item) is None
    assert "text" not in item and "filetype" not in item


def test_bb_returns_item_on_happy_path():
    item = _item_with_tree(
        "<html><body>"
        "<h1 id='header'>Urteil vom 1.1.2024</h1>"
        "<div id='metadata'><span>meta</span></div>"
        "<div>body content</div>"
        "</body></html>"
    )
    result = bb(item)
    assert result is item
    assert item["filetype"] == "html"
    assert "meta" in item["text"]
    assert "body content" in item["text"]
