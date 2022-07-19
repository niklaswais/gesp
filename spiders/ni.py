# -*- coding: utf-8 -*-
import scrapy
from pipelines import pre, ni, post
from src.output import output

class SpdrNI(scrapy.Spider):
    name = "spider_ni"
    base_url = "https://www.rechtsprechung.niedersachsen.de/jportal/portal/"
    custom_settings = {
        "ITEM_PIPELINES": { 
            pre.PrePipeline: 100,
            ni.NIPipeline: 200,
            post.PostPipeline: 300
        }
    }

    def __init__(self, path, courts="", states="", domains="", **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.domains = domains
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
                yield {
                        "court": tr.xpath(".//strong[1]/text()").get(),
                        "date": tr.xpath(".//td[1]/text()").get().replace("\n", ""),
                        "link": self.base_url + tr.xpath(".//a/@href").get(),
                        "az": az,
                }
            if response.xpath("//p[@class='skipNav']/strong[2]/following-sibling::a"):
                yield response.follow(response.xpath("//p[@class='skipNav']/strong[2]/following-sibling::a/@href").get(), callback=self.parse)
        else:
            output("empty search result list", "warn")