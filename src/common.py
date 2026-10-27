"""Gemeinsame Hilfen: Pfade, Abruf mit Wiederholung und der CSV-Speicher."""
import csv
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
MANUELL = os.path.join(DATA, "manual")
DOCS_DATA = os.path.join(ROOT, "docs", "data")
FELDER = ["indicator", "entity", "entity_type", "date", "value"]
# Sekunden Pause zwischen Abrufen. Tests setzen WELTMODELL_PAUSE=0.
PAUSE = float(os.environ.get("WELTMODELL_PAUSE", "1"))


class AbrufFehler(Exception):
    """Eine Quelle hat nicht geantwortet oder etwas Unerwartetes geliefert."""


def jetzt():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt(wert):
    """Zahl als Text mit 10 gültigen Stellen, damit die CSV-Dateien kompakt bleiben."""
    return format(float(wert), ".10g")


def hole_json(url, versuche=3):
    letzter = None
    for i in range(versuche):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "weltmodell/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            letzter = e
            if i < versuche - 1:
                time.sleep(PAUSE * 3 * (i + 1))
    raise AbrufFehler("Abruf fehlgeschlagen: %s" % letzter)


def lies_csv(name):
    """Liest data/<name>.csv als Wörterbuch (Kennzahl, Einheit, Datum) -> Zeile."""
    pfad = os.path.join(DATA, name + ".csv")
    zeilen = {}
    if os.path.exists(pfad):
        with open(pfad, newline="", encoding="utf-8") as f:
            for z in csv.DictReader(f):
                zeilen[(z["indicator"], z["entity"], z["date"])] = z
    return zeilen


def upsert(name, neue):
    """Fügt Zeilen hinzu oder überschreibt gleiche. Gibt (geändert, gesamt) zurück.
    Die Datei ist sortiert, damit Änderungen in Git klein und lesbar bleiben."""
    bestehend = lies_csv(name)
    geaendert = 0
    for z in neue:
        z = {f: z[f] for f in FELDER}
        key = (z["indicator"], z["entity"], z["date"])
        if bestehend.get(key) != z:
            geaendert += 1
        bestehend[key] = z
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, name + ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FELDER, lineterminator="\n")
        w.writeheader()
        for k in sorted(bestehend):
            w.writerow(bestehend[k])
    return geaendert, len(bestehend)
