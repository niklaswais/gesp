# -*- coding: utf-8 -*-
import lzma
import src.config
from datetime import datetime


class FingerprintExportPipeline:
    def open_spider(self, spider):
        if spider.fp:
            self.lzmac = lzma.LZMACompressor()
            self.path = spider.path + "fingerprint.xz"
            self.file = open(self.path, "wb")
            general_info = '{"version":"%s", "date": "%s", "args":{"c":"%s","s":"%s"}}' % (src.config.__version__, str(datetime.timestamp(datetime.now())), ",".join(spider.courts), ",".join(spider.states))
            self.file.write(self.lzmac.compress(general_info.encode()))

    def close_spider(self, spider):
        if spider.fp:
            self.file.write(self.lzmac.compress("}".encode()))
            self.file.write(self.lzmac.flush())
            self.file.close()

    def process_item(self, item, spider):
        if spider.fp:
            entry = '{"s":"%s","c":"%s","d":"%s","az":"%s"' % (spider.name[7:], item["court"], item["date"], item["az"])
            if "link" in item and not "docId" in item and not "body" in item: # "Klassisch" über Link
                entry = entry + ',"link":"%s"}' % (item["link"])
            elif "docId" in item: # JSON-Post (BE, HH, ....)
                entry = entry + ',"docId":"%s"}' % (item["docId"])
            elif "body" in item: # Sachsen (zum Teil)
                entry = entry + ',"body":"%s"}' % (item["body"])
            self.file.write(self.lzmac.compress(entry.encode()))
            return item