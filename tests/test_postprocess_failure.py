"""Failure semantics for parse_data_from_html and RawExporter."""

from unittest.mock import patch

import pytest

from gesp.src.htmlparser import DecisionHTMLParser, parse_data_from_html


def _item(**overrides):
    item = {"court": "ag-test", "az": "1-23", "text": "<html><body>x</body></html>"}
    item.update(overrides)
    return item


def test_parse_returns_parser_on_success(tmp_path):
    """When feed/complete_attributes/save_to_file all succeed, return the parser."""
    with (
        patch.object(DecisionHTMLParser, "feed", return_value=None),
        patch.object(DecisionHTMLParser, "complete_attributes", return_value=None),
        patch.object(DecisionHTMLParser, "save_to_file", return_value=None),
    ):
        result = parse_data_from_html(_item(), "nw", str(tmp_path))
    assert isinstance(result, DecisionHTMLParser)


def test_parse_returns_none_when_feed_raises(tmp_path, capsys):
    with patch.object(DecisionHTMLParser, "feed", side_effect=ValueError("boom")):
        result = parse_data_from_html(_item(), "nw", str(tmp_path))
    assert result is None
    out = capsys.readouterr().out
    assert "postprocess nw" in out
    assert "ag-test/1-23" in out


def test_parse_returns_none_when_save_raises(tmp_path, capsys):
    with (
        patch.object(DecisionHTMLParser, "feed", return_value=None),
        patch.object(DecisionHTMLParser, "complete_attributes", return_value=None),
        patch.object(DecisionHTMLParser, "save_to_file", side_effect=KeyError("missing")),
    ):
        result = parse_data_from_html(_item(), "sh", str(tmp_path))
    assert result is None
    assert "postprocess sh" in capsys.readouterr().out


def test_parse_returns_none_when_text_key_missing(tmp_path, capsys):
    """Item without 'text' / 'xmlfilename' fails cleanly, no crash."""
    item = {"court": "ag", "az": "1"}  # no text, no xmlfilename
    result = parse_data_from_html(item, "nw", str(tmp_path))
    assert result is None
    assert "could not load source" in capsys.readouterr().out


def test_parse_returns_none_when_xmlfilename_missing(tmp_path, capsys):
    """For bund/by, a missing on-disk xml file fails cleanly."""
    item = {"court": "bgh", "az": "1", "xmlfilename": str(tmp_path / "does-not-exist.xml")}
    result = parse_data_from_html(item, "bund", str(tmp_path))
    assert result is None
    assert "could not load source" in capsys.readouterr().out


@pytest.mark.parametrize("mode", ["bund", "by", "nw", "sh", "ni"])
def test_parse_logs_item_identifier_on_failure(tmp_path, capsys, mode):
    """Failure messages must include court/az so logs are actionable."""
    item = _item(court="lg-X", az="42-Y")
    if mode in ("bund", "by"):
        item["xmlfilename"] = str(tmp_path / "missing.xml")
    result = parse_data_from_html(item, mode, str(tmp_path))
    assert result is None
    assert "lg-X/42-Y" in capsys.readouterr().out
