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
MAX = 10             # hoechstens 10 Meldungen je Abfrage (Thema und Sprache)
PAUSE_GDELT = 12.0      # GDELT erlaubt hoechstens eine Abfrage je 5 Sekunden; wir lassen deutlich mehr Luft

# Thema (= Simulations-Typ) -> Suchausdruck
THEMEN = {
    "logistik":  '("Strait of Hormuz" OR "Suez Canal" OR "Red Sea" OR "Panama Canal" OR "shipping" OR "supply chain" OR "port strike" OR blockade)',
    "energie":   '(oil OR "natural gas" OR LNG OR OPEC OR pipeline OR "power outage" OR refinery)',
    "finanz":    '("central bank" OR "interest rate" OR "currency crisis" OR "debt crisis" OR "bond yields" OR "bank collapse")',
    "politik":   '(sanctions OR tariffs OR "trade war" OR embargo OR "export ban" OR "export controls")',
    "rohstoffe": '(wheat OR grain OR "rare earth" OR copper OR lithium OR fertilizer OR drought OR "crop failure")',
}
SPRACHEN = ["english", "german"]     # Deutsch nur, wenn Englisch glatt durchlief


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
    """Eine Abfrage, ohne Wiederholung. Wird sie abgewiesen (zum Beispiel HTTP 429), gibt es einen Fehler."""
    qs = urllib.parse.urlencode({"query": suche, "mode": "artlist", "format": "json", "maxrecords": MAX,
                                 "timespan": ZEITRAUM, "sort": "hybridrel"}, quote_via=urllib.parse.quote)
    t = _roh(BASIS + "?" + qs).strip()
    if not t:
        return []                        # GDELT antwortet bei null Treffern manchmal leer
    if not t.startswith("{"):
        raise AbrufFehler("abgewiesen: %s" % t[:80].replace("\n", " "))
    try:
        return json.loads(t).get("articles") or []
    except ValueError:
        raise AbrufFehler("ungueltiges JSON: %s" % t[:80].replace("\n", " "))


def _datum(s):
    s = str(s)                            # Format 20261027T143000Z
    return "%s-%s-%s" % (s[0:4], s[4:6], s[6:8])


def fetch(vorhanden):
    zeilen, warnungen = [], []
    for sprache in SPRACHEN:
        for thema, ausdruck in THEMEN.items():
            abgewiesen = False
            try:
                arts = _artikel("%s sourcelang:%s" % (ausdruck, sprache))
            except AbrufFehler as e:
                warnungen.append("%s/%s: %s" % (thema, sprache, str(e)[:100]))
                arts, abgewiesen = [], True
            for a in arts:
                titel = (a.get("title") or "").strip()
                url = (a.get("url") or "").strip()
                if not titel or not url.startswith("http") or not a.get("seendate"):
                    continue
                zeilen.append({"indicator": thema, "entity": url, "entity_type": "news",
                               "date": _datum(a["seendate"]), "value": titel})
            if PAUSE and not abgewiesen:
                time.sleep(PAUSE_GDELT)   # nur nach gelungenen Abfragen Abstand halten; nach einer Abweisung sofort weiter
    if not zeilen:
        raise AbrufFehler("GDELT lieferte keine Artikel. " + " | ".join(warnungen))
    return zeilen, warnungen
