"""GDELT: automatisch gesammelte Schlagzeilen aus Nachrichtenmedien weltweit.

GDELT (gdeltproject.org) wertet Nachrichten in vielen Sprachen aus und ist frei nutzbar.
Wir fragen je Thema (passend zu den Simulations-Typen) die neuesten Artikel ab und
speichern Titel, Link und Datum. Die Einordnung nach Kontinent erfolgt in export.py
anhand von Stichwoertern im Titel und ist eine Naeherung."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from common import AbrufFehler, PAUSE

NAME = "gdelt"
BASIS = "https://api.gdeltproject.org/api/v2/doc/doc"
ZEITRAUM = "3d"
MAX = 40
PAUSE_GDELT = 6.0       # GDELT erlaubt hoechstens eine Abfrage je 5 Sekunden

# Thema (= Simulations-Typ) -> Suchausdruck
THEMEN = {
    "logistik":  '("Strait of Hormuz" OR "Suez Canal" OR "Red Sea" OR "Panama Canal" OR "shipping" OR "supply chain" OR "port strike" OR blockade)',
    "energie":   '(oil OR "natural gas" OR LNG OR OPEC OR pipeline OR "power outage" OR refinery)',
    "finanz":    '("central bank" OR "interest rate" OR "currency crisis" OR "debt crisis" OR "bond yields" OR "bank collapse")',
    "politik":   '(sanctions OR tariffs OR "trade war" OR embargo OR "export ban" OR "export controls")',
    "rohstoffe": '(wheat OR grain OR "rare earth" OR copper OR lithium OR fertilizer OR drought OR "crop failure")',
}
SPRACHEN = ["english", "german"]


def _roh(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; weltmodell/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise AbrufFehler("HTTP %s" % e.code)
    except (urllib.error.URLError, TimeoutError) as e:
        raise AbrufFehler("Verbindung: %s" % e)


def _artikel(suche):
    qs = urllib.parse.urlencode({"query": suche, "mode": "artlist", "format": "json", "maxrecords": MAX,
                                 "timespan": ZEITRAUM, "sort": "hybridrel"}, quote_via=urllib.parse.quote)
    for versuch in (1, 2):
        try:
            text = _roh(BASIS + "?" + qs)
        except AbrufFehler as e:
            if versuch == 1 and "429" in str(e):
                time.sleep(PAUSE_GDELT * 2)
                continue
            raise
        t = text.strip()
        if not t:
            return []                    # GDELT antwortet bei null Treffern manchmal leer
        if not t.startswith("{"):
            if versuch == 1 and "limit" in t.lower():
                time.sleep(PAUSE_GDELT * 2)
                continue
            raise AbrufFehler("keine JSON-Antwort: %s" % t[:80].replace("\n", " "))
        try:
            return json.loads(t).get("articles") or []
        except ValueError:
            raise AbrufFehler("ungueltiges JSON: %s" % t[:80].replace("\n", " "))
    return []


def _datum(s):
    s = str(s)                            # Format 20261027T143000Z
    return "%s-%s-%s" % (s[0:4], s[4:6], s[6:8])


def fetch(vorhanden):
    zeilen, warnungen = [], []
    for thema, ausdruck in THEMEN.items():
        for sprache in SPRACHEN:
            try:
                arts = _artikel("%s sourcelang:%s" % (ausdruck, sprache))
            except AbrufFehler as e:
                warnungen.append("%s/%s: %s" % (thema, sprache, str(e)[:100]))
                arts = []
            for a in arts:
                titel = (a.get("title") or "").strip()
                url = (a.get("url") or "").strip()
                if not titel or not url.startswith("http") or not a.get("seendate"):
                    continue
                zeilen.append({"indicator": thema, "entity": url, "entity_type": "news",
                               "date": _datum(a["seendate"]), "value": titel})
            time.sleep(PAUSE_GDELT if PAUSE else 0)
    if not zeilen:
        raise AbrufFehler("GDELT lieferte keine Artikel. " + " | ".join(warnungen))
    return zeilen, warnungen
