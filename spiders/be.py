# -*- coding: utf-8 -*-
import datetime
import json
import scrapy
from pipelines import pre, be, post

class SpdrBE(scrapy.Spider):
    name = "spider_be"
    custom_settings = {
        "ITEM_PIPELINES": { 
            pre.PrePipeline: 100,
            be.BEPipeline: 200,
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
        if "fg" in self.courts: self.filter.append("finanzgericht")
        if "lag" in self.courts: self.filter.append("larbg")
        if "lg" in self.courts: self.filter.append("lg")
        if "lsg" in self.courts: self.filter.append("landessozialgericht")
        if "olg" in self.courts: self.filter.append("kg")
        if "ovg" in self.courts: self.filter.append("oberverwaltungsgericht")
        if "sg" in self.courts: self.filter.append("sg")
        if "vg" in self.courts: self.filter.append("vg")
        super().__init__(**kwargs)

    def start_requests(self):
        url = "https://gesetze.berlin.de/jportal/wsrest/recherche3/init"
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Origin": "https://gesetze.berlin.de",
            "Pragma": "no-cache",
            "Referer": "https://gesetze.berlin.de/bsbe/search",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36",
            "content-type": "application/json",
            "juris-portalid": "bsbe",
            "sec-ch-ua": "\"Chromium\";v=\"103\", \".Not/A)Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\""
        }
        self.cookies = {
            "up": "{\"search\":{\"hitsPerPage\":0,\"sort\":\"date\",\"categorySort\":null,\"disableComfortSearch\":false,\"extendedFieldsOpen\":true,\"previewDocument\":false},\"casefile\":{\"sort\":\"standard\"},\"menue\":{\"leftSearchColumnOpen\":true,\"rightSearchColumnOpen\":true,\"leftDocColumnOpen\":true,\"rightDocColumnOpen\":true,\"searchFrameLeftSplitter\":296,\"searchFrameRightSplitter\":300,\"docFrameLeftSplitter\":300,\"docFrameRightSplitter\":300},\"genericUI\":{\"leftColumnOpen\":true,\"rightColumnOpen\":true}}",
            "r3autologin": "\"bsbe\""
        }
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = '{"clientID":"bsbe","clientVersion":"bsbe - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (date, time)
        yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, dont_filter=True, callback=self.parse)

    def parse(self, response):
        yield self.extract_data(response)
        url = "https://gesetze.berlin.de/jportal/wsrest/recherche3/search"
        self.headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
        date = str(datetime.date.today())
        time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
        body = '{"searchTasks":{"CATEGORY_HITS":{},"RESULT_LIST":{"start":1,"size":51,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":52,"size":50},"SEARCH_WORD_HITS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bsbe","clientVersion":"bsbe - V06_07_00 - 23.06.2022 11:20","r3ID":"s%sT%sZ"}' % (date, time)
        yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, meta={"batch": 50}, dont_filter=True, callback=self.parse_scrolldown)

    def parse_scrolldown(self, response):
        results = json.loads(response.body)
        if "resultList" in results:
            # Noch nicht nach ganz unten gescrollt
            yield self.extract_data(response)
            url = "https://gesetze.berlin.de/jportal/wsrest/recherche3/search"
            batch = response.meta["batch"] + 50
            date = str(datetime.date.today())
            time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
            body = '{"searchTasks":{"RESULT_LIST":{"start":%s,"size":50,"sort":"date","addToHistory":true,"addCategory":true},"RESULT_LIST_CACHE":{"start":%s,"size":50},"FAST_ACCESS":{}},"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],"clientID":"bsbe","clientVersion":"bsbe - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (batch, batch + 50, date, time)
            yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, meta={"batch": batch}, dont_filter=True, callback=self.parse_scrolldown)
    
    def extract_data(self, response):
        results = json.loads(response.body)
        if "resultList" in results:
            for result in results["resultList"]:
                r = {
                        "court": result["titleList"][0],
                        "date": result["date"],
                        "az": result["titleList"][1],
                        "link": "https://gesetze.berlin.de/bsbe/document/" + result["docId"],
                        "docId": result["docId"],
                        "xcsrft" : self.headers["x-csrf-token"] 
                    }
                if self.filter:
                    for f in self.filter:
                        if r["court"][0:len(f)].lower() == f:
                            return r
                else:
                    return r