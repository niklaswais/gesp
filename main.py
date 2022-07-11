# -*- coding: utf-8 -*-
__version__ = "0.1"
__author__ = "Niklas Wais"
__licence__ = "MIT"

import argparse
import datetime
import logging
import os
from scrapy.crawler import CrawlerRunner
from scrapy.shell import inspect_response
from tldextract import extract       ### !!nur in DEV!!
from twisted.internet import reactor
from spiders import *
from output import output

COURTS = ["ag", "arbg", "bgh", "bfh", "bverwg", "bverfg", "bpatg", "bag", "bsg", "fg", "lag", "lg", "lsg", "olg", "ovg", "sg"] # vgh = ovg
STATES = ["bund", "bw", "by", "be", "bb", "hb", "hh", "he", "mv", "ni", "nw", "rp", "sl", "sn", "st", "sh", "th"]
DOMAINS = ["oeff", "zivil", "straf"]

def main():
    cl_courts, cl_states, cl_domains = [], [], []
    cl_parser = argparse.ArgumentParser(prog="gesp", description="Scraping and Pre-Processing of German court decisions")
    cl_parser.add_argument("-c", "--courts", type=str.lower, help="individual selection of the included courts (ag/lg/olg/...)")
    cl_parser.add_argument("-d", "--domains", type=str.lower, help="individual selection of the included legal domains (oeff/zivil/straf)")
    cl_parser.add_argument("-p", "--path", type=str, help="sets the path where the results will be stored")
    cl_parser.add_argument("-s", "--states", type=str.lower, help="individual selection of the included states (bund/bb/be/bw/by/...)")
    cl_parser.add_argument("-v", "--version", action="version", version=f"gesp {__version__} by {__author__} (nwais.de)", help="version of this package")
    args = cl_parser.parse_args()
    # -p (path)
    path = os.path.dirname(os.path.realpath(__file__)) + "/" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    if (args.path):
        if os.path.isdir(args.path):
            path = args.path
        else:
            output(f"creating new folder {args.path}...")
            try:
                os.makedirs(args.path)
            except:
                output(f"could not create folder {args.path}", "err")
            else:
                path = args.path
    else:
        # Für den Fall, dass der Standrad-Pfad durch einen früheren Durchgang belegt ist
        n = 1
        while os.path.exists(path):
            path = f"{path}_{n}"
            n += 1
        try:
            os.makedirs(path)
        except:
            output(f"could not create folder {path}", "err")
    if path[-1] != "/": path = path + "/"
    # -c (courts)
    if (args.courts):
        for court in args.courts.split(","):
            if (not court in COURTS and court != "larbg"):
                output("unknown court '" + court + "'", "err")
            elif (court == "larbg"): # larbg = lag
                output("court '" + court + "' is interpreted as 'lag'", "warn")
                cl_courts.append("lag")
            else:
                cl_courts.append(court)
    # -s (states)
    if (args.states):
        for state in args.states.split(","):
            if (not state in STATES):
                output("unknown state '" + state + "'", "err")
            else:
                cl_states.append(state)
    # -d (domains)
    if (args.domains):
        for domain in args.domains.split(","):
            if (not domain in DOMAINS):
                output("unknown legal domain '" + domain + "'", "err")
            else:
                cl_domains.append(domain)

    logging.getLogger('scrapy').propagate = True
    #logging.basicConfig(level=logging.INFO, filemode='w', filename='log.txt')
    logger = logging.getLogger('scrapy')
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    rnr = CrawlerRunner()
    if ("bund" in cl_states or not cl_states):
        rnr.crawl(bund.SpdrBund, path=path, courts=cl_courts, domains=cl_domains)
    if ("bw" in cl_states or not cl_states):
        rnr.crawl(bw.SpdrBW, path=path, courts=cl_courts, domains=cl_domains)
    if ("by" in cl_states or not cl_states):
        rnr.crawl(by.SpdrBY, path=path, courts=cl_courts, domains=cl_domains)
    if ("be" in cl_states or not cl_states):
        rnr.crawl(be.SpdrBE, path=path, courts=cl_courts, domains=cl_domains)
    if ("bb" in cl_states or not cl_states):
        rnr.crawl(bb.SpdrBB, path=path, courts=cl_courts, domains=cl_domains)
    if ("he" in cl_states or not cl_states):
        rnr.crawl(he.SpdrHE, path=path, courts=cl_courts, domains=cl_domains)
    if ("hh" in cl_states or not cl_states):
        rnr.crawl(hh.SpdrHH, path=path, courts=cl_courts, domains=cl_domains)
    if ("nw" in cl_states or not cl_states):
        rnr.crawl(nw.SpdrNW, path=path, courts=cl_courts, domains=cl_domains)
    if ("mv" in cl_states or not cl_states):
        rnr.crawl(mv.SpdrMV, path=path, courts=cl_courts, domains=cl_domains)
    if ("rp" in cl_states or not cl_states):
        rnr.crawl(rp.SpdrRP, path=path, courts=cl_courts, domains=cl_domains)
    if ("sl" in cl_states or not cl_states):
        rnr.crawl(sl.SpdrSL, path=path, courts=cl_courts, domains=cl_domains)
    if ("st" in cl_states or not cl_states):
        rnr.crawl(st.SpdrST, path=path, courts=cl_courts, domains=cl_domains)
    if ("th" in cl_states or not cl_states):
        rnr.crawl(th.SpdrTH, path=path, courts=cl_courts, domains=cl_domains)
    d = rnr.join()
    d.addBoth(lambda _: reactor.stop())
    reactor.run()

if __name__ == "__main__":
    main()


# TODO: Länder: Verfassungsgerichtshöfe (verfgh)? ++ Bremen +++