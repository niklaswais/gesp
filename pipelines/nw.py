# -*- coding: utf-8 -*-
import requests
from src.output import output

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0"}

class NWPipeline:
    def process_item(self, item, spider):
        try:
            item["text"] = requests.get(item["link"], headers=HEADERS).text
        except:
            output("could not retrieve " + item["link"], "err")
        else:
            a = "<!DOCTYPE html>"
            if item["text"][14] == " ": # Herausfiltern von leeren Seiten / bei leeren Seite ist text[14] == " " / schnellere Version
                item["filetype"] = "html"
                return item
            else:
                output("empty page " + item["link"], "err")