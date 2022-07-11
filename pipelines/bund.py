# -*- coding: utf-8 -*-
COURTS = ["bgh", "bfh", "bverwg", "bverfg", "bpatg", "bag", "bsg"]

class BundPipeline:
    def process_item(self, item, spider):
        # Gerichtsname
        item["court"] = item["court"].lower()
        for c in COURTS:
            if c in item["court"].split():
                item["court"] = c
        return item