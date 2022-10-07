# -*- coding: utf-8 -*-
import datetime
import scrapy
from ..src.output import output
from ..pipelines.formatters import AZsPipeline, DatesPipeline, CourtsPipeline
from ..pipelines.texts import TextsPipeline
from ..pipelines.exporters import ExportAsHtmlPipeline, FingerprintExportPipeline

class SpdrNW(scrapy.Spider):
    name = "spider_nw"
    base_url = "https://www.justiz.nrw.de/BS/nrwe2/index.php"
    custom_settings = {
        "ITEM_PIPELINES": { 
            AZsPipeline: 100,
            DatesPipeline: 200,
            CourtsPipeline: 300,
            TextsPipeline: 400,
            ExportAsHtmlPipeline: 500,
            FingerprintExportPipeline: 600
        }
    }

    def __init__(self, path, courts="", states="", fp=False, domains="", store_docId=False, **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.fp = fp
        self.domains = domains
        self.store_docId = store_docId
        super().__init__(**kwargs)

    def start_requests(self):
        start_req_bodies = []
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.justiz.nrw.de",
            "Pragma": "no-cache",
            "Referer": "https://www.justiz.nrw.de/BS/nrwe2/index.php",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36",
            "sec-ch-ua": "\"Chromium\";v=\"103\", \".Not/A)Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\""
        }
        date_from = "23.5.1949"
        date_until = datetime.datetime.today().strftime("%d.%m.%Y")
        body = "gerichtstyp={}&gerichtsbarkeit={}&gerichtsort=Alle+Gerichtsorte&entscheidungsart=&date=&von={}&bis={}&validFrom=&von2=&bis2=&aktenzeichen=&schlagwoerter=&q=&method=stem&qSize=100&sortieren_nach=datum_absteigend&absenden=Suchen&advanced_search=true"
        if self.courts:
            if "ag" in self.courts:
                start_req_bodies.append(body.format("Amtsgericht", "Ordentliche+Gerichtsbarkeit", date_from, date_until))
            if "arbg" in self.courts:
                start_req_bodies.append(body.format("Arbeitsgericht", "Arbeitsgerichtsbarkeit", date_from, date_until))
            if "fg" in self.courts:
                start_req_bodies.append(body.format("Finanzgericht", "Finanzgerichtsbarkeit", date_from, date_until))
            if "lag" in self.courts:
                start_req_bodies.append(body.format("Landesarbeitsgericht", "Arbeitsgerichtsbarkeit", date_from, date_until))
            if "lg" in self.courts:
                start_req_bodies.append(body.format("Landgericht", "Ordentliche+Gerichtsbarkeit", date_from, date_until))
            if "lsg" in self.courts:
                start_req_bodies.append(body.format("Landessozialgericht", "Sozialgerichtsbarkeit", date_from, date_until))
            if "olg" in self.courts:
                start_req_bodies.append(body.format("Oberlandesgericht", "Ordentliche+Gerichtsbarkeit", date_from, date_until))
            if "ovg" in self.courts:
                start_req_bodies.append(body.format("Oberverwaltungsgericht", "Verwaltungsgerichtsbarkeit", date_from, date_until))
            if "sg" in self.courts:
                start_req_bodies.append(body.format("Sozialgericht", "Sozialgerichtsbarkeit", date_from, date_until))
            if "vg" in self.courts:
                start_req_bodies.append(body.format("Verwaltungsgericht", "Verwaltungsgerichtsbarkeit", date_from, date_until))
        else:
            start_req_bodies.append(body.format("","", date_from, date_until))
        for start_req_body in start_req_bodies:
            yield scrapy.Request(url=self.base_url, method="POST", headers=self.headers, body=start_req_body, meta={"body":start_req_body, "page":1}, dont_filter=True, callback=self.parse)
    
    def parse(self, response):
        for result in self.extract_data(response):
            yield result
        if response.xpath("//input[@value='>']"): # Button für nächste Seite
            page = response.meta["page"] + 1
            body = "page" + str(page) + "=%3E&" + response.meta["body"]
            yield scrapy.Request(url=self.base_url, method="POST", headers=self.headers, body=body, meta={"body":response.meta["body"], "page":page}, dont_filter=True, callback=self.parse)

    def extract_data(self, response):
        if response.xpath("//div[@class='alleErgebnisse']"):
            for res_div in response.xpath("//div[@class='einErgebnis']"):
                r = {
                    "court": res_div.xpath("text()[1]").get().strip()[9:],
                    "date": res_div.xpath("text()[5]").get().strip()[21:],
                    "az": res_div.xpath("text()[3]").get().strip()[14:],
                    "link": res_div.xpath(".//a/@href").get(),
                }
                yield r
        else:
            output(f"blank search results page {response.url}", "warn")