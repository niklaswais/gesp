# -*- coding: utf-8 -*-
import re
import requests
from lxml import html
from output import output

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0"}

class SHPipeline:
    def process_item(self, item, spider):
        #Senate/Kammern abschneiden
        item["court"] = re.split(r"([-]?\d+)", item["court"])[0]
        # Eigennamen entfernen
        names = ["schleswig-holsteinisches-", "-fuer-das-land-schleswig-holstein", "-schleswig-holstein"]
        for name in names:
            if name in item["court"]:
                item["court"] = item["court"].replace(name, "")
        # Gerichtstypen abkürzen
        courts = {"finanzgericht":"fg", "landesarbeitsgericht":"lag", "landessozialgericht":"lsg", "landesverfassungsgericht":"verfgh", "oberlandesgericht":"olg", "oberverwaltungsgericht":"ovg", "verwaltungsgericht":"vg"}
        for key in courts:
            if key in item["court"]:
                 item["court"] = item["court"].replace(key, courts[key])
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
