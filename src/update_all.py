#!/usr/bin/env python3
"""Holt neue Daten aus allen Quellen und baut die Webseiten-Daten neu.

Aufruf:   python src/update_all.py
Eine Quelle, die ausfällt, stoppt die anderen nicht. Der Lauf gilt nur dann als
Fehler (Exit-Code 1), wenn keine einzige Quelle Daten geliefert hat."""
import json
import os
import sys

from common import DATA, jetzt, lies_csv, upsert
import export
from sources import portwatch, worldbank

QUELLEN = [worldbank, portwatch]


def main():
    os.makedirs(DATA, exist_ok=True)
    status_pfad = os.path.join(DATA, "status.json")
    status = {}
    if os.path.exists(status_pfad):
        with open(status_pfad, encoding="utf-8") as f:
            status = json.load(f)

    erfolge = 0
    for q in QUELLEN:
        zeit = jetzt()
        print("== %s ==" % q.NAME)
        try:
            zeilen, warnungen = q.fetch(lies_csv(q.NAME))
            geaendert, gesamt = upsert(q.NAME, zeilen)
            status[q.NAME] = {"ok": True, "zeit": zeit, "neu_oder_geaendert": geaendert,
                              "zeilen_gesamt": gesamt, "warnungen": warnungen}
            erfolge += 1
            print("  %d Zeilen abgerufen, %d neu oder geändert, %d insgesamt." % (len(zeilen), geaendert, gesamt))
            for w in warnungen:
                print("  Warnung:", w)
        except Exception as e:      # bewusst breit: eine kaputte Quelle darf den Rest nicht stoppen
            status[q.NAME] = {**status.get(q.NAME, {}), "ok": False, "letzter_versuch": zeit,
                              "fehler": str(e)[:300]}
            print("  FEHLER:", e)

    with open(status_pfad, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=1)
    export.run()
    print("\nFertig. Erfolgreiche Quellen: %d von %d." % (erfolge, len(QUELLEN)))
    return 0 if erfolge else 1


if __name__ == "__main__":
    sys.exit(main())
