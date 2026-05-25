import json
import lzma
import os
from datetime import datetime

from scrapy.exceptions import DropItem
from scrapy.utils.defer import deferred_to_future
from twisted.internet.defer import DeferredSemaphore
from twisted.internet.threads import deferToThread

from ..src import config
from ..src.create_file import save_as_html, save_as_pdf
from ..src.htmlparser import parse_data_from_html
from ..src.output import output
from ._base import CrawlerAware


class ExportPipeline(CrawlerAware):
    def __init__(self):
        self.sem = DeferredSemaphore(1)

    def open_spider(self, spider=None):
        spider = self._spider(spider)
        spdr_folder = os.path.join(spider.path, spider.name[7:])
        if not os.path.exists(spdr_folder):
            try:
                os.makedirs(spdr_folder)
            except OSError:
                output(f"could not create folder {spdr_folder}", "err")


class ExportAsHtmlPipeline(ExportPipeline):
    async def process_item(self, item, spider=None):
        spider = self._spider(spider)
        name, path, store_docId = spider.name[7:], spider.path, spider.store_docId
        return await deferred_to_future(
            self.sem.run(deferToThread, save_as_html, item, name, path, store_docId)
        )


class ExportAsPdfPipeline(ExportPipeline):
    async def process_item(self, item, spider=None):
        spider = self._spider(spider)
        name, path = spider.name[7:], spider.path
        return await deferred_to_future(self.sem.run(deferToThread, save_as_pdf, item, name, path))


class FingerprintExportPipeline(CrawlerAware):
    # Singleton state shared across per-spider instances so concurrently-running
    # spiders append to the same fp.xz instead of each truncating it on open.
    _file = None
    _compressor = None
    _refcount = 0

    def open_spider(self, spider=None):
        spider = self._spider(spider)
        if not spider.fp:
            return
        cls = type(self)
        if cls._file is None:
            cls._compressor = lzma.LZMACompressor()
            cls._file = open(os.path.join(spider.path, "fp.xz"), "wb")
            header = (
                json.dumps(
                    {
                        "version": config.__version__,
                        "date": str(datetime.timestamp(datetime.now())),
                        "args": {"c": ",".join(spider.courts), "s": ",".join(spider.states)},
                    }
                )
                + "|"
            )
            cls._file.write(cls._compressor.compress(header.encode()))
        cls._refcount += 1

    def close_spider(self, spider=None):
        spider = self._spider(spider)
        if not spider.fp:
            return
        cls = type(self)
        cls._refcount -= 1
        if cls._refcount == 0 and cls._file is not None:
            try:
                cls._file.write(cls._compressor.flush())
            finally:
                cls._file.close()
                cls._file = None
                cls._compressor = None

    def process_item(self, item, spider=None):
        if item is None:
            # An upstream extractor (e.g. get_text.nw) returns None when the
            # decision fetch fails; save_as_html and RawExporter already guard
            # against that, and we need to as well or fp.xz writing crashes.
            return None
        spider = self._spider(spider)
        if not spider.fp:
            return item
        cls = type(self)
        record = {
            "s": spider.name[7:],
            "c": item["court"],
            "d": item["date"],
            "az": item["az"],
        }
        if "docId" in item:
            record["docId"] = item["docId"]
        if "link" in item:
            record["link"] = item["link"]
        entry = json.dumps(record) + "|"
        cls._file.write(cls._compressor.compress(entry.encode()))
        return item


class RawExporter(CrawlerAware):
    def process_item(self, item, spider=None):
        if item is None:
            return None
        if not item.get("postprocess"):
            return item
        spider = self._spider(spider)
        # Pipeline order matters: RawExporter (900) runs after Export* (300/400)
        # and FingerprintExportPipeline (400/500/600), so dropping here does
        # not unwrite the raw html/pdf or poison fp.xz — it only flags the
        # optional preprocessed/<file> as missing, and Scrapy records the drop
        # in item_dropped_count.
        if parse_data_from_html(item, spider.name[7:], spider.path) is None:
            raise DropItem(f"postprocess failed for {item.get('court', '?')}/{item.get('az', '?')}")
        return item
