from types import SimpleNamespace
from unittest.mock import patch

from gesp.pipelines.exporters import FingerprintExportPipeline
from gesp.src.fingerprint import Fingerprint


def _make_spider(tmp_path, name="spider_nw"):
    return SimpleNamespace(
        fp=True,
        path=str(tmp_path),
        name=name,
        courts=["lg", "ag"],
        states=["nw"],
    )


def test_roundtrip_link_and_docid_entries(tmp_path):
    spider = _make_spider(tmp_path)
    pipeline = FingerprintExportPipeline()
    pipeline.open_spider(spider)
    pipeline.process_item(
        {"court": "lg-koeln", "date": "20200101", "az": "1-O-1-20", "link": "https://example/a"},
        spider,
    )
    pipeline.process_item(
        {"court": "lg-berlin", "date": "20200202", "az": "5-O-2-20", "docId": "doc-xyz"},
        spider,
    )
    pipeline.close_spider(spider)

    fp_file = tmp_path / "fp.xz"
    assert fp_file.exists()

    entries = list(Fingerprint.load_file(str(fp_file)))
    # First entry is the header (version/date/args), then the two items.
    assert len(entries) == 3
    header, e1, e2 = entries

    assert set(header.keys()) >= {"version", "date", "args"}
    assert header["args"]["c"] == "lg,ag"
    assert header["args"]["s"] == "nw"

    assert e1 == {"s": "nw", "c": "lg-koeln", "d": "20200101", "az": "1-O-1-20", "link": "https://example/a"}
    assert e2 == {"s": "nw", "c": "lg-berlin", "d": "20200202", "az": "5-O-2-20", "docId": "doc-xyz"}


def test_roundtrip_chunk_boundary_safe(tmp_path):
    """Many items in one file — exercises buffered reading across LZMA chunk boundaries."""
    spider = _make_spider(tmp_path)
    pipeline = FingerprintExportPipeline()
    pipeline.open_spider(spider)
    for n in range(50):
        pipeline.process_item(
            {"court": f"lg-{n}", "date": "20200101", "az": f"{n}-O-{n}-20", "link": f"https://example/{n}"},
            spider,
        )
    pipeline.close_spider(spider)

    entries = list(Fingerprint.load_file(str(tmp_path / "fp.xz")))
    # 1 header + 50 items.
    assert len(entries) == 51
    items = entries[1:]
    assert items[0]["c"] == "lg-0"
    assert items[-1]["c"] == "lg-49"
    assert all(e["s"] == "nw" for e in items)


def test_roundtrip_preserves_link_when_docid_also_present(tmp_path):
    """jportal items carry both docId and link; reconstruction needs the link
    because mv/rp/sh/sl/st/th extractors set Referer = item['link']."""
    spider = _make_spider(tmp_path, name="spider_mv")
    spider.states = ["mv"]
    pipeline = FingerprintExportPipeline()
    pipeline.open_spider(spider)
    pipeline.process_item(
        {
            "court": "ovg",
            "date": "20200101",
            "az": "1-A-1-20",
            "link": "https://www.landesrecht-mv.de/bsmv/document/MVRE12345",
            "docId": "MVRE12345",
        },
        spider,
    )
    pipeline.close_spider(spider)

    entries = list(Fingerprint.load_file(str(tmp_path / "fp.xz")))
    _, record = entries
    assert record["link"] == "https://www.landesrecht-mv.de/bsmv/document/MVRE12345"
    assert record["docId"] == "MVRE12345"


def _write_fp(tmp_path, state, record):
    spider = _make_spider(tmp_path, name=f"spider_{state}")
    spider.states = [state]
    pipeline = FingerprintExportPipeline()
    pipeline.open_spider(spider)
    pipeline.process_item(record, spider)
    pipeline.close_spider(spider)
    return tmp_path / "fp.xz"


