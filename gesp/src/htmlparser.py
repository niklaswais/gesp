import pkg_resources
from html.parser import HTMLParser
import os
import codecs
from datetime import datetime
import re
import csv
import difflib
import traceback
from .output import output

blanko = 'Gericht: {gericht}\nEntscheidungsdatum: {entscheidungsdatum}\nRechtskraft: {rechtskraft}\nAktenzeichen: {' \
         'aktenzeichen}\nECLI: {ecli}\nDokumenttyp: {dokumenttyp}\nQuelle:{quelle}\nNormen: {normen}\n' \
         'Dokumentnummer: {dokumentnummer}\nGerichtstyp: {gerichtstyp}\nGerichtsort: {gerichtsort}\n' \
         'Spruchkoerper: {spruchkoerper}\nVorinstanz: {vorinstanz}\nRegion Abk.: {region_abk}\n' \
         'Region Lang: {region_lang}\nMitwirkung: {mitwirkung}\nTitelzeile: {titelzeile}\n' \
         '========== Body ==========\n{text}'
date_pattern = r"\d\d\.\d\d\.\d\d\d\d|\d\.\d\d\.\d\d\d\d|\d\.\d\.\d\d\d\d|\d\d\.\d\.\d\d\d\d|\d\d\. " \
               r"(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember) \d\d\d\d"





