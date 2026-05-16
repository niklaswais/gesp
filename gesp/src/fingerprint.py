import datetime
import json
import lzma
import os

import requests

from . import config
from .create_file import save_as_html, save_as_pdf
from .get_text import bb, be, bw, by, he, hh, mv, ni, nw, rp, sh, sl, st, th
from .output import output


def _csrf_headers(state: str, url: str, headers: dict, cookies, body) -> dict:
    """Fetch a CSRF token from a jportal init endpoint and inject it into headers."""
    try:
        r = requests.post(url=url, headers=headers, cookies=cookies, data=body, timeout=10)
        headers["x-csrf-token"] = r.json()["csrfToken"]
    except Exception:
        output(f"{state}: could not get x-csrf-token", "err")
    return headers


# Map of jportal state codes to (init URL, headers, cookies, body template).
# Body templates take (date, time) as % args; see config.py for the formats.
_JPORTAL_INIT = {
    "be": (
        "https://gesetze.berlin.de/jportal/wsrest/recherche3/init",
        config.be_headers,
        config.be_cookies,
        config.be_body,
    ),
    "bw": (
        "https://www.landesrecht-bw.de/jportal/wsrest/recherche3/init",
        config.bw_headers,
        config.bw_cookies,
        config.bw_body,
    ),
    "he": (
        "https://www.lareda.hessenrecht.hessen.de/jportal/wsrest/recherche3/init",
        config.he_headers,
        config.he_cookies,
        config.he_body,
    ),
    "hh": (
        "https://www.landesrecht-hamburg.de/jportal/wsrest/recherche3/init",
        config.hh_headers,
        config.hh_cookies,
        config.hh_body,
    ),
    "mv": (
        "https://www.landesrecht-mv.de/jportal/wsrest/recherche3/init",
        config.mv_headers,
        config.mv_cookies,
        config.mv_body,
    ),
    "rp": (
        "https://www.landesrecht.rlp.de/jportal/wsrest/recherche3/init",
        config.rp_headers,
        config.rp_cookies,
        config.rp_body,
    ),
    "sl": (
        "https://recht.saarland.de/jportal/wsrest/recherche3/init",
        config.sl_headers,
        config.sl_cookies,
        config.sl_body,
    ),
    "st": (
        "https://www.landesrecht.sachsen-anhalt.de/jportal/wsrest/recherche3/init",
        config.st_headers,
        config.st_cookies,
        config.st_body,
    ),
    "th": (
        "https://landesrecht.thueringen.de/jportal/wsrest/recherche3/init",
        config.th_headers,
        config.th_cookies,
        config.th_body,
    ),
}

# State code → get_text extractor that consumes (item, headers, cookies) for jportal states.
_JPORTAL_EXTRACTORS = {
    "be": be,
    "bw": bw,
    "he": he,
    "hh": hh,
    "mv": mv,
    "rp": rp,
    "sl": sl,
    "st": st,
    "th": th,
}

# State code → get_text extractor that consumes just (item,) for non-jportal HTML states.
_SIMPLE_EXTRACTORS = {"bb": bb, "by": by, "ni": ni, "nw": nw, "sh": sh}


class Fingerprint:
    def __init__(self, path, fp_path, store_docId):
        for i in Fingerprint.load_file(fp_path):
            if "version" in i and "date" in i and "args" in i:
                output(f"reconstructing from fingerprint {fp_path} ({i['version']}, {i['date']}, {i['args']})")
                continue

            results_subfolder = os.path.join(path, i["s"])
            if not os.path.exists(results_subfolder):
                try:
                    os.makedirs(results_subfolder)
                except Exception:
                    output(f"could not create folder {results_subfolder}", "err")

            item = {"court": i["c"], "date": i["d"], "az": i["az"]}
            if "link" in i:
                item["link"] = i["link"]
            if "docId" in i:
                item["docId"] = i["docId"]

            state = i["s"]
            if state == "sn" and i.get("link") == "https://www.justiz.sachsen.de/esamosplus/pages/treffer.aspx":
                output("sn: reconstruction for AG/LG/OLG decisions is not supported", "warn")
                continue
            if state == "bund":
                save_as_html(item, state, path, store_docId)
                continue
            if state in ("hb", "sn"):
                save_as_pdf(item, state, path)
                continue

            if state in _JPORTAL_EXTRACTORS:
                date = str(datetime.date.today())
                time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
                url, headers, cookies, body_tpl = _JPORTAL_INIT[state]
                headers = _csrf_headers(state, url, headers, cookies, body_tpl % (date, time))
                item = _JPORTAL_EXTRACTORS[state](item, headers, cookies)
            elif state in _SIMPLE_EXTRACTORS:
                item = _SIMPLE_EXTRACTORS[state](item)
            else:
                output(f"unknown state '{state}' in fingerprint", "err")
                continue

            save_as_html(item, state, path, store_docId)

    @staticmethod
    def load_file(fp):
        buf = ""
        lzmad = lzma.LZMADecompressor()
        with open(fp, "rb") as f:
            while chunk := f.read(1024):
                buf += lzmad.decompress(chunk).decode()
                parts = buf.split("|")
                for line in parts[:-1]:
                    if line:
                        yield json.loads(line)
                buf = parts[-1]