def test_reconstruction_supplies_wait_to_jportal_extractor(tmp_path):
    """The jportal extractors (mv/sh/sl/st/th/rp) read item['wait']
    unconditionally; reconstruction must seed it or every download KeyErrors."""
    fp_file = _write_fp(
        tmp_path,
        "mv",
        {
            "court": "ovg",
            "date": "20200101",
            "az": "1-A-1-20",
            "link": "https://www.landesrecht-mv.de/bsmv/document/MVRE1",
            "docId": "MVRE1",
        },
    )

    captured = {}

    def fake_extractor(item, headers, cookies):
        captured["item"] = dict(item)
        item["text"] = "<html></html>"
        item["filetype"] = "html"
        return item

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    with (
        patch("gesp.src.fingerprint._csrf_headers", return_value={"x-csrf-token": "t"}),
        patch.dict("gesp.src.fingerprint._JPORTAL_EXTRACTORS", {"mv": fake_extractor}),
        patch("gesp.src.fingerprint.save_as_html"),
    ):
        Fingerprint(str(out_dir), str(fp_file), store_docId=False, wait=2.5)

    assert captured["item"]["wait"] == 2.5
    assert captured["item"]["link"] == "https://www.landesrecht-mv.de/bsmv/document/MVRE1"


def test_reconstruction_supplies_wait_to_simple_extractor(tmp_path):
    """Simple HTML extractors (bb/by/ni/nw) also read item['wait']."""
    fp_file = _write_fp(
        tmp_path,
        "nw",
        {
            "court": "lg-koeln",
            "date": "20200101",
            "az": "1-O-1-20",
            "link": "https://nrwesuche.justiz.nrw.de/doc/1",
        },
    )

    captured = {}

    def fake_extractor(item):
        captured["item"] = dict(item)
        item["text"] = "<html></html>"
        item["filetype"] = "html"
        return item

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    with (
        patch.dict("gesp.src.fingerprint._SIMPLE_EXTRACTORS", {"nw": fake_extractor}),
        patch("gesp.src.fingerprint.save_as_html"),
    ):
        Fingerprint(str(out_dir), str(fp_file), store_docId=False, wait=0)

    assert captured["item"]["wait"] == 0


def test_ni_extractor_fetches_detail_page_when_tree_absent(tmp_path):
    """Reconstruction never populates item['tree']; ni() must fetch the detail
    page itself instead of bailing with 'could not retrieve tree'."""
    from gesp.src.get_text import ni

    html_body = "<html><body><article><p>Entscheidungstext</p></article></body></html>"
    response = SimpleNamespace(text=html_body)
    item = {
        "court": "lg-hannover",
        "date": "20200101",
        "az": "1-O-1-20",
        "link": "https://voris.wolterskluwer-online.de/browse/document/abc",
        "wait": 0,
    }

    with patch("gesp.src.get_text.requests.get", return_value=response) as mock_get:
        result = ni(item)

    assert mock_get.called, "ni() must fetch item['link'] when tree is absent"
    assert result is item
    assert "<article>" in item["text"] and "Entscheidungstext" in item["text"]
    assert item["filetype"] == "html"


def test_by_reconstruction_dispatches_to_save_as_html(tmp_path):
    """by items store a ZIP link; reconstruction must bypass the by() text
    extractor and call save_as_html, which unpacks the zip."""
    fp_file = _write_fp(
        tmp_path,
        "by",
        {
            "court": "ag-muenchen",
            "date": "20200101",
            "az": "1-A-1-20",
            "link": "https://www.gesetze-bayern.de/Zip/Y-300-Z-1",
        },
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    with patch("gesp.src.fingerprint.save_as_html") as mock_save:
        Fingerprint(str(out_dir), str(fp_file), store_docId=False, wait=0)

    mock_save.assert_called_once()
    item_arg, state_arg, *_ = mock_save.call_args.args
    assert state_arg == "by"
    assert item_arg["link"] == "https://www.gesetze-bayern.de/Zip/Y-300-Z-1"


def test_fp_disabled_writes_nothing(tmp_path):
    spider = _make_spider(tmp_path)
    spider.fp = False
    pipeline = FingerprintExportPipeline()
    pipeline.open_spider(spider)
    pipeline.process_item({"court": "lg", "date": "x", "az": "y", "link": "z"}, spider)
    pipeline.close_spider(spider)
    assert not (tmp_path / "fp.xz").exists()


def test_process_item_tolerates_none(tmp_path):
    """Extractors in get_text return None on fetch/parse failure (e.g. nw()
    after 'could not retrieve'). The fingerprint pipeline must not crash on
    those — save_as_html and RawExporter already guard the same way."""
    spider = _make_spider(tmp_path)
    pipeline = FingerprintExportPipeline()
    pipeline.open_spider(spider)
    assert pipeline.process_item(None, spider) is None
    pipeline.close_spider(spider)
