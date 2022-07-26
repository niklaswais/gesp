# -*- coding: utf-8 -*-
from src.get_text import bb, be, bw, by, he, hh, mv, ni, nw, rp, sh, sl, sn, st, th

class TextsPipeline:
    def process_item(self, item, spider):
        if spider.name[7:] == "bb":
            return bb(item)
        elif spider.name[7:] == "be":
            return be(item, spider.headers, spider.cookies)
        elif spider.name[7:] == "bw":
            return bw(item)
        elif spider.name[7:] == "by":
            return by(item)
        elif spider.name[7:] == "he":
            return he(item, spider.headers, spider.cookies)
        elif spider.name[7:] == "hh":
            return hh(item, spider.headers, spider.cookies)
        elif spider.name[7:] == "mv":
            return mv(item, spider.headers, spider.cookies)
        elif spider.name[7:] == "ni":
            return ni(item)
        elif spider.name[7:] == "nw":
            return nw(item)
        elif spider.name[7:] == "rp":
            return rp(item, spider.headers, spider.cookies)
        elif spider.name[7:] == "sh":
            return sh(item)
        elif spider.name[7:] == "sl":
            return sl(item, spider.headers, spider.cookies)
        elif spider.name[7:] == "sn":
            return sn(item, spider.headers)
        elif spider.name[7:] == "st":
            return st(item, spider.headers, spider.cookies)
        elif spider.name[7:] == "th":
            return th(item, spider.headers, spider.cookies)