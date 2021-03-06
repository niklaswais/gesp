# -*- coding: utf-8 -*-

import argparse
import datetime
import logging
import os
import scrapy
from scrapy.shell import inspect_response
from tldextract import extract       ### !!nur in DEV!!
from twisted.internet import reactor
from spiders import *
import src.config
from src.output import output

def main():
    cl_courts, cl_states, cl_domains = [], [], []
    cl_parser = argparse.ArgumentParser(prog="gesp", description="scraping of german court decisions")
    cl_parser.add_argument("-c", "--courts", type=str.lower, help="individual selection of the included courts (ag/lg/olg/...)")
    cl_parser.add_argument("-d", "--domains", type=str.lower, help="individual selection of the included legal domains (oeff/zivil/straf)")
    cl_parser.add_argument("-p", "--path", type=str, help="sets the path where the results will be stored")
    cl_parser.add_argument("-s", "--states", type=str.lower, help="individual selection of the included states (bund/bb/be/bw/by/...)")
    cl_parser.add_argument("-v", "--version", action="version", version=f"gesp {src.config.__version__} by {src.config.__author__} (nwais.de)", help="version of this package")
    cl_parser.add_argument("-fp", "--fingerprint", nargs="?", const=True, help="creates (flag) or reads (argument, path) a fingerprint file")
    args = cl_parser.parse_args()
    # -p (path)
    path = os.path.dirname(os.path.realpath(__file__)) + "/results/" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
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
        n = 1
        while os.path.exists(path): # Für den Fall, dass der Standrad-Pfad durch einen früheren Durchgang belegt ist
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
            if (not court in src.config.COURTS and court != "larbg" and court != "vgh"):
                output(f"unknown court '{court}'", "err")
            elif (court == "larbg"): # larbg = lag
                output(f"court '{court}' is interpreted as 'lag'", "warn")
                cl_courts.append("lag")
            elif (court == "vgh"): # vgh = ovg
                output(f"court '{court}' is interpreted as 'ovg'", "warn")
                cl_courts.append("lag")
            else:
                cl_courts.append(court)
    # -s (states)
    if (args.states):
        for state in args.states.split(","):
            if (not state in src.config.STATES):
                output(f"unknown state '{state}'", "err")
            else:
                cl_states.append(state)
    # -d (domains)
    if (args.domains):
        for domain in args.domains.split(","):
            if (not domain in src.config.DOMAINS):
                output(f"unknown legal domain '{domain}'", "err")
            else:
                cl_domains.append(domain)
    # -fp (fingerprint)
    if isinstance(args.fingerprint, str): # fp als Argument
        fp = args.fingerprint
        if not os.path.exists(fp):
            output(f"file {fp} does not exist", "err")
        else:
            rnr = scrapy.crawler.CrawlerRunner()
            d = rnr.crawl(fgrprint.SpdrFP, path=path, fp=fp)
            d.addBoth(lambda _: reactor.stop())
            reactor.run()
    else:  # fp als Flag / kein fp
        if args.fingerprint == True:
            fp = args.fingerprint
        else:
            fp = False
        logging.getLogger('scrapy').propagate = True
        logger = logging.getLogger('scrapy')
        logger.propagate = False
        logger.setLevel(logging.DEBUG)
        rnr = scrapy.crawler.CrawlerRunner()
        if ("bund" in cl_states or not cl_states):
            rnr.crawl(bund.SpdrBund, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("bw" in cl_states or not cl_states):
            rnr.crawl(bw.SpdrBW, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("by" in cl_states or not cl_states):
            rnr.crawl(by.SpdrBY, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("be" in cl_states or not cl_states):
            rnr.crawl(be.SpdrBE, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("bb" in cl_states or not cl_states):
            rnr.crawl(bb.SpdrBB, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("hb" in cl_states or not cl_states):
            rnr.crawl(hb.SpdrHB, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("hh" in cl_states or not cl_states):
            rnr.crawl(hh.SpdrHH, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("he" in cl_states or not cl_states):
            rnr.crawl(he.SpdrHE, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("mv" in cl_states or not cl_states):
            rnr.crawl(mv.SpdrMV, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("ni" in cl_states or not cl_states):
            rnr.crawl(ni.SpdrNI, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("nw" in cl_states or not cl_states):
            rnr.crawl(nw.SpdrNW, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("rp" in cl_states or not cl_states):
            rnr.crawl(rp.SpdrRP, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("sh" in cl_states or not cl_states):
            rnr.crawl(sh.SpdrSH, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("sl" in cl_states or not cl_states):
            rnr.crawl(sl.SpdrSL, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("sn" in cl_states or not cl_states):
            rnr.crawl(sn.SpdrSN, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("st" in cl_states or not cl_states):
            rnr.crawl(st.SpdrST, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        if ("th" in cl_states or not cl_states):
            rnr.crawl(th.SpdrTH, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains)
        d = rnr.join()
        d.addBoth(lambda _: reactor.stop())
        reactor.run()

if __name__ == "__main__":
    main()


# TODO: Länder: Verfassungsgerichtshöfe (verfgh)? ++ Bremen +++