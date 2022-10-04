# -*- coding: utf-8 -*-

import argparse
import datetime
import logging
import os
import scrapy
import sys
from scrapy.shell import inspect_response
from tldextract import extract       ### !!nur in DEV!!
from twisted.internet import reactor
from spiders import bb, be, bund, bw, by, hb, hh, he, mv, ni, nw, rp, sh, sl, sn, st, th
import src.config
from src.output import output
from src.fingerprint import Fingerprint

def main():
    output("Due to the terms of use governing the databases accessed by gesp, the use of gesp is only permitted for non-commercial purposes. Do you use gesp exclusively for non-commercial purposes?")
    inp = input("[Y]es/[N]o: ")
    try:
        inp = inp.lower()
    except:
        sys.exit()
    else:
        if inp != "y" and inp != "yes":
            sys.exit()
    cl_courts, cl_states, cl_domains = [], [], []
    cl_parser = argparse.ArgumentParser(prog="gesp", description="scraping of german court decisions")
    cl_parser.add_argument("-c", "--courts", type=str.lower, help="individual selection of the included courts (ag/lg/olg/...)")
    cl_parser.add_argument("-d", "--domains", type=str.lower, help="individual selection of the included legal domains (oeff/zivil/straf)")
    cl_parser.add_argument("-p", "--path", type=str, help="sets the path where the results will be stored")
    cl_parser.add_argument("-s", "--states", type=str.lower, help="individual selection of the included states (bund/bb/be/bw/by/...)")
    cl_parser.add_argument("-v", "--version", action="version", version=f"gesp {src.config.__version__} by {src.config.__author__} (nwais.de)", help="version of this package")
    cl_parser.add_argument('--docId', action='store_true', help="appends the docId, if present, to the filename")
    cl_parser.add_argument("-fp", "--fingerprint", nargs="?", const=True, help="creates (flag) or reads (argument, path) a fingerprint file")
    args = cl_parser.parse_args()
    # -p (path)
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "results", datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"))
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
    #if path[-1] != "/": path = path + "/"
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
    else:
        if cl_courts and set(cl_courts).issubset({"bgh", "bfh", "bverwg", "bverfg", "bpatg", "bag", "bsg"}):
            cl_states.append("bund") # Nur Bundesgericht(e) angegebeben, aber nicht auf Bund eingegrenzt ("-s bund"): Eingrenzung auf Bundesportal
        else:
            cl_states.extend(src.config.HTML_STATES)  # Sachsen und Bremen (PDF) nur bei expliziter Nennung
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
        elif not os.path.isfile(fp):
            output(f"file {fp} is a folder, not a file", "err")
        else:
            fp_importer = Fingerprint(path, fp, args.store_docId)
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
            rnr.crawl(bund.SpdrBund, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("bw" in cl_states or not cl_states):
            rnr.crawl(bw.SpdrBW, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("by" in cl_states or not cl_states):
            rnr.crawl(by.SpdrBY, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("be" in cl_states or not cl_states):
            rnr.crawl(be.SpdrBE, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("bb" in cl_states or not cl_states):
            rnr.crawl(bb.SpdrBB, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("hb" in cl_states or not cl_states):
            rnr.crawl(hb.SpdrHB, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("hh" in cl_states or not cl_states):
            rnr.crawl(hh.SpdrHH, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("he" in cl_states or not cl_states):
            rnr.crawl(he.SpdrHE, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("mv" in cl_states or not cl_states):
            rnr.crawl(mv.SpdrMV, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("ni" in cl_states or not cl_states):
            rnr.crawl(ni.SpdrNI, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("nw" in cl_states or not cl_states):
            rnr.crawl(nw.SpdrNW, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("rp" in cl_states or not cl_states):
            rnr.crawl(rp.SpdrRP, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("sh" in cl_states or not cl_states):
            rnr.crawl(sh.SpdrSH, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("sl" in cl_states or not cl_states):
            rnr.crawl(sl.SpdrSL, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("sn" in cl_states or not cl_states):
            rnr.crawl(sn.SpdrSN, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("st" in cl_states or not cl_states):
            rnr.crawl(st.SpdrST, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        if ("th" in cl_states or not cl_states):
            rnr.crawl(th.SpdrTH, path=path, courts=cl_courts, states=cl_states, fp=fp, domains=cl_domains, store_docId=args.docId)
        d = rnr.join()
        d.addBoth(lambda _: reactor.stop())
        reactor.run()

if __name__ == "__main__":
    main()


# TODO: Länder: Verfassungsgerichtshöfe (verfgh)?