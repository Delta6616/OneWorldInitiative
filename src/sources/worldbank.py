"""Weltbank: Wirtschafts- und Gesellschaftskennzahlen je Land (frei, ohne Schlüssel).

Beim ersten Lauf wird die Geschichte ab 2000 geholt, danach nur die letzten Jahre.
Jede Kennzahl wird einzeln abgerufen. Scheitert eine, laufen die anderen weiter."""
import time
from datetime import date

from common import AbrufFehler, PAUSE, fmt, hole_json
from kontinente import KONTINENT

NAME = "worldbank"

INDIKATOREN = {
    "NY.GDP.MKTP.CD": "BIP, laufende US-Dollar",
    "NY.GDP.MKTP.KD.ZG": "BIP-Wachstum, Prozent pro Jahr",
    "FP.CPI.TOTL.ZG": "Inflation (Verbraucherpreise), Prozent pro Jahr",
    "SP.POP.TOTL": "Bevölkerung",
    "NE.TRD.GNFS.ZS": "Handel (Exporte plus Importe), Prozent des BIP",
    "GC.DOD.TOTL.GD.ZS": "Staatsschulden, Prozent des BIP",
    "PV.EST": "Politische Stabilität (Skala -2,5 bis +2,5)",
    "GE.EST": "Regierungswirksamkeit (Skala -2,5 bis +2,5)",
}

BASIS = "https://api.worldbank.org/v2/country/all/indicator/%s?format=json&per_page=1000"


def _seiten(url):
    zeilen, seite = [], 1
    while True:
        antwort = hole_json(url + "&page=%d" % seite)
        if not isinstance(antwort, list) or len(antwort) < 2 or not isinstance(antwort[1], list):
            raise AbrufFehler("Weltbank meldet: %s" % str(antwort)[:200])
        zeilen.extend(antwort[1])
        if seite >= int(antwort[0].get("pages", 1)):
            return zeilen
        seite += 1
        time.sleep(PAUSE * 0.5)


def _indikator(code, von):
    """Probiert mehrere Abfrageformen, bis eine Daten liefert."""
    basis = BASIS % code
    bis = date.today().year
    varianten = [
        basis + "&date=%d:%d" % (von, bis),
        basis + "&date=%d:%d&source=3" % (von, bis),   # Governance-Indikatoren liegen teils in Quelle 3
        basis + "&mrnev=1",                             # Notlösung: nur der neueste Wert je Land
    ]
    letzter = AbrufFehler("keine Abfrage versucht")
    for url in varianten:
        try:
            return _seiten(url)
        except AbrufFehler as e:
            letzter = e
    raise letzter


def fetch(vorhanden):
    von = date.today().year - 3 if vorhanden else 2000
    zeilen, warnungen = [], []
    for code in INDIKATOREN:
        try:
            for z in _indikator(code, von):
                iso3 = (z.get("countryiso3code") or "").strip()
                if iso3 not in KONTINENT or z.get("value") is None:
                    continue    # Regionen-Summen der Weltbank und leere Werte überspringen
                zeilen.append({"indicator": code, "entity": iso3, "entity_type": "country",
                               "date": str(z["date"]), "value": fmt(z["value"])})
        except AbrufFehler as e:
            warnungen.append("%s: %s" % (code, str(e)[:150]))
        time.sleep(PAUSE * 0.5)
    if not zeilen:
        raise AbrufFehler("Keine Daten erhalten. " + " | ".join(warnungen))
    return zeilen, warnungen
