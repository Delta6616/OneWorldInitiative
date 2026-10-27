"""IMF PortWatch: tägliche Schiffsdurchfahrten an 28 Meerengen und Kanälen
(zum Beispiel Suez, Panama, Hormus). Quelle: UN Global Platform, IMF PortWatch.

Gespeichert werden je Engstelle und Tag die Zahl aller Schiffe, der Tanker und der
Containerschiffe, ab Anfang 2024."""
import csv
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

from common import AbrufFehler, PAUSE, fmt, hole_json

NAME = "portwatch"
# Mehrere Schreibweisen der Adresse; die erste, die funktioniert, wird genommen.
BASEN = [
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query",
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query",
]
UAS = ["Mozilla/5.0 (compatible; weltmodell/1.0)"]
BASIS = BASEN[0]
WERTE = ["n_total", "n_tanker", "n_container"]
START = "2024-01-01"


def _datum(w):
    if isinstance(w, (int, float)):       # ArcGIS liefert Datumsangaben als Millisekunden seit 1970
        return datetime.fromtimestamp(w / 1000, timezone.utc).strftime("%Y-%m-%d")
    return str(w)[:10].replace("/", "-")


def _roh(url, ua):
    """Einfacher Abruf, ohne zusaetzliche Kopfzeilen. Liefert den Text der Antwort."""
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read().decode("utf-8-sig", "replace")
    except (urllib.error.URLError, TimeoutError) as e:
        raise AbrufFehler("Abruf fehlgeschlagen: %s" % e)


# Direkter Datei-Download des Datensatzes (Hub-Schnittstelle), als Ausweichweg.
CSV_URLS = [
    "https://portwatch.imf.org/api/download/v1/items/3da2b9ca97684916b75c4013f95d18ab/csv?layers=0",
    "https://www.arcgis.com/sharing/rest/content/items/3da2b9ca97684916b75c4013f95d18ab/data",
]


def _csv_abruf():
    fehler = []
    for url in CSV_URLS:
        try:
            text = _roh(url, UAS[0])
            kopf = text[:300].lstrip()
            if kopf.startswith("{") or kopf.startswith("<"):
                raise AbrufFehler("keine CSV-Datei: %s" % kopf[:60].replace("\n", " "))
            zeilen = [{(k or "").strip().lower(): v for k, v in z.items()}
                      for z in csv.DictReader(io.StringIO(text))]
            if zeilen:
                return zeilen, fehler
            raise AbrufFehler("leere Datei")
        except AbrufFehler as e:
            fehler.append("CSV %s: %s" % (url.split("/")[2], str(e)[:60]))
    return None, fehler


def _abfrage(where, schlank=False, basis=None, ua=None):
    zeilen, offset = [], 0
    while True:
        par = {"where": where, "outFields": "date,portname," + ",".join(WERTE),
               "resultOffset": offset, "resultRecordCount": 1000,
               "returnGeometry": "false", "f": "json"}
        if schlank:     # Notloesung: ohne Sortierung und mit Minimal-Parametern
            par = {"where": where, "outFields": "*", "f": "json"}
            if offset:
                par["resultOffset"] = offset
        else:
            par["orderByFields"] = "date ASC"
        try:
            a = json.loads(_roh((basis or BASIS) + "?" + urllib.parse.urlencode(par, quote_via=urllib.parse.quote),
                                ua or UAS[0]))
        except ValueError:
            raise AbrufFehler("keine gueltige JSON-Antwort")
        if not isinstance(a, dict) or "error" in a:
            raise AbrufFehler("PortWatch meldet: %s" % str(a)[:200])
        feats = a.get("features") or []
        zeilen.extend({k.lower(): v for k, v in f["attributes"].items()} for f in feats)
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
    jahr = int(seit[:4])
    # Von einfach zu genau; eine Variante zaehlt nur, wenn sie wirklich Zeilen ab "seit" liefert.
    varianten = [("1=1", True), ("year >= %d" % jahr, True),
                 ("year >= %d" % jahr, False), ("date >= TIMESTAMP '%s 00:00:00'" % seit, False)]
    fehler = []
    for where, schlank in varianten:
        for basis in BASEN:
            for ua in UAS:
                kurz = "%s | %s | %s" % (where, "ArcGIS" if "/ArcGIS/" in basis else "arcgis",
                                         "Layer0" if "/0/query" in basis else "ohneLayer")
                try:
                    daten = _abfrage(where, schlank, basis, ua)
                except AbrufFehler as e:
                    fehler.append("%s: %s" % (kurz.replace(" | ", "/"), str(e).replace("PortWatch meldet: {'error': ", "")[:45]))
                    continue
                zeilen = _umformen(daten, seit)
                if zeilen:
                    return zeilen, []
                schluessel = sorted(daten[0].keys())[:8] if daten else []
                fehler.append("%s: %d Datensaetze, 0 brauchbar, Felder %s" % (kurz.replace(" | ", "/"), len(daten), schluessel))
                break   # Adresse funktioniert, andere Kennung bringt nichts
    daten, csv_fehler = _csv_abruf()
    fehler.extend(csv_fehler)
    if daten:
        zeilen = _umformen(daten, seit)
        if zeilen:
            return zeilen, []
        fehler.append("CSV: %d Zeilen, 0 brauchbar, Felder %s" % (len(daten), sorted(daten[0])[:8]))
    raise AbrufFehler(" ## ".join(fehler))


def _umformen(daten, seit):
    zeilen = []
    for a in daten:
        if not a.get("portname") or a.get("date") is None:
            continue
        tag = _datum(a["date"])
        if tag < seit:
            continue
        for feld in WERTE:
            if a.get(feld) is not None:
                zeilen.append({"indicator": feld, "entity": a["portname"], "entity_type": "chokepoint",
                               "date": tag, "value": fmt(a[feld])})
    return zeilen
