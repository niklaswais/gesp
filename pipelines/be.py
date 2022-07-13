# -*- coding: utf-8 -*-
import datetime
import re
import requests
from lxml import html
from output import output

class BEPipeline:
    def process_item(self, item, spider):
        # Senate abschneiden (BE)
        item["court"] = re.split(r"([-]?\d+)", item["court"])[0]
        # Fachkammern / Fachsenate / Beschwerdesenate / Berufsgerichte abschneiden
        cut_at = ["fachkammer", "fachsenat", "beschwerdesenat", "kartellsenat", "vergabesenat", "senat", "berufsgericht"]
        for term in cut_at:
            if term in item["court"]:
                item["court"] = item["court"].split(term)[0]
                item["court"] = item["court"].strip("-")
        # Gerichtstypen abkürzen
        courts = {"finanzgericht":"fg","landessozialgericht": "lsg",  "oberverwaltungsgericht": "ovg", "verfassungsgerichtshof-des-landes-berlin": "verfgh"}
        for key in courts:
            if key in item["court"]:
                 item["court"] = item["court"].replace(key, courts[key])
        # item["text"]: Berlin ist JSON-Post-Response
        url = 'https://gesetze.berlin.de/jportal/wsrest/recherche3/document'
        headers = spider.headers
        headers["Referer"] = "https://gesetze.berlin.de/bsbe/document/" + item["docId"]
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = '{"docId":"%s","format":"xsl","keyword":null,"sourceParams":{"source":"Unknown","category":"Alles"},"searches":[],"clientID":"bsbe","clientVersion":"bsbe - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (item["docId"], date, time)
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
