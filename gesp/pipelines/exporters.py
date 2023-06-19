# -*- coding: utf-8 -*-
import lzma
import os
from ..src import config
from datetime import datetime
from ..src.output import output
from ..src.create_file import save_as_html, save_as_pdf
from ..src.htmlparser import parse_data_from_html

class ExportPipeline:
    def open_spider(self, spider):
        spdr_folder = os.path.join(spider.path, spider.name[7:])
        if (not os.path.exists(spdr_folder)):
            try:
                os.makedirs(spdr_folder)
            except:
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
        if spider.fp:
            self.lzmac = lzma.LZMACompressor()
            self.path = os.path.join(spider.path, "fingerprint.xz")
            self.file = open(self.path, "wb")
            general_info = '{"version":"%s","date":"%s","args":{"c":"%s","s":"%s"}}|' % (config.__version__, str(datetime.timestamp(datetime.now())), ",".join(spider.courts), ",".join(spider.states))
            self.file.write(self.lzmac.compress(general_info.encode()))

    def close_spider(self, spider):
        if spider.fp:
            self.file.write(self.lzmac.flush())
            self.file.close()

    def process_item(self, item, spider):
        if spider.fp:
            entry = '{"s":"%s","c":"%s","d":"%s","az":"%s"' % (spider.name[7:], item["court"], item["date"], item["az"])
            if "link" in item and not "docId" in item: # "Klassisch" über Link
                entry = entry + ',"link":"%s"}' % (item["link"])
            elif "docId" in item: # JSON-Post (BE, HH, ....)
                entry = entry + ',"docId":"%s"}' % (item["docId"])
            entry = entry + "|" # Ende-Zeichen für Deocder
            self.file.write(self.lzmac.compress(entry.encode()))
        return item ### items needs to be returned for further processing


class RawExporter:
    def process_item(self, item, spider):
        if (item is None): return
        if ("postprocess" in item):
            if (item["postprocess"] is not None):
                if (item["postprocess"] == True):
                   parse_data_from_html(item,spider.name[7:], spider.path) 
        return item