class DecisionHTMLParser(HTMLParser):
    mode = 'Baden-Württemberg'
    start_tag = ''

    text = ''
    gericht = ''
    entscheidungsdatum = ''
    rechtskraft = ''
    aktenzeichen = ''
    ecli = ''
    dokumenttyp = ''
    quelle = ''
    normen = ''
    dokumentnummer = ''
    gerichtstyp = ''
    gerichtsort = ''
    spruchkoerper = ''
    vorinstanz = ''
    region_abk = ''
    region_lang = ''
    mitwirkung = ''
    titelzeile = ''
   
    ## Bayern
    vorInstanz = False
    inRechtsmittelInstanz = False

    ## NRW
    feldbezeichnungsModus = False
    vorherigerFeldbezeichnungsModus = False
    feldname = ''
    NRWneu = False

    ## Niedersachsen und Hamburg
    bssmall = False
    inTitle = False
    bssmallNumber = 0
    inBody = False

    ## Rheinland-Pfalz
    aktuellerStrong = ''
    inTabelle = False
    tabellentiefe = 0
    bodyEnde = False
    randnummerLink = False

    # Brandenburg
    aktuellerTH = ''
    bbfooter = False

    # judicialis
    #endeDerEntscheidung = False

    eclitests = 0
    reextracted = 0
    waitforinput = False


    vorAZ = '1 BvR 1/1'

    # Lade die Gerichtscodes
    ecli_codes = {}
    gerichts_code_land = {}
    eclistream = pkg_resources.resource_stream(__name__, '../data/ECLI-Gerichtscodes.csv')
    utf8_reader = codecs.getreader("utf-8")
    csvfile = csv.reader(utf8_reader(eclistream))
    for land,gerichtsname,code in csvfile:
        if gerichtsname in ecli_codes: continue ### LG FFM has two abbreviations ...
        ecli_codes[gerichtsname] = code.strip()
        ecli_codes[code.strip()] = code.strip()
        gerichts_code_land[code.strip()] = land
        #print("%s -> %s" % (code,land))


    printTagData = False 
    #printTagData = True 
    

    def handle_starttag(self, tag, attrs):
        if (self.printTagData): print("Start tag:", tag)
        self.start_tag = tag
        self.vorherigerFeldbezeichnungsModus = self.feldbezeichnungsModus
        self.feldbezeichnungsModus = ('class','feldbezeichnung') in attrs
        self.bssmall = ('class','bssmall') in attrs
        self.inTitle = ('class','title') in attrs or ('class','intro') in attrs

        if tag == 'a':
            self.randnummerLink = False
            for (x,y) in attrs:
                if x == 'name':
                    self.randnummerLink = y.startswith("rd_")

        if tag == 'span':
            self.randnummerLink = False
            for (x,y) in attrs:
                if x == 'class':
                    self.randnummerLink = y == "absatzRechts"

        if tag == 'div' and ('id','bb-footer-bar') in attrs: self.bbfooter = True

        if tag == 'rechtsmittelinstanz': self.inRechtsmittelInstanz = True
        if tag == 'vorinstanz': self.vorInstanz = True
        if tag == 'hr': self.inBody = False
        if (tag == 'table') and ((('class','TableRahmenkpl') in attrs) or (('class','kopfTabelle') in attrs) or (('style','width:100%;border-spacing:5px;') in attrs)): self.inTabelle = True
        if (self.printTagData): print(f"\tTag {tag} attrs {attrs} in Tabelle {self.inTabelle}")
        
        if self.inTabelle and tag == 'table': self.tabellentiefe += 1
        if tag == 'a' and ('name','DocInhaltEnde') in attrs: self.bodyEnde = True
        
        if (self.printTagData): print(f"\tTabelle {self.inTabelle}")

    def handle_endtag(self, tag):
        if self.printTagData: print("End tag :", tag)
        if tag == 'rechtsmittelinstanz': self.inRechtsmittelInstanz = False
        if tag == 'vorinstanz': self.vorInstanz = False
        if self.inTabelle and tag == 'table': self.tabellentiefe -= 1
        if self.tabellentiefe == 0: self.inTabelle = False
        
        if (self.printTagData): print(f"\tTabelle {self.inTabelle}")

    def trenne_gericht_und_kammer(self,bezeichnung):
        nochGerichtsname = True
        derRueckgestellt = True
        for block in bezeichnung.split(" "):
            #print(block)
            if len(block) == 0: continue
            if block[0].isnumeric(): nochGerichtsname = False
            if (self.gericht != '' and ## Es gibt ein Gericht das "Vergabekammer" heißt
                    ('senat' in block.lower() or 'kammer' in block.lower() or
                    'kleine' in block.lower() or 'große' in block.lower() or
                    'schwurgericht' in block.lower() or 'ausschuss' == block.lower()
                    or 'präsident' == block.lower() or 'generalstaatsanwalt' == block.lower()
                    or 'einzelrichter' == block.lower()
                    or 'zivilabteilung' == block.lower()
                    or 'familiengericht' == block.lower()
                    or 'präsidium' == block.lower()
                    or 'rechtspfleger' == block.lower()
                    or 'schöffengericht' == block.lower()
                    or 'richter.' == block.lower()
                    or 'wertpapiererwerbs-' == block.lower()
                    or 'abt.' == block.lower()
                    or 'abteilung' == block.lower()
                    or 'disziplinarhof' == block.lower()
                    or 'flurbereinigungsgericht' == block.lower()
                    or 'v.' == block.lower()
                    or 'kein' == block.lower())): nochGerichtsname = False
            if 'der' == block.lower():
                derRueckgestellt = True
                continue
            if derRueckgestellt == True:
                if 'havel' == block.lower():
                    self.gericht += ' der'
                else:
                    self.spruchkoerper = 'Der'
                derRueckgestellt = False

            if nochGerichtsname:
                if len(self.gericht) > 0: self.gericht += ' '
                self.gericht += block
            else:
                if len(self.spruchkoerper) > 0: self.spruchkoerper += ' '
                self.spruchkoerper += block


    def handle_data(self, data):
        tag = self.start_tag
        if (self.printTagData): print("Some data [%s] : %s" % (tag,data))
        
        if self.mode in ('bund','by'):
            #print(tag)
            #print(data)
            #print("====================================================================")
            if self.inRechtsmittelInstanz or self.vorInstanz: return ## einfach ignorieren
            if not tag or re.fullmatch(r"\s*", data):
                return
            if tag == 'p' or tag == 'td' or tag == 'rd':
                self.text += '\n' + data
            elif tag == 'verweis.norm' or tag == 'v.abk' or tag == 'span' or tag == 'sub' or tag == 'sup' or tag == 'strong' or tag == 'em' or tag == 'span' or tag == 'ul':
                self.text += ' ' + data
            elif (tag in ('a', 'span')):
                if self.randnummerLink == False:
                    self.text += ' ' + data.strip()
            elif tag == 'doknr':
                self.dokumentnummer = data
            elif tag == 'ecli':
                self.ecli = data
            elif tag == 'gertyp':
                self.gerichtstyp = data
            elif tag == 'gerort':
                self.gerichtsort = data
            elif tag == 'spruchkoerper':
                self.spruchkoerper = data
            elif tag == 'entsch-datum':
                #print("Data: %s %s" % (data,self.mode))
                if self.mode == 'bund':
                    self.entscheidungsdatum = datetime.strptime(data, '%Y%m%d')
                elif self.mode == 'by':
                    self.entscheidungsdatum = datetime.strptime(data, '%Y-%m-%d')
                else:
                    self.entscheidungsdatum = datetime.strptime(data, '%d.%m.%Y')
            elif tag == 'aktenzeichen':
                self.aktenzeichen = data
            elif tag == 'doktyp':
                self.dokumenttyp = data
            elif tag == 'norm' or tag == 'enbez':
                self.normen = data
            elif tag == 'vorinstanz':
                if self.vorinstanz:
                    self.vorinstanz += '; ' + data
                else:
                    self.vorinstanz = data
            elif tag == 'abk':
                self.region_abk = data
            elif tag == 'long':
                self.region_lang = data
            elif tag == 'mitwirkung':
                self.mitwirkung = data
            elif tag == 'periodikum':
                self.quelle += data + ' ' 
            elif tag == 'zitstelle':
                self.quelle += data + ' '
            elif tag == 'titelzeile' or tag == 'title' or tag == 'h1':
                if self.titelzeile:
                    self.titelzeile += '; ' + data
                else:
                    self.titelzeile = data
            elif tag in ['gerid', 'gerichtsbarkeit', 'schlagwort']:
                pass 
            else:
                print(f"Unknown tag {tag}")
        ##
        elif self.mode == 'nw':    
            #print("TAG: %s %d\n%s" % (tag,self.NRWneu,data))
            if tag == 'div':
                if (self.feldbezeichnungsModus):
                    if (len(self.feldname) == 0):
                        self.feldname = data
                elif (self.vorherigerFeldbezeichnungsModus):
                    #print("Hi \"%s\"" % self.feldname)
                    if (self.feldname == 'Datum:'):
                        self.entscheidungsdatum = datetime.strptime(data, '%d.%m.%Y')
                    elif (self.feldname == 'Gericht:'):
                        self.gericht = data
                    elif (self.feldname == 'Spruchkörper:'): 
                        self.spruchkoerper = data
                    elif (self.feldname == 'Entscheidungsart:'):
                        self.dokumenttyp = data
                    elif (self.feldname == 'Aktenzeichen:'):
                        self.aktenzeichen = data
                    elif (self.feldname == 'ECLI:'):
                        self.ecli = data
                

                    self.feldname = ''
            elif tag in ('p','b','strong','span','em', 'sub', 'sup', 'ul', 'del', 'ins') or ((self.NRWneu == True) and (tag in ('u','li','i'))):  ## links? aka a href?
                if (data.isspace()): return
                if (data == '(Hier Freitext: Tatbestand, Gründe etc.)' and self.NRWneu == True): return
                if tag in ['span', 'em', 'sub', 'sup', 'ul', 'del', 'ins']:
                    if tag != 'span' or self.randnummerLink == False:
                        self.text += ' ' + data
                else:
                    self.text += '\n' + data
        elif self.mode in ('ni'):
            if (tag == 'p'):
                if (self.bssmall):
                    self.bssmallNumber += 1

                    if (self.bssmallNumber == 1):
                        splitted = data.split(",")
                        ## Gerichtsname
                        self.trenne_gericht_und_kammer(splitted[0])
                        ## Datum und Urteilstyp 
                        self.dokumenttyp = splitted[1].split("vom",1)[0].strip()
                        datumsstring = splitted[1].split("vom",1)[1].strip()
                        if len(datumsstring) > 10: datumsstring = datumsstring[-10:]
                        self.entscheidungsdatum = datetime.strptime(datumsstring, '%d.%m.%Y')

                        self.aktenzeichen = splitted[2].strip()
                        if '#' in self.aktenzeichen:
                            self.aktenzeichen = self.aktenzeichen.split('#')[-1]

                        for i in range(3,len(splitted)):
                            if ("ECLI" in splitted[i]):
                                self.ecli = splitted[i].strip()
                            else:
                                if len(self.normen) > 0: self.normen += ', '
                                self.normen += splitted[i].strip()
                elif not self.inTitle: ## nicht bssmall
                    if (data.isspace()): return
                    self.text += data + '\n'
            elif tag == 'h2':
                self.inBody = 'Dokumentansicht' in data
            elif (tag in ('h4','strong','br')):
                if self.inBody:
                    self.text += data + '\n'
        elif self.mode in ('rp','sh', 'be', 'he', 'mv', 'sl', 'st', 'th', 'hh', 'bw'):
            if data.isspace(): return
            #print(tag)
            #print(data)
            #print("====================================================================")
            if (tag == 'strong'):
                if self.inTabelle:
                    self.aktuellerStrong = data
                elif len(self.gericht) > 0:
                    self.text += '\n' + data ## Text, aber nur nach dem Header
            elif tag == 'td':
                if self.inTabelle:
                    if self.aktuellerStrong == 'Gericht:':
                        self.trenne_gericht_und_kammer(data)
                    elif self.aktuellerStrong == 'Entscheidungsdatum:':
                        self.entscheidungsdatum = datetime.strptime(data, '%d.%m.%Y')
                    elif self.aktuellerStrong == 'Aktenzeichen:':
                        self.aktenzeichen = data
                    elif self.aktuellerStrong == 'ECLI:':
                        self.ecli = data
                    elif self.aktuellerStrong == 'Dokumenttyp:':
                        self.dokumenttyp = data
                    elif self.aktuellerStrong == 'Normen:':
                        self.normen += data.strip()
                    self.aktuellerStrong = '' ## verbraucht
                elif len(self.gericht) > 0:
                    self.text += data + '\n' ## Text, aber nur nach dem Header
            elif (tag in ('a', 'span')):
                if self.randnummerLink == False and self.inTabelle == False and self.gericht != '' and not self.bodyEnde:
                    self.text += ' ' + data.strip()
            elif (tag in ('ul','sup', 'sub', 'em')):
                if self.randnummerLink == False and self.inTabelle == False and self.gericht != '' and not self.bodyEnde:
                    self.text += ' ' + data.strip()
            elif (tag in ('h4','br', 'p')):
                if self.gericht != '' and not self.bodyEnde:
                    self.text += '\n' + data.strip()
        #elif self.mode in ('bw'):
        #    if data.isspace(): return
        #    
        #    if (tag == 'h1'):
        #        splitted = re.split(",|vom",data)
        #                    
        #        ## Dokumententyp
        #        ersteSplitted = [ x for x in splitted[0].split(" ") if len(x) > 0]
        #        self.dokumenttyp = ersteSplitted[-1].strip()
        #           
        #        ### Gerichtsname
        #        gername = ersteSplitted[:-1]
        #        self.trenne_gericht_und_kammer(' '.join(gername))
        #        ### Datum und Urteilstyp 
        #        datumsstring = splitted[1].strip()
        #        self.entscheidungsdatum = datetime.strptime(datumsstring, '%d.%m.%Y')
        #
        #        self.aktenzeichen = ', '.join(splitted[2:]).strip()
        #    elif (tag in ('p','td','em','rd', 'span', 'ul', 'sub', 'sup', 'strong', 'br')):
        #        if len(self.gericht) == 0: return
        #        if data.strip().isnumeric(): return
        #        
        #        if tag in ['em', 'span', 'ul', 'sub', 'sup']:
        #            self.text += ' ' + data.strip()
        #        else:
        #            self.text += '\n' + data.strip()
