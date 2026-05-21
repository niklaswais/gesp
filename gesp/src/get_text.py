import datetime
import time as timelib

import requests
from lxml import etree, html

from . import config
from .output import output


def bb(item):
    if "tree" not in item:
        if item["wait"]:
            timelib.sleep(item["wait"])
        try:
            txt = requests.get(item["link"], timeout=30).text
        except requests.RequestException as e:
            output(f"could not retrieve {item['link']}: {e!r}", "err")
            return
        try:
            item["tree"] = html.fromstring(txt)
        except (etree.LxmlError, ValueError) as e:
            output(f"could not parse {item['link']}: {e!r}", "err")
            return
    if (
        not item["tree"].xpath("//h1[@id='header']/text()")[0].rstrip().strip() == "Entscheidung"
    ):  # Herausfiltern von leeren Seiten
        # Dokument Aufräumen (nur bestimmte Bereiche übernehmen)...
        body_meta = html.tostring(item["tree"].xpath("//div[@id='metadata']")[0]).decode("utf-8")
        body_content = html.tostring(item["tree"].xpath("//div[@id='metadata']/following::div[1]")[0]).decode("utf-8")
        doc = "<html><head><title>%s</title></head><body>%s%s</body></html>" % (item["az"], body_meta, body_content)
        item["text"] = doc
        item["filetype"] = "html"
        return item
    else:
        output("could not retrieve " + item["link"], "err")


def be(item, headers, cookies):  # spider.headers, spider.cookies
    # item["text"]: Berlin ist JSON-Post-Response
    url = "https://gesetze.berlin.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = "https://gesetze.berlin.de/bsbe/document/" + item["docId"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = (
        '{"docId":"%s","format":"xsl","keyword":null,"sourceParams":{"source":"Unknown","category":"Alles"},"searches":[],"clientID":"bsbe","clientVersion":"bsbe - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'
        % (item["docId"], date, time)
    )
    if item["wait"]:
        timelib.sleep(item["wait"])
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body, timeout=30)
        data = req.json()
        doc = html.fromstring(
            f"<!doctype html><html><head><title>{item['az']}</title></head><body>{data['head']}{data['text']}</body></html>"
        )
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
    except (requests.RequestException, ValueError, KeyError, TypeError, etree.LxmlError) as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
        return None
    item["filetype"] = "html"
    return item


def bw(item, headers, cookies):  # spider.headers, spider.cookies
    # item["text"]: BW ist JSON-Post-Response
    url = "https://www.landesrecht-bw.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = "https://www.landesrecht-bw.de/bsbw/document/" + item["docId"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = (
        '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bsbw","clientVersion":"bsbw - V08_18_00 - 24.04.2025 11:53","r3ID":"%sT%sZ"}'
        % (item["docId"], date, time)
    )
    if item["wait"]:
        timelib.sleep(item["wait"])
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body, timeout=30)
        data = req.json()
        doc = html.fromstring(
            f"<!doctype html><html><head><title>{item['az']}</title></head><body>{data['head']}{data['text']}</body></html>"
        )
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
    except (requests.RequestException, ValueError, KeyError, TypeError, etree.LxmlError) as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
        return None
    item["filetype"] = "html"
    return item


def by(item):
    try:
        txt = requests.get(item["link"], headers=config.HEADERS, timeout=30).text
    except requests.RequestException as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
    else:
        if (
            txt[154:160] != "Fehler"
        ):  # Herausfiltern von leeren Seiten / bei leeren Seite ist text[10] == "h" / schnellere Version
            tree = etree.fromstring(txt.replace("\r\n", "\n"))
            tree.xpath("//script")[0].getparent().remove(tree.xpath("//script")[0])  # Druck-Dialog entfernen
            item["text"] = etree.tostring(tree, pretty_print=True, xml_declaration=True).decode("ascii")
            item["filetype"] = "xhtml"
            return item
        else:
            output("empty page " + item["link"], "err")


