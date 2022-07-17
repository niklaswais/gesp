# -*- coding: utf-8 -*-
import datetime
import scrapy
from pipelines import pre, bw, post
from src.output import output

class SpdrBW(scrapy.Spider):
    name = "spider_bw"
    base_url = "https://lrbw.juris.de/cgi-bin/laender_rechtsprechung/"
    custom_settings = {
        "ITEM_PIPELINES": { 
            pre.PrePipeline: 100,
            bw.BWPipeline: 200,
            post.PostPipeline: 300        
        }
    }

    def __init__(self, path, courts="", domains="", **kwargs):
        self.path = path
        self.courts = courts
        self.domains = domains
        super().__init__(**kwargs)

    def start_requests(self):
        start_urls = []
        base_url = self.base_url + "list.py?Gericht=bw&Art=en"
        add_years = lambda url : [url + str(y) for y in range(2007, datetime.date.today().year + 1)] # Urteilsdatenbank BW startet mit dem Jahr 2007
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
                    "court": doc_link.xpath("../../td[@class='EGericht']/text()").get(),
                    "date": doc_link.xpath("../../td[@class='EDatum']/text()").get(),
                    "az": doc_link.xpath("text()").get(),
                    "link": self.base_url + doc_link.xpath("@href").get() + "&Blank=1"
                }
        if response.xpath("//img[@title='nächste Seite']"):
            yield response.follow(response.xpath("//img[@title='nächste Seite']/../@href").get(), callback=self.parse)