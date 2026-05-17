from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import BadZipFile, ZipFile

import pytest

from gesp.src.create_file import save_as_html, save_as_pdf

FIXTURES = Path(__file__).parent / "fixtures"


def test_save_as_html_none_item_returns_none(tmp_path):
    assert save_as_html(None, "nw", str(tmp_path), False) is None
    assert list(tmp_path.iterdir()) == []


def test_save_as_pdf_none_item_returns_none(tmp_path):
    assert save_as_pdf(None, "hb", str(tmp_path)) is None
    assert list(tmp_path.iterdir()) == []


def test_save_as_html_missing_link_no_crash(tmp_path):
    """An item with metadata but no 'link' or 'text' should log + return without raising."""
    item = {"court": "lg-koeln", "date": "20090813", "az": "37-O-143-09"}
    # No link, no text — falls to the else branch that used to KeyError on item["link"].
    save_as_html(item, "nw", str(tmp_path), False)


def test_save_as_pdf_missing_link_no_crash(tmp_path):
    item = {"court": "ovg", "date": "20200101", "az": "1-A-1-20"}
    # No link, no body — falls to the else branch that used to KeyError on item["link"].
    save_as_pdf(item, "hb", str(tmp_path))


def test_save_as_html_sanitizes_windows_unsafe_filename_parts(tmp_path):
    (tmp_path / "nw").mkdir()
    item = {
        "court": "lg:koeln",
        "date": "20200101",
        "az": '1/O:1?20*"',
        "docId": "/raw\\doc:42",
        "text": "<html></html>",
        "filetype": "html",
    }

    assert save_as_html(item, "nw", str(tmp_path), True) is item

    files = list((tmp_path / "nw").iterdir())
    assert [f.name for f in files] == ["lg-koeln_20200101_1-O-1-20_raw-doc-42.html"]


def test_save_as_pdf_sanitizes_windows_unsafe_filename_parts(tmp_path):
    (tmp_path / "hb").mkdir()
    item = {
        "court": "ovg:hb",
        "date": "20200101",
        "az": "1/A?1*20",
        "link": "https://example.test/file.pdf",
        "body": b"%PDF",
    }

    assert save_as_pdf(item, "hb", str(tmp_path)) is item

    files = list((tmp_path / "hb").iterdir())
    assert [f.name for f in files] == ["ovg-hb_20200101_1-A-1-20.pdf"]


def test_zip_xml_output_replaces_existing_target(tmp_path):
    by_dir = tmp_path / "by"
    by_dir.mkdir()
    target = by_dir / "ag_20200101_1-A-1.xml"
    target.write_text("old", encoding="utf-8")
    buf = BytesIO()
    with ZipFile(buf, "w") as zip_file:
        zip_file.writestr("nested/source.xml", "new")
    response = SimpleNamespace(content=buf.getvalue(), raise_for_status=lambda: None)
    item = {
        "court": "ag",
        "date": "20200101",
        "az": "1-A-1",
        "link": "https://example.test/archive.zip",
    }

    with patch("gesp.src.create_file.requests.get", return_value=response):
        assert save_as_html(item, "by", str(tmp_path), False) is item

    assert target.read_text(encoding="utf-8") == "new"
    assert item["xmlfilename"] == str(target)


def test_zip_xml_recovers_archive_with_trailing_junk(tmp_path):
    """gesetze-bayern.de occasionally appends junk (including a second, bogus
    EOCD signature) after a valid archive. Python's backwards EOCD scan lands
    on the junk EOCD and refuses to open the file; the trimming helper trims
    everything past the first *valid* EOCD so the real archive is recoverable.
    """
    (tmp_path / "by").mkdir()
    content = (FIXTURES / "by_corrupt.zip").read_bytes()
    # Sanity: the raw bytes really do trip vanilla zipfile.
    with pytest.raises(BadZipFile):
        with ZipFile(BytesIO(content)):
            pass

    response = SimpleNamespace(content=content, raise_for_status=lambda: None)
    item = {
        "court": "ag",
        "date": "20200101",
        "az": "1-A-1",
        "link": "https://www.gesetze-bayern.de/Content/Zip/Y-300-Z-BECKRS-B-2022-N-15750",
    }

    with patch("gesp.src.create_file.requests.get", return_value=response):
        assert save_as_html(item, "by", str(tmp_path), False) is item

    target = tmp_path / "by" / "ag_20200101_1-A-1.xml"
    assert target.exists()
    assert target.read_bytes().lstrip(b"\xef\xbb\xbf").startswith(b"<?xml")
    assert item["xmlfilename"] == str(target)


def test_zip_xml_bad_zip_download_does_not_raise(tmp_path, monkeypatch, capsys):
    (tmp_path / "by").mkdir()
    response = SimpleNamespace(content=b"<html>not a zip</html>", raise_for_status=lambda: None)
    item = {
        "court": "ag",
        "date": "20200101",
        "az": "1-A-1",
        "link": "https://example.test/archive.zip",
    }

    monkeypatch.setattr("gesp.src.create_file.time.sleep", lambda _seconds: None)
    with patch("gesp.src.create_file.requests.get", return_value=response):
        assert save_as_html(item, "by", str(tmp_path), False) is None

    captured = capsys.readouterr()
    assert "downloaded content is not a readable zip" in captured.out
