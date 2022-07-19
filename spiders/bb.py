# -*- coding: utf-8 -*-
import requests
import scrapy
from lxml import html
from pipelines import pre, bb, post

class SpdrBB(scrapy.Spider):
    name = "spider_bb"
    base_url = "https://gerichtsentscheidungen.brandenburg.de"
    custom_settings = {
        "ITEM_PIPELINES": { 
            pre.PrePipeline: 100,
            bb.BBPipeline: 200,
            post.PostPipeline: 300
        }
    }

    def __init__(self, path, courts="", states="", domains="", **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.domains = domains
        super().__init__(**kwargs)

    def start_requests(self):
        start_urls = []
        base_url = self.base_url + "/suche?"
        if self.courts:
            if "ag" in self.courts:
                ags = ["AG+Bad+Liebenwerda", "AG+Bernau", "AG+Brandenburg", "AG+Frankfurt+%28Oder%29", "AG+Königs+Wusterhausen", "AG+Oranienburg", "AG+Potsdam", "AG+Schwedt", "AG+Senftenberg", "AG+Zossen"]
                for ag in ags:
                    start_urls.append(base_url + "&select_source=" + ag)
            if "arbg" in self.courts:
                arbgs = ["ArbG+Brandenburg", "ArbG+Cottbus", "ArbG+Potsdam"]
                for arbg in arbgs:
                    start_urls.append(base_url + "&select_source=" + arbg)
            if "fg" in self.courts:
                start_urls.append(base_url + "&select_source=" + "FG+Berlin-Brandenburg")
            if "lag" in self.courts:
                start_urls.append(base_url + "&select_source=" + "LArbG+Berlin-Brandenburg")
            if "lg" in self.courts:
                lgs = ["LG+Cottbus", "LG+Frankfurt+%28Oder%29", "LG+Neuruppin", "LG+Potsdam"]
                for lg in lgs:
                    start_urls.append(base_url + "&select_source=" + lg)
            if "lsg" in self.courts:
                start_urls.append(base_url + "&select_source=" + "LSG+Berlin-Brandenburg")
            if "olg" in self.courts:
                start_urls.append(base_url + "&select_source=" + "OLG+Brandenburg")
            if "ovg" in self.courts:
                start_urls.append(base_url + "&select_source=" + "OVG+Berlin-Brandenburg")
            if "sg" in self.courts:
                sgs = ["SG+Cottbus", "SG+Frankfurt+%28Oder%29", "SG+Neuruppin", "SG+Potsdam"]
                for sg in sgs:
                    start_urls.append(base_url + "&select_source=" + sg)
            if "vg" in self.courts:
                vgs = ["VG+Cottbus", "VG+Frankfurt+%28Oder%29", "VG+Potsdam"]
                for vg in vgs:
                    start_urls.append(base_url + "&select_source=" + vg)
            #VerfG Potsdam
        else:
            start_urls.append(base_url + "&select_source=0")
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for result in response.xpath("//table[@id='resultlist']/tbody/tr"):
            link = self.base_url + result.xpath(".//a/@href").get()
            # Herausfinden des AZ...
            tree = html.fromstring(requests.get(link).text)
            az = tree.xpath("//div[@id='metadata']/div/table/tbody/tr[2]/td[1]/text()")[0]
            yield {
                    "court": result.xpath(".//td[5]/text()").get(),
                    "date": result.xpath(".//td[3]/text()").get(),
                    "link": link,
                    "az": az,
                    "tree": tree # Wenn ohnehin schon verarbeitet...
            }
        if response.xpath("//a[@aria-label='Weiter']"):
            yield response.follow(response.xpath("//a[@aria-label='Weiter']/@href").get(), callback=self.parse)