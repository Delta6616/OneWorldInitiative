"""Baut aus den CSV-Dateien eine SQLite-Datenbank und die JSON-Dateien für die Webseite.

Die Datenbank (data/weltmodell.db) wird bei jedem Lauf neu erzeugt und nicht in Git
gespeichert. Die CSV-Dateien sind die eigentliche, nachvollziehbare Ablage."""
import json
import os
import shutil
import sqlite3
from datetime import date, timedelta

from common import DATA, DOCS_DATA, MANUELL, jetzt, lies_csv
from kontinente import KONTINENT, NAMEN, kontinent_aus_text

QUELLEN = ["worldbank", "portwatch"]


def baue_db():
    pfad = os.path.join(DATA, "weltmodell.db")
    if os.path.exists(pfad):
        os.remove(pfad)
    con = sqlite3.connect(pfad)
    con.execute("CREATE TABLE beobachtung (quelle TEXT, indicator TEXT, entity TEXT, "
                "entity_type TEXT, date TEXT, value REAL)")
    con.execute("CREATE INDEX i_beob ON beobachtung (indicator, entity, date)")
    for q in QUELLEN:
        con.executemany("INSERT INTO beobachtung VALUES (?,?,?,?,?,?)",
                        [(q, z["indicator"], z["entity"], z["entity_type"], z["date"], float(z["value"]))
                         for z in lies_csv(q).values()])
    con.execute("CREATE TABLE land (iso3 TEXT PRIMARY KEY, kontinent TEXT)")
    con.executemany("INSERT INTO land VALUES (?,?)", sorted(KONTINENT.items()))
    con.commit()
    return con


def neueste(con, indikator):
    """Je Land der neueste vorhandene Wert: {iso3: (Jahr, Wert)}."""
    d = {}
    for e, dt, v in con.execute("SELECT entity, date, value FROM beobachtung "
                                "WHERE indicator=? AND entity_type='country' ORDER BY date", (indikator,)):
        d[e] = (dt, v)
    return d


def kontinent_kennzahlen(con):
    seed_pfad = os.path.join(MANUELL, "continents_seed.json")
    seed = {}
    if os.path.exists(seed_pfad):
        with open(seed_pfad, encoding="utf-8") as f:
            seed = json.load(f).get("kontinente", {})
    out = {k: dict(seed.get(k, {})) for k in NAMEN}
    for k in NAMEN:
        out[k]["abdeckung"] = {}

    gdp, pop = neueste(con, "NY.GDP.MKTP.CD"), neueste(con, "SP.POP.TOTL")
    ges_gdp = {k: sum(v for i, (_, v) in gdp.items() if KONTINENT[i] == k) for k in NAMEN}
    ges_pop = {k: sum(v for i, (_, v) in pop.items() if KONTINENT[i] == k) for k in NAMEN}
    for k in NAMEN:
        if ges_gdp[k]:
            out[k]["gdp"] = round(ges_gdp[k] / 1e9)
        if ges_pop[k]:
            out[k]["pop"] = round(ges_pop[k] / 1e6)

    def gewichtet(ind, gew, gesamt, cap=None):
        acc = {k: [0.0, 0.0] for k in NAMEN}
        for iso, (_, v) in neueste(con, ind).items():
            w = gew.get(iso, (None, 0))[1]
            if not w or w <= 0:
                continue
            if cap is not None:
                v = max(-cap, min(cap, v))
            k = KONTINENT[iso]
            acc[k][0] += v * w
            acc[k][1] += w
        return {k: (a[0] / a[1], a[1] / gesamt[k]) for k, a in acc.items() if a[1] > 0 and gesamt[k] > 0}

    # Feld, Weltbank-Kennzahl, Gewicht, Gesamtgewicht, Obergrenze gegen Ausreißer
    plan = [("wachstum", "NY.GDP.MKTP.KD.ZG", gdp, ges_gdp, None),
            ("inflation", "FP.CPI.TOTL.ZG", gdp, ges_gdp, 100),
            ("handel", "NE.TRD.GNFS.ZS", gdp, ges_gdp, None),
            ("schulden", "GC.DOD.TOTL.GD.ZS", gdp, ges_gdp, None),
            ("stab_roh", "PV.EST", pop, ges_pop, None),
            ("regierung", "GE.EST", pop, ges_pop, None)]
    for feld, ind, gew, gesamt, cap in plan:
        for k, (v, abd) in gewichtet(ind, gew, gesamt, cap).items():
            out[k][feld] = round(v, 2 if feld in ("stab_roh", "regierung") else 1)
            out[k]["abdeckung"][feld] = round(abd, 2)
    for k in NAMEN:
        if out[k].get("stab_roh") is not None:
            out[k]["stab"] = round((out[k]["stab_roh"] + 2.5) / 5 * 100)      # Skala -2,5..+2,5 auf 0..100
        if out[k].get("wachstum") is not None:
            out[k]["dyn"] = max(0, min(100, round((out[k]["wachstum"] + 2) / 8 * 100)))  # -2 %..+6 % auf 0..100
    bis = {}
    for ind in ("NY.GDP.MKTP.CD", "NY.GDP.MKTP.KD.ZG", "PV.EST"):
        r = con.execute("SELECT MAX(date) FROM beobachtung WHERE indicator=?", (ind,)).fetchone()[0]
        if r:
            bis[ind] = r
    return {"stand": jetzt(), "quelle": "Weltbank, neuester Wert je Land", "daten_bis": bis, "kontinente": out}