#        elif self.mode in ('judicialis'):
#            if data.isspace(): return
#            if tag == 'h4':
#                if data.startswith('Gericht:'):
#                    self.gericht = data.split(" ",1)[1].strip()

                #print(self.gericht)
            elif tag == 'br':
                #print("BR: " + data.strip() + " " + self.aktenzeichen)
                if self.dokumenttyp == '':
                    splitted = data.strip().split('verkündet am')
                    if len(splitted) != 2:
                        input()

                    self.dokumenttyp = splitted[0].strip()
                    self.entscheidungsdatum = datetime.strptime(splitted[1].strip(), '%d.%m.%Y')
                elif self.aktenzeichen == '':
                    self.aktenzeichen = data.strip().split(" ",1)[1].replace("  "," ")

                    if '\n' in self.aktenzeichen:
                        self.aktenzeichen = self.aktenzeichen.split("\n")[0].strip()
            
            elif tag in ('hr','p','a','div'):
                if len(self.aktenzeichen) > 0 and not self.endeDerEntscheidung:
                    if 'Diese Entscheidung enthält keinen zur Veröffentlichung bestimmten Leitsatz.' in data: return
                    if len(self.text) > 0:
                        if tag == 'a':
                            self.text += ' '
                        else: self.text += '\n'
                    self.text += data.strip()
            elif tag == 'b':
                if 'Ende der Entscheidung' in data: self.endeDerEntscheidung = True
        elif self.mode in ('bb'):
            if len(data) == 0 or data.isspace(): return
            if tag == 'h6' and data == 'Service': self.bbfooter = True
            if self.bbfooter == True: return
            if tag == 'th':
                self.aktuellerTH = data.strip()
            elif tag == 'td':
                if self.aktuellerTH == 'Gericht':
                    self.trenne_gericht_und_kammer(data.strip())
                elif self.aktuellerTH == 'Entscheidungsdatum':
                    self.entscheidungsdatum = datetime.strptime(data, '%d.%m.%Y')
                elif self.aktuellerTH == 'Aktenzeichen':
                    self.aktenzeichen = data
                elif self.aktuellerTH == 'ECLI':
                    self.ecli = data
                elif self.aktuellerTH == 'Dokumententyp':
                    self.dokumenttyp = data
                elif self.aktuellerTH == 'Normen':
                    self.normen += data.strip()
                self.aktuellerTH = '' ## verbraucht
            elif tag in ('sub', 'sup', 'a', 'span', 'strong', 'ul', 'em'):  
                if tag in ('a','span'):
                    if self.text == '': return
                if (data.isspace()): return
                self.text += ' ' + data
            elif tag in ('p','h4', 'br'):
                if (data.isspace()): return
                self.text += '\n' + data

    ## testet ob es diese Datei schon gibt!
    def teste_ecli_datei(self):
        if not os.path.exists(self.output_path):
            return False

        gerichtsCode = self.ecli.split(':')[2]
        gerichtsland = self.gerichts_code_land[gerichtsCode]
        land_path = os.path.join(self.output_path, gerichtsland)
        if not os.path.exists(land_path):
            return False

        gerichts_path = os.path.join(land_path, gerichtsCode)
        if not os.path.exists(gerichts_path):
            return False

        file_name = self.ecli + '.txt'
        file_path = os.path.join(gerichts_path, file_name)
        
        if os.path.exists(file_path):
            #os.remove(file_path)
            return True
        
        return False


    def save_to_file(self):
        file_text = blanko.format(text=self.text,
                                  gericht=self.gericht,
                                  entscheidungsdatum=self.entscheidungsdatum,
                                  rechtskraft=self.rechtskraft,
                                  aktenzeichen=self.aktenzeichen,
                                  ecli=self.ecli,
                                  dokumenttyp=self.dokumenttyp,
                                  quelle=self.quelle,
                                  normen=self.normen,
                                  dokumentnummer=self.dokumentnummer,
                                  gerichtstyp=self.gerichtstyp,
                                  gerichtsort=self.gerichtsort,
                                  spruchkoerper=self.spruchkoerper,
                                  vorinstanz=self.vorinstanz,
                                  region_abk=self.region_abk,
                                  region_lang=self.region_lang,
                                  mitwirkung=self.mitwirkung,
                                  titelzeile=self.titelzeile)

        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        
        gerichtsCode = self.ecli.split(':')[2]
        gerichtsland = self.gerichts_code_land[gerichtsCode]
        land_path = os.path.join(self.output_path, gerichtsland)
        if not os.path.exists(land_path):
            os.makedirs(land_path)

        gerichts_path = os.path.join(land_path, gerichtsCode)
        if not os.path.exists(gerichts_path):
            os.makedirs(gerichts_path)

        file_name = self.ecli + '.txt'
        file_path = os.path.join(gerichts_path, file_name)
        
        if os.path.exists(file_path):
            #os.remove(file_path)
            output("file already exists", "warn")
            self.reset_attributes()
            #input()
            return
       
        #print(file_name)
        #print(file_path)
        #print(file_text.split("== Body")[0])
        #print(f"Length of body: {len(file_text.split('== Body')[1])}")

        #### Normales Schreiben ...
        file = codecs.open(file_path, 'w', 'utf-8')
        file.write(file_text)
        file.close()
    
        self.reset_attributes()

    def complete_attributes(self):
        if not self.dokumenttyp:
            if 'Urteil' in self.titelzeile:
                self.dokumenttyp = 'Urteil'
            elif 'Beschluss' in self.titelzeile or 'Beschluß' in self.titelzeile:
                self.dokumenttyp = 'Beschluss'
        if self.dokumenttyp == 'Bes': self.dokumenttyp = 'Beschluss'
        if self.dokumenttyp == 'Urt': self.dokumenttyp = 'Urteil'

        if not self.entscheidungsdatum:
            match = re.findall(date_pattern, self.titelzeile)
            print(match)
            if match:
                self.entscheidungsdatum = datetime.strptime(match[0], '%d.%m.%Y')

        if self.gericht == '':
            if len(self.gerichtsort) > 0:
                self.gericht = self.gerichtstyp + ' ' + self.gerichtsort
            else:
                self.gericht = self.gerichtstyp

        if self.gerichtstyp == '' and self.gerichtsort == '':
            if (self.gericht.startswith("Hanseatisches Oberlandesgericht")):
                self.gerichtstyp = "Hanseatisches Oberlandesgericht"
                self.gerichtsort = "Hamburg"
            else:
                splitted = self.gericht.split(" ", 1)
                self.gerichtstyp = splitted[0]
                if len(splitted) == 2:
                    self.gerichtsort = splitted[1]

        # Gerichtstyp könnte eine Abkürzung sein. Wenn dem so ist, expandieren wir
        gerichtstypgeändert = False
        if (self.gerichtstyp == 'VerfGH'): self.gerichtstyp = 'Verfassungsgerichtshof'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'BayObLG'): self.gerichtstyp = 'Bayerisches Oberstes Landesgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'OLG'): self.gerichtstyp = 'Oberlandesgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'OVG'): self.gerichtstyp = 'Oberverwaltungsgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'LSG'): self.gerichtstyp = 'Landessozialgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'VGH'): self.gerichtstyp = 'Verwaltungsgerichtshof'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'LArbG'): self.gerichtstyp = 'Landesarbeitsgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'VG'): self.gerichtstyp = 'Verwaltungsgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'SG'): self.gerichtstyp = 'Sozialgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'AG'): self.gerichtstyp = 'Amtsgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'LG'): self.gerichtstyp = 'Landgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'FG'): self.gerichtstyp = 'Finanzgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'KG'): self.gerichtstyp = 'Kammergericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'ArbG'): self.gerichtstyp = 'Arbeitsgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'BFH'): self.gerichtstyp = 'Bundesfinanzhof'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'VerfG'): self.gerichtstyp = 'Verfassungsgericht'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'DGH'): self.gerichtstyp = 'Dienstgerichtshof'; gerichtstypgeändert = True
        if (self.gerichtstyp == 'LGHE'): self.gerichtstyp = 'Landgericht Frankfurt'; gerichtstypgeändert = True
        
        if gerichtstypgeändert:
            if len(self.gerichtsort) > 0:
                self.gericht = self.gerichtstyp + ' ' + self.gerichtsort
            else:
                self.gericht = self.gerichtstyp
        
        ## Einige Hessische Urteile enthalten eine nicht korret geformte ECLI, die mit "ECLI:ECLI:" beginnt
        if self.ecli.startswith("ECLI:ECLI"):
            old = self.ecli[5:]
            self.ecli = old

        ## Wenn wir keine ECLI erhalten, dann versuchen wir selbst eine zu konstruieren
        old = self.ecli.replace('/','.').replace(' ','');
        self.ecli = old
       

        self.ecli = '';
        if self.ecli == '':
            self.ecli = 'ECLI:DE:' + self.ecli_codes[self.gericht] + ':' + str(self.entscheidungsdatum.year) + ':'
            if (self.ecli_codes[self.gericht] in ('BGH', 'BVerwG', 'BSG', 'BAG', 'BFH', 'BPatG')):
                typcode = ''
                if (self.dokumenttyp == 'Urteil'): typcode = 'U'
                if (self.dokumenttyp == 'Versäumnisurteil'): typcode = 'U'
                if (self.dokumenttyp == 'Anerkenntnisurteil'): typcode = 'U'
                if (self.dokumenttyp == 'Teilurteil'): typcode = 'U'
                if (self.dokumenttyp == 'Beschluss'): typcode = 'B'
                if (self.dokumenttyp == 'Vorlagebeschluss'): typcode = 'B'
                if (self.dokumenttyp == 'Gerichtsbescheid'): typcode = 'G'
                if (self.dokumenttyp == 'EuGH-Vorlage'):
                    if (self.ecli_codes[self.gericht] == 'BFH'):
                        typcode = 'VE'
                    else:
                        typcode = 'B'
                if (self.dokumenttyp == 'Verfügung'): typcode = 'V'
                if (self.dokumenttyp == 'Sonstige'): typcode = 'S'


                if (typcode == 'B' and self.ecli_codes[self.gericht] == 'BFH'):
                    if ("Aussetzung der Vollziehung" in self.text): typcode += 'A' 

                if (self.ecli_codes[self.gericht] == 'BFH'): self.ecli += typcode + '.'


                self.ecli += self.entscheidungsdatum.strftime('%d%m%-y') 
                if (self.ecli_codes[self.gericht] in ('BAG','BFH')): self.ecli += '.'
                
                if (self.ecli_codes[self.gericht] != 'BFH'): self.ecli += typcode
                
                
                if (self.ecli_codes[self.gericht] in ('BAG')): self.ecli += '.'
                
                ## Kommas tauchen in Strafverfahren auf. Nur der Teil vor dem Komma gehört in die ECLI
                format_aktenzeichen = self.aktenzeichen.replace(" ","")
                if (self.ecli_codes[self.gericht] != 'BPatG'): format_aktenzeichen = format_aktenzeichen.upper()
                format_aktenzeichen = format_aktenzeichen.replace("Ä","AE").replace("Ö","OE").replace("Ü","UE").split(",", 1)[0]
                if (self.ecli_codes[self.gericht] in ('BFG') and format_aktenzeichen[-1] == ')'):
                    format_aktenzeichen = re.sub(r"\s*\([^()]*\)$", '', format_aktenzeichen)


                if (self.ecli_codes[self.gericht] in ('BSG')):
                    format_aktenzeichen = format_aktenzeichen.replace("/","").replace("(","").replace(")","")
                elif (self.ecli_codes[self.gericht] in ('BPatG', 'BAG')):
                    format_aktenzeichen = format_aktenzeichen.replace("/",".").replace("(","").replace(")","")
                else:
                    format_aktenzeichen = format_aktenzeichen.replace("/",".").replace("(",".").replace(")",".").replace("-","")
                
                if (self.ecli_codes[self.gericht] in ('BVerwG')):
                    format_aktenzeichen = format_aktenzeichen.replace("KST","KSt")

                self.ecli += format_aktenzeichen 
                if (self.ecli_codes[self.gericht] in ('BGH', 'BVerwG', 'BFH', 'BAG', 'BPatG')): self.ecli += '.'
                
