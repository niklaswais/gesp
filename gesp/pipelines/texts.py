from scrapy.utils.defer import deferred_to_future
from twisted.internet.defer import DeferredSemaphore
from twisted.internet.threads import deferToThread

from ..src.get_text import bb, be, bw, he, hh, mv, ni, nw, rp, sh, sl, sn, st, th
from ._base import CrawlerAware


class TextsPipeline(CrawlerAware):
    def __init__(self):
        self.sem = DeferredSemaphore(1)

    async def process_item(self, item, spider=None):
        spider = self._spider(spider)
        name = spider.name[7:]
        headers = getattr(spider, "headers", None)
        cookies = getattr(spider, "cookies", None)
        # Several get_text.* functions mutate headers["Referer"] per item (see
        # get_text.be, get_text.bw, etc.). Without copying, concurrent items
        # from the same portal would race on that mutation. Copy on the reactor
        # thread before deferring.
        if headers is not None:
            headers = dict(headers)
        if cookies is not None:
            cookies = dict(cookies)
        return await deferred_to_future(self.sem.run(deferToThread, self._dispatch, item, name, headers, cookies))

    @staticmethod
    def _dispatch(item, name, headers, cookies):
        if name == "bb":
            return bb(item)
        elif name == "be":
            return be(item, headers, cookies)
        elif name == "bw":
            return bw(item, headers, cookies)
        # by is intentionally absent — its decisions are zip files handled by
        # save_as_html, not by a get_text dispatch.
        elif name == "he":
            return he(item, headers, cookies)
        elif name == "hh":
            return hh(item, headers, cookies)
        elif name == "mv":
            return mv(item, headers, cookies)
        elif name == "ni":
            return ni(item)
        elif name == "nw":
            return nw(item)
        elif name == "rp":
            return rp(item, headers, cookies)
        elif name == "sh":
            return sh(item, headers, cookies)
        elif name == "sl":
            return sl(item, headers, cookies)
        elif name == "sn":
            return sn(item, headers)
        elif name == "st":
            return st(item, headers, cookies)
        elif name == "th":
            return th(item, headers, cookies)
