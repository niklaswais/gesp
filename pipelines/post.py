# -*- coding: utf-8 -*-
import os
from src.output import output

class PostPipeline:
    def open_spider(self, spider):
        if (not os.path.exists(spider.path + spider.name[7:])):
            try:
                os.makedirs(spider.path + spider.name[7:])
            except:
                output(f"could not create folder {spider.path}{spider.name[7:]}", "err")

    def process_item(self, item, spider):
        output("downloading " + item["link"] + "...")
        return item