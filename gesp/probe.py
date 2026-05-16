"""Capture the response that each spider's parse() reads, for fixture-based drift tests.

Used by `gesp --probe-only` and `tests/refresh_fixtures.py`. The captured fixture
is the same payload the spider would receive in production; the parse-drift tests
in `tests/test_spider_parse.py` then verify that the spider still extracts items
from it.

Two probe flows:
  * "simple"  — one HTTP request, response saved as-is.
  * "jportal" — two steps: POST init → grab CSRF token → POST search.
                The *search* response is what gets saved, since that's the one
                the spider's extract_data() actually parses.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import requests

from .src import config


# Truncate hooks: post-fetch transform to keep fixtures small. Bund returns the
# entire federal catalog (~20 MB), but parse() only iterates <item> elements —
# the first ~20 are plenty to exercise XPath drift.
def _trim_bund(body: bytes) -> bytes:
    """Keep only the first 20 <item>...</item> blocks of the bund XML feed."""
    head_end = body.find(b"<items>")
    if head_end == -1:
        return body
    head_end += len(b"<items>")
    rest = body[head_end:]
    cutoff = 0
    for _ in range(20):
        idx = rest.find(b"</item>", cutoff)
        if idx == -1:
            return body
        cutoff = idx + len(b"</item>")
    return body[:head_end] + rest[:cutoff] + b"\n</items>\n"


# Simple states: single request, response is what parse() reads.
# Keys: method, url, headers (optional), data (optional, str/bytes), ext,
# trim (optional callable bytes → bytes).
_SIMPLE_PROBES: dict[str, dict] = {
    "bund": {
        "method": "GET",
        "url": "http://www.rechtsprechung-im-internet.de/jportal/docs/bsjrs/",
        "ext": "xml",
        "trim": _trim_bund,
    },
    "by": {
        "method": "GET",
        "url": "https://www.gesetze-bayern.de/Search/Filter/DOKTYP/rspr",
        "ext": "html",
    },
    "bb": {
        "method": "GET",
        "url": "https://gerichtsentscheidungen.brandenburg.de/suche?&select_source=0",
        "ext": "html",
    },
    "hb": {
        "method": "GET",
        "url": "https://www.landesarbeitsgericht.bremen.de/entscheidungen/entscheidungsuebersicht-11508?max=10&skip=0",
        "ext": "html",
    },
    "ni": {
        "method": "GET",
        "url": (
            "https://voris.wolterskluwer-online.de/search?"
            "query=&in_publication=&in_year=&in_edition=&voris_number=&issuer=&date=&end_date_range="
            "&lawtaxonomy=&pit=&da_id=&issuer_label=&content_tree_nodes="
            "&publicationtype=publicationform-ats-filter%21ATS_Rechtsprechung"
        ),
        "ext": "html",
    },
    "nw": {
        "method": "POST",
        "url": "https://nrwesuche.justiz.nrw.de/index.php",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) gesp/probe",
        },
        "data": (
            "gerichtstyp=Landgericht&gerichtsbarkeit=Ordentliche+Gerichtsbarkeit"
            "&gerichtsort=&entscheidungsart=&date=&von=23.5.1949&bis=01.01.2024"
            "&validFrom=&von2=&bis2=&aktenzeichen=&schlagwoerter=&q=&method=stem"
            "&qSize=10&sortieren_nach=datum_absteigend&absenden=Suchen&advanced_search=false"
        ),
        "ext": "html",
    },
    "sn": {
        "method": "GET",
        "url": "https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx",
        "ext": "html",
    },
}

# jportal states: init URL → CSRF → search URL. clientID varies per portal.
_JPORTAL_PROBES: dict[str, tuple[str, str, str]] = {
    "be": (
        "https://gesetze.berlin.de/jportal/wsrest/recherche3/init",
        "https://gesetze.berlin.de/jportal/wsrest/recherche3/search",
        "bsbe",
    ),
    "bw": (
        "https://www.landesrecht-bw.de/jportal/wsrest/recherche3/init",
        "https://www.landesrecht-bw.de/jportal/wsrest/recherche3/search",
        "bsbw",
    ),
    "he": (
        "https://www.lareda.hessenrecht.hessen.de/jportal/wsrest/recherche3/init",
        "https://www.lareda.hessenrecht.hessen.de/jportal/wsrest/recherche3/search",
        "bshe",
    ),
    "hh": (
        "https://www.landesrecht-hamburg.de/jportal/wsrest/recherche3/init",
        "https://www.landesrecht-hamburg.de/jportal/wsrest/recherche3/search",
        "bshh",
    ),
    "mv": (
        "https://www.landesrecht-mv.de/jportal/wsrest/recherche3/init",
        "https://www.landesrecht-mv.de/jportal/wsrest/recherche3/search",
        "bsmv",
    ),
    "rp": (
        "https://www.landesrecht.rlp.de/jportal/wsrest/recherche3/init",
        "https://www.landesrecht.rlp.de/jportal/wsrest/recherche3/search",
        "bsrp",
    ),
    "sh": (
        "https://www.gesetze-rechtsprechung.sh.juris.de/jportal/wsrest/recherche3/init",
        "https://www.gesetze-rechtsprechung.sh.juris.de/jportal/wsrest/recherche3/search",
        "bssh",
    ),
    "sl": (
        "https://recht.saarland.de/jportal/wsrest/recherche3/init",
        "https://recht.saarland.de/jportal/wsrest/recherche3/search",
        "bssl",
    ),
    "st": (
        "https://www.landesrecht.sachsen-anhalt.de/jportal/wsrest/recherche3/init",
        "https://www.landesrecht.sachsen-anhalt.de/jportal/wsrest/recherche3/search",
        "bsst",
    ),
    "th": (
        "https://landesrecht.thueringen.de/jportal/wsrest/recherche3/init",
        "https://landesrecht.thueringen.de/jportal/wsrest/recherche3/search",
        "bsth",
    ),
}


def all_states() -> list[str]:
    return sorted(set(_SIMPLE_PROBES) | set(_JPORTAL_PROBES))


def is_jportal(state: str) -> bool:
    return state in _JPORTAL_PROBES


def fixture_filename(state: str) -> str:
    if state in _JPORTAL_PROBES:
        return f"{state}_search.json"
    return f"{state}_search.{_SIMPLE_PROBES[state]['ext']}"


def _headers_for(state: str, spec: dict) -> dict:
    """Combine the spider's config.<state>_headers (if any) with probe-specific overrides.

    Mirrors what the real scrapy spider sends, so the probe presents the same
    identity to the portal.
    """
    base = dict(getattr(config, f"{state}_headers", {}) or {})
    base.update(spec.get("headers") or {})
    return base


def _probe_simple(state: str, output_dir: Path) -> tuple[bool, str]:
    spec = _SIMPLE_PROBES[state]
    try:
        r = requests.request(
            spec["method"],
            spec["url"],
            headers=_headers_for(state, spec),
            data=spec.get("data"),
            timeout=30,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        return False, f"{type(e).__name__}: {e}"
    body = r.content
    trim = spec.get("trim")
    if trim is not None:
        body = trim(body)
    (output_dir / fixture_filename(state)).write_bytes(body)
    return True, f"{len(body)} bytes"


def _probe_jportal(state: str, output_dir: Path) -> tuple[bool, str]:
    init_url, search_url, client_id = _JPORTAL_PROBES[state]
    headers = dict(getattr(config, f"{state}_headers"))
    cookies = getattr(config, f"{state}_cookies")
    body_tpl = getattr(config, f"{state}_body")
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    try:
        r_init = requests.post(init_url, headers=headers, cookies=cookies, data=body_tpl % (date, time), timeout=30)
        r_init.raise_for_status()
        token = r_init.json()["csrfToken"]
    except (requests.RequestException, KeyError, ValueError) as e:
        return False, f"init failed: {type(e).__name__}: {e}"
    headers["x-csrf-token"] = token
    search_body = (
        '{"searchTasks":{"RESULT_LIST":{"start":1,"size":10,"sort":"date","addToHistory":true,"addCategory":true},'
        '"RESULT_LIST_CACHE":{"start":11,"size":10},"FAST_ACCESS":{},"SEARCH_WORD_HITS":{}},'
        '"filters":{"CATEGORY":["Rechtsprechung"]},"searches":[],'
        f'"clientID":"{client_id}","clientVersion":"{client_id} - V06_07_00 - 23.06.2022 11:20",'
        f'"r3ID":"s{date}T{time}Z"}}'
    )
    try:
        r_search = requests.post(search_url, headers=headers, cookies=cookies, data=search_body, timeout=30)
        r_search.raise_for_status()
    except requests.RequestException as e:
        return False, f"search failed: {type(e).__name__}: {e}"
    (output_dir / fixture_filename(state)).write_bytes(r_search.content)
    return True, f"{len(r_search.content)} bytes"


def run_probe(state: str, output_dir: Path) -> tuple[bool, str]:
    """Probe one state, save its fixture, return (ok, message)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if state in _JPORTAL_PROBES:
        return _probe_jportal(state, output_dir)
    if state in _SIMPLE_PROBES:
        return _probe_simple(state, output_dir)
    return False, "unknown state"
