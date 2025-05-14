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
            AZsPipeline: 100,
            DatesPipeline: 200,
            CourtsPipeline: 300,
            TextsPipeline: 400,
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
        self.base_url = "https://voris.wolterskluwer-online.de"
        super().__init__(**kwargs)

    async def start(self):
        filter_url = self.base_url + "/search?query=&in_publication=&in_year=&in_edition=&voris_number=&issuer=&date=&end_date_range=&lawtaxonomy=&pit=&da_id=&issuer_label=&content_tree_nodes=&publicationtype=publicationform-ats-filter%21ATS_Rechtsprechung"
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
        view_content = response.xpath('//ul[@class="view-content"]')
        if view_content:
            items = view_content[0].xpath('./li[@class="views-row"]')
            results = []
            for item in items:
                # Extrahieren des Links
                href = item.xpath('.//h3/a/@href').get()
                if href:
                    # Extrahieren der Meta-Informationen via Seiten-Aufruf
                    try:
                        txt = requests.get(self.base_url + href).text
                    except:
                        output("could not retrieve X " + self.base_url + href, "err")
                    else:
                        try:
                            tree = html.fromstring(txt)
                        except:
                            output("could not parse " + self.base_url + href, "err")
                        else:
                            article = tree.xpath('//article')
                            if article:
                                # Extraktion der Meta-Daten
                                court = tree.xpath('//section[@class="wkde-bibliography"]//dt[text()="Gericht"]/following-sibling::dd[1]/text()')
                                date = tree.xpath('//section[@class="wkde-bibliography"]//dt[text()="Datum"]/following-sibling::dd[1]/text()')
                                az = tree.xpath('//section[@class="wkde-bibliography"]//dt[text()="Aktenzeichen"]/following-sibling::dd[1]/text()')
                
                                yield {
                                    "postprocess": self.postprocess,
                                    "wait": self.wait,
                                    "court": court,
                                    "date": date,
                                    "az": az.rstrip(),
                                    "link": self.base_url + href
                                }
                
        # Button für nächste Seite
        next_page = response.xpath("//a[@class='wk-pagination-link' and @title='Zur nächsten Seite']/@aria-disabled").get()
        if next_page and next_page != "true":
            href = response.xpath("//a[@class='wk-pagination-link' and @title='Zur nächsten Seite']/@href").get()
            if href:
                yield response.follow(self.base_url + href, dont_filter=True, meta={'cookiejar': response.meta['cookiejar']}, callback=self.parse)
