# -*- coding: utf-8 -*-
import datetime
import re
import requests
from lxml import html
from output import output

class RPPipeline:
    def process_item(self, item, spider):
        # Senate / Kammern 4 abschneiden 
        item["court"] = re.split(r"([-]?\d+)", item["court"])[0]
        #  Eigennamen entfernen
        if "-rheinland-pfalz" in item["court"]:
            item["court"] = item["court"].replace("-rheinland-pfalz", "")
        # Gerichtstypen abkürzen
        courts = {"finanzgericht": "fg", "landesarbeitsgericht": "lag", "landessozialgericht": "lsg", "oberverwaltungsgericht": "ovg", "verfassungsgerichtshof": "verfgh" }
        for key in courts:
            if key in item["court"]:
                item["court"] = item["court"].replace(key, courts[key])
        # item["text"]: Rheinland-Pfalz ist JSON-Post-Response
        url = "https://www.landesrecht.rlp.de/jportal/wsrest/recherche3/document"
        headers = spider.headers
        headers["Referer"] = item["link"]
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bshe","clientVersion":"bsrp - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (item["docId"], date, time)
        try:
            req = requests.post(url=url, cookies=spider.cookies, headers=headers, data=body)
        except:
            output("could not retrieve " + item["link"], "err")
        else:
            data = req.json()
            doc = html.fromstring(f'<!doctype html><html><head><title>{item["az"]}</title></head><body>{data["head"]}{data["text"]}</body></html>')
            item["text"] = html.tostring(doc, pretty_print=True, encoding="utf-8").decode("utf-8")
            item["filetype"] = "html"
            return item