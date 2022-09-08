# -*- coding: utf-8 -*-
from fileinput import filename
import os
import requests
from io import BytesIO
from src.output import output
from zipfile import ZipFile

def info(item):
    if "link" in item:
        output("downloading " + item["link"] + "...")
    return item

def save_as_html(item, spider_name, spider_path): # spider.name, spider.path
    info(item)
    if spider_name == "bund": # Sonderfall Bund: *.zip mit *.xml
        filename = item["court"] + "_" + item["date"] + "_" + item["az"] + ".xml"
        try:
            with ZipFile(BytesIO((requests.get(item["link"]).content))) as zip_ref: # Im RAM entpacken
                for zipinfo in zip_ref.infolist(): # Teilweise auch Bilder in .zip enthalten
                    if (zipinfo.filename.endswith(".xml")):
                        zipinfo.filename = filename
                        zip_ref.extract(zipinfo, os.path.join(spider_path, "bund"))
        except:
            output(f"could not create file {filename}", "err")
        else:
            return item
    else:
        if "text" in item and "court" in item and "date" in item and "az" in item and "filetype" in item:
            filename = item["court"] + "_" + item["date"] + "_" + item["az"] + "." + item["filetype"]
            filepath = os.path.join(spider_path, spider_name, filename)
            enc = "utf-8" if spider_name != "by" else "ascii"
            try:
                with open(filepath, "w", encoding=enc) as f:
                    f.write(item["text"])
            except:
                output(f"could not create file {filepath}", "err")
            else:
                return item
        else:
            output("could not retrieve " + item["link"], "err")

def save_as_pdf(item, spider_name, spider_path): # spider.name, spider.path
    info(item)
    content = ""
    if "link" in item and not "body" in item: # Bremen / Sachsen (OVG)
        try:
            content = requests.get(url=item["link"]).content
        except:
            output("could not retrieve " + item["link"], "err")
    elif "body" in item: # Sachsen (AG/LG/OLG)
        content = item["body"]
    if content and "court" in item and "date" in item and "az" in item:
        filename = item["court"] + "_" + item["date"] + "_" + item["az"] + ".pdf"
        filepath = os.path.join(spider_path, spider_name, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(content)
        except:
            output(f"could not create file {filepath}", "err")
        else:
            return item
    else:
        output("missing information " + item["link"], "err")
