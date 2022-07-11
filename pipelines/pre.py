# -*- coding: utf-8 -*-
import re
import datetime

UMLAUTE = {ord('ä'):'ae', ord('ö'):'oe', ord('ß'):'ss', ord('ü'):'ue'}

class PrePipeline:
    def process_item(self, item, spider):                
        # Standard-Formatierung der Gerichtsnamen für alle LÄNDER
        if spider.name != "spider_bund":
            item["court"] = item["court"].lower()
            item["court"] = item["court"].strip()
            item["court"] = re.sub(r"\s", "-", item["court"])
            item["court"] = item["court"].translate(UMLAUTE)
        #Formattierunng der Aktenzeichen
        item["az"] = item["az"].strip() 
        item["az"] = item["az"].replace("/", "-")
        item["az"] = item["az"].replace(".", "-")
        item["az"] = re.sub(r"\s", "-", item["az"]) # Alle Arten von Leerzeichen (normale, geschützte, ...)
        #Formattierung der Daten
        if not spider.name == "spider_bund":
            item["date"] = item["date"].strip()
            item["date"] = datetime.datetime.strptime(item["date"], "%d.%m.%Y").strftime("%Y%m%d")
        # Weitergabe an die individuellen Pipelines
        return item