# -*- coding: utf-8 -*-
import datetime
import re
from src import config

class AZsPipeline:
    def process_item(self, item, spider):                
        #Formattierunng der Aktenzeichen
        item["az"] = item["az"].strip() 
        item["az"] = item["az"].replace("/", "-")
        item["az"] = item["az"].replace(".", "-")
        item["az"] = re.sub(r"\s", "-", item["az"]) # Alle Arten von Leerzeichen (normale, geschützte, ...)
        return item

class DatesPipeline:
    def process_item(self, item, spider):                
        #Formattierung der Daten
        item["date"] = item["date"].strip()
        item["date"] = datetime.datetime.strptime(item["date"], "%d.%m.%Y").strftime("%Y%m%d")
        # Weitergabe an die individuellen Pipelines
        return item

class CourtsPipeline:
    def __cut_at_nr(self, court):
        #Senate/Kammern abschneiden ("-|7.-senat")
        return re.split(r"([-]?\d+)", court)[0]

    def __cut_at_term(self, court, terms_as_list):
        # Fachkammern / Fachsenate / Beschwerdesenate / Berufsgerichte abschneiden
        for term in terms_as_list:
            if term in court:
                court = court.split(term)[0]
                court = court.strip("-")
        return court

    def __replace_terms(self, court, terms_as_dict):
        # Gerichtstypen abkürzen
        for key in terms_as_dict:
            if key in court:
                 court = court.replace(key, terms_as_dict[key])
        return court
    
    def __remove_terms(self, court, terms_as_list):
        #  Eigennamen entfernen
        for term in terms_as_list:
            if term in court:
                court = court.replace(term, "")
        return court

    def process_item(self, item, spider):
        court = item["court"]
        if spider.name[7:] == "bund":
            court = court.lower()
            for c in ["bgh", "bfh", "bverwg", "bverfg", "bpatg", "bag", "bsg"]:
                if c in court.split():
                    court = c
        else:
            # Standard-Formatierung der Gerichtsnamen für alle LÄNDER
            court = court.lower()
            court = court.strip()
            court = re.sub(r"\s", "-", court)
            court = court.translate(config.UMLAUTE)
            # Individuelle Formatierungen
            if spider.name[7:] != "sn" and spider.name[7:] != "bw":
                court = self.__cut_at_nr(court)
            if spider.name[7:] == "be":
                court = self.__cut_at_term(court, ["fachkammer", "fachsenat", "beschwerdesenat", "kartellsenat", "vergabesenat", "senat", "berufsgericht"])
                court = self.__replace_terms(court, {"finanzgericht":"fg","landessozialgericht": "lsg",  "oberverwaltungsgericht": "ovg", "verfassungsgerichtshof-des-landes-berlin": "verfgh"})
            if spider.name[7:] == "he":
                court = self.__cut_at_term(court, ["hessischer-", "hessisches-", "-abteilung"])
                court = self.__replace_terms(court, {"finanzgericht": "fg", "landesarbeitsgericht": "lag", "landessozialgericht": "lsg", "verwaltungsgerichtshof": "vgh" })
            if spider.name[7:] == "hh":
                court = self.__cut_at_term(court, ["fachkammer", "fachsenat", "beschwerdesenat", "vergabesenat", "senat", "berufsgericht"])
                court = self.__remove_terms(court, ["hanseatisches-", "hamburgisches-"])
                court = self.__replace_terms(court, {"landesarbeitsgericht": "lag", "landessozialgericht": "lsg", "oberlandesgericht": "olg", "oberverwaltungsgericht": "ovg", "verfassungsgericht": "verfgh"})
            if spider.name[7:] == "mv":
                court = self.__remove_terms(court, ["-mecklenburg-vorpommern", "-fuer-das-land"])
                court = self.__replace_terms(court, {"finanzgericht": "fg", "landesarbeitsgericht": "lag", "landessozialgericht": "lsg", "oberverwaltungsgericht": "ovg"})
            if spider.name[7:] == "nw":
                court = self.__replace_terms(court, {"amtsgericht":"ag", "finanzgericht":"fg", "landgericht":"lg", "landesarbeitsgericht":"lag", "arbeitsgericht":"arbg", "oberlandesgericht":"olg", "oberverwaltungsgericht":"ovg", "landessozialgericht": "lsg", "sozialgericht":"sg", "verfassungsgerichtshof":"verfgh", "verwaltungsgericht": "vg"})
            if spider.name[7:] == "rp":
                court = self.__remove_terms(court, ["-rheinland-pfalz"])
                court = self.__remove_terms(court, {"finanzgericht": "fg", "landesarbeitsgericht":"lag", "oberverwaltungsgericht": "ovg", "verfassungsgerichtshof": "verfgh"})
            if spider.name[7:] == "sh":
                court = self.__remove_terms(court, ["schleswig-holsteinisches-", "-fuer-das-land-schleswig-holstein", "-schleswig-holstein"])
                court = self.__replace_terms(court, {"finanzgericht":"fg", "landesarbeitsgericht":"lag", "landessozialgericht":"lsg", "landesverfassungsgericht":"verfgh", "oberlandesgericht":"olg", "oberverwaltungsgericht":"ovg", "verwaltungsgericht":"vg"})
            if spider.name[7:] == "sl":
                court = self.__remove_terms(court, ["saarlaendisches-", "-des-saarlandes", "-fuer-das-saarland"])
                court = self.__replace_terms(court, {"finanzgericht": "fg", "landesarbeitsgericht": "lag", "landessozialgericht": "lsg", "oberlandesgericht": "olg", "oberverwaltungsgericht": "ovg", "sozialgericht": "sg", "verfassungsgerichtshof": "verfgh", "verwaltungsgericht":"vg"})
            if spider.name[7:] == "sn":
                court = self.__replace_terms(court, {"amtsgericht":"ag","landgericht": "lg", "oberlandesgericht": "olg"})
            if spider.name[7:] == "st":
                court = self.__remove_terms(court, ["-des-landes-sachsen-anhalt", "-sachsen-anhalt"])
                court = self.__replace_terms(court, {"finanzgericht": "fg", "landesarbeitsgericht": "lag", "landessozialgericht": "lsg", "oberlandesgericht":"olg", "oberverwaltungsgericht": "ovg", "landesverfassungsgericht": "verfgh"})
            if spider.name[7:] == "th":
                court = self.__remove_terms(court, ["thueringer-", ""])
                court = self.__replace_terms(court, {"finanzgericht": "fg", "landesarbeitsgericht": "lag", "landessozialgericht": "lsg", "oberlandesgericht":"olg", "oberverwaltungsgericht": "ovg", "verfassungsgerichtshof": "verfgh"})
        item["court"] = court
        return item




        

        
