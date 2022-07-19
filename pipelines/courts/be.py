# -*- coding: utf-8 -*-
import re

class BECourtPipeline:
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
        return item