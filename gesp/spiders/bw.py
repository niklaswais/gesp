# -*- coding: utf-8 -*-
import datetime
import json
import scrapy
from ..src import config
from ..pipelines.formatters import AZsPipeline, DatesPipeline, CourtsPipeline
from ..pipelines.texts import TextsPipeline
from ..pipelines.exporters import ExportAsHtmlPipeline, FingerprintExportPipeline, RawExporter

class SpdrBW(scrapy.Spider):
    name = "spider_bw"
    custom_settings = {
        "DOWNLOAD_DELAY": 2, # minimum download delay 
        "AUTOTHROTTLE_ENABLED": True,
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

    def __init__(self, path, courts="", states="", fp=False, domains="", store_docId=False, postprocess=False, wait=False, **kwargs):
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
        if "fg" in self.courts: self.filter.append("fg")
        if "lag" in self.courts: self.filter.append("landesarbeitsgericht")
        if "lg" in self.courts: self.filter.append("lg")
        if "lsg" in self.courts: self.filter.append("landessozialgericht")
        if "olg" in self.courts: self.filter.append("olg")
        if "ovg" in self.courts: self.filter.append("verwaltungsgerichtshof")
        if "sg" in self.courts: self.filter.append("sg")
        if "vg" in self.courts: self.filter.append("vg")
        super().__init__(**kwargs)

    async def start(self):
        url = "https://www.landesrecht-bw.de/jportal/wsrest/recherche3/init"
        self.headers = config.bw_headers
        self.cookies = config.bw_cookies
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = config.bw_body % (date, time)
        yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, dont_filter=True, callback=self.parse)

    def parse(self, response):
        for result in self.extract_data(response):
            yield result
        url = "https://www.landesrecht-bw.de/jportal/wsrest/recherche3/search"
        self.headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = '{"searchTasks":{"RESULT_LIST":{"start":1,"size":25,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":25,"size":27},"FAST_ACCESS":{},"SEARCH_WORD_HITS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bsbw","clientVersion":"bsbw - V08_18_00 - 24.04.2025 11:53","r3ID":"%sT%sZ"}' % (date, time)
        yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, meta={"batch": 25}, dont_filter=True, callback=self.parse_nextpage)

    def parse_nextpage(self, response):
        results = json.loads(response.body)
        if "resultList" in results:
            for result in self.extract_data(response):
                yield result
            url = "https://www.landesrecht-bw.de/jportal/wsrest/recherche3/search"
            date = str(datetime.date.today())
            time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
            batch = response.meta["batch"]
            body = '{"searchTasks":{"RESULT_LIST":{"start":%s,"size":27,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":%s,"size":27},"FAST_ACCESS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bsbw","clientVersion":"bsbw - V08_18_00 - 24.04.2025 11:53","r3ID":"%sT%sZ"}' % (batch, batch + 25, date, time)
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
                    "link": "https://www.landesrecht-bw.de/bsbw/document/" + result["docId"],
                    "docId": result["docId"],
                }
                if self.filter:
                    for f in self.filter:
                        if r["court"][0:len(f)].lower() == f:
                            yield r
                else:
                    yield r
