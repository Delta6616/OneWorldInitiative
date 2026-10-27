"""Rohstoffpreise aus FRED (Federal Reserve Bank of St. Louis), frei abrufbar ohne Schluessel.

FRED stellt Preisreihen als einfache CSV-Datei bereit (fredgraph.csv). Die Reihen stammen
unter anderem von der US-Energiebehoerde EIA (Oel, Gas USA) und vom IWF (Weltmarktpreise
monatlich). Jede Reihe wird einzeln abgerufen; faellt eine aus, laufen die anderen weiter."""
import csv
import io
import time
import urllib.error
import urllib.request
from datetime import date

from common import AbrufFehler, PAUSE, fmt

NAME = "rohstoffe"
BASIS = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s&cosd=%s"
START = "2020-01-01"

# FRED-Kennung -> (Anzeigename, Einheit, Takt, Simulations-Typ)
REIHEN = {
    "DCOILBRENTEU": ("Rohöl Brent", "US-Dollar je Barrel", "täglich", "energie"),
    "DCOILWTICO":   ("Rohöl WTI", "US-Dollar je Barrel", "täglich", "energie"),
    "DHHNGSP":      ("Erdgas USA (Henry Hub)", "US-Dollar je MMBtu", "täglich", "energie"),
    "PNGASEUUSDM":  ("Erdgas Europa", "US-Dollar je MMBtu", "monatlich", "energie"),
    "PWHEAMTUSDM":  ("Weizen", "US-Dollar je Tonne", "monatlich", "rohstoffe"),
    "PMAIZMTUSDM":  ("Mais", "US-Dollar je Tonne", "monatlich", "rohstoffe"),
    "PCOPPUSDM":    ("Kupfer", "US-Dollar je Tonne", "monatlich", "rohstoffe"),
    "PALUMUSDM":    ("Aluminium", "US-Dollar je Tonne", "monatlich", "rohstoffe"),
}


def _roh(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; weltmodell/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8-sig", "replace")
    except urllib.error.HTTPError as e:
        raise AbrufFehler("HTTP %s" % e.code)
    except (urllib.error.URLError, TimeoutError) as e:
        raise AbrufFehler("Verbindung: %s" % e)


def _reihe(kennung):
    text = _roh(BASIS % (kennung, START))
    if text.lstrip().startswith("<"):
        raise AbrufFehler("keine CSV-Datei erhalten")
    lese = csv.reader(io.StringIO(text))
    kopf = next(lese, None)
    if not kopf or len(kopf) < 2:
        raise AbrufFehler("leere Antwort")
    out = []
    for z in lese:
        if len(z) < 2 or not z[1] or z[1] == ".":
            continue                     # FRED markiert fehlende Tage mit einem Punkt
        try:
            out.append((z[0][:10], float(z[1])))
        except ValueError:
            continue
    if not out:
        raise AbrufFehler("keine Werte in der Datei")
    return out


def fetch(vorhanden):
    zeilen, warnungen = [], []
    for kennung in REIHEN:
        try:
            for tag, wert in _reihe(kennung):
                zeilen.append({"indicator": kennung, "entity": "Welt", "entity_type": "commodity",
                               "date": tag, "value": fmt(wert)})
        except AbrufFehler as e:
            warnungen.append("%s: %s" % (kennung, str(e)[:100]))
        if PAUSE:
            time.sleep(1.0)
    if not zeilen:
        raise AbrufFehler("Keine Preise erhalten. " + " | ".join(warnungen))
    return zeilen, warnungen