#                if self.mode == 'judicialis' or self.mode == 'bund' or old != '': self.ecli += str(0)

                i = 0
                while self.mode != 'bund' and old == '': # and self.mode != 'judicialis'
                    temp = self.ecli
                    self.ecli += str(i)
                    if self.teste_ecli_datei():
                        self.ecli = temp
                        old = ''
                        i += 1
                    else:
                        break

            elif (self.ecli_codes[self.gericht] in ('BVerfG')):
                if ("PBv" in self.aktenzeichen):
                    self.ecli += 'up' ## Plenarentscheidung
                else:
                    bverfpattern = re.compile("B[vV]([a-zA-Z]*)")
                    self.ecli += bverfpattern.search(self.aktenzeichen).group(1).lower()
                    if ("Kammer" in self.spruchkoerper): self.ecli += 'k'
                    else: self.ecli += 's'

                self.ecli += self.entscheidungsdatum.strftime('%Y%m%d') + '.'
                
                format_aktenzeichen = self.aktenzeichen.split(",", 1)[0]
                bverfpattern = re.compile("([1-2]) ([P]?)B[vV]([a-zA-Z]*) ([0-9]*)/([0-9]*)")
                res = bverfpattern.search(format_aktenzeichen)
                format_aktenzeichen = res.group(1) + res.group(2) + "Bv" + res.group(3)
                for _ in range(4 - len(res.group(4))): format_aktenzeichen += '0'
                format_aktenzeichen += res.group(4) + res.group(5)

                self.ecli += format_aktenzeichen.lower()
                
                if self.teste_ecli_datei():
                    i = 1
                    old = ''
                    while self.mode != 'judicialis':
                        temp = self.ecli
                        self.ecli += '.' + str(i)
                        if self.teste_ecli_datei():
                            old = ''
                            self.ecli = temp
                            i += 1
                        else:
                            break

            else:
                self.ecli += self.entscheidungsdatum.strftime('%m%d') + '.'

                az_splitted = self.aktenzeichen.upper().replace("Ä","AE").replace("Ö","OE").replace("Ü","UE").split(",", 1)
                format_aktenzeichen = az_splitted[0]
                if len(az_splitted) > 1: ### Finanzgerichte: 9 K 1828/11 K,G
                    if len(az_splitted[1]) <=3:
                        format_aktenzeichen += "," + az_splitted[1]
                #if format_aktenzeichen.endswith(" OVG"): format_aktenzeichen = format_aktenzeichen.rsplit(' ', 1)[0] ## OVG MV
                #if format_aktenzeichen.endswith(" HGW"): format_aktenzeichen = format_aktenzeichen.rsplit(' ', 1)[0] ## VG Greifswald
                #if format_aktenzeichen.endswith(" SN"): format_aktenzeichen = format_aktenzeichen.rsplit(' ', 1)[0] ## VG Schwerin
                prev = ' '
                azblock = ''
                if self.ecli_codes[self.gericht] == "VERFGHT": azblock = "VERFGH" # Verfassungsbericht Thürigen fügt Gerichtsnamen ins AZ intu anders ...
                if self.ecli_codes[self.gericht] == "STGHNI": azblock = "STGH" # Verfassungsbericht Thürigen fügt Gerichtsnamen ins AZ intu anders ...
                
                if self.ecli_codes[self.gericht] == "OVGBEBB": ## Oberverwaltungsgericht Berlin Brandenburg
                    if not (format_aktenzeichen.startswith("OVG")):
                        azblock = "OVG"

                if self.ecli_codes[self.gericht] == "LSGNIHB": ## Oberverwaltungsgericht Berlin Brandenburg
                    if not (format_aktenzeichen.startswith("L")):
                        azblock = "L"

                splitstring = '[^a-zA-Z0-9.]'
                if self.ecli_codes[self.gericht] in ["OVGNRW","VGK","VGD","VFGHNRW", "VGGE", "VGAC", "VGMI", "VGMS", "VGAR", "OLGHAM"]:
                    splitstring = '[^a-zA-Z0-9]'
                
                for block in re.split(splitstring, format_aktenzeichen): ## if the AZ contains a dot, this seems to be kept usually
                    if len(block) == 0: continue
                    if (block[0].isalpha() and prev[-1].isalpha()): azblock += '.'
                    if (block[0].isnumeric() and prev[-1].isnumeric()): azblock += '.'
                    azblock += block
                    prev = block

                azblock = azblock[0:17] ## nur die ersten 17 Zeichen werden Teil der ECLI
                if azblock[-1] == '.': azblock = azblock[:-1]
                self.ecli += azblock
                self.ecli += '.0'
                

                if self.mode == 'bb' or old != '' or True: # or self.mode == 'judicialis'
                    self.ecli += '0'
                else:
                    i = 0
                    while self.mode != 'bb' and old == '' and False: # and self.mode != 'judicialis' 
                        temp = self.ecli
                        self.ecli += str(i)
                        if self.teste_ecli_datei():
                            old = ''
                            i+=1
                            self.ecli = temp
                        else:
                            break

            if (old != ''):
                self.eclitests += 1
                if (self.ecli[:-1] != old[:-1]):
                    print("\tECLI prediction incorrect %s != %s" % (old,self.ecli))
                    self.waitforinput = True
                    self.ecli = old
                else:
                    print("\tECLI prediction   correct " + self.ecli)
            else:
                print("\tNo ECLI given predicting  " + self.ecli)

    def reset_attributes(self):
        self.start_tag = []
        self.text = ''
        self.gericht = ''
        self.entscheidungsdatum = ''
        self.rechtskraft = ''
        self.aktenzeichen = ''
        self.ecli = ''
        self.dokumenttyp = ''
        self.quelle = ''
        self.normen = ''
        self.dokumentnummer = ''
        self.gerichtstyp = ''
        self.gerichtsort = ''
        self.spruchkoerper = ''
        self.vorinstanz = ''
        self.region_abk = ''
        self.region_lang = ''
        self.mitwirkung = ''
        self.titelzeile = ''

        self.inRechtsmittelInstanz = False
        self.vorInstanz = False
        self.inBody = False
        
        self.feldname = ''
        self.feldbezeichnungsModus = False
        self.vorherigerFeldbezeichnungsModus = False

        self.aktuellerStrong = ''
        self.aktuellerTH = ''
        self.inTabelle = False
        self.tabellentiefe = 0
        self.bodyEnde = False
        
        self.endeDerEntscheidung = False
        
        self.bssmallNumber = 0



