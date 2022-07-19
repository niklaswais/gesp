# -*- coding: utf-8 -*-
import re

class HHCourtPipeline:
    def process_item(self, item, spider):
        # Senate abschneiden 
        item["court"] = re.split(r"([-]?\d+)", item["court"])[0]
        # Fachkammern / Fachsenate / Beschwerdesenate / Berufsgerichte abschneiden
        cut_at = ["fachkammer", "fachsenat", "beschwerdesenat", "vergabesenat", "senat", "berufsgericht"]
        for term in cut_at:
            if term in item["court"]:
                item["court"] = item["court"].split(term)[0]
        #  Eigennamen entfernen
        names = ["hanseatisches-", "hamburgisches-"]
        for name in names:
                if name in item["court"]:
                    item["court"] = item["court"].replace(name, "")
        # Gerichtstypen abkürzen
        courts = {"landesarbeitsgericht": "lag", "landessozialgericht": "lsg", "oberlandesgericht": "olg", "oberverwaltungsgericht": "ovg", "verfassungsgericht": "verfgh"}
        for key in courts:
            if key in item["court"]:
                item["court"] = item["court"].replace(key, courts[key])
        return item