def he(item, headers, cookies):  # spider.headers, spider.cookies
    # item["text"]: Hessen ist JSON-Post-Response
    url = "https://www.lareda.hessenrecht.hessen.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = "https://www.lareda.hessenrecht.hessen.de/bshe/document/" + item["docId"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = (
        '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bshe","clientVersion":"bshe - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'
        % (item["docId"], date, time)
    )
    if item["wait"]:
        timelib.sleep(item["wait"])
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body, timeout=30)
        data = req.json()
        doc = html.fromstring(
            f"<!doctype html><html><head><title>{item['az']}</title></head><body>{data['head']}{data['text']}</body></html>"
        )
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
    except (requests.RequestException, ValueError, KeyError, TypeError, etree.LxmlError) as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
        return None
    item["filetype"] = "html"
    return item


def hh(item, headers, cookies):  # spider.headers, spider.cookies
    # item["text"]: Hamburg ist JSON-Post-Response
    url = "https://www.landesrecht-hamburg.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = "https://www.landesrecht-hamburg.de/bsha/document/" + item["docId"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = (
        '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bsha","clientVersion":"bsha - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'
        % (item["docId"], date, time)
    )
    if item["wait"]:
        timelib.sleep(item["wait"])
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body, timeout=30)
        data = req.json()
        doc = html.fromstring(
            f"<!doctype html><html><head><title>{item['az']}</title></head><body>{data['head']}{data['text']}</body></html>"
        )
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
    except (requests.RequestException, ValueError, KeyError, TypeError, etree.LxmlError) as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
        return None
    item["filetype"] = "html"
    return item


def mv(item, headers, cookies):  # spider.headers, spider.cookies
    # item["text"]: Mecklenburg-Vorpommern ist JSON-Post-Response
    url = "https://www.landesrecht-mv.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = item["link"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = (
        '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bsmv","clientVersion":"bsmv - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'
        % (item["docId"], date, time)
    )
    if item["wait"]:
        timelib.sleep(item["wait"])
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body, timeout=30)
        data = req.json()
        doc = html.fromstring(
            f"<!doctype html><html><head><title>{item['az']}</title></head><body>{data['head']}{data['text']}</body></html>"
        )
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
    except (requests.RequestException, ValueError, KeyError, TypeError, etree.LxmlError) as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
        return None
    item["filetype"] = "html"
    return item


def ni(item):
    # In normal runs the spider pre-fetches the detail page and attaches `tree`.
    # During fingerprint reconstruction the spider is bypassed, so fetch here.
    if "tree" not in item:
        if item.get("wait"):
            timelib.sleep(item["wait"])
        try:
            txt = requests.get(item["link"], headers=config.ni_headers, timeout=30).text
        except requests.RequestException as e:
            output(f"could not retrieve {item['link']}: {e!r}", "err")
            return
        try:
            item["tree"] = html.fromstring(txt)
        except (etree.LxmlError, ValueError) as e:
            output(f"could not parse {item['link']}: {e!r}", "err")
            return
    tree = item["tree"]
    article = tree.xpath("//article")
    if article:
        # Abspeichern des Texts
        body = html.tostring(tree.xpath("//article")[0]).decode("utf-8")
        doc = "<html><head><title>%s - %s - %s</title></head><body>%s</body></html>" % (
            item["court"],
            item["date"],
            item["az"],
            body,
        )
        item["text"] = doc
        item["filetype"] = "html"
        return item


def nw(item):
    if item["wait"]:
        timelib.sleep(item["wait"])
    try:
        item["text"] = requests.get(item["link"], headers=config.HEADERS, timeout=30).text
    except requests.RequestException as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
        return
    if (
        item["text"][14] == " "
    ):  # Herausfiltern von leeren Seiten / bei leeren Seite ist text[14] == " " / schnellere Version
        item["filetype"] = "html"
        return item
    output("empty page " + item["link"], "err")


def rp(item, headers, cookies):  # spider.headers, spider.cookies
    # item["text"]: Rheinland-Pfalz ist JSON-Post-Response
    url = "https://www.landesrecht.rlp.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = item["link"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = (
        '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bsrp","clientVersion":"bsrp - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'
        % (item["docId"], date, time)
    )
    if item["wait"]:
        timelib.sleep(item["wait"])
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body, timeout=30)
        data = req.json()
        doc = html.fromstring(
            f"<!doctype html><html><head><title>{item['az']}</title></head><body>{data['head']}{data['text']}</body></html>"
        )
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
    except (requests.RequestException, ValueError, KeyError, TypeError, etree.LxmlError) as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
        return None
    item["filetype"] = "html"
    return item


