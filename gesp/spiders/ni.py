# -*- coding: utf-8 -*-
import scrapy
import urllib.parse
from ..src.output import output
from ..pipelines.formatters import AZsPipeline, DatesPipeline, CourtsPipeline
from ..pipelines.texts import TextsPipeline
from ..pipelines.exporters import ExportAsHtmlPipeline, FingerprintExportPipeline, RawExporter

class SpdrNI(scrapy.Spider):
    name = "spider_ni"
    base_url = "https://www.rechtsprechung.niedersachsen.de/jportal/portal/"
    custom_settings = {
        'DOWNLOAD_DELAY': 2, # minimum download delay 
        'AUTOTHROTTLE_ENABLED': False,
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

    def __init__(self, path, courts="", states="", fp=False, domains="", store_docId=False, postprocess=False, wait = False, **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.fp = fp
        self.domains = domains
        self.store_docId = store_docId
        self.postprocess = postprocess
        self.wait = wait
        self.base_url = "https://www.rechtsprechung.niedersachsen.de/jportal/portal/"
        super().__init__(**kwargs)

    def start_requests(self):
        start_urls = [] 
        filter_url = self.base_url + "page/bsndprod.psml?nav=ger&node=BS-ND%5B%23%5D%4000"
        if self.courts:
            if "ag" in self.courts:
                start_urls.append(filter_url + "40%40Amtsgerichte%5B%23%5D")
            if "arbg" in self.courts:
                # Herausfiltern des lag
                arbgs = ["Braunschweig", "Celle", "Emden", "Göttingen", "Hannover", "Lingen", "Nienburg", "Oldenburg+%28Oldenburg%29", "Osnabrück", "Verden"]
                for arbg in arbgs:
                    start_urls.append(filter_url + f"70%40Arbeitsgerichte%5B%23%5D%400002%40ArbG+{arbg}%5B%24%5DArbG+{arbg}%7B.%7D%5B%23%5D")
            if "fg" in self.courts:
                start_urls.append(filter_url + "80%40Finanzgericht%7B.%7D%5B%23%5D")
            if "lag" in self.courts:
                n = "Landesarbeitsgericht+Niedersachsen"
                start_urls.append(filter_url + f"70%40Arbeitsgerichte%5B%23%5D%400001%40{n}%5B%24%5D{n}%7B.%7D%5B%23%5D")
            if "lg" in self.courts:
                start_urls.append(filter_url + "30%40Landgerichte%5B%23%5D")
            if "lsg" in self.courts:
                n = "Landessozialgericht+Niedersachsen-Bremen"
                start_urls.append(filter_url + f"60%40Sozialgerichte%5B%23%5D%400001%40{n}%5B%24%5D{n}%7B.%7D%5B%23%5D")
            if "olg" in self.courts:
                start_urls.append(filter_url + "20%40Oberlandesgerichte%5B%23%5D")
            if "ovg" in self.courts:
                n = "Niedersächsiches+Oberverwaltungsgericht"
                start_urls.append(filter_url + f"50%40Verwaltungsgerichte%5B%23%5D%400001%40{n}%5B%24%5D{n}%7B.%7D%5B%23%5D")
            if "sg" in self.courts:
                # Herausfiltern des lsg
                sgs = ["Aurich", "Braunschweig", "Hannover", "Hildesheim", "Lüneburg", "Oldenburg+%28Oldenburg%29", "Osnabrück", "Stade"]
                for sg in sgs:
                    start_urls.append(filter_url + f"60%40Sozialgerichte%5B%23%5D%400002%40SG+{sg}%5B%24%5DSG+{sg}%7B.%7D%5B%23%5D")
            if "vg" in self.courts:
                # Herausfiltern des ovg
                vgs = ["Braunschweig", "Göttingen", "Hannover", "Lüneburg", "Oldenburg+%28Oldenburg%29", "Osnabrück", "Stade"]
                for vg in vgs:
                    start_urls.append(filter_url + f"50%40Verwaltungsgerichte%5B%23%5D%400002%40Verwaltungsgericht+{vg}%5B%24%5DVerwaltungsgericht+{vg}%7B.%7D%5B%23%5D")
        else:
            start_urls.append(self.base_url + "page/bsndprod.psml/js_peid/FastSearch/media-type/html?form=bsIntFastSearch&sm=fs&query=")

        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if (response.xpath("//table")):
            for tr in response.xpath("//tr"):
                az = tr.xpath(".//a/text()[2]").get()
                az = az.replace("\n", "")
                az = az.replace(" | ", "")
                link = self.base_url + tr.xpath(".//a/@href").get()
                yield {
                       "postprocess": self.postprocess,
                       "wait": self.wait,
                        "court": tr.xpath(".//strong[1]/text()").get(),
                        "date": tr.xpath(".//td[1]/text()").get().replace("\n", ""),
                        "link": link,
                        "az": az,
                        "docId": urllib.parse.parse_qs(urllib.parse.urlparse(link).query)['doc.id'][0]

                }
            if response.xpath("//p[@class='skipNav']/strong[2]/following-sibling::a"):
                yield response.follow(response.xpath("//p[@class='skipNav']/strong[2]/following-sibling::a/@href").get(), callback=self.parse)
        else:
            output("empty search result list", "warn")
