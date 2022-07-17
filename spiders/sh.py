# -*- coding: utf-8 -*-
import scrapy
from pipelines import pre, sh, post

class SpdrSH(scrapy.Spider):
    name = "spider_sh"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0"}
    custom_settings = {
        "ITEM_PIPELINES": { 
            pre.PrePipeline: 100,
            sh.SHPipeline: 200,
            post.PostPipeline: 300        
        }
    }
    def __init__(self, path, courts="", domains="", **kwargs):
        self.path = path
        self.courts = courts
        self.domains = domains
        self.filter = []
        if "ag" in self.courts: self.filter.append("ag")
        if "arbg" in self.courts: self.filter.append("arbg")
        if "fg" in self.courts: self.filter.append("schleswig-holsteinisches finanzgericht")
        if "lag" in self.courts: self.filter.append("landesarbeitsgericht")
        if "lg" in self.courts: self.filter.append("lg")
        if "lsg" in self.courts: self.filter.append("schleswig-holsteinisches landessozialgericht ")
        if "olg" in self.courts: self.filter.append("schleswig-holsteinisches oberlandesgericht")
        if "ovg" in self.courts: self.filter.append("oberverwaltungsgericht")
        if "sg" in self.courts: self.filter.append("sg")
        if "vg" in self.courts: self.filter.append("schleswig-holsteinisches verwaltungsgericht")
        super().__init__(**kwargs)
    
    def start_requests(self):
        start_url = "http://www.gesetze-rechtsprechung.sh.juris.de/jportal/portal/page/bsshoprod.psml"
        yield scrapy.Request(url=start_url, headers=self.headers, callback=self.parse)

    def parse(self, response):
        # Zunächst durch das Menü (1); notwendig, da dynamisch generierte URLs
        url_1 = response.xpath("//base/@href").get()
        url_2 = response.xpath("//div[@id='StLst1TaAnchor']/a/@href").get()
        yield scrapy.Request(url=url_1+url_2, headers=self.headers, dont_filter=True, callback=self.parse_2)

    
    def parse_2(self, response):
        # Zunächst durch das Menü (2); notwendig, da dynamisch generierte URLs
        url_1 = response.xpath("//base/@href").get()
        url_2 = response.xpath("//a[@class='NaviSelect']/@href").get()
        yield scrapy.Request(url=url_1+url_2, headers=self.headers, dont_filter=True, callback=self.parse_content)

    def parse_content(self, response):
        def extract_data(tr):
            az = tr.xpath(".//td[3]/a/span/text()[2]").get()
            az = az.replace("\n", "")
            az = az.replace(" | ", "")
            return {
                "court": tr.xpath(".//td[3]/a/span/strong[1]/text()").get(),
                "date": tr.xpath(".//td[2]/span/text()").get(),
                "link": tr.xpath("//base/@href").get() + tr.xpath(".//td[3]/a[1]/@href").get(),
                "az": az,
            }
        for tr in response.xpath("//table[@class='TableSchnInnen']/tr[@valign='top']"):
            court = tr.xpath(".//td[3]/a/span/strong[1]/text()").get()
            if self.filter:
                for f in self.filter:
                    if court[0:len(f)].lower() == f:
                        yield extract_data(tr)
            else:
                yield extract_data(tr)
        if response.xpath("//input[@title='weiter']"):
            if not "pos" in response.meta: # Erster Aufruf durch parse_2() noch ohne Position
                pos = 1
            else:
                pos = response.meta["pos"] + 25
            base_url = response.xpath("//base/@href").get()
            url = base_url + f"page/bsshoprod.psml/js_peid/Trefferliste/media-type/html?action=portlets.jw.ResultListFormAction&currentNavigationPosition={pos}&sortmethod=standard"
            yield scrapy.Request(url=url, meta={"pos": pos}, headers=self.headers, dont_filter=True, callback=self.parse_content)