def meerengen(con):
    def reihe(ind):
        d = {}
        for e, dt, v in con.execute("SELECT entity, date, value FROM beobachtung WHERE indicator=? "
                                    "AND entity_type='chokepoint' ORDER BY entity, date", (ind,)):
            d.setdefault(e, []).append((date.fromisoformat(dt), v))
        return d

    def mittel(liste, von, bis):
        w = [v for d, v in liste if von < d <= bis]
        return sum(w) / len(w) if w else None

    total, tanker = reihe("n_total"), reihe("n_tanker")
    out = []
    for name, lst in total.items():
        ende = lst[-1][0]
        a7 = mittel(lst, ende - timedelta(days=7), ende)
        a90 = mittel(lst, ende - timedelta(days=97), ende - timedelta(days=7))
        t7 = mittel(tanker.get(name, []), ende - timedelta(days=7), ende)
        out.append({"name": name, "bis": ende.isoformat(), "tag7": round(a7, 1),
                    "tag90": round(a90, 1) if a90 is not None else None,
                    "aenderung": round(a7 / a90 - 1, 3) if a90 else None,
                    "tanker7": round(t7, 1) if t7 is not None else None,
                    "verlauf": [round(v) for _, v in lst[-60:]]})
    out.sort(key=lambda x: -(x["tag90"] or x["tag7"] or 0))
    return {"stand": jetzt(), "quelle": "IMF PortWatch (UN Global Platform)", "engstellen": out}


def meldungen(tage=5, je_thema_und_tag=10):
    """Aktuelle Schlagzeilen aus GDELT, neueste zuerst, je Thema und Tag begrenzt, Duplikate entfernt."""
    seit = (date.today() - timedelta(days=tage)).isoformat()
    roh = [z for z in lies_csv("gdelt").values() if z["date"] >= seit]
    roh.sort(key=lambda z: (z["date"], z["entity"]), reverse=True)
    gesehen, je, dom, out = set(), {}, {}, []
    for z in roh:
        titel = z["value"]
        schl = "".join(ch for ch in titel.lower() if ch.isalnum())[:60]
        host = z["entity"].split("/")[2].replace("www.", "") if z["entity"].count("/") >= 2 else ""
        if schl in gesehen or je.get((z["indicator"], z["date"]), 0) >= je_thema_und_tag or dom.get((z["indicator"], host), 0) >= 3:
            continue
        gesehen.add(schl)
        je[(z["indicator"], z["date"])] = je.get((z["indicator"], z["date"]), 0) + 1
        dom[(z["indicator"], host)] = dom.get((z["indicator"], host), 0) + 1
        out.append({"t": titel, "u": z["entity"], "d": z["date"], "q": host, "type": z["indicator"],
                    "c": kontinent_aus_text(titel)})
    out.sort(key=lambda x: x["d"], reverse=True)
    return {"stand": jetzt(), "quelle": "GDELT Project (gdeltproject.org)",
            "hinweis": "Automatisch gesammelte Schlagzeilen, ungeprüft. Thema und Kontinent werden aus Suchbegriffen und Stichwörtern im Titel abgeleitet und können danebenliegen.",
            "items": out}


