import os
import time
from io import BytesIO
from zipfile import ZipFile

import requests
from requests.exceptions import RequestException

from .output import output


def info(item):
    if item is None:
        return None
    if "link" in item:
        output("downloading " + item["link"] + "...")
    return item


def save_as_html(item, spider_name, spider_path, store_docId):  # spider.name, spider.path
    if item is None:
        output("dropped empty item", "warn")
        return None
    info(item)
    is_zip_xml = False
    if spider_name == "bund":
        if not item["link"].startswith("https://www.bundesverfassungsgericht.de/"):
            is_zip_xml = True
    if spider_name == "by":
        is_zip_xml = True
    if is_zip_xml:  # Sonderfall Bund und Bayern: *.zip mit *.xml
        filename = item["court"] + "_" + item["date"] + "_" + item["az"]
        if store_docId and item.get("docId"):
            filename += "_" + item["docId"]
        filename += ".xml"

        retries = 3  # Anzahl der Versuche
        for attempt in range(retries):
            try:
                response = requests.get(item["link"], timeout=10)
                response.raise_for_status()
                with ZipFile(BytesIO(response.content)) as zip_ref:  # Im RAM entpacken
                    for zipinfo in zip_ref.infolist():  # Teilweise auch Bilder in .zip enthalten
                        if zipinfo.filename.endswith(".xml") and ("manifest" not in zipinfo.filename):
                            original_path = os.path.join(spider_path, spider_name, zipinfo.filename)
                            target_path = os.path.join(spider_path, spider_name, filename)
                            zip_ref.extract(zipinfo, os.path.join(spider_path, spider_name))
                            os.rename(original_path, target_path)
                            # bayportalrsp
                            item["xmlfilename"] = target_path
                            return item
                output(f"could not create file {filename}: no suitable .xml found in zip", "err")
                break
            except RequestException as e:
                output(f"Attempt {attempt + 1}/{retries} failed: {e}", "warn")
                if attempt < retries - 1:
                    time.sleep(2)  # Warte 2 Sekunden vor dem nächsten Versuch
                else:
                    output(f"could not create file {filename}: {e}", "err")
    else:
        if "text" in item and "court" in item and "date" in item and "az" in item and "filetype" in item:
            filename = item["court"] + "_" + item["date"] + "_" + item["az"]
            if store_docId and item.get("docId"):
                filename += "_" + item["docId"]
            filename += "." + item["filetype"]
            filepath = os.path.join(spider_path, spider_name, filename)
            enc = "utf-8" if spider_name != "by" else "ascii"
            try:
                with open(filepath, "w", encoding=enc) as f:
                    f.write(item["text"])
            except OSError:
                output(f"could not create file {filepath}", "err")
            else:
                return item
        elif "link" in item:
            filename = item["court"] + "_" + item["date"] + "_" + item["az"]
            if store_docId and item.get("docId"):
                filename += "_" + item["docId"]
            filename += ".html"
            filepath = os.path.join(spider_path, spider_name, filename)
            enc = "utf-8"
            try:
                with open(filepath, "w", encoding=enc) as f:
                    f.write(requests.get(item["link"]).content.decode(enc))
            except (OSError, RequestException):
                output(f"could not create file {filepath}", "err")
        else:
            output(f"could not retrieve item {item.get('court', '?')}/{item.get('az', '?')}", "err")


def save_as_pdf(item, spider_name, spider_path):  # spider.name, spider.path
    if item is None:
        output("dropped empty item", "warn")
        return None
    info(item)
    content = ""
    if "link" in item and "body" not in item:  # Bremen / Sachsen (OVG)
        try:
            content = requests.get(url=item["link"]).content
        except RequestException:
            output("could not retrieve " + item["link"], "err")
    elif "body" in item:  # Sachsen (AG/LG/OLG)
        content = item["body"]
    if content and "court" in item and "date" in item and "az" in item:
        basename = item["court"] + "_" + item["date"] + "_" + item["az"]
        if item["link"].endswith(".docx"):
            filename = basename + ".docx"
        else:
            filename = basename + ".pdf"
        filepath = os.path.join(spider_path, spider_name, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(content)
        except OSError:
            output(f"could not create file {filepath}", "err")
        else:
            return item
    else:
        output(
            f"missing information for item {item.get('court', '?')}/{item.get('az', '?')} ({item.get('link', '?')})",
            "err",
        )
