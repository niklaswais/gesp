# -*- coding: utf-8 -*-
import re

class SHCourtPipeline:
    def process_item(self, item, spider):
        #Senate/Kammern abschneiden
        item["court"] = re.split(r"([-]?\d+)", item["court"])[0]
        # Eigennamen entfernen
        names = ["schleswig-holsteinisches-", "-fuer-das-land-schleswig-holstein", "-schleswig-holstein"]
        for name in names:
            if name in item["court"]:
                item["court"] = item["court"].replace(name, "")
        # Gerichtstypen abkürzen
        courts = {"finanzgericht":"fg", "landesarbeitsgericht":"lag", "landessozialgericht":"lsg", "landesverfassungsgericht":"verfgh", "oberlandesgericht":"olg", "oberverwaltungsgericht":"ovg", "verwaltungsgericht":"vg"}
        for key in courts:
            if key in item["court"]:
                 item["court"] = item["court"].replace(key, courts[key])
        return item