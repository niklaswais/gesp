# -*- coding: utf-8 -*-
import lzma
import src.config
from datetime import datetime


class FingerprintExportPipeline:
    def open_spider(self, spider):
        self.lzmac = lzma.LZMACompressor()
        self.path = spider.path + "fingerprint.json"
        self.file = open(self.path, "w")
        general_info = '{"version":"%s", "date": "%s", "args":{"c":"%s","s":"%s"}}' % (src.config.version, datetime.timestamp(datetime.now()), ",".join(spider.courts), ",".join(spider.states))
        self.file.write(self.lzmac.compress(general_info))

    def close_spider(self, spider):
        self.file.write(self.lzmac.compress("}"))
        self.file.write(self.lzmac.flush())
        self.file.close()

    def process_item(self, item, spider):
        entry = '{"s":"%s","c":"%s","d":"%s","az":"%s"' % (spider.name[7:], item["court"], item["date"], item["az"])
        if "link" in item:
            entry = entry + ',"link":"%s"}' % (item["link"])
        elif "header" in item and "body" in item:
            entry = entry + ',"link":"%s"}' % (item["link"])
        self.file.write(self.lzmac.compress(entry))
        return item