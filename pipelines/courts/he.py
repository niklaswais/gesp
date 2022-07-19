# -*- coding: utf-8 -*-
import re

class HECourtPipeline:
    def process_item(self, item, spider):
        # Senate / Kammern / Einzelrichter abschneiden 
        item["court"] = re.split(r"([-]?\d+)", item["court"])[0]
        #  Eigennamen entfernen
        names = ["hessischer-", "hessisches-", "-abteilung"]
        for name in names:
                if name in item["court"]:
                    item["court"] = item["court"].replace(name, "")
        # Gerichtstypen abkürzen
        courts = {"finanzgericht": "fg", "landesarbeitsgericht": "lag", "landessozialgericht": "lsg", "verwaltungsgerichtshof": "vgh" }
        for key in courts:
            if key in item["court"]:
                item["court"] = item["court"].replace(key, courts[key])
        return item