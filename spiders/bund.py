# -*- coding: utf-8 -*-
import scrapy
from pipelines import pre, courts, post
from pipelines.exporters import as_html, fp_lzma

class SpdrBund(scrapy.Spider):
    name = "spider_bund"
    start_urls = ["http://www.rechtsprechung-im-internet.de/jportal/docs/bsjrs/"]
    custom_settings = {
        "ITEM_PIPELINES": { 
            pre.PrePipeline: 100,
            courts.CourtsPipeline: 200,
            post.PostPipeline: 300,
            as_html.TextToHtmlExportPipeline: 400,
            fp_lzma.FingerprintExportPipeline: 500  
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
            y = {
                "court": item.xpath("gericht/text()").get(),
                "date": item.xpath("entsch-datum/text()").get(),
                "az": item.xpath("aktenzeichen/text()").get(),
                "link": item.xpath("link/text()").get()
            }
            if self.courts:
                for court in self.courts:
                    if y["court"][0:len(court)].lower() == court:
                        if court == "bgh" and self.domains:
                            for domain in self.domains:
                                if domain in y["court"].lower(): yield y
                        else: yield y
            else: yield y