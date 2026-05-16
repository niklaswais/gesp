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
        Fingerprint(str(out_dir), str(fp_file), store_docId=False, wait=True)

    assert captured["item"]["wait"] is True
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
        Fingerprint(str(out_dir), str(fp_file), store_docId=False, wait=False)

    assert captured["item"]["wait"] is False


def test_fp_disabled_writes_nothing(tmp_path):
    spider = _make_spider(tmp_path)
    spider.fp = False
    pipeline = FingerprintExportPipeline()
    pipeline.open_spider(spider)
    pipeline.process_item({"court": "lg", "date": "x", "az": "y", "link": "z"}, spider)
    pipeline.close_spider(spider)
    assert not (tmp_path / "fp.xz").exists()
