# -*- coding: utf-8 -*-
import re
import scrapy
from ..src.output import output
from ..pipelines.formatters import AZsPipeline, DatesPipeline, CourtsPipeline
from ..pipelines.texts import TextsPipeline
from ..pipelines.exporters import ExportAsHtmlPipeline, FingerprintExportPipeline, RawExporter

class SpdrBY(scrapy.Spider):
    name = "spider_by"
    base_url = "https://www.gesetze-bayern.de"
    custom_settings = {
        "ITEM_PIPELINES": { 
            AZsPipeline: 100,
            DatesPipeline: 200,
            CourtsPipeline: 300,
            #TextsPipeline: 400,
            ExportAsHtmlPipeline: 500,
            FingerprintExportPipeline: 600,
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
        super().__init__(**kwargs)

    def start_requests(self):
        start_urls = []
        base_url = self.base_url + "/Search/Filter/"
        if self.courts:
            if "ag" in self.courts: start_urls.append("LEVEL2RSPRTREENODE/Amtsgerichte/Ordentliche%20Gerichtsbarkeit")
            if "arbg" in self.courts: start_urls.append("LEVEL2RSPRTREENODE/Arbeitsgerichte/Arbeitsgerichtsbarkeit")
            if "fg" in self.courts:
                start_urls.append("LEVEL2RSPRTREENODE/FG%20N%C3%BCrnberg/Finanzgerichtsbarkeit")
                start_urls.append("LEVEL2RSPRTREENODE/FG%20M%C3%BCnchen/Finanzgerichtsbarkeit")
            if ("lag" in self.courts):
                start_urls.append("LEVEL2RSPRTREENODE/LArbG%20M%C3%BCnchen/Arbeitsgerichtsbarkeit")
                start_urls.append("LEVEL2RSPRTREENODE/LArbG%20N%C3%BCrnberg/Arbeitsgerichtsbarkeit")
            if "lg" in self.courts: start_urls.append("LEVEL2RSPRTREENODE/Landgerichte/Ordentliche%20Gerichtsbarkeit")
            if "lsg" in self.courts: start_urls.append("LEVEL2RSPRTREENODE/LSG%20M%C3%BCnchen/Sozialgerichtsbarkeit")
            if "olg" in self.courts:
                start_urls.append("LEVEL2RSPRTREENODE/OLG%20Bamberg/Ordentliche%20Gerichtsbarkeit")
                start_urls.append("LEVEL2RSPRTREENODE/OLG%20M%C3%BCnchen/Ordentliche%20Gerichtsbarkeit")
                start_urls.append("LEVEL2RSPRTREENODE/OLG%20N%C3%BCrnberg/Ordentliche%20Gerichtsbarkeit")
                start_urls.append("LEVEL2RSPRTREENODE/BayObLG%20M%C3%BCnchen/Ordentliche%20Gerichtsbarkeit") # Sonderfall Bayern (BayObLG)...
            if "ovg" in self.courts: start_urls.append("LEVEL2RSPRTREENODE/VGH%20M%C3%BCnchen/Verwaltungsgerichtsbarkeit")
            if "sg" in self.courts: start_urls.append("LEVEL2RSPRTREENODE/Sozialgerichte/Sozialgerichtsbarkeit")
            if "vg" in self.courts: start_urls.append("LEVEL2RSPRTREENODE/Verwaltungsgerichte/Verwaltungsgerichtsbarkeit")
            if "verfgh" in self.courts: start_urls.append("LEVEL1RSPRTREENODE/Verfassungsgerichtsbarkeit")
        else:
            start_urls.append("DOKTYP/rspr")

        for i, url in enumerate(start_urls):
            yield scrapy.Request(url=base_url + url, meta={'cookiejar': i}, dont_filter=True, callback=self.parse)
    
    def parse(self, response):
        if not response.xpath("//div[@id='hinweis']"): # Bei Hinweis Seite ohne Suchergebnisse
            for item in response.xpath("//li[@class='hitlistItem']"):
                # Wenn Rechtsgebiet ausgewählt weitere Unterscheidung notwendig, da ag + lg + olg == Straf UND Zivil
                # ggf. Filtern nach Aktenzeichen?
                if ("straf" in self.domains and not "zivil" in self.domains):
                    output("filter (-s by -d straf) not yet implemented", "warn")
                    # Ausbauen ....
                elif ("zivil" in self.domains and not "straf" in self.domains):
                    output("filter (-s by -d zivil) not yet implemented", "warn")
                    # Ausbauen .... 
                # Gerichtsbezeichnung ggf. von Zsf. der Entscheidung trennen
                court = item.xpath(".//a/b/text()").get()
                if ":" in court: court = court.split(":")[0]
                # AZ und Datum auftrennen
                subtitel = item.xpath(".//div[@class='hlSubTitel']/text()").get()
                date = re.search("([0-9]{2}\.[0-9]{2}\.[0-9]{4})", subtitel)[0]
                az = subtitel.split(" – ")[1]
                zipLink = self.base_url + item.xpath(".//a/@href").get()[:-8].replace("Document","Zip")
                
                yield {
                    "postprocess": self.postprocess,
                    "court": court,
                    "date": date,
                    "az": az.rstrip(),
                    "link": zipLink
                }

        if response.xpath("//a[text()='→']"):
            yield response.follow(response.xpath("//a[text()='→']/@href").get(), dont_filter=True, meta={'cookiejar': response.meta['cookiejar']}, callback=self.parse)
