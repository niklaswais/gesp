"""Shared pipeline base — keeps spider access out of `process_item` signatures.

Scrapy 2.15+ deprecates pipeline methods that take `spider` as a required arg
(see scrapy/middleware.py:_check_mw_method_spider_arg). The recommended path is
to capture the crawler via `from_crawler` and read `self.crawler.spider`.

Keeping `spider` as an optional kwarg lets tests and direct callers pass it
explicitly without going through Scrapy.
"""


class CrawlerAware:
    @classmethod
    def from_crawler(cls, crawler):
        obj = cls()
        obj.crawler = crawler
        return obj

    def _spider(self, spider=None):
        return spider if spider is not None else self.crawler.spider
