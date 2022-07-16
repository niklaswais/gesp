# -*- coding: utf-8 -*-
import os
from attr import asdict
import requests
from lxml import html
from output import output

class SNPipeline:
    def open_spider(self, spider):
        if (not os.path.exists(spider.path + spider.name[7:])):
            try:
                os.makedirs(spider.path + spider.name[7:])
            except:
                output(f"could not create folder {spider.path}{spider.name[7:]}", "err")

    def process_item(self, item, spider):
        # Gerichtstypen abkürzen
        courts = { "amtsgericht":"ag","landgericht": "lg", "oberlandesgericht": "olg" }
        for key in courts:
            if key in item["court"]:
                 item["court"] = item["court"].replace(key, courts[key])
        # item["text"]: In Sachsen nur PDF
        if ("body" in item): # AG/LG/OLG-Subportal
            url = "https://www.justiz.sachsen.de/esamosplus/pages/treffer.aspx"
            headers = spider.headers
            headers["Referer"] = "Referer: https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx"
            try:
                req = requests.post(url=url, headers=headers, data=item["body"])
            except:
                output("could not retrieve " + item["az"], "err")
        elif ("link" in item): # OVG-Subportal
            try:
                tree = html.fromstring(requests.get(item["link"]).text)
            except:
                output("could not retrieve " + item["link"], "err")
            else:
                filelink = "https://www.justiz.sachsen.de/ovgentschweb/" + tree.xpath("//a[@target='_blank']/@href")[0]
                try:
                    req = requests.get(filelink)
                except:
                    output("could not retrieve " + filelink, "err")
        if (req):
            output("downloading " + req.url + "...")
            filename = spider.path + spider.name[7:] + "/" + item["court"] + "_" + item["date"] + "_" + item["az"] + ".pdf"
            try:
                with open(filename, "wb") as f:
                    f.write(req.content)
            except:
                output(f"could not create file {filename}", "err")

