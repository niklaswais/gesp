# -*- coding: utf-8 -*-
import re

class RPCourtsPipeline:
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
        return item