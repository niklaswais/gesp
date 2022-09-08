# -*- coding: utf-8 -*-
import src.config
from src.output import output
from lxml import etree, html
import datetime
import requests

def bb(item):
    if not "tree" in item:
        item["tree"] = html.fromstring(requests.get(item["link"]).text)
    if not item["tree"].xpath("//h1[@id='header']/text()")[0].rstrip().strip() == "Entscheidung": # Herausfiltern von leeren Seiten
        # Dokument Aufräumen (nur bestimmte Bereiche übernehmen)...
        body_meta = html.tostring(item["tree"].xpath("//div[@id='metadata']")[0]).decode("utf-8")
        body_content = html.tostring(item["tree"].xpath("//div[@id='metadata']/following::div[1]")[0]).decode("utf-8")
        doc = "<html><head><title>%s</title></head><body>%s%s</body></html>" % (item["az"], body_meta, body_content)
        item["text"] = doc
        item["filetype"] = "html"
        return item
    else:
        output("could not retrieve " + item["link"], "err")

def be(item, headers, cookies): # spider.headers, spider.cookies
    # item["text"]: Berlin ist JSON-Post-Response
    url = "https://gesetze.berlin.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = "https://gesetze.berlin.de/bsbe/document/" + item["docId"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = '{"docId":"%s","format":"xsl","keyword":null,"sourceParams":{"source":"Unknown","category":"Alles"},"searches":[],"clientID":"bsbe","clientVersion":"bsbe - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (item["docId"], date, time)
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body)
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        data = req.json()
        doc = html.fromstring(f'<!doctype html><html><head><title>{item["az"]}</title></head><body>{data["head"]}{data["text"]}</body></html>')
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
        item["filetype"] = "html"
        return item

def bw(item):
    try:
        item["text"] = requests.get(item["link"], headers=src.config.HEADERS).text
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        if item["text"][1] == "h": # Herausfiltern von leeren Seiten / bei leeren Seite ist text[1] == "!" / schnellere Version
            item["filetype"] = "html"
            return item
        else:
            output("empty page " + item["link"], "err")

def by(item):
    try:
        txt = requests.get(item["link"], headers=src.config.HEADERS).text
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        if txt[154:160] != "Fehler": # Herausfiltern von leeren Seiten / bei leeren Seite ist text[10] == "h" / schnellere Version
            tree = etree.fromstring(txt.replace('\r\n', '\n'))
            tree.xpath("//script")[0].getparent().remove(tree.xpath("//script")[0]) # Druck-Dialog entfernen
            item["text"] = etree.tostring(tree, pretty_print=True, xml_declaration=True).decode("ascii")
            item["filetype"] = "xhtml"
            return item
        else:
            output("empty page " + item["link"], "err")

def he(item, headers, cookies): # spider.headers, spider.cookies
    # item["text"]: Hessen ist JSON-Post-Response
    url = "https://www.lareda.hessenrecht.hessen.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = "https://www.lareda.hessenrecht.hessen.de/bshe/document/" + item["docId"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bshe","clientVersion":"bshe - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (item["docId"], date, time)
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body)
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        data = req.json()
        doc = html.fromstring(f'<!doctype html><html><head><title>{item["az"]}</title></head><body>{data["head"]}{data["text"]}</body></html>')
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
        item["filetype"] = "html"
        return item

def hh(item, headers, cookies): # spider.headers, spider.cookies
    # item["text"]: Hamburg ist JSON-Post-Response
    url = 'https://www.landesrecht-hamburg.de/jportal/wsrest/recherche3/document'
    headers["Referer"] = "https://www.landesrecht-hamburg.de/bsha/document/" + item["docId"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bsha","clientVersion":"bsha - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (item["docId"], date, time)
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body)
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        data = req.json()
        doc = html.fromstring(f'<!doctype html><html><head><title>{item["az"]}</title></head><body>{data["head"]}{data["text"]}</body></html>')
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
        item["filetype"] = "html"
        return item

def mv(item, headers, cookies): # spider.headers, spider.cookies
    # item["text"]: Mecklenburg-Vorpommern ist JSON-Post-Response
    url = "https://www.landesrecht-mv.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = item["link"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bsmv","clientVersion":"bsmv - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (item["docId"], date, time)
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body)
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        data = req.json()
        doc = html.fromstring(f'<!doctype html><html><head><title>{item["az"]}</title></head><body>{data["head"]}{data["text"]}</body></html>')
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
        item["filetype"] = "html"
        return item

def ni(item):
    # Entscheidungstext bereinigen (kein Menü etc.)
    try:
        tree = html.fromstring(requests.get(item["link"]).text)
    except:
        output("could not parse " + item["link"], "err")
    else:
        if tree.xpath("//div[@id='bsentscheidung']"): # Herausfiltern von leeren Seiten
            body_content = html.tostring(tree.xpath("//div[@class='jurisText']")[0]).decode("utf-8")
            doc = "<html><head><title>%s</title></head><body>%s</body></html>" % (item["az"], body_content)
            item["text"] = doc
            item["filetype"] = "html"
            return item
        else:
            output("empty page " + item["link"], "err")

