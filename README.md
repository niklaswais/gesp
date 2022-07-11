## gesp: Convenient scraping of German court decisions

The federal and state governments in Germany make court decisions available for download on individual online platforms. In addition to the lack of uniformity, these platforms only allow individual retrieval out of the box. With gesp, decisions can be downloaded in large quantities in a filter-based and reproducible manner.

### Usage

A call without command-line argument will result in the retrival of **all** available court decisions regardless of state or court type. If only a **subset** is to be downloaded, the arguments **"-s"** (followed by abbreviations of states) and **"-t"** (followed by abbreviations of court types) can be used.
```shell
gesp.py -s bund,by,hh,nw -c bgh,ag,lg,olg


