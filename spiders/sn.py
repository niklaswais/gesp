# -*- coding: utf-8 -*-
import datetime
import re
import urllib
import scrapy
from pipelines import pre, courts, post
from pipelines.exporters import as_pdf, fp_lzma

class SpdrSN(scrapy.Spider):
    name = "spider_sn"
    custom_settings = {
        "ITEM_PIPELINES": { 
            pre.PrePipeline: 100,
            courts.CourtsPipeline: 200,
            post.PostPipeline: 300,
            as_pdf.PdfExportPipeline: 400,
            fp_lzma.FingerprintExportPipeline: 500
        }
    }

    def __init__(self, path, courts="", states="", fp=False, domains="", **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.fp = fp
        self.domains = domains
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.justiz.sachsen.de",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36",
            "sec-ch-ua": "\"Chromium\";v=\"103\", \".Not/A)Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\""
        }
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
            self.headers["Sec-Fetch-Dest"] = "frame"
            date_from = "03.10.1990"
            date_until = datetime.datetime.today().strftime("%d.%m.%Y")
            body = f"aktenzeichen=&datum={date_from}-{date_until}&stichwort=+++++++++++++++++++++&rules=+++++++++++++++++++++&ok=Suche+starten"
            yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, dont_filter=True, callback=self.parse_results_ovg)

    def parse(self, response):
        url = "https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx"
        headers = self.headers
        headers["Referer"] = "https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx"
        viewstate = urllib.parse.quote_plus(response.xpath("//input[@id='__VIEWSTATE']/@value").get())
        viewstategen = urllib.parse.quote_plus(response.xpath("//input[@id='__VIEWSTATEGENERATOR']/@value").get())
        if "ag" in self.courts:
            ags = {"Aue": 1016, "Dippoldiswalde": 1021, "D%C3%B6beln": 1018, "Dresden": 1019, "Eilenburg": 1027, "Hainichen": 1017, "Leipzig": 1025, "Mei%C3%9Fen": 1022, "Pirna": 1023, "Riesa": 1024, "Stollberg": 1015, "Torgau": 1028}
            for ag, nr in ags.items():
                body = f"__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&__VIEWSTATEGENERATOR={viewstategen}&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=0&DV1_C24=Suchen&DV1_C33=Amtsgericht+{ag}&DV1_C34=&DV1_C35=&DV1_C36=&DV1_C37=&DV1_C38={nr}&DV1_C39={nr}&DV13_C8=&BOX_RETURN_VALUE=-1"
                yield scrapy.Request(url=url, method="POST", headers=headers, body=body, dont_filter=True, callback=self.parse_results)
        if "lg" in self.courts:
            lgs = {"Dresden": 1020, "Leipzig": 1026, "Zwickau": 1029}
            for lg, nr in lgs.items():
                body = f"__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&__VIEWSTATEGENERATOR={viewstategen}&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=0&DV1_C24=Suchen&DV1_C33=Landgericht+{lg}&DV1_C34=&DV1_C35=&DV1_C36=&DV1_C37=&DV1_C38={nr}&DV1_C39={nr}&DV13_C8=&BOX_RETURN_VALUE=-1"
                yield scrapy.Request(url=url, method="POST", headers=headers, body=body, dont_filter=True, callback=self.parse_results)
        if "olg" in self.courts:
            body = f"__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&__VIEWSTATEGENERATOR={viewstategen}&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=0&DV1_C24=Suchen&DV1_C33=Oberlandesgericht+Dresden&DV1_C34=&DV1_C35=&DV1_C36=&DV1_C37=&DV1_C38=1012&DV1_C39=1012&DV13_C8=&BOX_RETURN_VALUE=-1"
            yield scrapy.Request(url=url, method="POST", headers=headers, body=body, dont_filter=True, callback=self.parse_results)


    def parse_results(self, response):
        viewstate = urllib.parse.quote_plus(response.xpath("//input[@id='__VIEWSTATE']/@value").get())
        viewstategen = urllib.parse.quote_plus(response.xpath("//input[@id='__VIEWSTATEGENERATOR']/@value").get())
        for i, tr in enumerate(response.xpath("//table[@id='DV13_Table']/tbody/tr[not(@class)]")):
            dv1_c45 = urllib.parse.quote_plus(response.xpath("//input[@id='DV1_C45']/@value").get())
            dv13_name = f"DV13_Table$ctl{i+3:02d}$DV13_Table_Col3_C1"
            dv13_value = urllib.parse.quote_plus(response.xpath(f"//input[@name='{dv13_name}']/@value").get())
            dv13_name = urllib.parse.quote_plus(dv13_name)
            dv13_c16 = urllib.parse.quote_plus(response.xpath("//input[@id='DV13_C16']/@value").get())
            body = f"__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&__VIEWSTATEGENERATOR={viewstategen}&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=0&DV1_C44=&DV1_C45={dv1_c45}&DV1_C46=&DV1_C47=&DV1_C48=&DV13_C16={dv13_c16}&{dv13_name}={dv13_value}&BOX_RETURN_VALUE=-1"
            yield {
                "date": tr.xpath(".//td[2]/div/input/@value").get(),
                "az":  tr.xpath(".//td[3]/div/input/@value").get(),
                "court": tr.xpath(".//td[4]/div/input/@value").get(),
                "body": body
            }
        if response.xpath("//input[@value='Vorwärts']") and not response.xpath("//input[@value='Vorwärts']/@disabled").get() == "disabled":
            url = "https://www.justiz.sachsen.de/esamosplus/pages/treffer.aspx"
            headers = self.headers
            headers["Referer"] = "https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx"
            dv13c16_value = urllib.parse.quote_plus(response.xpath("//input[@id='DV13_C16']/@value").get())
            body = f"__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&__VIEWSTATEGENERATOR{viewstategen}&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=0&DV1_C44=&DV1_C45=Oberlandesgericht+Dresden&DV1_C46=&DV1_C47=&DV1_C48=&DV13_C16={dv13c16_value}&ctl21=Vorw%C3%A4rts&BOX_RETURN_VALUE=-1"
            yield scrapy.Request(url=url, method="POST", headers=headers, body=body, dont_filter=True, callback=self.parse_results)
            
    def parse_results_ovg(self, response):
        for table in response.xpath("//table"):
            link = table.xpath(".//td[2]/a/@href").get()
            link = re.findall(r"'([^']*)'", link)
            link = "https://www.justiz.sachsen.de/ovgentschweb/document.phtml?id=" + link[0]
            data = table.xpath(".//td[2]/a/text()").get()[15:]
            yield {
                "date": data[-11:-1],
                "az": data.split("(")[0].strip(),
                "court": "ovg",
                "link": link
            }