# -*- coding: utf-8 -*-
import os
import requests
from io import BytesIO
from output import output
from zipfile import ZipFile

class PostPipeline:
    def open_spider(self, spider):
        if (not os.path.exists(spider.path + spider.name[7:])):
            try:
                os.makedirs(spider.path + spider.name[7:])
            except:
                output(f"could not create folder {spider.path}{spider.name[7:]}", "err")

    def process_item(self, item, spider):
        output("downloading " + item["link"] + "...")
        if spider.name == "spider_bund": # Sonderfall Bund: *.zip mit *.xml
            filename = item["court"] + "_" + item["date"] + "_" + item["az"] + ".xml"
            try:
                with ZipFile(BytesIO((requests.get(item["link"]).content))) as zip_ref: # Im RAM entpacken
                    for zipinfo in zip_ref.infolist(): # Teilweise auch Bilder in .zip enthalten
                        if (zipinfo.filename.endswith(".xml")):
                            zipinfo.filename = filename
                            zip_ref.extract(zipinfo, spider.path + "bund/")
            except:
                output(f"could not create file {filename}", "err")
        else:
            if "text" in item:
                filename = spider.path + spider.name[7:] + "/" + item["court"] + "_" + item["date"] + "_" + item["az"] + "." + item["filetype"]
                try:
                    with open(filename, "w") as f:
                        f.write(item["text"])
                except:
                    output(f"could not create file {filename}", "err")
            else:
                output("could not retrieve " + item["link"], "err")
                