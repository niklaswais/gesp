## gesp: Convenient scraping of German court decisions

The federal and state governments in Germany make court decisions available for download on individual online platforms. In addition to the lack of uniformity, these platforms only allow individual retrieval out of the box. With gesp, decisions can be downloaded in large quantities in a filter-based and reproducible manner.

### A. Usage
A call without command-line argument will result in the retrival of **all** available court decisions regardless of state or court type. If only a **subset** is to be downloaded, the arguments **"-s"** (followed by abbreviations of states) and **"-t"** (followed by abbreviations of court types) can be used. Multiple states or court types are separated by a comma.
```Shell
gesp.py -s bund,by,hh,nw -c bgh,ag,lg,olg
```

A specific path under which the decisions are to be stored can be specified with the argument "-p". If the folder has not been created yet, gesp will take care of that.
```Shell
gesp.py -p path/to/folder
```

### B. Results
If no specific path is passed with "-p", gesp will create a folder for the results in the program folder. The name of the folder is based on the date and time of execution.

### C. Appendix
#### 1. Abbreviations for "-s" (federal/states)
| Name | Abbreviation |
| --- | --- |
| Federal | *bund* |
| Baden-Württemberg | *bw* |
| Bavaria | *by* |
| Berlin | *be* |
| Brandenburg | *bb* |
| Bremen | *hb* |
| Hamburg | *hh* |
| Hesse | *he* |
| Mecklenburg-Vorpommern | *mv* |
| Lower Saxony | *ni* |
| North Rhine-Westphalia | *nw* |
| Rhineland-Palatinate | *rp* |
| Saarland | *sl* |
| Saxony | *sn* |
| Saxony-Anhalt | *st* |
| Schleswig-Holstein | *sh* |
| Thuringia | *th* |

#### 2. Abbreviations for "-c" (court types)
| Name | Abbreviation |
| --- | --- |
| Amtsgerichte | *ag* |
| Arbeitsgerichte | *arbg* |
| Bundesgerichtshof | *bgh* |
| Bundesfinanzhof | *bfh* |
| Bundesverwaltungsgericht | *bverwg* |
| Bundesverfassungsgericht | *bverfg* |
| Bundespatentgericht | *bpatg* |
| Bundesarbeitsgericht | *bag* |
| Bundessozialgericht | *bsg* |
| Finanzgerichte | *fg* |
| Landesarbeitsgerichte | *lag* |
| Landgerichte | *lg* |
| Landessozialgerichte | *lsg* |
| Oberlandesgerichte (incl. KG, BayObLG) | *olg* |
| Oberverwaltungsgerichte (incl. vgh) | *ovg* |
| Sozialgerichte | *sg* |
 