def anstiege(reihe, tage=30):
    """Alle Preisanstiege (nur positive) ueber je 'tage' Tage in einer sortierten Reihe [(Datum, Wert)]."""
    import bisect
    tage_liste = [d for d, _ in reihe]
    out = []
    for d, v in reihe:
        ziel = (date.fromisoformat(d) - timedelta(days=tage)).isoformat()
        i = bisect.bisect_right(tage_liste, ziel) - 1
        if i < 0:
            continue
        alt = reihe[i][1]
        if alt > 0 and v > alt:
            out.append(v / alt - 1)
    return sorted(out)


def perzentil(sortiert, p):
    """Wert am p-ten Prozent (0 bis 100) einer sortierten Liste."""
    if not sortiert:
        return None
    pos = p / 100 * (len(sortiert) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sortiert) - 1)
    return sortiert[lo] + (sortiert[hi] - sortiert[lo]) * (pos - lo)


def preise():
    """Rohstoffpreise: letzter Wert, Veraenderung gegen etwa 30 Tage und 12 Monate vorher, Verlauf."""
    from sources.rohstoffe import REIHEN
    je = {}
    for z in lies_csv("rohstoffe").values():
        je.setdefault(z["indicator"], []).append((z["date"], float(z["value"])))
    out = []
    for kennung, (name, einheit, takt, typ, gruppe, leit) in REIHEN.items():
        reihe = sorted(je.get(kennung, []))
        if not reihe:
            continue
        tag, letzter = reihe[-1]

        def davor(tage):
            ziel = (date.fromisoformat(tag) - timedelta(days=tage)).isoformat()
            alt = [v for d, v in reihe if d <= ziel]
            return alt[-1] if alt else None
        a30, a365 = davor(30), davor(365)
        # Massstab fuer die Simulation: Schweregrad s (5..100) = s-tes Perzentil aller 30-Tage-Anstiege seit 2020
        ans = anstiege(reihe)
        stufen = [round(perzentil(ans, s), 3) for s in range(5, 101, 5)] if len(ans) >= 20 else []
        aktuell = letzter / a30 - 1 if a30 else None
        lage = 0
        if stufen and aktuell and aktuell > 0:
            lage = round(100 * sum(1 for x in ans if x <= aktuell) / len(ans))
        # Verlauf: bei taeglichen Reihen die letzten 90 Tage, bei monatlichen die letzten 24 Monate
        verlauf = [v for d, v in reihe[-(90 if takt == "täglich" else 24):]]
        out.append({"id": kennung, "name": name, "einheit": einheit, "takt": takt, "type": typ,
                    "gruppe": gruppe, "leit": leit,
                    "wert": round(letzter, 2), "datum": tag,
                    "d30": round(letzter / a30 - 1, 3) if a30 else None,
                    "d365": round(letzter / a365 - 1, 3) if a365 else None,
                    "verlauf": [round(v, 2) for v in verlauf],
                    "stufen": stufen, "lage": lage})
    return {"stand": jetzt(), "quelle": "FRED, Federal Reserve Bank of St. Louis (Daten von EIA und IWF)", "preise": out}


def schreibe(name, inhalt):
    with open(os.path.join(DOCS_DATA, name), "w", encoding="utf-8") as f:
        json.dump(inhalt, f, ensure_ascii=False, indent=1)


def run():
    os.makedirs(DOCS_DATA, exist_ok=True)
    con = baue_db()
    schreibe("continents.json", kontinent_kennzahlen(con))
    schreibe("chokepoints.json", meerengen(con))
    schreibe("news.json", meldungen())
    schreibe("prices.json", preise())
    con.close()
    for n in ("flows.json", "events.json"):                # von Hand gepflegte Dateien
        quelle = os.path.join(MANUELL, n)
        if os.path.exists(quelle):
            shutil.copyfile(quelle, os.path.join(DOCS_DATA, n))
    status = os.path.join(DATA, "status.json")
    if os.path.exists(status):
        shutil.copyfile(status, os.path.join(DOCS_DATA, "status.json"))
