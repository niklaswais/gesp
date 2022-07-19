# -*- coding: utf-8 -*-
import re

class SLCourtPipeline:
    def process_item(self, item, spider):
        # Senate / Kammern 4 abschneiden 
        item["court"] = re.split(r"([-]?\d+)", item["court"])[0]
        #  Eigennamen entfernen
        names = ["saarlaendisches-", "-des-saarlandes", "-fuer-das-saarland"]
        for name in names:
                if name in item["court"]:
                    item["court"] = item["court"].replace(name, "")
        # Gerichtstypen abkürzen
        courts = {"finanzgericht": "fg", "landesarbeitsgericht": "lag", "landessozialgericht": "lsg", "oberlandesgericht": "olg", "oberverwaltungsgericht": "ovg", "sozialgericht": "sg", "verfassungsgerichtshof": "verfgh", "verwaltungsgericht":"vg" }
        for key in courts:
            if key in item["court"]:
                item["court"] = item["court"].replace(key, courts[key])
        return item