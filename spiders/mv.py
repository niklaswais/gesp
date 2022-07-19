# -*- coding: utf-8 -*-
import datetime
import json
import scrapy
from pipelines import pre, mv, post

class SpdrMV(scrapy.Spider):
    name = "spider_mv"
    custom_settings = {
        "ITEM_PIPELINES": { 
            pre.PrePipeline: 100,
            mv.MVPipeline: 200,
            post.PostPipeline: 300        
        }
    }

    def __init__(self, path, courts="", states="", domains="", **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.domains = domains
        self.filter = []
        if "ag" in self.courts: self.filter.append("ag")
        if "arbg" in self.courts: self.filter.append("arbg")
        if "fg" in self.courts: self.filter.append("finanzgericht")
        if "lag" in self.courts: self.filter.append("landesarbeitsgericht")
        if "lg" in self.courts: self.filter.append("lg")
        if "lsg" in self.courts: self.filter.append("landessozialgericht")
        if "olg" in self.courts: self.filter.append("olg")
        if "ovg" in self.courts: self.filter.append("oberverwaltungsgericht")
        if "sg" in self.courts: self.filter.append("sg")
        if "vg" in self.courts: self.filter.append("vg")
        super().__init__(**kwargs)

    def start_requests(self):
        url = "https://www.landesrecht-mv.de/jportal/wsrest/recherche3/init"
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Origin": "https://www.landesrecht-mv.de",
            "Referer": "https://www.landesrecht-mv.de/bsmv/search",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36",
            "content-type": "application/json",
            "juris-portalid": "bsmv",
            "sec-ch-ua": "\"Chromium\";v=\"103\", \".Not/A)Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\""
        }
        self.cookies = {
            "r3autologin": "\"bsmv\""
        }
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = '{"clientID":"bsmv","clientVersion":"bsmv - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (date, time)
        yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, dont_filter=True, callback=self.parse)

    def parse(self, response):
        yield self.extract_data(response)
        url = "https://www.landesrecht-mv.de/jportal/wsrest/recherche3/search"
        self.headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = '{"searchTasks":{"RESULT_LIST":{"start":1,"size":26,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":25,"size":27},"FAST_ACCESS":{},"SEARCH_WORD_HITS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bsmv","clientVersion":"bsmv - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (date, time)
        yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, meta={"batch": 25}, dont_filter=True, callback=self.parse_scrolldown)

    def parse_scrolldown(self, response):
        results = json.loads(response.body)
        if "resultList" in results:
            yield self.extract_data(response)
            url = "https://www.landesrecht-mv.de/jportal/wsrest/recherche3/search"
            batch = response.meta["batch"]
            date = str(datetime.date.today())
            time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
            body = '{"searchTasks":{"RESULT_LIST":{"start":%s,"size":27,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":%s,"size":27},"FAST_ACCESS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bshe","clientVersion":"bshe - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (batch, batch + 25, date, time)
            batch += 25
            yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, meta={"batch": batch}, dont_filter=True, callback=self.parse_scrolldown)
    
    def extract_data(self, response):
        results = json.loads(response.body)
        if "resultList" in results:
            for result in results["resultList"]:
                r = {
                    "court": result["titleList"][0],
                    "date": result["date"],
                    "az": result["titleList"][1],
                    "link": "https://www.landesrecht-mv.de/bsmv/document/" + result["docId"],
                    "docId": result["docId"],
                    "xcsrft" : self.headers["x-csrf-token"] 
                }
                if self.filter:
                    for f in self.filter:
                        if r["court"][0:len(f)].lower() == f:
                            return r
                else:
                    return r