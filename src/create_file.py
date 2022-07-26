# -*- coding: utf-8 -*-
import requests
from io import BytesIO
from src.output import output
from zipfile import ZipFile

def info(item):
    if "link" in item:
        output("downloading " + item["link"] + "...")
    elif "req" in item:
        output("downloading " + item["req"].url + "...")
    return item

def save_as_html(item, spider_name, spider_path): # spider.name, spider.path
    info(item)
    if spider_name == "spider_bund": # Sonderfall Bund: *.zip mit *.xml
        filename = item["court"] + "_" + item["date"] + "_" + item["az"] + ".xml"
        try:
            with ZipFile(BytesIO((requests.get(item["link"]).content))) as zip_ref: # Im RAM entpacken
                for zipinfo in zip_ref.infolist(): # Teilweise auch Bilder in .zip enthalten
                    if (zipinfo.filename.endswith(".xml")):
                        zipinfo.filename = filename
                        zip_ref.extract(zipinfo, spider_path + "bund/")
        except:
            output(f"could not create file {filename}", "err")
        else:
            return item
    else:
        if "text" in item:
            filename = spider_path + spider_name + "/" + item["court"] + "_" + item["date"] + "_" + item["az"] + "." + item["filetype"]
            try:
                with open(filename, "w") as f:
                    f.write(item["text"])
            except:
                output(f"could not create file {filename}", "err")
            else:
                return item
        else:
            output("could not retrieve " + item["link"], "err")

def save_as_pdf(item, spider_name, spider_path): # spider.name, spider.path
    if "link" in item: # Bremen / Sachsen
        if "headers" in item and "body" in item : # Sachsen: AG/LG/OLG-Supportal
            try:
                req = requests.post(url=item["link"], headers=item["headers"], data=item["body"])
            except:
                output("could not retrieve " + item["link"], "err")
        else:
            try:
                req = requests.get(url=item["link"])
            except:
                output("could not retrieve " + item["link"], "err")
    info(item) # Erst hier, da req.url benötigt wird
    filename = spider_path + spider_name + "/" + item["court"] + "_" + item["date"] + "_" + item["az"] + ".pdf"
    try:
        with open(filename, "wb") as f:
            f.write(req.content)
    except:
        output(f"could not create file {filename}", "err")
    else:
        return item