# -*- coding: utf-8 -*-
import requests
from lxml import html
from src.output import output

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0"}

class SHToTextPipeline:
    def process_item(self, item, spider):
        # Urteilsseite laden
        try:
            tree = html.fromstring(requests.get(item["link"], headers=HEADERS).text)
        except:
            output("could not retrieve " + item["link"], "err")
        else:
            base = tree.xpath("//base/@href")[0]
            link = tree.xpath("//a[@name='dokument.drucken']/@href")[0]
            if link:
                # Druckseite öffnen, Druckdialog entfernen
                tree = html.fromstring(requests.get(base + link, headers=HEADERS).text)
                tree.xpath("//script[last()]")[0].getparent().remove(tree.xpath("//script[last()]")[0])
                item["text"] = html.tostring(tree, pretty_print=True, encoding="utf-8").decode("utf-8")
                item["filetype"] = "html"
                return item
            else:
                output("could not retrieve " + base + link, "err")