def parse_data_from_html(item, spider_name, spider_path):
    verbose = False
    parser = DecisionHTMLParser()
    
    parser.mode = spider_name
    if parser.mode in ('bund','nw','ni', 'hh', 'rp', 'sh', 'bb'):
        codec = 'utf-8'
    else:
        codec = 'iso-8859-1'

    parser.output_path = os.path.join(spider_path, "preprocessed")

    i = 0
    #print("File #%5d (%5d) [%5d]: mode %s" % (i,parser.eclitests,parser.reextracted, parser.mode))

    if (parser.mode == "bund") or (parser.mode == "by"):
        # bund mode only extracts the zip files. contents of the file are never loaded into the RAM
        file = codecs.open(item["xmlfilename"], 'r', codec)
        text = file.read()
        file.close()
    else:
        text = item["text"]
    
    ## SH decisions sometimes contain invalid HTML which causes the parser to crash
    if parser.mode == "sh":
        try:
            parser.feed(text)
            parser.complete_attributes()
            parser.save_to_file()
            if parser.waitforinput:
                #input()
                parser.waitforinput = False

            return parser
        except KeyError as e:
            print(e)
            traceback.print_exc()
            output("invalid HTML @ sh", "err")

    else:
        try:
            parser.feed(text)
            parser.complete_attributes()

            parser.save_to_file()
            if parser.waitforinput:
                #input()
                parser.waitforinput = False
        except Exception as e:
            print(e)
            traceback.print_exc()
            #os._exit(1)
