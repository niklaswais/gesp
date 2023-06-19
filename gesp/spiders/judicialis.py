# -*- coding: utf-8 -*-
import re
import scrapy
from ..pipelines.formatters import AZsPipeline, CourtsPipeline
from ..pipelines.texts import TextsPipeline
from ..pipelines.exporters import ExportAsHtmlPipeline, FingerprintExportPipeline, RawExporter

class SpdrJudicialis(scrapy.Spider):
    name = "spider_judicialis"
    start_urls = ["https://www.judicialis.de/"]
    custom_settings = {
        "ITEM_PIPELINES": { 
            AZsPipeline: 100,
            CourtsPipeline: 200,
            TextsPipeline: 300,
            ExportAsHtmlPipeline: 400,
            FingerprintExportPipeline: 500,
            RawExporter : 900
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

        civil_and_penal_courts = ["Bundesgerichtshof", "Oberlandesgericht", "Kammergericht", "Oberstes-Landesgericht"]
        civil_courts = ["Bundesgerichtshof", "Oberlandesgericht", "Kammergericht", "Oberstes-Landesgericht", "Landesarbeitsgericht", "Finanzgericht", 
                        "Bundessozialgericht", "Bundesfinanzhof", "Bundesarbeitsgericht"]
        public_courts = ["Bundesverfassungsgericht", "Bundesverwaltungsgericht", "Oberverwaltungsgericht", "Verwaltungsgerichtshof"]
        if ("zivil" in domains and not any(court in courts for court in civil_courts)):
            courts.extend(civil_courts)
        if ("oeff" in domains and not any(court in courts for court in public_courts)):
            courts.extend(public_courts)
        if ("straf" in domains and not any(court in courts for court in civil_and_penal_courts)):
            courts.extend(civil_and_penal_courts)

        super().__init__(**kwargs)
    
    def parse(self, response):
        for item in response.xpath('//*[contains(text(),"Beginn der Entscheidung")]'):
            date = ""
            az = ""
            for entry in item.xpath('//h4[@itemprop="name"]/text()[preceding-sibling::br]'):
                if "verkündet am" in entry.get():
                    date = entry.get().strip().split('verkündet am')[1].strip()
                if "Aktenzeichen:" in entry.get():
                    az = entry.get().replace("Aktenzeichen:","").strip()

            y =  { 
                "court": item.xpath('//h4[@itemprop="name"]/text()').get().replace("Gericht:","").strip(),
                "date": date,
                "az": az,
                "link": response.url,
                "docId": response.url.split('/')[3],
                "postprocess": self.postprocess
            }

            yield y
            
        for item in response.xpath('//h5/a'):
            link = item.xpath('@href').get()
            if link.startswith('/'): link = 'https://www.judicialis.de' + link
            if "Europäisch" in link: continue ## don't donwload EU decisions

            acceptLink = False

            if self.courts:
                for court in self.courts:
                    if court in link:
                        acceptLink = True
            else: acceptLink = True



            if acceptLink: yield scrapy.Request(link, self.parse)

