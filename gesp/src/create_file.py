import os
import time
from io import BytesIO
from zipfile import BadZipFile, ZipFile

import requests
from requests.exceptions import RequestException

from .filenames import safe_filename_part
from .output import output


def _item_filename(item, extension, store_docId=False):
    parts = [safe_filename_part(item["court"]), safe_filename_part(item["date"]), safe_filename_part(item["az"])]
    if store_docId and item.get("docId"):
        parts.append(safe_filename_part(item["docId"]))
    return "_".join(parts) + "." + safe_filename_part(str(extension).lstrip("."))


def info(item):
    if item is None:
        return None
    if "link" in item:
        output("downloading " + item["link"] + "...")
    return item


def _trim_trailing_zip_junk(content: bytes) -> bytes:
    """Drop bytes after the first valid EOCD record.

    Some portal-generated zips (observed on gesetze-bayern.de) append junk
    after a perfectly good archive, and the junk contains a second EOCD
    signature with wrong fields. Python's zipfile scans backwards for the
    EOCD and lands on the bogus one, then fails with BadZipFile because the
    declared central-directory offset doesn't point at PK\\x01\\x02.

    Iterate EOCD candidates from earliest; keep the first whose declared
    CD offset lands on a real CD entry. If none validates, return the input
    untouched so the existing BadZipFile path still handles it.
    """
    pos = 0
    while True:
        idx = content.find(b"PK\x05\x06", pos)
        if idx < 0 or idx + 22 > len(content):
            return content
        cd_off = int.from_bytes(content[idx + 16 : idx + 20], "little")
        if content[cd_off : cd_off + 4] == b"PK\x01\x02":
            comment_len = int.from_bytes(content[idx + 20 : idx + 22], "little")
            return content[: idx + 22 + comment_len]
        pos = idx + 1


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
        filename = _item_filename(item, "xml", store_docId)

        retries = 3  # Anzahl der Versuche
        if item.get("wait"):
            time.sleep(item["wait"])
        for attempt in range(retries):
            try:
                response = requests.get(item["link"], timeout=10)
                response.raise_for_status()
                with ZipFile(BytesIO(_trim_trailing_zip_junk(response.content))) as zip_ref:  # Im RAM entpacken
                    for zipinfo in zip_ref.infolist():  # Teilweise auch Bilder in .zip enthalten
                        if zipinfo.filename.endswith(".xml") and ("manifest" not in zipinfo.filename):
                            original_path = os.path.join(spider_path, spider_name, zipinfo.filename)
                            target_path = os.path.join(spider_path, spider_name, filename)
                            zip_ref.extract(zipinfo, os.path.join(spider_path, spider_name))
                            os.replace(original_path, target_path)
                            # bayportalrsp
                            item["xmlfilename"] = target_path
                            return item
                output(f"could not create file {filename}: no suitable .xml found in zip", "err")
                break
            except BadZipFile as e:
                # Server returned the same bytes; retrying can't change that.
                output(f"could not create file {filename}: downloaded content is not a readable zip ({e})", "err")
                break
            except RequestException as e:
                output(f"Attempt {attempt + 1}/{retries} failed: {e}", "warn")
                if attempt < retries - 1:
                    time.sleep(2)  # Warte 2 Sekunden vor dem nächsten Versuch
                else:
                    output(f"could not create file {filename}: {e}", "err")
            except OSError as e:
                output(f"could not create file {filename}: {e}", "err")
                break
    else:
        if "text" in item and "court" in item and "date" in item and "az" in item and "filetype" in item:
            filename = _item_filename(item, item["filetype"], store_docId)
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
            filename = _item_filename(item, "html", store_docId)
            filepath = os.path.join(spider_path, spider_name, filename)
            enc = "utf-8"
            if item.get("wait"):
                time.sleep(item["wait"])
            # Fetch + decode before opening: if either fails (RequestException, or
            # UnicodeDecodeError on a non-utf-8 body), opening the target in "w" mode
            # would otherwise leave a zero-byte file behind.
            try:
                content = requests.get(item["link"], timeout=30).content.decode(enc)
            except (RequestException, ValueError) as e:
                output(f"could not retrieve {item['link']}: {e!r}", "err")
                return None
            try:
                with open(filepath, "w", encoding=enc) as f:
                    f.write(content)
            except OSError:
                output(f"could not create file {filepath}", "err")
            else:
                return item
        else:
            output(f"could not retrieve item {item.get('court', '?')}/{item.get('az', '?')}", "err")


def save_as_pdf(item, spider_name, spider_path):  # spider.name, spider.path
    if item is None:
        output("dropped empty item", "warn")
        return None
    info(item)
    content = ""
    if "link" in item and "body" not in item:  # Bremen / Sachsen (OVG)
        if item.get("wait"):
            time.sleep(item["wait"])
        try:
            content = requests.get(url=item["link"], timeout=30).content
        except RequestException:
            output("could not retrieve " + item["link"], "err")
    elif "body" in item:  # Sachsen (AG/LG/OLG)
        content = item["body"]
    if content and "court" in item and "date" in item and "az" in item:
        if item.get("link", "").endswith(".docx"):
            filename = _item_filename(item, "docx")
        else:
            filename = _item_filename(item, "pdf")
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
