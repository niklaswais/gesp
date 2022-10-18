# -*- coding: utf-8 -*-
import scrapy
from ..src.output import output
from ..pipelines.formatters import AZsPipeline, DatesPipeline, CourtsPipeline
from ..pipelines.exporters import ExportAsPdfPipeline, FingerprintExportPipeline

class SpdrHB(scrapy.Spider):
    name = "spider_hb"
    custom_settings = {
        "ITEM_PIPELINES": {
            AZsPipeline: 100,
            DatesPipeline: 200,
            CourtsPipeline: 300,
            ExportAsPdfPipeline: 500,
            FingerprintExportPipeline: 600
        }
    }

    def __init__(self, path, courts="", states="", fp=False, domains="", store_docId=False, postprocess=False, **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.fp = fp
        self.domains = domains
        self.store_docId = store_docId
        self.postprocess = postprocess
        super().__init__(**kwargs)

    def start_requests(self):
        # In Bremen nur vereinzelte Gerichte mit Online-Entscheidungen
        if not self.courts or "lag" in self.courts:
            url = "https://www.landesarbeitsgericht.bremen.de/entscheidungen/entscheidungsuebersicht-11508?max=100&skip=0"
            yield scrapy.Request(url=url, dont_filter=True, meta={"c":"lag"}, callback=self.parse)
        if not self.courts or "olg" in self.courts:
            url = "https://www.oberlandesgericht.bremen.de/entscheidungen/entscheidungsuebersicht-2335?max=100&skip=0"
            yield scrapy.Request(url=url, dont_filter=True, meta={"c":"olg"}, callback=self.parse)
        if not self.courts or "ovg" in self.courts:
            url = "https://www.oberverwaltungsgericht.bremen.de/entscheidungen/entscheidungsuebersicht-11265?max=100&skip=0"
            yield scrapy.Request(url=url, dont_filter=True, meta={"c":"ovg"}, callback=self.parse)
        if not self.courts or "sg" in self.courts:
            url = "https://www.sozialgericht-bremen.de/entscheidungen/entscheidungsuebersicht-14912?max=100&skip=0"
            yield scrapy.Request(url=url, dont_filter=True, meta={"c":"sg"}, callback=self.parse)
        if not self.courts or "vg" in self.courts:
            url = "https://www.verwaltungsgericht.bremen.de/entscheidungen/entscheidungsuebersicht-13039?max=100&skip=0"
            yield scrapy.Request(url=url, dont_filter=True, meta={"c":"vg"}, callback=self.parse)
    
    def parse(self, response):
        for td in response.xpath("//tr/td[@class='dotright'][1]"):
            link = "https://" + response.url.split("/")[2] + td.xpath(".//following-sibling::td/a[1]/@href").get()
            yield {
                "postprocess": self.postprocess,
                "court": response.meta["c"],
                "date": td.xpath(".//em/text()").get(),
                "az": td.xpath("text()").get(),
                "link": link
            }
        if response.xpath("//a[@title='nächste Seite']"):
            yield response.follow(response.xpath("//a[@title='nächste Seite']/@href").get())
