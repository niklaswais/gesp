# -*- coding: utf-8 -*-
import datetime
import re
import urllib
import requests
import scrapy
from ..src import config
from lxml import html
from ..src.output import output
from ..pipelines.formatters import AZsPipeline, DatesPipeline, CourtsPipeline
from ..pipelines.exporters import ExportAsPdfPipeline, FingerprintExportPipeline, RawExporter

class SpdrSN(scrapy.Spider):
    name = "spider_sn"
    custom_settings = {
        "ITEM_PIPELINES": { 
            AZsPipeline: 100,
            DatesPipeline: 200,
            CourtsPipeline: 300,
            ExportAsPdfPipeline: 400,
            FingerprintExportPipeline: 500,
            RawExporter: 900
        },
        "AUTOTHROTTLE_ENABLED": True
    }

    def __init__(self, path, courts="", states="", fp=False, domains="", store_docId=False, postprocess=False, **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.fp = fp
        self.domains = domains
        self.store_docId = store_docId
        self.postprocess = postprocess
        self.headers = config.sn_headers
        super().__init__(**kwargs)

    def start_requests(self):
        supported_courts = ["ag", "lg", "olg"]
        if not self.courts or any(c in supported_courts for c in self.courts):
            url = "https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx"
            yield scrapy.Request(url=url, dont_filter=True, callback=self.parse)
        if not self.courts or "ovg" in self.courts:
            # OVG mit eigener Sub-Plattform
            url = "https://www.justiz.sachsen.de/ovgentschweb/searchlist.phtml"
            self.headers["Referer"] = "https://www.justiz.sachsen.de/ovgentschweb/searchmask.phtml"
            self.headers["Sec-Fetch-Dest"] = "iframe"
            date_from = "03.10.1990"
            date_until = datetime.datetime.today().strftime("%d.%m.%Y")
            body = f"aktenzeichen=&datum={date_from}-{date_until}&stichwort=+++++++++++++++++++++&rules=+++++++++++++++++++++&ok=Suche+starten"
            yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, dont_filter=True, callback=self.parse_results_ovg)
        if not self.courts or "verfgh" in self.courts:
            # VerfGH auch mit eigener Sub-Plattform
            url = "https://www.justiz.sachsen.de/esaver/index.php"
            self.headers["Referer"] = "https://www.justiz.sachsen.de/esaver/index.php"
            for year in range(1970, 2030):
                subsequent = year + 1
                body = f"aktion=suchen&verfart=&akz=&datumvon=01.01.{year}&datumbis=01.01.{subsequent}&stichwort=&set_grund=&feldgrund=&set_norm=&feldnorm="
                yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, dont_filter=True, callback=self.parse_results_verfgh)

    def parse(self, response):
        url = "https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx"
        headers = self.headers
        headers["Referer"] = url
        viewstate = urllib.parse.quote_plus(response.xpath("//input[@id='__VIEWSTATE']/@value").get())
        viewstategen = urllib.parse.quote_plus(response.xpath("//input[@id='__VIEWSTATEGENERATOR']/@value").get())
        if not self.courts or "ag" in self.courts:
            ags = {"Aue": 1016, "Dippoldiswalde": 1021, "D%C3%B6beln": 1018, "Dresden": 1019, "Eilenburg": 1027, "Hainichen": 1017, "Leipzig": 1025, "Mei%C3%9Fen": 1022, "Pirna": 1023, "Riesa": 1024, "Stollberg": 1015, "Torgau": 1028}
            for ag, nr in ags.items():
                body = f"__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&__VIEWSTATEGENERATOR={viewstategen}&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=0&DV1_C24=Suchen&DV1_C33=Amtsgericht+{ag}&DV1_C34=&DV1_C35=&DV1_C36=&DV1_C37=&DV1_C38={nr}&DV1_C39={nr}&DV13_C8=&BOX_RETURN_VALUE=-1"
                yield scrapy.Request(url=url, method="POST", headers=headers, body=body, meta={"cookiejar": nr}, dont_filter=True, callback=self.parse_results)
        if not self.courts or "lg" in self.courts:
            lgs = {"Dresden": 1020, "Leipzig": 1026, "Zwickau": 1029}
            for lg, nr in lgs.items():
                body = f"__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&__VIEWSTATEGENERATOR={viewstategen}&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=0&DV1_C24=Suchen&DV1_C33=Landgericht+{lg}&DV1_C34=&DV1_C35=&DV1_C36=&DV1_C37=&DV1_C38={nr}&DV1_C39={nr}&DV13_C8=&BOX_RETURN_VALUE=-1"
                yield scrapy.Request(url=url, method="POST", headers=headers, body=body, meta={"cookiejar": nr}, dont_filter=True, callback=self.parse_results)
        if not self.courts or "olg" in self.courts:
            body = f"__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&__VIEWSTATEGENERATOR={viewstategen}&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=0&DV1_C24=Suchen&DV1_C33=Oberlandesgericht+Dresden&DV1_C34=&DV1_C35=&DV1_C36=&DV1_C37=&DV1_C38=1012&DV1_C39=1012&DV13_C8=&BOX_RETURN_VALUE=-1"
            yield scrapy.Request(url=url, method="POST", headers=headers, body=body, meta={"cookiejar": nr}, dont_filter=True, callback=self.parse_results)

    def parse_results(self, response):
        viewstate = urllib.parse.quote_plus(response.xpath("//input[@id='__VIEWSTATE']/@value").get())
        viewstategen = urllib.parse.quote_plus(response.xpath("//input[@id='__VIEWSTATEGENERATOR']/@value").get())
        dv1_c45 = response.xpath("//input[@name='DV1_C45']/@value").get()
        dv13_c16 = response.xpath("//input[@name='DV13_C16']/@value").get()
        for i, tr in enumerate(response.xpath("//table[@id='DV13_Table']/tbody/tr[not(@class)]")):
            dv13_name = f"DV13_Table$ctl{i+3:02d}$DV13_Table_Col3_C1"
            dv13_value = response.xpath(f"//input[@name='{dv13_name}']/@value").get()
            if dv1_c45 and dv13_c16 and dv13_value:
                dv1_c45 = urllib.parse.quote_plus(dv1_c45)
                dv13_c16 = urllib.parse.quote_plus(dv13_c16)
                dv13_value = urllib.parse.quote_plus(dv13_value)
                body = f"__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&__VIEWSTATEGENERATOR={viewstategen}&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=0&DV1_C44=&DV1_C45={dv1_c45}&DV1_C46=&DV1_C47=&DV1_C48=&DV13_C16={dv13_c16}&{dv13_name}={dv13_value}&BOX_RETURN_VALUE=-1"
                url = "https://www.justiz.sachsen.de/esamosplus/pages/treffer.aspx"
                headers = self.headers
                headers["Referer"] = "Referer: https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx"
                item = {
                    "date": tr.xpath(".//td[2]/div/input/@value").get(),
                    "az":  tr.xpath(".//td[3]/div/input/@value").get(),
                    "court": tr.xpath(".//td[4]/div/input/@value").get(),
                    "link": url
                }
                yield scrapy.Request(url=url, method="POST", meta={"cookiejar": response.meta["cookiejar"], "item": item}, headers=headers, body=body, dont_filter=True, callback=self.parse_results_dl)
            else:
                output("sn: can not parse results page", "err")
        if response.xpath("//input[@value='Vorwärts']") and not response.xpath("//input[@value='Vorwärts']/@disabled").get() == "disabled":
            url = "https://www.justiz.sachsen.de/esamosplus/pages/treffer.aspx"
            headers = self.headers
            headers["Referer"] = "https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx"
            if response.xpath("//input[@id='DV13_C16']"):
                dv13c16_value = urllib.parse.quote_plus(response.xpath("//input[@id='DV13_C16']/@value").get())
                body = f"__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&__VIEWSTATEGENERATOR{viewstategen}&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=0&DV1_C44=&DV1_C45=Oberlandesgericht+Dresden&DV1_C46=&DV1_C47=&DV1_C48=&DV13_C16={dv13c16_value}&ctl21=Vorw%C3%A4rts&BOX_RETURN_VALUE=-1"
                yield scrapy.Request(url=url, method="POST", meta={'cookiejar': response.meta['cookiejar']}, headers=headers, body=body, dont_filter=True, callback=self.parse_results)
            else:
                output("sn: can not proceed to the next page of results", "err")

    def parse_results_dl(self, response):
        item = response.meta["item"]
        item["body"] = response.body
        yield item

    def parse_container(self, response):
        slots = response.xpath("//result/node()").get().split("^")
        date_us = slots[5]
        date_de = date_us[8:10] + "." + date_us[5:7] + "." + date_us[0:4]
        filename = slots[11]
        az = slots[1]
        if "" == filename:
            output("sn: file missing for az " + az, "err")
            return
        location = "https://www.justiz.sachsen.de/esaver/internet/" + slots[16]
        url = location + "/" + filename
        yield {
            "date": date_de,
            "az": az,
            "court": "verfgh",
            "link": url
        }

    def parse_results_verfgh(self, response):
        for anchor in response.xpath("//table/tr/td/a"):
            retrieval = anchor.xpath("./@onclick").get()
            container = retrieval.split("'")[1]
            url = "https://www.justiz.sachsen.de/esaver/answers.php?funkt=get_satz&container=" + container
            yield scrapy.Request(url=url, dont_filter=True, callback=self.parse_container)

    def parse_results_ovg(self, response):
        for table in response.xpath("//table"):
            tmp_link = table.xpath(".//td[2]/a/@href").get()
            tmp_link = re.findall(r"'([^']*)'", tmp_link)
            tmp_link = "https://www.justiz.sachsen.de/ovgentschweb/document.phtml?id=" + tmp_link[0]
            data = table.xpath(".//td[2]/a/text()").get()[15:]
            try: # Zwischengeschaltete Seite, von der aus erst der Filelink kopiert werden muss
                tree = html.fromstring(requests.get(tmp_link).text)
            except:
                output("could not retrieve " + tmp_link, "err")
            else:
                yield {
                    "postprocess": self.postprocess,
                    "date": data[-11:-1],
                    "az": data.split("(")[0].strip(),
                    "court": "ovg",
                    "link": "https://www.justiz.sachsen.de/ovgentschweb/" + tree.xpath("//a[@target='_blank']/@href")[0]
                }
