# -*- coding: utf-8 -*-
import requests
from lxml import html
from src.output import output

class BBToTextPipeline:
    def process_item(self, item, spider):
        if not "tree" in item:
            item["tree"] = html.fromstring(requests.get(item["link"]).text)
        if not item["tree"].xpath("//h1[@id='header']/text()")[0].rstrip().strip() == "Entscheidung": # Herausfiltern von leeren Seiten
            # Dokument Aufräumen (nur bestimmte Bereiche übernehmen)...
            body_meta = html.tostring(item["tree"].xpath("//div[@id='metadata']")[0]).decode("utf-8")
            body_content = html.tostring(item["tree"].xpath("//div[@id='metadata']/following::div[1]")[0]).decode("utf-8")
            doc = "<html><head><title>%s</title></head><body>%s%s</body></html>" % (item["az"], body_meta, body_content)
            item["text"] = doc
            item["filetype"] = "html"
            return item
        else:
            output("could not retrieve " + item["link"], "err")