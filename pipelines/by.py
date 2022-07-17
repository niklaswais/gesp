# -*- coding: utf-8 -*-
from lxml import etree
import requests
from src.output import output

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0"}

class BYPipeline:
    def process_item(self, item, spider):
        try:
            txt = requests.get(item["link"], headers=HEADERS).text
        except:
            output("could not retrieve " + item["link"], "err")
        else:
            if txt[10] == "H": # Herausfiltern von leeren Seiten / bei leeren Seite ist text[10] == "h" / schnellere Version
                tree = etree.fromstring(txt.replace('\r\n', '\n'))
                tree.xpath("//script")[0].getparent().remove(tree.xpath("//script")[0]) # Druck-Dialog entfernen
                item["text"] = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="utf-8").decode("utf-8")
                item["filetype"] = "xhtml"
                return item
            else:
                output("empty page " + item["link"], "err")