def nw(item):
    try:
        item["text"] = requests.get(item["link"], headers=src.config.HEADERS).text
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        if item["text"][14] == " ": # Herausfiltern von leeren Seiten / bei leeren Seite ist text[14] == " " / schnellere Version
            item["filetype"] = "html"
            return item
        else:
            output("empty page " + item["link"], "err")


def rp(item, headers, cookies): # spider.headers, spider.cookies
    # item["text"]: Rheinland-Pfalz ist JSON-Post-Response
    url = "https://www.landesrecht.rlp.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = item["link"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bshe","clientVersion":"bsrp - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (item["docId"], date, time)
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body)
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        data = req.json()
        doc = html.fromstring(f'<!doctype html><html><head><title>{item["az"]}</title></head><body>{data["head"]}{data["text"]}</body></html>')
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
        item["filetype"] = "html"
        return item

def sh(item):
    try: # Urteilsseite laden
        tree = html.fromstring(requests.get(item["link"], headers=src.config.HEADERS).text)
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        base = tree.xpath("//base/@href")[0]
        link = tree.xpath("//a[@name='dokument.drucken']/@href")[0]
        if link:
            # Druckseite öffnen, Druckdialog entfernen
            tree = html.fromstring(requests.get(base + link, headers=src.config.HEADERS).text)
            tree.xpath("//script[last()]")[0].getparent().remove(tree.xpath("//script[last()]")[0])
            item["text"] = html.tostring(tree, pretty_print=True).decode("utf-8")
            item["filetype"] = "html"
            return item
        else:
            output("could not retrieve " + base + link, "err")

def sl(item, headers, cookies): # spider.headers, spider.cookies
    # item["text"]: Saarland ist JSON-Post-Response
    url = "https://recht.saarland.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = item["link"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bssl","clientVersion":"bssl - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (item["docId"], date, time)
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body)
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        data = req.json()
        doc = html.fromstring(f'<!doctype html><html><head><title>{item["az"]}</title></head><body>{data["head"]}{data["text"]}</body></html>')
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
        item["filetype"] = "html"
        return item

def sn(item, headers): # spider.headers
    if "body" in item: # AG/LG/OLG-Subportal
        url = "https://www.justiz.sachsen.de/esamosplus/pages/treffer.aspx"
        headers["Referer"] = "Referer: https://www.justiz.sachsen.de/esamosplus/pages/suchen.aspx"
        try:
            item["req"] = requests.post(url=url, headers=headers, data=item["body"])
        except:
            output("could not retrieve " + item["az"], "err")
        else:
            return item
    elif "link" in item: # OVG-Subportal
        try:
            # Zwischengeschaltete Seite, von der aus erst der Filelink kopiert werden muss
            tree = html.fromstring(requests.get(item["link"]).text)
        except:
            output("could not retrieve " + item["link"], "err")
        else:
            item["link"] = "https://www.justiz.sachsen.de/ovgentschweb/" + tree.xpath("//a[@target='_blank']/@href")[0]
            return item

def st(item, headers, cookies):
    # item["text"]: Sachsen-Anhalt ist JSON-Post-Response
    url = "https://www.landesrecht.sachsen-anhalt.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = item["link"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bsst","clientVersion":"bsst - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (item["docId"], date, time)
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body)
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        data = req.json()
        doc = html.fromstring(f'<!doctype html><html><head><title>{item["az"]}</title></head><body>{data["head"]}{data["text"]}</body></html>')
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
        item["filetype"] = "html"
        return item

def th(item, headers, cookies): # spider.headers, spider.cookies
    # item["text"]: Thüringen ist JSON-Post-Response
    url = "https://landesrecht.thueringen.de/jportal/wsrest/recherche3/document"
    headers["Referer"] = item["link"]
    date = str(datetime.date.today())
    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
    body = '{"docId":"%s","format":"xsl","keyword":null,"docPart":"L","sourceParams":{"source":"TL","position":1,"sort":"date","category":"Rechtsprechung"},"searches":[],"clientID":"bsth","clientVersion":"bsth - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}' % (item["docId"], date, time)
    try:
        req = requests.post(url=url, cookies=cookies, headers=headers, data=body)
    except:
        output("could not retrieve " + item["link"], "err")
    else:
        data = req.json()
        doc = html.fromstring(f'<!doctype html><html><head><title>{item["az"]}</title></head><body>{data["head"]}{data["text"]}</body></html>')
        item["text"] = html.tostring(doc, pretty_print=True).decode("utf-8")
        item["filetype"] = "html"
        return item