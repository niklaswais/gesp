# -*- coding: utf-8 -*-
import datetime
import json
import lzma
import os
import requests
import scrapy # Sachsen (Subportal)
from . import config
from twisted.internet import reactor # Sachsen (Subportal)
from ..spiders.sn import SpdrSN # Sachsen (Subportal)
from .output import output
from .get_text import bb, be, bw, by, he, hh, mv, ni, nw, rp, sh, sl, sn, st, th
from .create_file import save_as_html, save_as_pdf

class Fingerprint:
    def __init__(self, path, fp_path, store_docId):
        for i in self.load_file(fp_path): 
            if "version" in i and "date" in i and "args" in i: # Erste Zeile enthält noch keine Entscheidung
                output("reconstructing from fingerprint %s (%s, %s, %s)" % (fp_path, i["version"], i["date"], i["args"]))
            else:
                # Ordner erstellen
                results_subfolder = os.path.join(path, i["s"])
                if (not os.path.exists(results_subfolder)):
                    try:
                        os.makedirs(results_subfolder)
                    except:
                        output(f"could not create folder {results_subfolder}", "err")
                # Umwandeln in item-Format
                item = { "court": i["c"], "date": i["d"], "az": i["az"] }
                if "link" in i:
                    item["link"] = i["link"]
                if "docId" in i: # JSON-Post (BE, HH, ....)
                    item["docId"] = i["docId"]
                # Sonderfall Sachsen (AG/LG/OLG-Subportal)
                if i["s"] == "sn" and i["link"] == "https://www.justiz.sachsen.de/esamosplus/pages/treffer.aspx": 
                    output("sn: reconstruction for AG/LG/OLG decisions is not supported", "warn")
                # Wenn keine To-Text-Umwandlung notwendig ist: Entscheidung herunterladen
                elif i["s"] == "bund":
                    save_as_html(item, i["s"], path, store_docId)
                elif i["s"] in ["hb", "sn"]:
                    save_as_pdf(item, i["s"], path)
                # Ansonsten: Bei JSON-Portalen zunächst x-csrf-Token in die Header einfügen (Teil der Spider)
                # & bei allen: an get_text-Funktionen weiterleiten
                else:
                    date = str(datetime.date.today())
                    time = str(datetime.datetime.now(datetime.timezone.utc).time())[0:-3]
                    if i["s"] == "bb":
                        item = bb(item)
                    elif i["s"]  == "be":
                        url = "https://gesetze.berlin.de/jportal/wsrest/recherche3/init"
                        headers = config.be_headers
                        body = config.be_body % (date, time)
                        try:
                            response = requests.post(url=url, headers=headers, cookies=config.be_cookies, data=body)
                        except:
                            output("be: could not get x-csrf-token", "err")
                        else:
                            headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
                        item = be(item, headers, config.be_cookies)
                    elif i["s"] == "bw":
                        url = "https://www.landesrecht-bw.de/jportal/wsrest/recherche3/init"
                        headers = config.bw_headers
                        body = config.bw_body % (date, time)
                        try:
                            response = requests.post(url=url, headers=headers, cookies=config.bw_cookies, data=body)
                        except:
                            output("bw: could not get x-csrf-token", "err")
                        else:
                            headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
                        item = bw(item, headers, config.bw_cookies)
                    elif i["s"] == "by":
                        item = by(item)
                    elif i["s"]  == "he":
                        url = "https://www.lareda.hessenrecht.hessen.de/jportal/wsrest/recherche3/init"
                        headers = config.he_headers
                        body = config.he_body % (date, time)
                        try:
                            response = requests.post(url=url, headers=headers, cookies=config.he_cookies, data=body)
                        except:
                            output("he: could not get x-csrf-token", "err")
                        else:
                            headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
                        item = he(item, headers, config.he_cookies)
                    elif i["s"]  == "hh":
                        url = "https://www.landesrecht-hamburg.de/jportal/wsrest/recherche3/init"
                        headers = config.hh_headers
                        body = config.hh_body % (date, time)
                        try:
                            response = requests.post(url=url, headers=headers, cookies=config.hh_cookies, data=body)
                        except:
                            output("hh: could not get x-csrf-token", "err")
                        else:
                            headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
                        item = hh(item, headers, config.hh_cookies)
                    elif i["s"]  == "mv":
                        url = "https://www.landesrecht-mv.de/jportal/wsrest/recherche3/init"
                        headers = config.mv_headers
                        body = config.mv_body % (date, time)
                        try:
                            response = requests.post(url=url, headers=headers, cookies=config.mv_cookies, data=body)
                        except:
                            output("mv: could not get x-csrf-token", "err")
                        else:
                            headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
                        item = mv(item, headers, config.mv_cookies)
                    elif i["s"] == "ni":
                        item = ni(item)
                    elif i["s"] == "nw":
                        item = nw(item)
                    elif i["s"]  == "rp":
                        url = "https://www.landesrecht.rlp.de/jportal/wsrest/recherche3/init"
                        headers = config.rp_headers
                        body = config.rp_body % (date, time)
                        try:
                            response = requests.post(url=url, headers=headers, cookies=config.rp_cookies, data=body)
                        except:
                            output("rp: could not get x-csrf-token", "err")
                        else:
                            headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
                        item = rp(item, headers, config.rp_cookies)
                    elif i["s"]  == "sh":
                        item = sh(item)
                    elif i["s"]  == "sl":
                        url = "https://recht.saarland.de/jportal/wsrest/recherche3/init"
                        headers = config.sl_headers
                        body = config.sl_body % (date, time)
                        try:
                            response = requests.post(url=url, headers=headers, cookies=config.sl_cookies, data=body)
                        except:
                            output("sl: could not get x-csrf-token", "err")
                        else:
                            headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
                        item = sl(item, headers, config.sl_cookies)
                    elif i["s"]  == "st":
                        url = "https://www.landesrecht.sachsen-anhalt.de/jportal/wsrest/recherche3/init"
                        headers = config.st_headers
                        body = config.st_body % (date, time)
                        try:
                            response = requests.post(url=url, headers=headers, cookies=config.st_cookies, data=body)
                        except:
                            output("st: could not get x-csrf-token", "err")
                        else:
                            headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
                        item = st(item, headers, config.st_cookies)
                    elif i["s"]  == "th":
                        url = "https://landesrecht.thueringen.de/jportal/wsrest/recherche3/init"
                        headers = config.th_headers
                        body = config.th_body % (date, time)
                        try:
                            response = requests.post(url=url, headers=headers, cookies=config.th_cookies, data=body)
                        except:
                            output("th: could not get x-csrf-token", "err")
                        else:
                            headers["x-csrf-token"] = json.loads(response.body)["csrfToken"]
                        item = th(item, headers, config.th_cookies)
                    save_as_html(item, i["s"], path, store_docId)
   
    def load_file(self, fp):
        input = ""
        lzmad = lzma.LZMADecompressor()
        with open(fp, "rb") as f:
            while chunk := f.read(1024):
                cunk_decomp = lzmad.decompress(chunk) # compressed -> decompressed
                chunk_as_str = cunk_decomp.decode() # bytes -> string (json)
                input = input + chunk_as_str
                json_lines = input.split("|")
                if json_lines[1]:
                    for line in json_lines[:-1]:
                        yield json.loads(line) # string (json) -> item (dict)
                    if not json_lines[-1] == "":
                        input = json_lines[-1] # Rest an Input anhängen
                elif json_lines[0] != "":
                    yield json.loads(json_lines[0])