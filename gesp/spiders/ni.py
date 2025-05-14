# -*- coding: utf-8 -*-
import scrapy
import urllib.parse
from ..src.output import output
from ..pipelines.formatters import AZsPipeline, DatesPipeline, CourtsPipeline
from ..pipelines.texts import TextsPipeline
from ..pipelines.exporters import ExportAsHtmlPipeline, FingerprintExportPipeline, RawExporter

class SpdrNI(scrapy.Spider):
    name = "spider_ni"
    base_url = "https://voris.wolterskluwer-online.de/"
    custom_settings = {
        "DOWNLOAD_DELAY": 2, # minimum download delay 
        "AUTOTHROTTLE_ENABLED": False,
        "ITEM_PIPELINES": { 
            TextsPipeline: 100,
            AZsPipeline: 200,
            DatesPipeline: 300,
            CourtsPipeline: 400,
            ExportAsHtmlPipeline: 500,
            FingerprintExportPipeline: 600,
            RawExporter: 900
        }
    }

    def __init__(self, path, courts="", states="", fp=False, domains="", store_docId=False, postprocess=False, wait=False, **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.fp = fp
        self.domains = domains
        self.store_docId = store_docId
        self.postprocess = postprocess
        self.wait = wait
        self.base_url = "https://voris.wolterskluwer-online.de/"
        super().__init__(**kwargs)

    async def start(self):
        filter_url = base_url + "search?query=&in_publication=&in_year=&in_edition=&voris_number=&issuer=&date=&end_date_range=&lawtaxonomy=&pit=&da_id=&issuer_label=&content_tree_nodes=&publicationtype=publicationform-ats-filter%21ATS_Rechtsprechung"
        start_urls = [] 
        if self.courts:
            if "ag" in self.courts:
                start_urls.append(filter_url + "_Strafgerichte_AG")
                start_urls.append(filter_url + "_Zivilgerichte_AG")
            if "arbg" in self.courts:
                start_urls.append(filter_url + "_Arbeitsgerichte_ArbG")
            if "fg" in self.courts:
                start_urls.append(filter_url + "_Finanzgerichte")
            if "lag" in self.courts:
                start_urls.append(filter_url + "_Arbeitsgerichte_LAG")
            if "lg" in self.courts:
                start_urls.append(filter_url + "_Strafgerichte_LG")
                start_urls.append(filter_url + "_Zivilgerichte_LG")
            if "lsg" in self.courts:
                start_urls.append(filter_url + "_Sozialgerichte_LSG")
            if "olg" in self.courts:
                start_urls.append(filter_url + "_Strafgerichte_OLG")
                start_urls.append(filter_url + "_Zivilgerichte_OLG")
            if "ovg" in self.courts:
                start_urls.append(filter_url + "_Verwaltungsgerichte_OVG_VGH")
            if "sg" in self.courts:
                start_urls.append(filter_url + "_Sozialgerichte_SG")
            if "vg" in self.courts:
                start_urls.append(filter_url + "_Verwaltungsgerichte_VG")
        else:
            start_urls.append(filter_url)

        for i, url in enumerate(start_urls):
            yield scrapy.Request(url=url, meta={'cookiejar': i}, dont_filter=True, callback=self.parse)

    def parse(self, response):
       
        #  Extract Text
        if view_content == tree.xpath('//ul[@class="view-content"]')
            items = view_content[0].xpath('./li[@class="views-row"]')
            results = []
            for item in items:c
                # Extrahieren des Links
                link_elem = item.xpath('.//h3/a')
                if link_elem:
                    href = link_elem[0].get('href')
                    yield {
                        "postprocess": self.postprocess,
                        "wait": self.wait,
                        # Veränderte Reihenfolge: Meta-Informationen werden aus Dokument extrahiert
                        #"court": court,
                        #"date": date,
                        #"az": az.rstrip(),
                        "link": href
                    }
                
        # Button für nächste Seite
        next_page = response.xpath("//a[@class='wk-pagination-link' and @title='Zur nächsten Seite']")
        if next_page and next_page[0].get("aria-disabled") != "true":
            href = next_page[0].get("href")
            if href:
                yield response.follow(self.base_url + href, dont_filter=True, meta={'cookiejar': response.meta['cookiejar']}, callback=self.parse)
