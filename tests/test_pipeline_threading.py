import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from twisted.internet.defer import Deferred, succeed

from gesp.pipelines.exporters import ExportAsHtmlPipeline, ExportAsPdfPipeline
from gesp.pipelines.texts import TextsPipeline


def _spider(name, **extra):
    return SimpleNamespace(name=f"spider_{name}", path="/tmp/x", store_docId=False, **extra)


@pytest.mark.parametrize(
    "pipeline_cls, target_func_name, extra_args",
    [
        (ExportAsHtmlPipeline, "save_as_html", [False]),
        (ExportAsPdfPipeline, "save_as_pdf", []),
    ],
)
def test_exporters_defer_with_unpacked_args(pipeline_cls, target_func_name, extra_args):
    pipe = pipeline_cls()
    item = {"court": "ag", "date": "20240101", "az": "1-2-3"}
    spider = _spider("bw")
    # succeed(None) makes deferred_to_future resolve immediately so the
    # coroutine completes inside asyncio.run().
    with patch("gesp.pipelines.exporters.deferToThread", return_value=succeed(None)) as m:
        asyncio.run(pipe.process_item(item, spider=spider))
    args, _ = m.call_args
    fn, *rest = args
    assert fn.__name__ == target_func_name
    assert rest == [item, "bw", "/tmp/x"] + extra_args


def test_texts_copies_headers_and_cookies():
    pipe = TextsPipeline()
    headers = {"Referer": "before"}
    cookies = {"r3autologin": "x"}
    spider = _spider("bw", headers=headers, cookies=cookies)
    item = {"docId": "abc", "wait": 0, "az": "1-2-3", "link": "u"}
    with patch("gesp.pipelines.texts.deferToThread", return_value=succeed(None)) as m:
        asyncio.run(pipe.process_item(item, spider=spider))
    args, _ = m.call_args
    _, _, name, passed_headers, passed_cookies = args
    assert name == "bw"
    assert passed_headers == headers and passed_headers is not headers
    assert passed_cookies == cookies and passed_cookies is not cookies


def test_texts_tolerates_missing_headers_cookies():
    pipe = TextsPipeline()
    spider = _spider("bb")  # bb has no headers/cookies on self
    with patch("gesp.pipelines.texts.deferToThread", return_value=succeed(None)) as m:
        asyncio.run(pipe.process_item({}, spider=spider))
    args, _ = m.call_args
    _, _, name, passed_headers, passed_cookies = args
    assert name == "bb"
    assert passed_headers is None and passed_cookies is None


def test_semaphore_serializes_per_pipeline_instance():
    """Two items into the same pipeline instance: the second must wait until the
    first's threaded call resolves. This is the per-portal courtesy guarantee."""
    pipe = ExportAsHtmlPipeline()
    pending = [Deferred(), Deferred()]
    handed_out = []

    def fake_defer(*args, **kwargs):
        d = pending[len(handed_out)]
        handed_out.append(d)
        return d

    async def driver():
        with patch("gesp.pipelines.exporters.deferToThread", side_effect=fake_defer) as m:
            spider = _spider("bw")
            t1 = asyncio.ensure_future(pipe.process_item({"i": 1}, spider=spider))
            t2 = asyncio.ensure_future(pipe.process_item({"i": 2}, spider=spider))
            # Let both tasks reach their await point.
            for _ in range(5):
                await asyncio.sleep(0)
            assert m.call_count == 1, "second item slipped past the semaphore before the first resolved"
            # Firing pending[0] synchronously runs the Twisted release chain,
            # which admits t2's acquire Deferred → executes deferToThread again.
            pending[0].callback(None)
            assert m.call_count == 2, "second item never admitted after the first resolved"
            # Drain both tasks so asyncio.run doesn't warn about pending futures.
            pending[1].callback(None)
            await t1
            await t2

    asyncio.run(driver())