def sh(item, headers, cookies):
    # item["text"]: Schleswig-Holstein ist JSON-Post-Response
    url = "https://www.gesetze-rechtsprechung.sh.juris.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = item["link"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = (
        '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bssh","clientVersion":"bssh - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'
        % (item["docId"], date, time)
    )
    if item["wait"]:
        timelib.sleep(item["wait"])
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body, timeout=30)
        data = req.json()
        doc = html.fromstring(
            f"<!doctype html><html><head><title>{item['az']}</title></head><body>{data['head']}{data['text']}</body></html>"
        )
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
    except (requests.RequestException, ValueError, KeyError, TypeError, etree.LxmlError) as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
        return None
    item["filetype"] = "html"
    return item


def sl(item, headers, cookies):  # spider.headers, spider.cookies
    # item["text"]: Saarland ist JSON-Post-Response
    url = "https://recht.saarland.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = item["link"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = (
        '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bssl","clientVersion":"bssl - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'
        % (item["docId"], date, time)
    )
    if item["wait"]:
        timelib.sleep(item["wait"])
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body, timeout=30)
        data = req.json()
        doc = html.fromstring(
            f"<!doctype html><html><head><title>{item['az']}</title></head><body>{data['head']}{data['text']}</body></html>"
        )
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
    except (requests.RequestException, ValueError, KeyError, TypeError, etree.LxmlError) as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
        return None
    item["filetype"] = "html"
    return item


def sn(item, headers):  # spider.headers
    if "body" in item:  # AG/LG/OLG-Subportal
        url = "https://www.justiz.sachsen.de/esamosplus/pages/treffer.aspx"
        headers["Referer"] = "https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx"
        if item["wait"]:
            timelib.sleep(item["wait"])
        try:
            item["req"] = requests.post(url=url, headers=headers, data=item["body"], timeout=30)
        except requests.RequestException as e:
            output(f"could not retrieve {item['az']}: {e!r}", "err")
        else:
            return item
    elif "link" in item:  # OVG-Subportal
        if item["wait"]:
            timelib.sleep(item["wait"])
        try:
            # Zwischengeschaltete Seite, von der aus erst der Filelink kopiert werden muss
            tree = html.fromstring(requests.get(item["link"], timeout=30).text)
        except (requests.RequestException, etree.LxmlError, ValueError) as e:
            output(f"could not retrieve {item['link']}: {e!r}", "err")
        else:
            hrefs = tree.xpath("//a[@target='_blank']/@href")
            if not hrefs:
                output(f"sn: no detail link on {item['link']}", "err")
                return None
            item["link"] = "https://www.justiz.sachsen.de/ovgentschweb/" + hrefs[0]
            return item


def st(item, headers, cookies):
    # item["text"]: Sachsen-Anhalt ist JSON-Post-Response
    url = "https://www.landesrecht.sachsen-anhalt.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = item["link"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = (
        '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bsst","clientVersion":"bsst - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'
        % (item["docId"], date, time)
    )
    if item["wait"]:
        timelib.sleep(item["wait"])
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body, timeout=30)
        data = req.json()
        doc = html.fromstring(
            f"<!doctype html><html><head><title>{item['az']}</title></head><body>{data['head']}{data['text']}</body></html>"
        )
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
    except (requests.RequestException, ValueError, KeyError, TypeError, etree.LxmlError) as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
        return None
    item["filetype"] = "html"
    return item


def th(item, headers, cookies):  # spider.headers, spider.cookies
    # item["text"]: Thüringen ist JSON-Post-Response
    url = "https://landesrecht.thueringen.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = item["link"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = (
        '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bsth","clientVersion":"bsth - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'
        % (item["docId"], date, time)
    )
    if item["wait"]:
        timelib.sleep(item["wait"])
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body, timeout=30)
        data = req.json()
        doc = html.fromstring(
            f"<!doctype html><html><head><title>{item['az']}</title></head><body>{data['head']}{data['text']}</body></html>"
        )
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
    except (requests.RequestException, ValueError, KeyError, TypeError, etree.LxmlError) as e:
        output(f"could not retrieve {item['link']}: {e!r}", "err")
        return None
    item["filetype"] = "html"
    return item
