# -*- coding: utf-8 -*-
import requests
from io import BytesIO
from src.output import output
from zipfile import ZipFile

class PdfExportPipeline:
    def process_item(self, item, spider):
        if not "req" in item and "link" in item: # Bremen / Sachsen: OVG-Subportal; AG/LG/OLG-Supportal bereits mit req
            try:
                req = requests.get(item["link"])
            except:
                output("could not retrieve " + item["link"], "err")
        #### PROBLEM: item["link"] für "Download..."-Ausgabe bei post.py; muss in spider / pipeline docs
        filename = spider.path + spider.name[7:] + "/" + item["court"] + "_" + item["date"] + "_" + item["az"] + ".pdf"
        try:
            with open(filename, "wb") as f:
                f.write(req.content)
        except:
            output(f"could not create file {filename}", "err")