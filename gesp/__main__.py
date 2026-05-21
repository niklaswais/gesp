import argparse
import datetime
import logging
import os
import sys

from scrapy.utils.reactor import install_reactor

# Scrapy requires install_reactor() to run before any spider modules are imported,
# so the remaining imports must stay below this line (ruff: noqa: E402).
install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")
from scrapy.crawler import CrawlerRunner  # noqa: E402
from scrapy.settings import Settings  # noqa: E402
from twisted.internet import reactor  # noqa: E402

from .spiders import bb, be, bund, bw, by, hb, he, hh, mv, ni, nw, rp, sh, sl, sn, st, th  # noqa: E402
from .src import config  # noqa: E402
from .src.config import SCRAPY_SETTINGS  # noqa: E402
from .src.fingerprint import Fingerprint  # noqa: E402
from .src.output import output  # noqa: E402

STATE_SPIDERS = {
    "bund": bund.SpdrBund,
    "bw": bw.SpdrBW,
    "by": by.SpdrBY,
    "be": be.SpdrBE,
    "bb": bb.SpdrBB,
    "hb": hb.SpdrHB,
    "hh": hh.SpdrHH,
    "he": he.SpdrHE,
    "mv": mv.SpdrMV,
    "ni": ni.SpdrNI,
    "nw": nw.SpdrNW,
    "rp": rp.SpdrRP,
    "sh": sh.SpdrSH,
    "sl": sl.SpdrSL,
    "sn": sn.SpdrSN,
    "st": st.SpdrST,
    "th": th.SpdrTH,
}

# Scrapy-Einstellungen setzen
settings = Settings()
for setting, value in SCRAPY_SETTINGS.items():
    settings.set(setting, value, priority="project")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gesp", description="scraping of german court decisions")
    p.add_argument("-c", "--courts", type=str.lower, help="individual selection of the included courts (ag/lg/olg/...)")
    p.add_argument(
        "-d", "--domains", type=str.lower, help="individual selection of the included legal domains (oeff/zivil/straf)"
    )
    p.add_argument("-p", "--path", type=str, help="sets the path where the results will be stored")
    p.add_argument(
        "-s", "--states", type=str.lower, help="individual selection of the included states (bund/bb/be/bw/by/...)"
    )
    p.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"gesp {config.__version__} by {config.__author__} (nwais.de)",
        help="version of this package",
    )
    p.add_argument("--docId", action="store_true", help="appends the docId, if present, to the filename")
    p.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="confirm non-commercial use non-interactively (for CI/cron)",
    )
    p.add_argument("--probe-only", action="store_true", dest="probe_only", help=argparse.SUPPRESS)
    p.add_argument(
        "-fp",
        "--fingerprint",
        nargs="?",
        const=True,
        help="creates (flag) or reads (argument, path) a fingerprint file",
    )
    p.add_argument(
        "-pp",
        "--postprocess",
        action=argparse.BooleanOptionalAction,
        help="turns on postprocessing of the downloaded decisions, removing all html elements and transforming them into a more easily machine readable format",
    )
    p.add_argument(
        "-w",
        "--wait",
        type=float,
        nargs="?",
        const=1.75,
        default=0.0,
        metavar="SECONDS",
        help="sleep N seconds before each per-decision fetch to avoid bans (mainly juris). "
        "Bare -w uses 1.75s; pass -w 3 for 3s. Default: 0 (no delay).",
    )
    return p


