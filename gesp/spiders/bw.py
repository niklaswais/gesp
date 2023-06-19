# -*- coding: utf-8 -*-
import datetime
import scrapy
from ..src.output import output
from ..pipelines.formatters import AZsPipeline, DatesPipeline, CourtsPipeline
from ..pipelines.texts import TextsPipeline
from ..pipelines.exporters import ExportAsHtmlPipeline, FingerprintExportPipeline, RawExporter

class SpdrBW(scrapy.Spider):
    name = "spider_bw"
    base_url = "https://lrbw.juris.de/cgi-bin/laender_rechtsprechung/"
    custom_settings = {
        "DOWNLOAD_DELAY": 1, # minimum download delay 
        "AUTOTHROTTLE_ENABLED": True,
        "ITEM_PIPELINES": { 
            AZsPipeline: 100,
            DatesPipeline: 200,
            CourtsPipeline: 300,
            TextsPipeline: 400,
            ExportAsHtmlPipeline: 500,
            FingerprintExportPipeline: 600,
            RawExporter : 900
        }
    }

    def __init__(self, path, courts="", states="", fp=False, domains="", store_docId=False, postprocess=False, wait=False **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.fp = fp
        self.domains = domains
        self.store_docId = store_docId
        self.postprocess = postprocess
        self.wait = wait
        super().__init__(**kwargs)

    def start_requests(self):
        start_urls = []
        base_url = self.base_url + "list.py?Gericht=bw&Art=en"
        add_years = lambda url : [url + str(y) for y in reversed(range(2007, datetime.date.today().year + 1))] # Urteilsdatenbank BW startet mit dem Jahr 2007
        if self.courts:
            if "ag" in self.courts: start_urls.extend(add_years(base_url + "&GerichtAuswahl=Amtsgerichte&Datum="))
            if "arbg" in self.courts: start_urls.extend(add_years(base_url + "&GerichtAuswahl=Arbeitsgerichte&Datum="))
            if "fg" in self.courts: start_urls.extend(add_years(base_url + "&GerichtAuswahl=Finanzgericht&Datum="))
            if "lag" in self.courts: start_urls.extend(add_years(base_url + "&GerichtAuswahl=Arbeitsgerichte&Datum="))
            if "lg" in self.courts: start_urls.extend(add_years(base_url + "&GerichtAuswahl=Landgerichte&Datum="))
            if "lsg" in self.courts: start_urls.extend(add_years(base_url + "&GerichtAuswahl=Sozialgerichte&Datum="))
            if "olg" in self.courts: start_urls.extend(add_years(base_url + "&GerichtAuswahl=Oberlandesgerichte&Datum="))
            if "ovg" in self.courts: start_urls.extend(add_years(base_url + "&GerichtAuswahl=Verwaltungsgerichte&Datum="))
            if "sg" in self.courts: start_urls.extend(add_years(base_url + "&GerichtAuswahl=Sozialgerichte&Datum="))
            if "vg" in self.courts: start_urls.extend(add_years(base_url + "&GerichtAuswahl=Verwaltungsgerichte&Datum="))
        else:
            start_urls.extend(add_years(base_url + "&Datum="))
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if not response.xpath("//p[@class='FehlerMeldung']"): #  Hinweis-Seite ohne Suchergebnisse, d.h. alle Seiten für das Jahr wurden durchgegangen
            for doc_link in response.xpath("//a[@class='doklink']"):
                if self.courts:
                    # Auswahl notwendig, da ArbG & LAG == Arbeitsgerichte, SG & LSG == Sozialgerichte, VG & VGH == Verwaltungserichte
                    # Nur wenn self.courts, um Geschwindigkeit (XPath...) bei ungefiltertem Durchgang nicht zu bremsen
                    doc_court = doc_link.xpath("../../td[@class='EGericht']/text()").get().split()[0].lower()
                    if not doc_court in self.courts:
                        continue
                    # Wenn Rechtsgebiet ausgewählt weitere Unterscheidung notwendig, da ag + lg + olg == Straf UND Zivil
                    # ggf. Filtern nach Aktenzeichen?
                    if "straf" in self.domains and not "zivil" in self.domains:
                        output("filter (-s bw -d straf) not yet implemented", "warn")
                        # Ausbauen ....
                    elif "zivil" in self.domains and not "straf" in self.domains:
                        output("filter (-s bw -d zivil) not yet implemented", "warn")
                        # Ausbauen ....            
                yield {
                    "postprocess": self.postprocess,
                    "wait": self.wait,
                    "court": doc_link.xpath("../../td[@class='EGericht']/text()").get(),
                    "date": doc_link.xpath("../../td[@class='EDatum']/text()").get(),
                    "az": doc_link.xpath("text()").get(),
                    "link": self.base_url + doc_link.xpath("@href").get() + "&Blank=1"
                }
        if response.xpath("//img[@title='nächste Seite']"):
            yield response.follow(response.xpath("//img[@title='nächste Seite']/../@href").get(), callback=self.parse)
