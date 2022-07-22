# -*- coding: utf-8 -*-
import datetime
import json
import lzma
import scrapy
from pipelines import post
from pipelines.docs import *
from pipelines.exporters import as_html, as_pdf
from src.output import output
import src.config

class FingerprintImportPipeline:
    def process_item(self, item, spider):
        r = {
            "court": item["c"],
            "date": item["d"],
            "az": item ["a"]
        }
        if "link" in item:
            r["link"] = item["link"]
        elif "docId" in item:
            r["docId"] = item["docId"]
        elif "body" in item:
            r["body"] = item["body"]
        return r

class SpdrFP(scrapy.Spider):
    name = "spider_fp"
    items = []
    input = ""
    custom_settings = {
        "ITEM_PIPELINES": {
            FingerprintImportPipeline: 50,
            bb.BBToTextPipeline: 100,
            be.BEToTextPipeline: 101,
            bw.BWToTextPipeline: 102,
            by.BYToTextPipeline: 103,
            he.HEToTextPipeline: 104,
            hh.HHToTextPipeline: 105,
            mv.MVToTextPipeline: 106,
            ni.NIToTextPipeline: 107,
            nw.NWToTextPipeline: 108,
            rp.RPToTextPipeline: 109,
            sh.SHToTextPipeline: 110,
            sl.SLToTextPipeline: 111,
            sn.SNPdfLinkPipeline: 112,
            he.HEToTextPipeline: 113,
            post.PostPipeline: 200,
            as_html.TextToHtmlExportPipeline: 300,
            as_pdf.PdfExportPipeline: 301
        }
    }

    def __init__(self, path, fp, **kwargs):
        self.path = path
        self.fp = fp
        self.headers = ""
        self.cookies = ""
        super().__init__(**kwargs)

    def start_requests(self):    
        self.load_file(self.fp)
        for i, item in enumerate(self.items[1:]): # Einfügen der zum Teil für ->ToText benötigten Extra-Informationen
            i += 1 # Da self.items[1:0]
            self.name = "spider_" + item["s"] # Anpassen für Ordner-Erstellug (in post.py) etc.
            if item["s"] in ["bund", "bb", "bw", "by", "hb", "ni", "nw", "sh"]:
                yield item
            elif item["s"] == "sn":
                yield item
                #AUSBAU!!! Hier zum Teil item["body"]
            else:
                date = str(datetime.date.today())
                time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
                meta = '{"i":%s}' % (i) # Um später das richtige Element der items-Liste zu yielden
                if item["s"] == "be":
                    url = "https://gesetze.berlin.de/jportal/wsrest/recherche3/init"
                    self.headers = src.config.be_headers
                    self.cookies = src.config.be_cookies
                    body = src.config.be_body % (date, time)
                elif item["s"] == "he":
                    url = "https://www.lareda.hessenrecht.hessen.de/jportal/wsrest/recherche3/init"
                    self.headers = src.config.he_headers
                    self.cookies = src.config.he_cookies
                    body = src.config.he_body % (date, time)
                elif item["c"] == "hh":
                    url = "https://www.landesrecht-hamburg.de/jportal/wsrest/recherche3/init"
                    self.headers = src.config.hh_headers
                    self.cookies = src.config.hh_cookies
                    body = src.config.hh_body % (date, time)
                elif item["s"] == "mv":
                    url = "https://www.landesrecht-mv.de/jportal/wsrest/recherche3/init"
                    self.headers = src.config.mv_headers
                    self.cookies = src.config.mv_cookies
                    body = src.config.mv_body % (date, time)
                elif item["s"] == "rp":
                    url = "https://www.landesrecht.rlp.de/jportal/wsrest/recherche3/init"
                    self.headers = src.config.rp_headers
                    self.cookies = src.config.rp_cookies
                    body = src.config.rp_body % (date, time)
                elif item["s"] == "rl":
                    url = "https://recht.saarland.de/jportal/wsrest/recherche3/init"
                    self.headers = src.config.sl_headers
                    self.cookies = src.config.sl_cookies
                    body = src.config.be_body % (date, time)
                elif item["s"] == "st":
                    url = "https://www.landesrecht.sachsen-anhalt.de/jportal/wsrest/recherche3/init"
                    self.headers = src.config.st_headers
                    self.cookies = src.config.st_cookies
                    body = src.config.st_body % (date, time)
                elif item["s"] == "th":
                    url = "https://landesrecht.thueringen.de/jportal/wsrest/recherche3/init"
                    self.headers = src.config.th_headers
                    self.cookies = src.config.th_cookies
                    body = src.config.th_body % (date, time)
                yield scrapy.Request(url=url, method="POST", headers=self.headers, body=body, cookies=self.cookies, meta=meta, dont_filter=True, callback=self.add_xcsrft)


    def add_xcsrft(self, response):
        self.headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
        yield self.items[response.meta["i"]]

    def load_file(self, fp):
        lzmad = lzma.LZMADecompressor()
        with open(fp, "rb") as f:
            while chunk := f.read(1024):
                r = lzmad.decompress(chunk) # compressed -> decompressed
                r = r.decode() # bytes -> string (json)
                self.to_item(r)
        
    def to_item(self, chunk_as_str):
        self.input = self.input + chunk_as_str
        json_lines = self.input.split("|")
        if json_lines[1]:
            for line in json_lines[:-1]:
                self.items.append(json.loads(line)) # string (json) -> item (dict)
            if not json_lines[-1] == "":
                self.input = json_lines[-1] # Rest an Input anhängen
        elif json_lines[0] != "":
            self.items.append(json.loads(json_lines[0]))