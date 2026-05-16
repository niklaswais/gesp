from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

from gesp.src.create_file import save_as_html, save_as_pdf


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
