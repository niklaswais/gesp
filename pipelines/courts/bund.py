# -*- coding: utf-8 -*-

class BundCourtPipeline:
    def process_item(self, item, spider):
        # Gerichtsname
        COURTS = ["bgh", "bfh", "bverwg", "bverfg", "bpatg", "bag", "bsg"]
        item["court"] = item["court"].lower()
        for c in COURTS:
            if c in item["court"].split():
                item["court"] = c
        return item