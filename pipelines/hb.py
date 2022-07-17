# -*- coding: utf-8 -*-
import os
import requests
from lxml import html
from src.output import output

class HBPipeline:
    def open_spider(self, spider):
        if (not os.path.exists(spider.path + spider.name[7:])):
            try:
                os.makedirs(spider.path + spider.name[7:])
            except:
                output(f"could not create folder {spider.path}{spider.name[7:]}", "err")

    def process_item(self, item, spider):
        if ("link" in item): # Kein item["text"]: In Bremen nur PDF
            try:
                req = requests.get(item["link"])
            except:
                output("could not retrieve " + item["link"], "err")
            else: 
                output("downloading " + req.url + "...")
                filename = spider.path + spider.name[7:] + "/" + item["court"] + "_" + item["date"] + "_" + item["az"] + ".pdf"
                try:
                    with open(filename, "wb") as f:
                        f.write(req.content)
                except:
                    output(f"could not create file {filename}", "err")