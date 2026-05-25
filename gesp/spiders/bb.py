import time as timelib

import requests
import scrapy
from lxml import etree, html
from scrapy.utils.defer import deferred_to_future
from twisted.internet.defer import DeferredSemaphore
from twisted.internet.threads import deferToThread

from ..pipelines.exporters import ExportAsHtmlPipeline, FingerprintExportPipeline, RawExporter
from ..pipelines.formatters import AZsPipeline, CourtsPipeline, DatesPipeline
from ..pipelines.texts import TextsPipeline
from ..src.output import output


class SpdrBB(scrapy.Spider):
    name = "spider_bb"
    base_url = "https://gerichtsentscheidungen.brandenburg.de"
    custom_settings = {
        "DOWNLOAD_DELAY": 5,  # minimum download delay
        "AUTOTHROTTLE_ENABLED": True,
        "ITEM_PIPELINES": {
            AZsPipeline: 100,
            DatesPipeline: 200,
            CourtsPipeline: 300,
            TextsPipeline: 400,
            ExportAsHtmlPipeline: 500,
            FingerprintExportPipeline: 600,
            RawExporter: 900,
        },
    }

    def __init__(
        self,
        path,
        courts="",
        states="",
        fp=False,
        domains="",
        store_docId=False,
        postprocess=False,
        wait=0,
        **kwargs,
    ):
        self.path = path
        self.courts = courts
        self.states = states
        self.domains = domains
        self.store_docId = store_docId
        self.fp = fp
        self.postprocess = postprocess
        self.wait = wait
        self.detail_sem = DeferredSemaphore(1)
        super().__init__(**kwargs)

    @staticmethod
    def _fetch_detail_tree(link, wait):
        if wait:
            timelib.sleep(wait)
        try:
            return html.fromstring(requests.get(link, timeout=30).text)
        except (requests.RequestException, etree.LxmlError, ValueError) as e:
            output(f"could not retrieve {link}: {e!r}", "err")
            return None

    async def start(self):
        start_urls = []
        base_url = self.base_url + "/suche?"
        if self.courts:
            if "ag" in self.courts:
                ags = [
                    "AG+Bad+Liebenwerda",
                    "AG+Bernau",
                    "AG+Brandenburg",
                    "AG+Frankfurt+%28Oder%29",
                    "AG+Königs+Wusterhausen",
                    "AG+Oranienburg",
                    "AG+Potsdam",
                    "AG+Schwedt",
                    "AG+Senftenberg",
                    "AG+Zossen",
                ]
                for ag in ags:
                    start_urls.append(base_url + "&select_source=" + ag)
            if "arbg" in self.courts:
                arbgs = ["ArbG+Brandenburg", "ArbG+Cottbus", "ArbG+Potsdam"]
                for arbg in arbgs:
                    start_urls.append(base_url + "&select_source=" + arbg)
            if "fg" in self.courts:
                start_urls.append(base_url + "&select_source=" + "FG+Berlin-Brandenburg")
            if "lag" in self.courts:
                start_urls.append(base_url + "&select_source=" + "LArbG+Berlin-Brandenburg")
            if "lg" in self.courts:
                lgs = ["LG+Cottbus", "LG+Frankfurt+%28Oder%29", "LG+Neuruppin", "LG+Potsdam"]
                for lg in lgs:
                    start_urls.append(base_url + "&select_source=" + lg)
            if "lsg" in self.courts:
                start_urls.append(base_url + "&select_source=" + "LSG+Berlin-Brandenburg")
            if "olg" in self.courts:
                start_urls.append(base_url + "&select_source=" + "OLG+Brandenburg")
            if "ovg" in self.courts:
                start_urls.append(base_url + "&select_source=" + "OVG+Berlin-Brandenburg")
            if "sg" in self.courts:
                sgs = ["SG+Cottbus", "SG+Frankfurt+%28Oder%29", "SG+Neuruppin", "SG+Potsdam"]
                for sg in sgs:
                    start_urls.append(base_url + "&select_source=" + sg)
            if "vg" in self.courts:
                vgs = ["VG+Cottbus", "VG+Frankfurt+%28Oder%29", "VG+Potsdam"]
                for vg in vgs:
                    start_urls.append(base_url + "&select_source=" + vg)
            # VerfG Potsdam
        else:
            start_urls.append(base_url + "&select_source=0")
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    async def parse(self, response):
        if response.xpath("//a[@aria-label='Weiter']"):
            yield response.follow(response.xpath("//a[@aria-label='Weiter']/@href").get(), callback=self.parse)
        for result in response.xpath("//table[@id='resultlist']/tbody/tr"):
            docid = result.xpath(".//a/@href").get()
            if not docid:
                # Row without an anchor — skip; concatenating `None` below would TypeError.
                output("bb: result row missing detail link", "warn")
                continue
            link = self.base_url + docid
            # Herausfinden des AZ...
            wait = self.wait
            tree = await deferred_to_future(self.detail_sem.run(deferToThread, self._fetch_detail_tree, link, wait))
            if tree is None:
                continue
            az_cells = tree.xpath("//div[@id='metadata']/div/table/tbody/tr[2]/td[1]/text()")
            if not az_cells:
                output(f"bb: no az on detail page {link}", "err")
                continue
            yield {
                "postprocess": self.postprocess,
                "wait": self.wait,
                "court": result.xpath(".//td[5]/text()").get(),
                "date": result.xpath(".//td[3]/text()").get(),
                "link": link,
                "az": az_cells[0],
                "docId": docid,
                "tree": tree,  # Wenn ohnehin schon verarbeitet...
            }