def main():
    args = build_parser().parse_args()
    if args.probe_only:
        sys.exit(_run_probes(args))
    if not args.yes:
        output(
            "Due to the terms of use governing the databases accessed by gesp, the use of gesp is only permitted for non-commercial purposes. Do you use gesp exclusively for non-commercial purposes?"
        )
        try:
            inp = input("[Y]es/[N]o: ").strip().lower()
        except EOFError:
            sys.exit()
        if inp not in ("y", "yes"):
            sys.exit()
    cl_courts, cl_states, cl_domains = [], [], []
    # -p (path)
    base = os.path.join(os.getcwd(), "results", datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"))
    path = base
    if args.path:
        if os.path.isdir(args.path):
            path = args.path
        else:
            output(f"creating new folder {args.path}...")
            try:
                os.makedirs(args.path)
            except OSError:
                output(f"could not create folder {args.path}", "err")
                sys.exit(1)
            else:
                path = args.path
    else:
        n = 1
        while os.path.exists(path):
            path = f"{base}_{n}"
            n += 1
        try:
            os.makedirs(path)
        except OSError:
            output(f"could not create folder {path}", "err")
            sys.exit(1)
    # if path[-1] != "/": path = path + "/"
    # -c (courts)
    if args.courts:
        for court in args.courts.split(","):
            if court not in config.COURTS and court != "larbg" and court != "vgh":
                output(f"unknown court '{court}'", "err")
            elif court == "larbg":  # larbg = lag
                output(f"court '{court}' is interpreted as 'lag'", "warn")
                cl_courts.append("lag")
            elif court == "vgh":  # vgh = ovg
                output(f"court '{court}' is interpreted as 'ovg'", "warn")
                cl_courts.append("ovg")
            else:
                cl_courts.append(court)
    # -s (states)
    if args.states:
        for state in args.states.split(","):
            if state not in config.STATES:
                output(f"unknown state '{state}'", "err")
            else:
                cl_states.append(state)
    elif cl_courts and set(cl_courts).issubset({"bgh", "bfh", "bverwg", "bverfg", "bpatg", "bag", "bsg"}):
        cl_states.append("bund")  # Nur Bundesgericht(e) angegeben → Bundesportal
    else:
        cl_states.extend(config.HTML_STATES)  # Sachsen und Bremen (PDF) nur bei expliziter Nennung
    # -d (domains)
    if args.domains:
        for domain in args.domains.split(","):
            if domain not in config.DOMAINS:
                output(f"unknown legal domain '{domain}'", "err")
            else:
                cl_domains.append(domain)
    args.postprocess = bool(args.postprocess)
    # -fp (fingerprint)
    if isinstance(args.fingerprint, str):  # fp als Argument
        fp = args.fingerprint
        if not os.path.exists(fp):
            output(f"file {fp} does not exist", "err")
        elif not os.path.isfile(fp):
            output(f"file {fp} is a folder, not a file", "err")
        else:
            Fingerprint(path, fp, args.docId, wait=args.wait)
    else:  # fp als Flag / kein fp
        fp = args.fingerprint is True
        logger = logging.getLogger("scrapy")
        logger.propagate = False
        logger.setLevel(logging.DEBUG)
        rnr = CrawlerRunner(settings=settings)
        for state, spider_cls in STATE_SPIDERS.items():
            if not cl_states or state in cl_states:
                rnr.crawl(
                    spider_cls,
                    path=path,
                    courts=cl_courts,
                    states=cl_states,
                    fp=fp,
                    domains=cl_domains,
                    store_docId=args.docId,
                    postprocess=args.postprocess,
                    wait=args.wait,
                )
        d = rnr.join()
        d.addBoth(lambda _: reactor.stop())
        reactor.run()


def _run_probes(args) -> int:
    """Hidden maintenance mode: refresh tests/fixtures/<state>_search.* from live portals."""
    from pathlib import Path

    from .probe import all_states, run_probe

    output_dir = Path(args.path) if args.path else Path.cwd() / "tests" / "fixtures"
    states = args.states.split(",") if args.states else all_states()
    print(f"probing {len(states)} state(s) → {output_dir}")
    failures = 0
    for state in states:
        ok, msg = run_probe(state, output_dir)
        status = "OK  " if ok else "FAIL"
        print(f"  {state:6}  {status}  {msg}")
        if not ok:
            failures += 1
    print(f"{len(states) - failures}/{len(states)} succeeded")
    return 1 if failures else 0


if __name__ == "__main__":
    main()
