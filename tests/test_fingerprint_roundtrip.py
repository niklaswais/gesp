from types import SimpleNamespace

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

    fp_file = tmp_path / "fingerprint.xz"
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

    entries = list(Fingerprint.load_file(str(tmp_path / "fingerprint.xz")))
    # 1 header + 50 items.
    assert len(entries) == 51
    items = entries[1:]
    assert items[0]["c"] == "lg-0"
    assert items[-1]["c"] == "lg-49"
    assert all(e["s"] == "nw" for e in items)


def test_fp_disabled_writes_nothing(tmp_path):
    spider = _make_spider(tmp_path)
    spider.fp = False
    pipeline = FingerprintExportPipeline()
    pipeline.open_spider(spider)
    pipeline.process_item({"court": "lg", "date": "x", "az": "y", "link": "z"}, spider)
    pipeline.close_spider(spider)
    assert not (tmp_path / "fingerprint.xz").exists()
