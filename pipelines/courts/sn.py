# -*- coding: utf-8 -*-
import requests
from lxml import html
from src.output import output

class SNPipeline:
    def process_item(self, item, spider):
        # Gerichtstypen abkürzen
        courts = { "amtsgericht":"ag","landgericht": "lg", "oberlandesgericht": "olg" }
        for key in courts:
            if key in item["court"]:
                 item["court"] = item["court"].replace(key, courts[key])
        return item