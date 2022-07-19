# -*- coding: utf-8 -*-
import requests
from lxml import html
from src.output import output

class NIToTextPipeline:
    def process_item(self, item, spider):
        # Entscheidungstext bereinigen (kein Menü etc.)
        try:
            tree = html.fromstring(requests.get(item["link"]).text)
        except:
            output("could not parse " + item["link"], "err")
        else:
            if tree.xpath("//div[@id='bsentscheidung']"): # Herausfiltern von leeren Seiten
                body_content = html.tostring(tree.xpath("//div[@class='jurisText']")[0]).decode("utf-8")
                doc = "<html><head><title>%s</title></head><body>%s</body></html>" % (item["az"], body_content)
                item["text"] = doc
                item["filetype"] = "html"
                return item
            else:
                output("empty page " + item["link"], "err")