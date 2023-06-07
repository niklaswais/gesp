# -*- coding: utf-8 -*-
import datetime
import json
import urllib.parse
import scrapy
from ..src import config
from ..pipelines.formatters import AZsPipeline, DatesPipeline, CourtsPipeline
from ..pipelines.texts import TextsPipeline
from ..pipelines.exporters import ExportAsHtmlPipeline, FingerprintExportPipeline, RawExporter

class SpdrSH(scrapy.Spider):
    name = "spider_sh"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0"}
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
        url = "https://www.gesetze-rechtsprechung.sh.juris.de/jportal/wsrest/recherche3/init"
        self.headers = config.sh_headers
        self.cookies = config.sh_cookies
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = config.sh_body % (date, time)
        yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, dont_filter=True, callback=self.parse)

    def parse(self, response):
<<<<<<< HEAD
        for result in self.extract_data(response):
            yield result
        url = "https://www.gesetze-rechtsprechung.sh.juris.de/jportal/wsrest/recherche3/search"
        self.headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = '{"searchTasks":{"RESULT_LIST":{"start":1,"size":26,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":25,"size":27},"FAST_ACCESS":{},"SEARCH_WORD_HITS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bssh","clientVersion":"bssh - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (date, time)
        yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, meta={"batch": 25}, dont_filter=True, callback=self.parse_nextpage)
||||||| f557017
        # Zunächst durch das Menü (1); notwendig, da dynamisch generierte URLs
        url_1 = response.xpath("//base/@href").get()
        url_2 = response.xpath("//div[@id='StLst1TaAnchor']/a/@href").get()
        yield scrapy.Request(url=url_1+url_2, headers=self.headers, dont_filter=True, callback=self.parse_2)
=======
        for result in self.extract_data(response):
            yield result
        url = "https://www.gesetze-rechtsprechung.sh.juris.de/jportal/wsrest/recherche3/search"
        self.headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = '{"searchTasks":{"RESULT_LIST":{"start":1,"size":25,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":25,"size":27},"FAST_ACCESS":{},"SEARCH_WORD_HITS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bssh","clientVersion":"bssh - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (date, time)
        yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, meta={"batch": 26}, dont_filter=True, callback=self.parse_nextpage)
>>>>>>> niklas/master

<<<<<<< HEAD
    def parse_nextpage(self, response):
        results = json.loads(response.body)
        if "resultList" in results:
            for result in self.extract_data(response):
                yield result
            url = "https://www.gesetze-rechtsprechung.sh.juris.de/jportal/wsrest/recherche3/search"
            batch = response.meta["batch"]
            date = str(datetime.date.today())
            time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
            body = '{"searchTasks":{"RESULT_LIST":{"start":%s,"size":27,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":%s,"size":27},"FAST_ACCESS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bssh","clientVersion":"bssh - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (batch, batch + 25, date, time)
            batch += 25
            yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, meta={"batch": batch}, dont_filter=True, callback=self.parse_nextpage)
    
    def extract_data(self, response):
        results = json.loads(response.body)
        if "resultList" in results:
            for result in results["resultList"]:
                r = {
                    "postprocess": self.postprocess,
                    "wait": self.wait,
                    "court": result["titleList"][0],
                    "date": result["date"],
                    "az": result["titleList"][1],
                    "link": "https://www.gesetze-rechtsprechung.sh.juris.de/bssh/document/" + result["docId"],
                    "docId": result["docId"],
                    "xcsrft" : self.headers["x-csrf-token"] 
                }
                if self.filter:
                    for f in self.filter:
                        if r["court"][0:len(f)].lower() == f:
                            yield r
                else:
                    yield r
||||||| f557017
    
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
            link = tr.xpath("//base/@href").get() + tr.xpath(".//td[3]/a[1]/@href").get()
            return {
                "court": tr.xpath(".//td[3]/a/span/strong[1]/text()").get(),
                "date": tr.xpath(".//td[2]/span/text()").get(),
                "link": link,
                "az": az,
                "docId": urllib.parse.parse_qs(urllib.parse.urlparse(link).query)['doc.id'][0]
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
=======
    def parse_nextpage(self, response):
        results = json.loads(response.body)
        if "resultList" in results:
            for result in self.extract_data(response):
                yield result
            url = "https://www.gesetze-rechtsprechung.sh.juris.de/jportal/wsrest/recherche3/search"
            batch = response.meta["batch"]
            date = str(datetime.date.today())
            time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
            body = '{"searchTasks":{"RESULT_LIST":{"start":%s,"size":25,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":%s,"size":27},"FAST_ACCESS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bssh","clientVersion":"bssh - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (batch, batch + 25, date, time)
            batch += 25
            yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, meta={"batch": batch}, dont_filter=True, callback=self.parse_nextpage)

    def extract_data(self, response):
        results = json.loads(response.body)
        if "resultList" in results:
            for result in results["resultList"]:
                r = {
                    "court": result["titleList"][0],
                    "date": result["date"],
                    "az": result["titleList"][1],
                    "link": "https://www.gesetze-rechtsprechung.sh.juris.de/bssh/document/" + result["docId"],
                    "docId": result["docId"],
                    "xcsrft" : self.headers["x-csrf-token"] 
                }
                if self.filter:
                    for f in self.filter:
                        if r["court"][0:len(f)].lower() == f:
                            yield r
                else:
                    yield r
>>>>>>> niklas/master
