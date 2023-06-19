**Copyright notice**: Automated retrieval of decisions from federal and state databases is permitted for non-commercial purposes only. Since gesp accesses these databases, the use of gesp is also permitted for **non-commercial purposes only**.

## gesp: convenient scraping of German court decisions

The federal and state governments in Germany make court decisions available for download on individual online platforms. In addition to the lack of uniformity, these platforms only allow individual retrieval out of the box. With gesp, decisions can be downloaded in large quantities in a filter-based and reproducible manner.

### A. Installation
Download & build the package:
```Shell
git clone https://github.com/niklaswais/gesp && cd gesp && python -m build
```
Install the local .tar.gz:
```Shell
python -m pip install dist/gesp-0.1.tar.gz
```

### B. Basic Usage
A call without command-line arguments will result in the retrival of all **machine-readable** (= non-PDF) court decisions. If only a **subset** is to be downloaded, the arguments **"-s"** (followed by abbreviations of states) and **"-t"** (followed by abbreviations of court types) can be used. Multiple states or court types are separated by commas.
```Shell
python -m gesp -s bund,by,hh,nw -c bgh,ag,lg,olg
```
Since Saxony and Bremen provide court decisions only as PDF files, they are excluded when gesp is run without flags. An explicit call nevertheless makes the corresponding files available (-s sn,hb).

A specific path under which the decisions are to be stored can be specified with the argument "-p". If the folder has not been created yet, gesp will take care of that. If the folder has already been created and contains the results of a previous execution, this will cause an **update** of the dataset.
```Shell
python -m gesp -p path/to/folder
```

An existing fingerprint (see C.) can be used to **reconstruct** a dataset. To do so, the path to the fingerprint file must be passed as an argument using "-fp". Naturally, "-c" and "-s" arguments are not allowed in this case.
```Shell
python -m gesp -fp /path/to/fingerprint
```

You can use the command line option "-w" to add a delay between two consecutive downloads of decisions from the same source. This reduces the server load for the provider of the decisions.

### C. Results
If no specific path is passed with "-p", gesp will create a folder for the results in the current working directory ("results/"). The name of the subfolder is based on the date and time of execution to avoid conflicts in subsequent runs. Decisions that are available as **html/xhtml** files are preferentially downloaded as such. However, some federal states unfortunately provide decisions only as pdf files. The editable documents are minimally cleaned up (e.g., print dialogs and navigation menus are removed), but **not pre-processed**.

### D. Reproducibility
If you want to reconstruct the dataset of a previos run, e.g. because you are working on multiple machines or in a team, simply share the fingerprint file that gesp automatically creates in the folder with the results. Using the fingerprint file by means of the "-fp" argument will result in the assembly of an identical collection.

The fingerprinting feature of gesp can also be used to meet good scientific practice standards without the need to provide large collections of data. Since it is part of good scientific practice to disclose the data basis of the results obtained, publications on the empirical study of court decisions must be accompanied by relatively large data sets. Instead of making the entire collection of decisions available for retrieval online, simply share the fingerprint file that others may use to retrieve your data.

### E. Appendix
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
| Landesverfassungsgerichte | *verfgh* |
| Oberlandesgerichte (incl. KG, BayObLG) | *olg* |
| Oberverwaltungsgerichte (incl. vgh) | *ovg* |
| Sozialgerichte | *sg* |
 
