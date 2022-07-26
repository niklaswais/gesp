# -*- coding: utf-8 -*-

__version__ = "0.1"
__author__ = "Niklas Wais"
__licence__ = "MIT"

UMLAUTE = {ord('ä'):'ae', ord('ö'):'oe', ord('ß'):'ss', ord('ü'):'ue'}
COURTS = ["ag", "arbg", "bgh", "bfh", "bverwg", "bverfg", "bpatg", "bag", "bsg", "fg", "lag", "lg", "lsg", "olg", "ovg", "sg", "vg"] # vgh = ovg
STATES = ["bund", "bw", "by", "be", "bb", "hb", "hh", "he", "mv", "ni", "nw", "rp", "sl", "sn", "st", "sh", "th"]
DOMAINS = ["oeff", "zivil", "straf"]
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0"}

json_headers_base = {
    "Accept": "*/*",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36",
    "content-type": "application/json",
    "sec-ch-ua": "\"Chromium\";v=\"103\", \".Not/A)Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\""
}

be_headers = json_headers_base | {
    "Origin": "https://gesetze.berlin.de",
    "Referer": "https://gesetze.berlin.de/bsbe/search",
    "juris-portalid": "bsbe"
}
be_cookies = {
    "up": "{\"search\":{\"hitsPerPage\":0,\"sort\":\"date\",\"categorySort\":null,\"disableComfortSearch\":false,\"extendedFieldsOpen\":true,\"previewDocument\":false},\"casefile\":{\"sort\":\"standard\"},\"menue\":{\"leftSearchColumnOpen\":true,\"rightSearchColumnOpen\":true,\"leftDocColumnOpen\":true,\"rightDocColumnOpen\":true,\"searchFrameLeftSplitter\":296,\"searchFrameRightSplitter\":300,\"docFrameLeftSplitter\":300,\"docFrameRightSplitter\":300},\"genericUI\":{\"leftColumnOpen\":true,\"rightColumnOpen\":true}}",
    "r3autologin": "\"bsbe\""
}
be_body = '{"clientID":"bsbe","clientVersion":"bsbe - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'

he_headers = json_headers_base | {
    "Origin": "https://www.lareda.hessenrecht.hessen.de",
    "Referer": "https://www.lareda.hessenrecht.hessen.de/bshe/search",
    "juris-portalid": "bshe"
}
he_cookies = {
    "r3autologin": "\"bshe\""
}
he_body = '{"clientID":"bshe","clientVersion":"bshe - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'

hh_headers = json_headers_base | {
    "Origin": "https://www.landesrecht-hamburg.de",
    "Referer": "https://www.landesrecht-hamburg.de/bsha/search",
    "juris-portalid": "bsha"
}
hh_cookies = {
    "r3autologin": "\"bsha\""
}
hh_body = '{"clientID":"bsha","clientVersion":"bsha - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'

mv_headers = json_headers_base | {
    "Origin": "https://www.landesrecht-mv.de",
    "Referer": "https://www.landesrecht-mv.de/bsmv/search",
    "juris-portalid": "bsmv"
}
mv_cookies = {
    "r3autologin": "\"bsmv\""
}
mv_body = '{"clientID":"bsmv","clientVersion":"bsmv - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'

rp_headers = json_headers_base | {
    "Origin": "https://www.landesrecht.rlp.de",
    "Referer": "https://www.landesrecht.rlp.de/bsrp/search",
    "juris-portalid": "bsrp"
}
rp_cookies = {
    "r3autologin": "\"bsrp\""
}
rp_body = '{"clientID":"bsrp","clientVersion":"bsrp - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'

sl_headers = json_headers_base | {
    "Origin": "https://recht.saarland.de",
    "Referer": "https://recht.saarland.de/bssl/search",
    "juris-portalid": "bssl"
}
sl_cookies = {
    "r3autologin": "\"bssl\""
}
sl_body = '{"clientID":"bssl","clientVersion":"bssl - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'

sn_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.justiz.sachsen.de",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36",
    "sec-ch-ua": "\"Chromium\";v=\"103\", \".Not/A)Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\""
}

st_headers = json_headers_base | {
    "Origin": "https://www.landesrecht.sachsen-anhalt.de",
    "Referer": "https://www.landesrecht.sachsen-anhalt.de/bsst/search",
    "juris-portalid": "bsst"
}
st_cookies = {
    "r3autologin": "\"bsst\""
}
st_body = '{"clientID":"bsst","clientVersion":"bsst - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'

th_headers = json_headers_base | {
    "Origin": "https://landesrecht.thueringen.de",
    "Referer": "https://landesrecht.thueringen.de/bsth/search",
    "juris-portalid": "bsth"
}
th_cookies = {
    "r3autologin": "\"bsth\""
}
th_body = '{"clientID":"bsth","clientVersion":"bsth - V06_07_00 - 23.06.2022 11:20","r3ID":"%sT%sZ"}'