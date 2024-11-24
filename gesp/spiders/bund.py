# -*- coding: utf-8 -*-
import re
import scrapy
from ..src import config
from ..pipelines.formatters import AZsPipeline, CourtsPipeline
from ..pipelines.exporters import ExportAsHtmlPipeline, FingerprintExportPipeline, RawExporter

class SpdrBund(scrapy.Spider):
    name = "spider_bund"
    start_urls = ["http://www.rechtsprechung-im-internet.de/jportal/docs/bsjrs/"]
    custom_settings = {
        "ITEM_PIPELINES": { 
            AZsPipeline: 100,
            CourtsPipeline: 200,
            ExportAsHtmlPipeline: 300,
            FingerprintExportPipeline: 400,
            RawExporter: 900
        }
    }

    def __init__(self, path, courts="", states="", fp=False, domains="", store_docId=False, postprocess=False, **kwargs):
        self.path = path
        self.courts = courts
        self.states = states
        self.fp = fp
        self.domains = domains
        self.store_docId = store_docId
        self.postprocess = postprocess
        self.bverfg_az_bmj = {}
        if ("zivil" in domains and not any(court in courts for court in ["bgh", "bpatg", "bag"])):
            courts.extend(["bgh", "bpatg", "bag"])
        if ("oeff" in domains and not any(court in courts for court in ["bfh", "bsg", "bverfg", "bverwg"])):
            courts.extend(["bfh", "bsg", "bverfg", "bverwg"])
        if ("straf" in domains and not "bgh" in courts):
            courts.append("bgh")
        super().__init__(**kwargs)
    
    def parse(self, response):
        if not self.courts or "bverfg" in self.courts:
            for item in response.xpath("//item"):
                link = item.xpath("link/text()").get()
                if item.xpath("gericht/text()").get().startswith("BVerfG"):
                    azs = item.xpath("aktenzeichen/text()").get()
                    for az in azs.split(", "):
                        if "..." != az:
                            self.bverfg_az_bmj[az] = True
            yield scrapy.Request(
                url="https://www.bundesverfassungsgericht.de/DE/Entscheidungen/Entscheidungen/Amtliche%20Sammlung%20BVerfGE.html",
                callback=self.parse_bverfg_collection,
                headers=config.HEADERS | {
                    'Referer':'https://www.bundesverfassungsgericht.de/'
                }
            )
        for item in response.xpath("//item"):
            link = item.xpath("link/text()").get()
            y = {
                "court": item.xpath("gericht/text()").get(),
                "date": item.xpath("entsch-datum/text()").get(),
                "az": item.xpath("aktenzeichen/text()").get(),
                "link": link,
                "docId": re.fullmatch(r'.+/jb\-([0-9A-Z]+)\.zip', link)[1],
                "postprocess": self.postprocess
            }
            if self.courts:
                for court in self.courts:
                    if y["court"][0:len(court)].lower() == court:
                        if court == "bgh" and self.domains:
                            for domain in self.domains:
                                if domain in y["court"].lower(): yield y
                        else: yield y
            else: yield y

    def parse_bverfg_collection(self, response):
        for link in response.xpath("//a/@href"):
            if "/Entscheidungen/Liste/" in link.get():
                yield scrapy.Request(
                    url=response.urljoin(link.get()),
                    callback=self.parse_bverfg_list,
                    headers=config.HEADERS
                )

    def parse_bverfg_list(self, response):
        for row in response.xpath("//tr"):
            needed = None
            az_column = row.xpath(".//td[3]/text()").get()
            if az_column:
                azs = az_column
                azs = re.sub("[),]$", "", azs)
                azs = re.sub("\xa0", " ", azs)
                azs = re.sub("([0-9]+) (/[0-9]+)", "\\1\\2", azs)
                azs = re.sub(",? u[.] ?a[.]? ?(,|$)", "\\1", azs)
                pat_range = "([A-Z,] ?)([0-9]+) bis ([0-9]+)(/[0-9]+)"
                if re.match("^.*" + pat_range + ".*$", azs):
                    pre = re.sub("^.*(" + pat_range + ").*$", "\\1", azs)
                    last = re.sub("^" + pat_range + "$", "\\1", pre)
                    start = int(re.sub("^" + pat_range + "$", "\\2", pre))
                    end = int(re.sub("^" + pat_range + "$", "\\3", pre))
                    year = re.sub("^" + pat_range + "$", "\\4", pre)
                    post = last
                    delimiter = ""
                    for n in range(start, end + 1):
                        post += delimiter + str(n) + year
                        delimiter = ", "
                    azs = post.join(azs.split(pre))
                # xxx und yyy/zz -> xxx/zz, yyy/zz
                pat_n = "([A-Z,] )([0-9]+) und ([0-9]+)(/[0-9]+)"
                while re.match("^.*" + pat_n + ".*$", azs):
                    azs = re.sub(pat_n, "\\1\\2\\4, \\3\\4", azs)
                # xxx, yyy/zz -> xxx/zz, yyy/zz
                pat_n = "([A-Z,] ?)([0-9]+), ?([0-9]+)(/[0-9]+)"
                while re.match("^.*" + pat_n + ".*$", azs):
                    azs = re.sub(pat_n, "\\1\\2\\4, \\3\\4", azs)
                rz = "(Bv[ABCEFGHKLMNOPQR]|PBv[UV])"
                # x Rr yyy/zz, uuu/vv -> x Rr yyy,zz, x Rr uuu/vv
                pat_ny = "([0-9] " + rz + ") ([0-9]+/[0-9]+), ([0-9]+/[0-9]+)"
                while re.match("^.*" + pat_ny + ".*$", azs):
                    azs = re.sub(pat_ny, "\\1 \\3, \\1 \\4", azs)
                pat_az = "([0-9] " + rz + "|PBvV) [0-9]+/[0-9]+"
                for az in azs.split(", "):
                    az = re.sub(" +$", "", az)
                    if not az in self.bverfg_az_bmj:
                        needed = az
                        break
            if not needed:
                continue
            for link in row.xpath(".//td[1]/a/@href"):
                if "/Entscheidungen/" in link.get():
                    monate = {
                        'Januar': '01',
                        'Februar': '02',
                        'März': '03',
                        'April': '04',
                        'Mai': '05',
                        'Juni': '06',
                        'Juli': '07',
                        'August': '08',
                        'September': '09',
                        'Oktober': '10',
                        'November': '11',
                        'Dezember': '12',
                    }
                    monat = "(" + "|".join(list(monate)) + ")"
                    pat_d = "([0-9]+)[.] " + monat + " ([0-9]{4})"
                    pat = "(Beschluss|Urteil) vom " + pat_d
                    date_raw = row.xpath(".//td[2]/text()").get()
                    if not re.match(pat, date_raw):
                        continue
                    date_raw = re.sub(
                        "^(Beschluss|Urteil) vom (" + pat_d + ")$",
                        "\\2",
                        date_raw
                    )
                    date_ymd = re.sub(
                        pat_d,
                        "\\3",
                        date_raw
                    ) + monate[
                        re.sub(pat_d, "\\2", date_raw)
                    ] + re.sub(
                        pat_d,
                        "\\1",
                        date_raw
                    ).zfill(2)
                    yield {
                        "wait": self.wait,
                        "date": date_ymd,
                        "az": needed,
                        "court": "bverfg",
                        "link": response.urljoin(link.get()),
                    }
