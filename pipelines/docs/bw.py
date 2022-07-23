# -*- coding: utf-8 -*-
import requests
from src.output import output
import src.config

class BWToTextPipeline:
    def process_item(self, item, spider):
        try:
            item["text"] = requests.get(item["link"], headers=src.config.HEADERS).text
        except:
            output("could not retrieve " + item["link"], "err")
        else:
            if item["text"][1] == "h": # Herausfiltern von leeren Seiten / bei leeren Seite ist text[1] == "!" / schnellere Version
                item["filetype"] = "html"
                return item
            else:
                output("empty page " + item["link"], "err")