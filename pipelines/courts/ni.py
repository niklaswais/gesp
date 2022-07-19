# -*- coding: utf-8 -*-
import re

class NICourtPipeline:
    def process_item(self, item, spider):
        #Senate/Kammern abschneiden
        item["court"] = re.split(r"([-]?\d+)", item["court"])[0]
        return item
