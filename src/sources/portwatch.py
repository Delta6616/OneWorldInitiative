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


def _abfrage(where):
    zeilen, offset = [], 0
    while True:
        qs = urllib.parse.urlencode({
            "where": where, "outFields": "date,portname," + ",".join(WERTE),
            "orderByFields": "date,portid", "resultOffset": offset, "resultRecordCount": 2000,
            "returnGeometry": "false", "f": "json"})
        a = hole_json(BASIS + "?" + qs)
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
    varianten = ["date >= TIMESTAMP '%s 00:00:00'" % seit, "date >= '%s'" % seit]
    letzter = AbrufFehler("keine Abfrage versucht")
    daten = None
    for where in varianten:
        try:
            daten = _abfrage(where)
            break
        except AbrufFehler as e:
            letzter = e
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
