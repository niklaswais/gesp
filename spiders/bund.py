# -*- coding: utf-8 -*-
import re
import scrapy
from pipelines.formatters import AZsPipeline, CourtsPipeline
from pipelines.exporters import ExportAsHtmlPipeline, FingerprintExportPipeline

class SpdrBund(scrapy.Spider):
    name = "spider_bund"
    start_urls = ["http://www.rechtsprechung-im-internet.de/jportal/docs/bsjrs/"]
    custom_settings = {
        "ITEM_PIPELINES": { 
            AZsPipeline: 100,
            CourtsPipeline: 200,
            ExportAsHtmlPipeline: 300,
            FingerprintExportPipeline: 400
        }
    }

    def __init__(self, path, courts="", states="", fp=False, domains="", **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.fp = fp
        self.domains = domains
        if ("zivil" in domains and not any(court in courts for court in ["bgh", "bpatg", "bag"])):
            courts.extend(["bgh", "bpatg", "bag"])
        if ("oeff" in domains and not any(court in courts for court in ["bfh", "bsg", "bverfg", "bverwg"])):
            courts.extend(["bfh", "bsg", "bverfg", "bverwg"])
        if ("straf" in domains and not "bgh" in courts):
            courts.append("bgh")
        super().__init__(**kwargs)
    
    def parse(self, response):
        for item in response.xpath("//item"):
            link = item.xpath("link/text()").get()
            y = {
                "court": item.xpath("gericht/text()").get(),
                "date": item.xpath("entsch-datum/text()").get(),
                "az": item.xpath("aktenzeichen/text()").get(),
                "link": link,
                "docId": re.fullmatch(r'.+/jb\-([0-9A-Z]+)\.zip', link)[1]
            }
            if self.courts:
                for court in self.courts:
                    if y["court"][0:len(court)].lower() == court:
                        if court == "bgh" and self.domains:
                            for domain in self.domains:
                                if domain in y["court"].lower(): yield y
                        else: yield y
            else: yield y