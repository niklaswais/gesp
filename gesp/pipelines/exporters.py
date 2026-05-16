import json
import lzma
import os
from datetime import datetime

from ..src import config
from ..src.create_file import save_as_html, save_as_pdf
from ..src.htmlparser import parse_data_from_html
from ..src.output import output


class ExportPipeline:
    def open_spider(self, spider):
        spdr_folder = os.path.join(spider.path, spider.name[7:])
        if not os.path.exists(spdr_folder):
            try:
                os.makedirs(spdr_folder)
            except OSError:
                output(f"could not create folder {spdr_folder}", "err")


class ExportAsHtmlPipeline(ExportPipeline):
    def process_item(self, item, spider):
        save_as_html(item, spider.name[7:], spider.path, spider.store_docId)
        return item


class ExportAsPdfPipeline(ExportPipeline):
    def process_item(self, item, spider):
        save_as_pdf(item, spider.name[7:], spider.path)
        return item


class FingerprintExportPipeline:
    def open_spider(self, spider):
        if not spider.fp:
            return
        self.lzmac = lzma.LZMACompressor()
        self.path = os.path.join(spider.path, "fingerprint.xz")
        self.file = open(self.path, "wb")
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
        self.file.write(self.lzmac.compress(header.encode()))

    def close_spider(self, spider):
        if spider.fp:
            self.file.write(self.lzmac.flush())
            self.file.close()

    def process_item(self, item, spider):
        if not spider.fp:
            return item
        record = {
            "s": spider.name[7:],
            "c": item["court"],
            "d": item["date"],
            "az": item["az"],
        }
        if "docId" in item:
            record["docId"] = item["docId"]
        elif "link" in item:
            record["link"] = item["link"]
        entry = json.dumps(record) + "|"
        self.file.write(self.lzmac.compress(entry.encode()))
        return item


class RawExporter:
    def process_item(self, item, spider):
        if item is None:
            return None
        if item.get("postprocess"):
            parse_data_from_html(item, spider.name[7:], spider.path)
        return item
