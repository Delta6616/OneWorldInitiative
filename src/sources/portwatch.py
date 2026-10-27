"""IMF PortWatch: tägliche Schiffsdurchfahrten an 28 Meerengen und Kanälen
(zum Beispiel Suez, Panama, Hormus). Quelle: UN Global Platform, IMF PortWatch.

Gespeichert werden je Engstelle und Tag die Zahl aller Schiffe, der Tanker und der
Containerschiffe, ab Anfang 2024."""
import time
import urllib.parse
from datetime import date, datetime, timedelta, timezone

from common import AbrufFehler, PAUSE, fmt, hole_json

NAME = "portwatch"
BASIS = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
         "Daily_Chokepoints_Data/FeatureServer/0/query")
WERTE = ["n_total", "n_tanker", "n_container"]
START = "2024-01-01"


def _datum(w):
    if isinstance(w, (int, float)):       # ArcGIS liefert Datumsangaben als Millisekunden seit 1970
        return datetime.fromtimestamp(w / 1000, timezone.utc).strftime("%Y-%m-%d")
    return str(w)[:10]


def _abfrage(where, schlank=False):
    zeilen, offset = [], 0
    while True:
        par = {"where": where, "outFields": "date,portname," + ",".join(WERTE),
               "resultOffset": offset, "resultRecordCount": 1000,
               "returnGeometry": "false", "f": "json"}
        if schlank:     # Notloesung: ohne Sortierung und mit Minimal-Parametern
            par = {"where": where, "outFields": "*", "f": "json", "resultOffset": offset}
        else:
            par["orderByFields"] = "date ASC"
        a = hole_json(BASIS + "?" + urllib.parse.urlencode(par, quote_via=urllib.parse.quote))
        if not isinstance(a, dict) or "error" in a:
            raise AbrufFehler("PortWatch meldet: %s" % str(a)[:200])
        feats = a.get("features") or []
        zeilen.extend(f["attributes"] for f in feats)
        if not feats or not a.get("exceededTransferLimit"):
            return zeilen
        offset += len(feats)
        time.sleep(PAUSE * 0.5)


def fetch(vorhanden):
    if vorhanden:   # nur die letzten Tage nachladen, mit Puffer für nachträgliche Korrekturen
        letztes = max(k[2] for k in vorhanden)
        seit = (date.fromisoformat(letztes) - timedelta(days=10)).isoformat()
    else:
        seit = START
    jahr, monat = int(seit[:4]), int(seit[5:7])
    varianten = [("date >= TIMESTAMP '%s 00:00:00'" % seit, False),
                 ("date >= DATE '%s'" % seit, False),
                 ("year >= %d" % jahr, False),
                 ("year >= %d" % jahr, True),
                 ("1=1", True)]
    fehler = []
    daten = None
    for where, schlank in varianten:
        try:
            daten = _abfrage(where, schlank)
            break
        except AbrufFehler as e:
            fehler.append("[%s] %s" % (where, str(e)[:120]))
    letzter = AbrufFehler(" | ".join(fehler))
    if daten is None:
        raise letzter
    zeilen = []
    for a in daten:
        if not a.get("portname") or a.get("date") is None:
            continue
        for feld in WERTE:
            if a.get(feld) is not None:
                zeilen.append({"indicator": feld, "entity": a["portname"], "entity_type": "chokepoint",
                               "date": _datum(a["date"]), "value": fmt(a[feld])})
    if not zeilen:
        raise AbrufFehler("PortWatch lieferte keine Zeilen.")
    return zeilen, []
