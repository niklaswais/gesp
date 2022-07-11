# -*- coding: utf-8 -*-
import re
from lxml import html
from output import output

class BBPipeline:
    def process_item(self, item, spider):
        #Senate/Kammern abschneiden
        item["court"] = re.split(r"([-]?\d+)", item["court"])[0]
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
