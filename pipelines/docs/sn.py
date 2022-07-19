# -*- coding: utf-8 -*-
import requests
from lxml import html
from src.output import output

class SNPdfLinkPipeline: # Kein item["text"]: In Sachsen nur PDF
    def process_item(self, item, spider):
        if "body" in item: # AG/LG/OLG-Subportal
            url = "https://www.justiz.sachsen.de/esamosplus/pages/treffer.aspx"
            headers = spider.headers
            headers["Referer"] = "Referer: https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx"
            try:
                item["req"] = requests.post(url=url, headers=headers, data=item["body"])
            except:
                output("could not retrieve " + item["az"], "err")
            else:
                return item
        elif "link" in item: # OVG-Subportal
            try:
                tree = html.fromstring(requests.get(item["link"]).text)
            except:
                output("could not retrieve " + item["link"], "err")
            else:
                item["link"] = "https://www.justiz.sachsen.de/ovgentschweb/" + tree.xpath("//a[@target='_blank']/@href")[0]
                return item