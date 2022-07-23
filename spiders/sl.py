# -*- coding: utf-8 -*-
import datetime
import json
import scrapy
from pipelines import pre, courts, post
from pipelines.docs import sl
from pipelines.exporters import as_html, fp_lzma
import src.config

class SpdrSL(scrapy.Spider):
    name = "spider_sl"
    custom_settings = {
        "ITEM_PIPELINES": { 
            pre.PrePipeline: 100,
            courts.CourtsPipeline: 200,
            post.PostPipeline: 300,
            sl.SLToTextPipeline: 400,
            as_html.TextToHtmlExportPipeline: 500,
            fp_lzma.FingerprintExportPipeline: 600  
        }
    }

    def __init__(self, path, courts="", states="", fp=False, domains="", **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.fp = fp
        self.domains = domains
        self.filter = []
        if "ag" in self.courts: self.filter.append("ag")
        if "arbg" in self.courts: self.filter.append("arbg")
        if "fg" in self.courts: self.filter.append("finanzgericht")
        if "lag" in self.courts: self.filter.append("landesarbeitsgericht")
        if "lg" in self.courts: self.filter.append("lg")
        if "lsg" in self.courts: self.filter.append("landessozialgericht")
        if "olg" in self.courts: self.filter.append("saarländisches oberlandesgericht")
        if "ovg" in self.courts: self.filter.append("oberverwaltungsgericht")
        if "sg" in self.courts: self.filter.append("sozialgericht")
        if "vg" in self.courts: self.filter.append("verwaltungsgericht")
        super().__init__(**kwargs)

    def start_requests(self):
        url = "https://recht.saarland.de/jportal/wsrest/recherche3/init"
        self.headers = src.config.sl_headers
        self.cookies = src.config.sl_cookies
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = src.config.be_body % (date, time)
        yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, dont_filter=True, callback=self.parse)

    def parse(self, response):
        yield self.extract_data(response)
        url = "https://recht.saarland.de/jportal/wsrest/recherche3/search"
        self.headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = '{"searchTasks":{"RESULT_LIST":{"start":1,"size":26,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":25,"size":27},"FAST_ACCESS":{},"SEARCH_WORD_HITS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bssl","clientVersion":"bssl - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (date, time)
        yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, meta={"batch": 25}, dont_filter=True, callback=self.parse_nextpage)

    def parse_nextpage(self, response):
        results = json.loads(response.body)
        if "resultList" in results:
            yield self.extract_data(response)
            url = "https://recht.saarland.de/jportal/wsrest/recherche3/search"
            batch = response.meta["batch"]
            date = str(datetime.date.today())
            time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
            body = '{"searchTasks":{"RESULT_LIST":{"start":%s,"size":27,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":%s,"size":27},"FAST_ACCESS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bssl","clientVersion":"bssl - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (batch, batch + 25, date, time)
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
                    "link": "https://recht.saarland.de/bssl/document/" + result["docId"],
                    "docId": result["docId"],
                    "xcsrft" : self.headers["x-csrf-token"] 
                }
                if self.filter:
                    for f in self.filter:
                        if r["court"][0:len(f)].lower() == f:
                            return r
                else:
                    return r